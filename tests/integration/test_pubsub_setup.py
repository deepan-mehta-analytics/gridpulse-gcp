import os  # Access environment variables to detect whether the Pub/Sub emulator is configured

import pytest  # Testing framework
from google.cloud import pubsub_v1  # GCP Pub/Sub client library (talks to the emulator when PUBSUB_EMULATOR_HOST is set)

from ingest.contracts.pubsub_setup import (  # Import the module under test — constants and the setup function
    DLQ_SUBSCRIPTION,  # Name of the DLQ replay pull subscription
    DLQ_TOPIC,  # Name of the dead-letter topic
    MAIN_SUBSCRIPTION,  # Name of the main Beam-consumed subscription
    MAIN_TOPIC,  # Name of the main bronze ingest topic
    PROJECT_ID,  # Emulator/local project ID used to build resource paths
    ensure_schema_and_topics,  # Function under test: creates schema, topics, and subscriptions idempotently
)

pytestmark = pytest.mark.skipif(  # Skip this whole module unless the emulator env var is set
    "PUBSUB_EMULATOR_HOST" not in os.environ,  # Condition: emulator host not configured in this environment
    reason="requires the Pub/Sub emulator (make up)",  # Explanation shown in skip report
)


def test_ensure_schema_and_topics_creates_expected_resources():  # Verifies topics + subscriptions exist and setup is idempotent
    publisher = pubsub_v1.PublisherClient()  # Client for topic operations against the emulator
    subscriber = pubsub_v1.SubscriberClient()  # Client for subscription operations against the emulator

    ensure_schema_and_topics(publisher=publisher, subscriber=subscriber)  # First run: creates all resources
    ensure_schema_and_topics(publisher=publisher, subscriber=subscriber)  # Second run: must not raise (idempotency)

    topics = {  # Build a set of all topic resource names currently in the emulator project
        t.name for t in publisher.list_topics(request={"project": f"projects/{PROJECT_ID}"})  # List all topics for this project
    }
    assert publisher.topic_path(PROJECT_ID, MAIN_TOPIC) in topics  # Main bronze topic must exist
    assert publisher.topic_path(PROJECT_ID, DLQ_TOPIC) in topics  # DLQ topic must exist

    subs = {  # Build a set of all subscription resource names currently in the emulator project
        s.name
        for s in subscriber.list_subscriptions(request={"project": f"projects/{PROJECT_ID}"})  # List all subscriptions for this project
    }
    assert subscriber.subscription_path(PROJECT_ID, MAIN_SUBSCRIPTION) in subs  # Main Beam-consumed subscription must exist
    assert subscriber.subscription_path(PROJECT_ID, DLQ_SUBSCRIPTION) in subs  # DLQ replay subscription must exist


def test_schema_enforcement_status_is_reported():  # Verifies ensure_schema_and_topics reports which enforcement branch fired
    publisher = pubsub_v1.PublisherClient()  # Client for topic operations against the emulator
    subscriber = pubsub_v1.SubscriberClient()  # Client for subscription operations against the emulator
    schema_client = pubsub_v1.SchemaServiceClient()  # Client for schema-service operations against the emulator

    # Intentionally permissive: whether the emulator accepts native Avro
    # schema enforcement is unverified (see plan's "Verified-at-design-time
    # facts" §2) — either outcome is valid, the collector validates
    # client-side regardless. This test documents whichever branch fires.
    enforced = ensure_schema_and_topics(  # Call setup with all three clients supplied, capture the enforcement result
        schema_client=schema_client, publisher=publisher, subscriber=subscriber  # Pass explicit clients rather than letting the function construct its own
    )
    assert isinstance(enforced, bool)  # Return value must always be a bool regardless of which branch fired
