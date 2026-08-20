"""Airflow DAG wrapper — thin by design, all logic lives in
replay_logic.py so it's testable without an Airflow install. Only loaded
inside the Airflow container (docker-compose.yml mounts
orchestrate/dags). Manual trigger only for Phase 1 — schedule=None."""
from datetime import datetime  # Fixed start_date for the DAG definition below

from airflow import DAG  # Airflow's DAG object — only imported here, never in replay_logic.py
from airflow.operators.python import PythonOperator  # Runs an arbitrary Python callable as a task
from google.cloud import pubsub_v1  # GCP Pub/Sub client library — real clients constructed at task-run time

from bmrs_dlq_replay.replay_logic import replay_dlq_messages  # Pure replay logic, imported relative to the mounted dags/ folder


def _run_replay():
    # Task callable: construct real Pub/Sub clients and run the replay.
    subscriber = pubsub_v1.SubscriberClient()  # Real subscriber client — talks to whichever Pub/Sub endpoint the container is configured for
    publisher = pubsub_v1.PublisherClient()  # Real publisher client — talks to whichever Pub/Sub endpoint the container is configured for
    count = replay_dlq_messages(subscriber=subscriber, publisher=publisher)  # Delegate to the pure, unit-tested replay logic
    print(f"Replayed {count} messages from bmrs-bronze-dlq")  # Surface the result in the Airflow task log for manual verification


with DAG(
    dag_id="bmrs_dlq_replay",  # Unique DAG identifier shown in the Airflow UI
    description="Manually-triggered replay of bmrs-bronze-dlq back onto bmrs-bronze",  # Human-readable summary shown in the UI
    schedule=None,  # Manual trigger only for Phase 1 — no auto-replay schedule
    start_date=datetime(2026, 8, 16),  # Fixed start_date, required by Airflow even with schedule=None
    catchup=False,  # Never backfill past runs — this DAG has no schedule to backfill against
    tags=["gridpulse", "phase1", "dlq-replay"],  # UI filter tags for discoverability
) as dag:
    replay_task = PythonOperator(task_id="replay_dlq_messages", python_callable=_run_replay)  # Single task: run the replay callable
