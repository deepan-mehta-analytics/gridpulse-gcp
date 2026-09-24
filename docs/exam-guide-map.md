# PDE Exam Guide v4.2 — Skills Coverage Map

Maps each sub-objective of the Google Cloud Professional Data Engineer exam
guide (v4.2) to the place in this repo that demonstrates it, and says
honestly how far that demonstration has got.

- **Official guide:** https://cloud.google.com/learn/certification/data-engineer
  (the guide itself is the linked PDF on that page). Structure and section
  weights were re-checked on 2026-09-24 and are unchanged from the
  2026-08-16 baseline. See `exam-guide-delta.md`.
- **Topic summaries below are my own shorthand, not Google's wording.**
  Read the official guide for the authoritative text.

**Status legend**

| Status | Meaning |
|---|---|
| ✅ Shown | Runnable code exists and has been exercised, currently on the **local emulator stack** (not real GCP). The Evidence column says which part of the objective. Anything not listed there is still to do. |
| 🟡 Designed | An ADR, cost doc, or Terraform module stub exists. Nothing runnable yet. |
| ⬜ Not started | Only a placeholder directory README. |

**Current coverage: 6 ✅ · 10 🟡 · 3 ⬜ (19 sub-objectives)** — as of 2026-09-24, end of Phase 1 Task 8.

| § | Sub-objective (shorthand) | Planned module | File path | Status | Evidence so far |
|---|---|---|---|---|---|
| 1.1 | Security & compliance: IAM, encryption, PII, residency, governance, dev/prod split | IAM & security baseline | `infra/iam/` | 🟡 Designed | PII/masking strategy in [ADR 0003](adr/0003-masking-policy-household-data.md); `infra/iam/` not started |
| 1.2 | Reliability & fidelity: cleaning, validation, monitoring, fault tolerance, ACID choices | Bitemporal restatement engine | `transform/beam/` | ✅ Shown | Avro bronze contract validation, DLQ routing of bad records, and replay (`ingest/contracts/`, `tests/contract/`, `orchestrate/dags/`); ACID/restatement choice in [ADR 0001](adr/0001-bitemporal-restatement-model.md). DR still to do |
| 1.3 | Flexibility & portability: requirements mapping, portability, staging/cataloging | Multi-env Terraform | `infra/terraform/` | 🟡 Designed | Local emulator twin runs via `docker compose`; Terraform modules are stubs, validated in CI but with no resources yet |
| 1.4 | Data migrations: current-state analysis, migration planning and tooling | Data migration plan | `infra/terraform/modules/datastream/` | 🟡 Designed | Datastream module stub only |
| 2.1 | Pipeline planning: sources, sinks, transform and orchestration logic | Cloud Run collectors | `ingest/collectors/` | ✅ Shown | BMRS REST client + collector publishing to Pub/Sub (emulator), containerised |
| 2.2 | Building pipelines: cleansing, service choice, batch + streaming transforms, late data | Beam windowing + Dataproc backfill | `transform/beam/`, `transform/spark/` | ✅ Shown | Response normalisation + Beam event-time windowing pipeline landing bronze in MinIO. Spark/Dataproc backfill and AI enrichment still to do |
| 2.3 | Deploying & operationalising: job automation, orchestration, CI/CD | Composer/Workflows, CI/CD | `orchestrate/dags/`, `orchestrate/workflows/`, `.github/workflows/` | ✅ Shown | Airflow DLQ-replay DAG verified end-to-end in local Airflow; GitHub Actions CI (Terraform fmt/validate, compose config). Cloud Workflows and CI test steps still to do |
| 3.1 | Choosing storage systems: access patterns, managed-service choice, lifecycle | BigLake/Iceberg lakehouse | `transform/spark/`, `infra/terraform/modules/biglake/` | 🟡 Designed | Bigtable-vs-BigQuery decision in [ADR 0002](adr/0002-bigtable-vs-bigquery-hot-lookups.md) |
| 3.2 | Warehouse planning: data modelling, normalisation, access patterns | Bitemporal Dataform marts | `transform/dataform/` | 🟡 Designed | Silver bitemporal model defined in [ADR 0001](adr/0001-bitemporal-restatement-model.md); no SQLX yet |
| 3.3 | Using a data lake: discovery, access and cost controls, processing | BigLake/Iceberg lakehouse | `transform/spark/` | 🟡 Designed | Bronze lands as objects in MinIO (GCS twin); BigLake module is a stub |
| 3.4 | Data platform design: catalog, federated governance | Dataplex zones & DQ scans | `govern/dataplex/` | 🟡 Designed | Dataplex module stub only |
| 4.1 | Preparing data for visualisation: BI tools, precomputation, masking/security | DLP + policy-tag masking | `govern/dlp/`, `govern/policy_tags/` | 🟡 Designed | Masking approach in [ADR 0003](adr/0003-masking-policy-household-data.md); DLP module stub |
| 4.2 | Preparing data for AI/ML: features, training/serving, unstructured data for RAG | BQML + embeddings/RAG | `ml/forecasting/`, `ml/classification/`, `ml/embeddings/`, `agents/rag/` | ⬜ Not started | — |
| 4.3 | Sharing data: sharing rules, dataset and report publishing | Analytics Hub sharing | `serving/` | ⬜ Not started | — |
| 5.1 | Optimising resources: cost vs. need, persistent vs. job-based clusters | Dataproc Serverless backfill | `transform/spark/` | 🟡 Designed | Budget-alert Terraform resource (`infra/terraform/modules/budget/`) + `cost-model.md`; not yet applied |
| 5.2 | Automation & repeatability: scheduled, repeatable orchestration | Composer/Workflows orchestration | `orchestrate/dags/` | ✅ Shown | Replay DAG runs in local Airflow (manual trigger); scheduled DAGs still to do |
| 5.3 | Organising workloads: capacity planning, interactive vs. batch | Editions/reservations study | `ops/cost/` | ⬜ Not started | — |
| 5.4 | Monitoring & troubleshooting: observability, usage, errors, quotas | Monitoring & alerting | `ops/monitoring/` | 🟡 Designed | Monitoring module stub only |
| 5.5 | Handling failures: fault tolerance, restarts, multi-region, failover | DR runbook | `ops/dr/` | ✅ Shown | Dead-letter queue + replay keeps failed messages recoverable; multi-region and DR runbook still to do |
