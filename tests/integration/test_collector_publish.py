import json  # Serialize/deserialize the pulled Pub/Sub message payload for assertions
import os  # Read PUBSUB_EMULATOR_HOST to detect whether the emulator is configured
from pathlib import Path  # Cross-platform path handling for locating the fixtures directory

import pytest  # Testing framework
from google.cloud import pubsub_v1  # GCP Pub/Sub client library (talks to the emulator when PUBSUB_EMULATOR_HOST is set)

from ingest.collectors.bmrs.client import BASE_URL  # Base URL used to build the mocked BMRS API endpoints
from ingest.collectors.bmrs.collector import publish_settlement_date  # Module under test: polls, normalizes, publishes/DLQs
from ingest.contracts.pubsub_setup import (  # Task 2's Pub/Sub resource constants and idempotent setup function
    MAIN_SUBSCRIPTION,  # Name of the main Beam-consumed subscription, used to pull back published messages
    PROJECT_ID,  # Emulator/local project ID used to build resource paths
    ensure_schema_and_topics,  # Creates the schema, topics, and subscriptions before the test runs
)

pytestmark = pytest.mark.skipif(  # Skip this whole module unless the emulator env var is set
    "PUBSUB_EMULATOR_HOST" not in os.environ,  # Condition: emulator host not configured in this environment
    reason="requires the Pub/Sub emulator (make up)",  # Explanation shown in skip report
)

FIXTURES = Path(__file__).parents[1] / "fixtures"  # tests/fixtures directory, one level up from tests/integration


def _load_fixture(name: str) -> dict:  # Helper to load a JSON fixture file by name
    return json.loads((FIXTURES / name).read_text())  # Read the file and parse it as JSON into a dict


@pytest.fixture
def pubsub_clients():  # Fixture providing a publisher and subscriber wired against the emulator, resources pre-created
    publisher = pubsub_v1.PublisherClient()  # Client for topic operations against the emulator
    subscriber = pubsub_v1.SubscriberClient()  # Client for subscription operations against the emulator
    ensure_schema_and_topics(publisher=publisher, subscriber=subscriber)  # Idempotently create schema/topics/subscriptions
    yield publisher, subscriber  # Hand both clients to the test


def test_publish_settlement_date_routes_good_and_bad_periods(requests_mock, pubsub_clients):  # End-to-end: one good period, one bad period
    publisher, subscriber = pubsub_clients  # Unpack the fixture's publisher/subscriber clients
    valid = _load_fixture("bmrs_response_valid.json")  # Well-formed BMRS response for settlement period 1
    malformed = _load_fixture("bmrs_response_malformed.json")  # Response missing a required field (systemSellPrice) for period 2

    requests_mock.get(  # Stub the BMRS API call for settlement period 1 to return the valid fixture
        f"{BASE_URL}/balancing/settlement/system-prices/2026-08-10/1", json=valid
    )
    requests_mock.get(  # Stub the BMRS API call for settlement period 2 to return the malformed fixture
        f"{BASE_URL}/balancing/settlement/system-prices/2026-08-10/2", json=malformed
    )

    counts = publish_settlement_date("2026-08-10", publisher=publisher, periods=range(1, 3))  # Run the collector over periods 1-2 only
    assert counts == {"published": 1, "dead_lettered": 1, "skipped": 0}  # Period 1 publishes, period 2 is dead-lettered, none skipped

    subscription_path = subscriber.subscription_path(PROJECT_ID, MAIN_SUBSCRIPTION)  # Fully-qualified main subscription resource path
    response = subscriber.pull(  # Pull back whatever landed on the main (non-DLQ) subscription
        request={"subscription": subscription_path, "max_messages": 5}, timeout=5
    )
    assert len(response.received_messages) == 1  # Only the one successfully-published record should be on the main topic
    published = json.loads(response.received_messages[0].message.data)  # Decode the published message body back into a dict
    assert published["settlement_period"] == 1  # Confirm it's the record from the valid (period 1) fixture
    ack_ids = [m.ack_id for m in response.received_messages]  # Collect ack IDs so the pulled message doesn't get redelivered
    subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": ack_ids})  # Acknowledge to clean up subscription state
