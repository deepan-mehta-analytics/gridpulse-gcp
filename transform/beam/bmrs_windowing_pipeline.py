"""Beam pipeline: pulls a batch of currently-available messages from the
bmrs-bronze subscription, windows them by settlement period in event
time, and writes every version to MinIO as bronze Avro — no dedup or
merge, that belongs to Phase 2's restatement engine."""
from __future__ import annotations  # Enable postponed evaluation of type hints (Python 3.10+)

import datetime  # Parse each record's start_time and assign it as the Beam event timestamp
import json  # Decode pulled Pub/Sub message bytes and load the Avro schema JSON
import logging  # Structured logging for pipeline run diagnostics

import apache_beam as beam  # Core Beam SDK: Pipeline, DoFn, ParDo, Create, WindowInto
from apache_beam.io.avroio import WriteToAvro  # Beam's Avro file sink, used to land bronze output in MinIO
from apache_beam.options.pipeline_options import PipelineOptions  # Runner/filesystem configuration (S3 endpoint, credentials, etc.)
from apache_beam.transforms import window  # FixedWindows + TimestampedValue for event-time windowing
from google.cloud import pubsub_v1  # GCP Pub/Sub client library (talks to the emulator when PUBSUB_EMULATOR_HOST is set)

from ingest.contracts.pubsub_setup import MAIN_SUBSCRIPTION, PROJECT_ID, SCHEMA_PATH  # Task 2's resource constants: subscription name, project ID, Avro schema path

logger = logging.getLogger("bmrs-beam-pipeline")  # Named logger for this module's log records

SETTLEMENT_PERIOD_SECONDS = 30 * 60  # each settlement period is 30 minutes

# Placeholder allowed lateness: BMRS's Insights portal typically publishes
# the initial ("II") settlement run within a few minutes of period close.
# No real running history exists yet to measure actual publication lag —
# this value should be recalibrated from observed data once this pipeline
# has run against live traffic for a while. Not a silent guess: documented
# here, and revisited when Phase 2's restatement engine needs precise
# timing behavior.
ALLOWED_LATENESS_SECONDS = 15 * 60


def _schema() -> dict:  # Load and parse the Avro bronze contract, reused by the WriteToAvro sink
    return json.loads(SCHEMA_PATH.read_text())  # Read the .avsc file text and parse it as JSON


def _decode_avro_json_record(raw_record: dict, schema: dict) -> dict:
    """Reverses the Avro-JSON union-wrapping the collector applies before
    publishing to a schema-enforced topic (see
    ingest.collectors.bmrs.collector._avro_json_body): a non-null value in
    a nullable union field (e.g. replacement_price) arrives wire-encoded
    as {"double": value} rather than a bare value. fastavro's binary Avro
    writer (used by WriteToAvro below) expects the bare Python value, so
    every such field is unwrapped here before windowing/writing."""
    decoded = dict(raw_record)  # Shallow copy so we don't mutate the caller's parsed record dict
    for field in schema["fields"]:  # Walk each field definition in the Avro schema
        field_type = field["type"]  # This field's declared Avro type (a union list for nullable fields)
        if isinstance(field_type, list) and "null" in field_type:  # Only nullable union fields can carry the wire wrapper
            value = decoded.get(field["name"])  # Current value for this field in the record
            if isinstance(value, dict):  # A dict here means it's still wire-wrapped (e.g. {"double": 97.76}), not yet a bare Python value
                other_type = next(t for t in field_type if t != "null")  # The union's non-null branch, e.g. "double"
                decoded[field["name"]] = value[other_type]  # Unwrap back to the bare value fastavro expects
    return decoded  # Hand back the record with every nullable field in fastavro-native form


class ParseAndTimestamp(beam.DoFn):
    """Parses a bronze JSON record and assigns its Beam event timestamp
    from the record's own start_time, so windowing reflects the
    settlement period the data describes, not wall-clock arrival time."""

    def __init__(self):
        self.schema = _schema()  # Load the Avro schema once at construction, reused for every element's union-unwrapping

    def process(self, element):  # Beam calls this once per input element (one raw Pub/Sub message body)
        raw = json.loads(element)  # Decode the raw JSON bytes into a bronze record dict, still wire-wrapped for nullable fields
        record = _decode_avro_json_record(raw, self.schema)  # Unwrap Avro-JSON union wrapping so fastavro's writer accepts it
        start_time = datetime.datetime.strptime(  # Parse the record's own ISO-8601 UTC start_time string
            record["start_time"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=datetime.UTC)  # Attach explicit UTC tzinfo so .timestamp() is unambiguous
        yield window.TimestampedValue(record, start_time.timestamp())  # Emit the record tagged with its event-time timestamp for downstream windowing


def pull_available_messages(subscriber, subscription_path, max_messages: int = 1000) -> list[bytes]:
    """Pulls and acks up to max_messages currently queued on the
    subscription. Returns their raw message bodies."""
    response = subscriber.pull(  # Synchronous pull request against the subscription (emulator or real Pub/Sub)
        request={"subscription": subscription_path, "max_messages": max_messages}, timeout=10
    )
    if not response.received_messages:  # Nothing was queued at pull time
        return []  # Nothing to process — caller treats an empty list as "no work available"
    ack_ids = [m.ack_id for m in response.received_messages]  # Collect ack IDs for every message actually received
    subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": ack_ids})  # Ack immediately so these messages aren't redelivered
    return [m.message.data for m in response.received_messages]  # Return just the raw message bodies (bytes) to the caller


def build_pipeline(
    pipeline_options: PipelineOptions, output_path: str, messages: list[bytes]
) -> beam.Pipeline:
    pipeline = beam.Pipeline(options=pipeline_options)  # Construct a new Beam pipeline (DirectRunner unless overridden by pipeline_options)
    (
        pipeline
        | "CreateFromPulledMessages" >> beam.Create(messages)  # Seed the pipeline with the already-pulled bounded batch of message bytes
        | "ParseAndTimestamp" >> beam.ParDo(ParseAndTimestamp())  # Decode each message and assign its event-time timestamp
        | "WindowBySettlementPeriod" >> beam.WindowInto(  # Group records into 30-minute settlement-period windows by event time
            window.FixedWindows(SETTLEMENT_PERIOD_SECONDS),
            allowed_lateness=ALLOWED_LATENESS_SECONDS,
        )
        | "WriteBronzeToMinIO" >> WriteToAvro(output_path, schema=_schema(), file_name_suffix=".avro")  # Write every windowed record as bronze Avro to MinIO (S3-compatible)
    )
    return pipeline  # Hand the fully-constructed (not yet run) pipeline back to the caller


def run(argv: list[str] | None = None) -> None:
    pipeline_options = PipelineOptions(argv)  # Parse runner/filesystem flags from argv (or the process's own sys.argv if None)
    subscriber = pubsub_v1.SubscriberClient()  # Construct a real (or emulator-backed, via PUBSUB_EMULATOR_HOST) subscriber client
    subscription_path = subscriber.subscription_path(PROJECT_ID, MAIN_SUBSCRIPTION)  # Fully-qualified path to the Beam-consumed subscription

    messages = pull_available_messages(subscriber, subscription_path)  # Pull whatever is currently queued — a bounded batch, not a streaming daemon
    if not messages:  # Nothing was queued at invocation time
        logger.info("No messages currently available on %s — nothing to process.", subscription_path)  # Log the no-op outcome for visibility
        return  # Nothing further to do this invocation

    output_path = (  # Bronze output prefix in the real bronze bucket, partitioned by today's date
        f"s3://gridpulse-bronze/bmrs/settlement-system-prices/"
        f"{datetime.date.today().isoformat()}/part"
    )
    pipeline = build_pipeline(pipeline_options, output_path, messages)  # Build the windowing pipeline over the pulled batch
    pipeline.run().wait_until_finish()  # Execute it synchronously and wait for completion before this invocation returns


if __name__ == "__main__":  # Only run when invoked as a script/module, not on import
    logging.getLogger().setLevel(logging.INFO)  # Ensure INFO-level log lines (like the no-op message above) are actually emitted
    run()  # Execute the pipeline entrypoint
