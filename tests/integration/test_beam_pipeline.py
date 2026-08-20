# Integration test: publishes one bronze record to the Pub/Sub emulator,
# pulls it back with the pipeline's own pull helper, runs the Beam
# pipeline against it, and asserts the windowed output actually landed
# as an Avro object in MinIO. Requires both live local services.
import os  # Read PUBSUB_EMULATOR_HOST / MinIO credential env vars

import boto3  # AWS SDK — used here as the S3-compatible client against local MinIO
import pytest  # Test framework: fixtures, skipif marker
from apache_beam.options.pipeline_options import PipelineOptions  # Beam pipeline configuration, including the S3 filesystem flags
from google.cloud import pubsub_v1  # GCP Pub/Sub client library (talks to the emulator when PUBSUB_EMULATOR_HOST is set)

from ingest.collectors.bmrs.collector import _avro_json_body, _schema  # Reuse Task 5's Avro-JSON union encoder — the emulator enforces the schema, so bare non-null values in nullable fields (e.g. replacement_price) are rejected otherwise
from ingest.contracts.pubsub_setup import MAIN_SUBSCRIPTION, PROJECT_ID, ensure_schema_and_topics  # Task 2's resource constants + idempotent setup function
from transform.beam.bmrs_windowing_pipeline import build_pipeline, pull_available_messages  # This task's own pipeline-building and pull functions

pytestmark = pytest.mark.skipif(  # Skip the whole module when the emulator isn't configured, matching this repo's existing integration-test pattern
    "PUBSUB_EMULATOR_HOST" not in os.environ,
    reason="requires the Pub/Sub emulator and MinIO (make up)",
)

BUCKET = "gridpulse-bronze-test"  # Dedicated test bucket in the local MinIO instance, separate from the real bronze bucket


@pytest.fixture
def s3_client():  # Fixture: a boto3 S3 client pointed at local MinIO, with the test bucket ensured to exist
    client = boto3.client(  # Construct an S3-compatible client against the local MinIO endpoint
        "s3",
        endpoint_url="http://localhost:9000",  # MinIO's S3 API port, per docker-compose.yml
        aws_access_key_id=os.environ.get("MINIO_ACCESS_KEY", "gridpulse"),  # Local-only credential, falls back to compose default
        aws_secret_access_key=os.environ.get("MINIO_SECRET_KEY", "gridpulse_local_minio"),  # Local-only credential, falls back to compose default
    )
    try:
        client.create_bucket(Bucket=BUCKET)  # Idempotently ensure the test bucket exists
    except client.exceptions.BucketAlreadyOwnedByYou:  # Bucket already created by a prior test run — fine, not an error
        pass
    return client  # Hand the ready client to the test


def test_pipeline_windows_and_writes_bronze_to_minio(s3_client):
    publisher = pubsub_v1.PublisherClient()  # Emulator-backed publisher client (PUBSUB_EMULATOR_HOST routes it there)
    subscriber = pubsub_v1.SubscriberClient()  # Emulator-backed subscriber client
    ensure_schema_and_topics(publisher=publisher, subscriber=subscriber)  # Idempotently ensure topics/subscriptions exist before publishing

    record = {  # One valid bronze record matching bmrs_bronze_v1.avsc, Avro-JSON-encoded below before publish
        "schema_version": 1, "source_dataset": "DISEBSP",
        "settlement_date": "2026-08-10", "settlement_period": 1,
        "start_time": "2026-08-09T23:00:00Z", "created_date_time": "2026-08-10T23:44:25Z",
        "system_sell_price": 97.71, "system_buy_price": 97.71, "bsad_defaulted": False,
        "price_derivation_code": "N", "reserve_scarcity_price": 0.0,
        "net_imbalance_volume": -99.15, "sell_price_adjustment": 0.0, "buy_price_adjustment": 0.0,
        "replacement_price": 97.76, "replacement_price_reference_volume": 1.0,
        "total_accepted_offer_volume": 593.26, "total_accepted_bid_volume": -809.81,
        "total_adjustment_sell_volume": 0.0, "total_adjustment_buy_volume": 117.5,
        "total_system_tagged_accepted_offer_volume": 593.26,
        "total_system_tagged_accepted_bid_volume": -808.81,
        "total_system_tagged_adjustment_sell_volume": None,
        "total_system_tagged_adjustment_buy_volume": 117.5,
        "ingested_at": "2026-08-16T12:00:00Z",
    }
    main_topic_path = publisher.topic_path(PROJECT_ID, "bmrs-bronze")  # Fully-qualified main topic resource path
    # This emulator run has schema enforcement active (ensure_schema_and_topics'
    # create_schema succeeded), so the topic validates published bytes against
    # the Avro-JSON encoding spec, not bare flat JSON — a bare non-null value in
    # a nullable union field (e.g. replacement_price: 97.76) is rejected with
    # "Could not parse message" unless wrapped as {"double": 97.76}. Same root
    # cause collector.py's _avro_json_body works around; reused here rather than
    # re-deriving the fix (see task-5-report.md for the original diagnosis).
    publisher.publish(main_topic_path, _avro_json_body(record, _schema())).result(timeout=5)  # Publish the Avro-JSON-encoded record and block until the emulator confirms it

    subscription_path = subscriber.subscription_path(PROJECT_ID, MAIN_SUBSCRIPTION)  # Fully-qualified Beam-consumed subscription path
    messages = pull_available_messages(subscriber, subscription_path)  # Pull the just-published message back off the subscription
    assert len(messages) == 1  # Exactly the one record published above should be queued

    output_path = f"s3://{BUCKET}/bmrs/test-run/part"  # Bronze output prefix inside the local MinIO test bucket
    pipeline_options = PipelineOptions([  # Beam S3 filesystem flags pointing the AWS connector at local MinIO, not real AWS
        "--s3_endpoint_url=http://localhost:9000",
        f"--s3_access_key_id={os.environ.get('MINIO_ACCESS_KEY', 'gridpulse')}",
        f"--s3_secret_access_key={os.environ.get('MINIO_SECRET_KEY', 'gridpulse_local_minio')}",
        "--s3_disable_ssl",
    ])
    pipeline = build_pipeline(pipeline_options, output_path, messages)  # Build the windowing pipeline over the pulled messages
    pipeline.run().wait_until_finish()  # Execute it synchronously (DirectRunner) and wait for completion

    objects = s3_client.list_objects_v2(Bucket=BUCKET, Prefix="bmrs/test-run/")  # List whatever the pipeline wrote under the test prefix
    assert objects.get("KeyCount", 0) > 0  # At least one Avro shard should have landed in MinIO
