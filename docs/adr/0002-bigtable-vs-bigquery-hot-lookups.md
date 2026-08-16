# ADR 0002: Bigtable vs. BigQuery for Hot Lookups

## Status
Accepted (comparison/ADR only — Bigtable is not wired into the Phase 0–6
pipeline; this ADR documents the reasoning for the exam's storage-selection
objective, §3.1).

## Context
Exam §3.1 requires reasoning about managed-service selection based on
access patterns. GridPulse has one plausible hot-lookup use case: serving
"current imbalance price for BMU X" to the FastAPI layer at low latency for
a live dashboard, as opposed to the analytical (scan-heavy, aggregation-
heavy) queries BigQuery is built for.

## Decision
BigQuery gold marts remain the source of truth and the only store wired
into the Phase 0–6 pipeline. Bigtable is evaluated in this ADR and
exercised via its local emulator in `docker-compose.yml`, but not adopted
as a production hot-path store in this repo, because:

- The actual measured query pattern (per the Results-section throughput/
  latency metrics once real traffic exists) is dashboard-refresh-rate
  lookups, not high-QPS single-key point lookups — BigQuery's BI Engine +
  materialized views (exam §4.1) are the better-fit tool for that access
  pattern, not a second wide-column store.
- Running Bigtable in the cloud demo window (§1.2) means an extra billed,
  single-node cluster to provision and tear down within an already
  budget-capped window — not justified without a demonstrated latency
  requirement BigQuery can't meet.

## Consequences
**Positive:** avoids operating two storage systems for one dataset; keeps
the cloud demo window's footprint smaller.
**Negative:** the exam's Bigtable-selection reasoning is demonstrated via
this ADR and the local emulator rather than a live production comparison
under real load — logged honestly, not hidden.

## Alternatives rejected
- **Bigtable as the serving layer for `serving/fastapi`** — rejected per
  Decision above; revisit if a real sub-100ms single-key lookup
  requirement emerges once Phase 5's FastAPI serving layer has measured
  traffic.
