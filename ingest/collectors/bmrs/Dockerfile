# ingest/collectors/bmrs/Dockerfile

# Slim Python 3.11 base image, matches this repo's CLAUDE.md floor.
FROM python:3.11-slim

# All collector work happens under /app inside the container.
WORKDIR /app

# Copy packaging metadata first so pip install has what it needs.
COPY pyproject.toml /app/pyproject.toml

# Copy the ingest package tree — the only source this image needs.
COPY ingest /app/ingest

# Install the collector and its pinned dependencies.
RUN pip install --no-cache-dir .

# Default entrypoint runs one full poll pass; BMRS_SETTLEMENT_DATE
# overrides which settlement date gets polled (defaults to yesterday,
# see collector.py's main()).
ENTRYPOINT ["python", "-m", "ingest.collectors.bmrs.collector"]
