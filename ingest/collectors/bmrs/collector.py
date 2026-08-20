"""BMRS collector entrypoint: polls Elexon Insights for one settlement
date's periods, normalizes results, validates against the bronze
contract, and publishes to Pub/Sub — malformed responses go straight to
the DLQ topic since they never reach a valid publish."""
from __future__ import annotations  # Enable postponed evaluation of type hints (Python 3.10+)

import json  # Serialize records/DLQ payloads to JSON bytes for Pub/Sub publish calls
import logging  # Structured logging for collector run diagnostics
import os  # Read BMRS_SETTLEMENT_DATE env var for the entrypoint's default run date
from datetime import date, timedelta  # Compute "yesterday" as the default settlement date

import fastavro  # Client-side Avro schema validation before publishing to the main topic
from google.cloud import pubsub_v1  # GCP Pub/Sub client library (talks to the emulator when PUBSUB_EMULATOR_HOST is set)

from ingest.collectors.bmrs.client import BmrsApiError, fetch_system_prices  # Task 3's BMRS HTTP client + its error type
from ingest.collectors.bmrs.normalize import NormalizationError, normalize_records  # Task 4's raw-to-bronze normalizer + its error type
from ingest.contracts.pubsub_setup import (  # Task 2's Pub/Sub resource constants and idempotent setup function
    DLQ_TOPIC,  # Name of the dead-letter topic failed records/records are routed to
    MAIN_TOPIC,  # Name of the main bronze ingest topic successful records are published to
    PROJECT_ID,  # Emulator/local project ID used to build resource paths
    SCHEMA_PATH,  # Path to the Avro bronze contract file, reused here for client-side validation
    ensure_schema_and_topics,  # Idempotently creates schema/topics/subscriptions before a real run
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")  # Configure root logger format/level for this process
logger = logging.getLogger("bmrs-collector")  # Named logger for this module's log records

SETTLEMENT_PERIODS_PER_DAY = 48  # A UK settlement day has 48 half-hour periods (49 on the extra clock-change day, still safe as a default range bound)


def _schema() -> dict:  # Load and parse the Avro bronze contract for client-side validation
    return json.loads(SCHEMA_PATH.read_text())  # Read the .avsc file text and parse it as JSON


def _avro_json_body(record: dict, schema: dict) -> bytes:
    """Encode a bronze record as Pub/Sub-compatible Avro-JSON bytes.

    Root cause this works around: when the main topic has schema_settings
    with JSON encoding attached (true both on real GCP Pub/Sub whenever a
    schema is registered, and on this emulator once schema creation
    succeeds — see pubsub_setup.py's known-limitation note), Pub/Sub
    validates published bytes against the Avro JSON Encoding spec, not
    against plain flat JSON. For a nullable union field (e.g. ["null",
    "double"]), that spec requires non-null values to be wrapped as
    {"double": value} rather than a bare value — fastavro's own
    client-side validate() accepts plain Python values either way, so a
    record can pass that check yet still be rejected by Pub/Sub itself,
    with the failure surfacing only on the unfetched publish() Future —
    see .superpowers/sdd/2026-08-16-gridpulse-phase1-stream-ingest/
    task-5-report.md for how this was diagnosed."""
    encoded = dict(record)  # Shallow copy so we don't mutate the caller's record dict
    for field in schema["fields"]:  # Walk each field definition in the Avro schema
        field_type = field["type"]  # This field's declared Avro type (a union list for nullable fields)
        if isinstance(field_type, list) and "null" in field_type:  # Only nullable union fields need wrapping
            value = encoded.get(field["name"])  # Current value for this field in the record
            if value is not None:  # Avro-JSON only wraps the non-null branch; null stays bare null
                other_type = next(t for t in field_type if t != "null")  # The union's non-null branch, e.g. "double"
                encoded[field["name"]] = {other_type: value}  # Avro-JSON union encoding: {"double": value}
    return json.dumps(encoded).encode("utf-8")  # Serialize the Avro-JSON-compliant dict to bytes for Pub/Sub


def publish_settlement_date(
    settlement_date: str,  # The BMRS settlement date to poll, format yyyy-MM-dd
    *,
    publisher: pubsub_v1.PublisherClient,  # Injected Pub/Sub publisher client (real or emulator-backed)
    periods: range = range(1, SETTLEMENT_PERIODS_PER_DAY + 1),  # Which settlement periods to poll; defaults to all 48
) -> dict[str, int]:
    """Poll every settlement period for one date, publish each normalized
    record, and route any failure to the DLQ topic. Returns counts:
    {"published": N, "dead_lettered": N, "skipped": N}."""
    main_topic_path = publisher.topic_path(PROJECT_ID, MAIN_TOPIC)  # Fully-qualified main topic resource path
    dlq_topic_path = publisher.topic_path(PROJECT_ID, DLQ_TOPIC)  # Fully-qualified DLQ topic resource path
    schema = _schema()  # Load the Avro schema once up front, reused for every record's validation
    counts = {"published": 0, "dead_lettered": 0, "skipped": 0}  # Running tally returned to the caller

    for period in periods:  # Iterate over every requested settlement period for this date
        try:
            raw = fetch_system_prices(settlement_date, period)  # Call the BMRS API for this date/period
        except BmrsApiError:  # API call failed (4xx immediately, or 5xx/connection error after retries)
            logger.exception("BMRS API call failed for %s period %s", settlement_date, period)  # Log full traceback for diagnosability
            counts["dead_lettered"] += 1  # Count this period as dead-lettered
            publisher.publish(  # Route the failure to the DLQ topic since there's no record to publish
                dlq_topic_path,
                json.dumps({  # DLQ payload describing what failed and why
                    "error": "api_call_failed",  # Machine-readable error category
                    "settlement_date": settlement_date,  # Which date failed
                    "period": period,  # Which period failed
                }).encode("utf-8"),  # Pub/Sub message data must be bytes
            )
            continue  # Move on to the next period

        try:
            records = normalize_records(raw)  # Convert the raw API response into zero or more bronze records
        except NormalizationError as exc:  # Raw response couldn't be mapped onto the bronze contract (e.g. missing required field)
            logger.error("Normalization failed for %s period %s: %s", settlement_date, period, exc)  # Log the specific normalization failure
            counts["dead_lettered"] += 1  # Count this period as dead-lettered
            publisher.publish(  # Route the failure to the DLQ topic, including the raw response for debugging/replay
                dlq_topic_path,
                json.dumps({  # DLQ payload describing what failed, why, and the offending raw data
                    "error": str(exc),  # Human-readable normalization error message
                    "settlement_date": settlement_date,  # Which date failed
                    "period": period,  # Which period failed
                    "raw": raw,  # Original raw API response, preserved for manual replay/inspection
                }).encode("utf-8"),  # Pub/Sub message data must be bytes
            )
            continue  # Move on to the next period

        if not records:  # Empty list is a valid, non-error state: the period hasn't been published by Elexon yet
            counts["skipped"] += 1  # Count as skipped rather than published or dead-lettered
            continue  # Move on to the next period

        for record in records:  # Publish each normalized record individually (usually just one per period)
            if not fastavro.validation.validate(record, schema, raise_errors=False):  # Client-side schema check, mirrors Pub/Sub-native enforcement when unavailable (see pubsub_setup.py)
                logger.error("Record failed client-side schema validation: %s", record)  # Log the record that failed validation
                counts["dead_lettered"] += 1  # Count this record as dead-lettered
                publisher.publish(  # Route the schema-invalid record to the DLQ topic instead of the main topic
                    dlq_topic_path,
                    json.dumps({"error": "schema_validation_failed", "record": record}).encode("utf-8"),  # DLQ payload with the offending record
                )
                continue  # Move on to the next record in this period
            publisher.publish(main_topic_path, _avro_json_body(record, schema))  # Publish the valid record, Avro-JSON-encoded so schema-enforced topics accept it
            counts["published"] += 1  # Count this record as published

    return counts  # Hand back the final published/dead_lettered/skipped tally


def main() -> None:  # Dockerfile entrypoint (Task 6): `python -m ingest.collectors.bmrs.collector`
    settlement_date = os.environ.get(  # Read the target settlement date from env, defaulting to yesterday
        "BMRS_SETTLEMENT_DATE", (date.today() - timedelta(days=1)).isoformat()  # BMRS data for "today" isn't final until settled, so default to yesterday
    )
    publisher = pubsub_v1.PublisherClient()  # Construct a real (or emulator-backed, via PUBSUB_EMULATOR_HOST) publisher client
    subscriber = pubsub_v1.SubscriberClient()  # Construct a real (or emulator-backed) subscriber client, needed by ensure_schema_and_topics
    ensure_schema_and_topics(publisher=publisher, subscriber=subscriber)  # Idempotently ensure schema/topics/subscriptions exist before publishing
    counts = publish_settlement_date(settlement_date, publisher=publisher)  # Run the full poll/publish/DLQ cycle for the target date
    logger.info("Done for %s: %s", settlement_date, counts)  # Log the final run summary


if __name__ == "__main__":  # Only run main() when invoked as a script/module, not on import
    main()  # Execute the collector entrypoint
