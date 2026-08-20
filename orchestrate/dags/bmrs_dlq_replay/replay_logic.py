"""Pure Pub/Sub replay logic for the bmrs-bronze-dlq topic — no Airflow
import here, so it's unit-testable without installing apache-airflow.
The thin DAG wrapper (../bmrs_dlq_replay_dag.py) is the only file that
imports Airflow, and only runs inside the Airflow container.

Scope gap (pre-flight ruling, T5/T8 DLQ envelope mismatch): this replay
assumes messages on the DLQ replay subscription are already flat bronze
records — true for messages Pub/Sub itself dead-lettered after exceeding
MAX_DELIVERY_ATTEMPTS on the main subscription, but NOT true for the 3
collector-side diagnostic error-envelope shapes Task 5 publishes directly
to the DLQ on API/normalization/schema-validation failures. Per-error-type
envelope unwrapping is out of scope for this task; do not build it here.
"""
from __future__ import annotations  # Allow forward-referenced type hints without runtime evaluation cost

from google.cloud import pubsub_v1  # GCP Pub/Sub client library — only used here for type hints on injected clients

from ingest.contracts.pubsub_setup import DLQ_SUBSCRIPTION, MAIN_TOPIC, PROJECT_ID  # Shared topic/subscription/project constants from Task 2


def replay_dlq_messages(
    *,
    subscriber: pubsub_v1.SubscriberClient,  # Injected Pub/Sub subscriber client (real or mocked)
    publisher: pubsub_v1.PublisherClient,  # Injected Pub/Sub publisher client (real or mocked)
    max_messages: int = 100,  # Upper bound on messages pulled per invocation
) -> int:
    """Re-publishes up to max_messages currently queued on the DLQ replay
    subscription back onto the main topic, then acks them off the DLQ.
    Returns the number replayed. Manual trigger for Phase 1 — no
    auto-replay schedule."""
    subscription_path = subscriber.subscription_path(PROJECT_ID, DLQ_SUBSCRIPTION)  # Build the fully-qualified DLQ replay subscription resource path
    main_topic_path = publisher.topic_path(PROJECT_ID, MAIN_TOPIC)  # Build the fully-qualified main bronze topic resource path

    response = subscriber.pull(
        request={"subscription": subscription_path, "max_messages": max_messages}, timeout=10
    )  # Pull up to max_messages currently sitting on the DLQ replay subscription
    if not response.received_messages:  # Nothing to replay
        return 0  # Short-circuit: no publish, no acknowledge, zero replayed

    for received in response.received_messages:  # Republish each pulled message's raw payload, unchanged
        publisher.publish(main_topic_path, received.message.data)  # Re-publish the exact bytes onto the main topic

    ack_ids = [m.ack_id for m in response.received_messages]  # Collect ack IDs for every message just republished
    subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": ack_ids})  # Ack them off the DLQ so they aren't replayed again
    return len(response.received_messages)  # Report how many messages were replayed
