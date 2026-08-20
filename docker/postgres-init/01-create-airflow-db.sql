-- Creates the separate gridpulse_airflow database that Airflow's own
-- metadata store points at (kept apart from gridpulse_ops, the CDC-watched
-- schema — see docker-compose.yml's airflow service comment for why).
-- Postgres's official image runs every .sql/.sh file in
-- /docker-entrypoint-initdb.d/ once, only on a fresh (empty) data
-- directory — this container has no volume mount, so it re-runs on every
-- fresh container start, which is what we want for local dev.
CREATE DATABASE gridpulse_airflow;
