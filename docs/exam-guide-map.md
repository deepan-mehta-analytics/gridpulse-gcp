# PDE Exam Guide v4.2 — Coverage Map

Source: https://cloud.google.com/certification/guides/data-engineer
(fetched 2026-08-16). One row per official sub-objective. Status starts
`⏳ Pending` for everything — updated as modules land.

| § | Sub-objective | Module | File path | Status |
|---|---|---|---|---|
| 1.1 | Designing for security and compliance (IAM, encryption/key mgmt, PII strategy, data sovereignty, legal/regulatory, project/dataset/table governance, dev vs. prod) | IAM & security baseline | `infra/iam/` | ⏳ Pending |
| 1.2 | Designing for reliability and fidelity (data cleaning incl. LLM query-gen prompting, pipeline monitoring/orchestration, DR/fault tolerance, ACID decisions, data validation) | Bitemporal restatement engine | `transform/beam/` | ⏳ Pending |
| 1.3 | Designing for flexibility and portability (business-requirement mapping, multi-cloud/data-residency portability, staging/cataloging/profiling/discovery) | Multi-env Terraform | `infra/terraform/` | ⏳ Pending |
| 1.4 | Designing data migrations (stakeholder/current-state analysis, migration planning via BQ DTS/DMS/Transfer Appliance/Datastream) | Data migration plan | `infra/terraform/modules/datastream/` | ⏳ Pending |
| 2.1 | Planning the data pipelines (sources/sinks, transform/orchestration logic, networking, encryption) | Cloud Run collectors | `ingest/collectors/` | ⏳ Pending |
| 2.2 | Building the pipelines (cleansing, service selection — Dataflow/Beam/Dataproc/Data Fusion/BigQuery/Pub/Sub/Spark/Hadoop/Kafka, batch+streaming transforms incl. windowing/late data, AI data enrichment, acquisition/import, new-source integration) | Beam windowing pipeline + Dataproc Serverless backfill | `transform/beam/`, `transform/spark/` | ⏳ Pending |
| 2.3 | Deploying and operationalizing the pipelines (job automation/orchestration via Composer/Workflows, CI/CD) | Composer/Workflows orchestration, CI/CD pipeline | `orchestrate/dags/`, `orchestrate/workflows/`, `.github/workflows/` | ⏳ Pending |
| 3.1 | Selecting storage systems (access-pattern analysis, managed-service choice among BigQuery/BigLake/AlloyDB/Bigtable/Spanner/Cloud SQL/GCS/Firestore/Memorystore, cost/performance planning, lifecycle mgmt) | BigLake/Iceberg lakehouse | `transform/spark/`, `infra/terraform/modules/biglake/` | ⏳ Pending |
| 3.2 | Planning for using a data warehouse (data model design, normalization degree, business-requirement mapping, access-pattern architecture) | Bitemporal silver/gold Dataform marts | `transform/dataform/` | ⏳ Pending |
| 3.3 | Using a data lake (lake mgmt — discovery/access/cost controls, processing, monitoring) | BigLake/Iceberg lakehouse | `transform/spark/` | ⏳ Pending |
| 3.4 | Designing for a data platform (Dataplex/Dataplex Catalog/BigQuery/GCS platform build, federated governance for distributed systems) | Dataplex zones & DQ scans | `govern/dataplex/` | ⏳ Pending |
| 4.1 | Preparing data for visualization (tool connections, precalculated fields, BI Engine/materialized views, query troubleshooting, security/masking/IAM/DLP) | DLP + policy-tag masking | `govern/dlp/`, `govern/policy_tags/` | ⏳ Pending |
| 4.2 | Preparing data for AI and ML (feature engineering/training/serving via BQML, unstructured-data prep for embeddings/RAG) | BQML forecasting & classification, embeddings + RAG | `ml/forecasting/`, `ml/classification/`, `ml/embeddings/`, `agents/rag/` | ⏳ Pending |
| 4.3 | Sharing data (share-rule definition, dataset publishing, report/viz publishing, Analytics Hub) | Analytics Hub sharing | `serving/` | ⏳ Pending |
| 5.1 | Optimizing resources (cost minimization, business-critical resource availability, persistent vs. job-based clusters e.g. Dataproc) | Dataproc Serverless backfill | `transform/spark/` | ⏳ Pending |
| 5.2 | Designing automation and repeatability (Composer DAGs, repeatable scheduling/orchestration) | Composer/Workflows orchestration | `orchestrate/dags/` | ⏳ Pending |
| 5.3 | Organizing workloads based on business requirements (capacity mgmt via BigQuery Editions/reservations, interactive vs. batch jobs) | BigQuery Editions/reservations study | `ops/cost/` | ⏳ Pending |
| 5.4 | Monitoring and troubleshooting processes (observability via Cloud Monitoring/Logging/BQ admin panel, planned-usage monitoring, error/billing/quota troubleshooting, workload mgmt) | Monitoring & alerting | `ops/monitoring/` | ⏳ Pending |
| 5.5 | Maintaining awareness of failures and mitigating impact (fault tolerance/restarts, multi-region/zone jobs, data corruption prep, replication/failover e.g. Cloud SQL/Redis) | DR runbook | `ops/dr/` | ⏳ Pending |
