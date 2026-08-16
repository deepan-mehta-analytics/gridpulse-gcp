"""Creates the BMRS bronze Pub/Sub topics, schema, and dead-lettered
subscriptions against the Pub/Sub emulator. Idempotent — safe to re-run.
"""
import os  # Read GCP_PROJECT_ID env var (falls back to a local-only default)
from pathlib import Path  # Cross-platform path handling for locating the Avro schema file

from google.api_core.exceptions import AlreadyExists  # Raised when a topic/subscription/schema already exists — the idempotency signal
from google.cloud import pubsub_v1  # GCP Pub/Sub client library (talks to the emulator when PUBSUB_EMULATOR_HOST is set)
from google.pubsub_v1.types import Encoding, Schema  # Types needed to build schema-service and topic schema_settings requests

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "gridpulse-local")  # Emulator/local project ID; real GCP project overrides via env var
SCHEMA_PATH = Path(__file__).parent / "bmrs_bronze_v1.avsc"  # Task 1's Avro contract file, read by path from this same package
SCHEMA_ID = "bmrs-bronze-v1"  # Pub/Sub schema resource ID registered with the schema service
MAIN_TOPIC = "bmrs-bronze"  # Main ingest topic collectors publish bronze records to
DLQ_TOPIC = "bmrs-bronze-dlq"  # Dead-letter topic that receives messages the main subscription can't deliver
MAIN_SUBSCRIPTION = "bmrs-bronze-beam"  # Pull subscription Beam consumes from, with a dead-letter policy attached
DLQ_SUBSCRIPTION = "bmrs-bronze-dlq-replay"  # Plain pull subscription on the DLQ topic, used for manual replay/inspection
MAX_DELIVERY_ATTEMPTS = 5  # Number of delivery attempts before a message is routed to the DLQ


def ensure_schema_and_topics(schema_client=None, publisher=None, subscriber=None) -> bool:
    """Create the Avro schema, main topic, DLQ topic, and both
    subscriptions (main, with a dead-letter policy pointing at the DLQ
    topic; and a plain pull subscription on the DLQ topic for replay).

    Returns True if the emulator accepted native schema enforcement on
    the main topic, False if it fell back to an unenforced topic. See
    this module's known limitation below — either outcome is handled.
    """
    schema_client = schema_client or pubsub_v1.SchemaServiceClient()  # Use injected client (tests) or construct a real one
    publisher = publisher or pubsub_v1.PublisherClient()  # Use injected client (tests) or construct a real one
    subscriber = subscriber or pubsub_v1.SubscriberClient()  # Use injected client (tests) or construct a real one

    schema_definition = SCHEMA_PATH.read_text()  # Load the raw Avro schema JSON text from Task 1's contract file
    schema_path = schema_client.schema_path(PROJECT_ID, SCHEMA_ID)  # Fully-qualified schema resource path for this project
    schema_enforced = True  # Optimistically assume native schema enforcement will succeed; flipped to False on failure below
    try:
        schema_client.create_schema(  # Register the Avro schema with the Pub/Sub schema service
            request={
                "parent": f"projects/{PROJECT_ID}",  # Parent project resource under which the schema is created
                "schema_id": SCHEMA_ID,  # Resource ID to assign the new schema
                "schema": Schema(  # Schema payload: type and raw definition text
                    name=schema_path, type_=Schema.Type.AVRO, definition=schema_definition  # Avro schema, definition loaded from bmrs_bronze_v1.avsc
                ),
            }
        )
    except AlreadyExists:  # Schema already registered from a prior run — idempotent no-op
        pass
    except Exception as exc:  # noqa: BLE001  # Broad catch is intentional: emulator schema-service support is unverified (see module docstring)
        # Known limitation: the Pub/Sub emulator's schema-service support
        # has historically been incomplete (Google issue tracker #228984312).
        # Fall back to an unenforced topic rather than blocking local dev —
        # the same Avro schema still validates client-side in the collector
        # (fastavro), so message shape is still checked, just not by
        # Pub/Sub itself locally. Real GCP Pub/Sub (make cloud-up) enforces
        # it natively.
        schema_enforced = False  # Record that native enforcement is unavailable in this environment
        print(  # Surface which branch fired — real information about this environment, not noise
            f"Pub/Sub emulator rejected schema creation ({exc!r}); "  # Include the actual exception for diagnosability
            "falling back to client-side-only validation for local dev."
        )

    dlq_topic_path = publisher.topic_path(PROJECT_ID, DLQ_TOPIC)  # Fully-qualified DLQ topic resource path
    try:
        publisher.create_topic(request={"name": dlq_topic_path})  # Create the DLQ topic (no schema enforcement needed on it)
    except AlreadyExists:  # DLQ topic already exists from a prior run — idempotent no-op
        pass

    main_topic_path = publisher.topic_path(PROJECT_ID, MAIN_TOPIC)  # Fully-qualified main topic resource path
    topic_request = {"name": main_topic_path}  # Base topic-creation request, extended below if schema enforcement is available
    if schema_enforced:  # Only attach schema_settings when the schema service actually accepted the schema
        topic_request["schema_settings"] = {"schema": schema_path, "encoding": Encoding.JSON}  # Enforce the Avro schema on this topic, JSON wire encoding
    try:
        publisher.create_topic(request=topic_request)  # Create the main bronze topic, with or without schema enforcement
    except AlreadyExists:  # Main topic already exists from a prior run — idempotent no-op
        pass

    main_sub_path = subscriber.subscription_path(PROJECT_ID, MAIN_SUBSCRIPTION)  # Fully-qualified main subscription resource path
    try:
        subscriber.create_subscription(  # Create the Beam-consumed pull subscription with a dead-letter policy
            request={
                "name": main_sub_path,  # Subscription resource name
                "topic": main_topic_path,  # Subscribes to the main bronze topic
                "dead_letter_policy": {  # Route repeatedly-failing messages to the DLQ topic
                    "dead_letter_topic": dlq_topic_path,  # DLQ topic that receives undeliverable messages
                    "max_delivery_attempts": MAX_DELIVERY_ATTEMPTS,  # Attempts before a message is dead-lettered
                },
            }
        )
    except AlreadyExists:  # Main subscription already exists from a prior run — idempotent no-op
        pass

    dlq_sub_path = subscriber.subscription_path(PROJECT_ID, DLQ_SUBSCRIPTION)  # Fully-qualified DLQ replay subscription resource path
    try:
        subscriber.create_subscription(request={"name": dlq_sub_path, "topic": dlq_topic_path})  # Plain pull subscription on the DLQ topic for manual replay
    except AlreadyExists:  # DLQ replay subscription already exists from a prior run — idempotent no-op
        pass

    return schema_enforced  # Report which branch fired to the caller (True = native enforcement, False = client-side-only fallback)
