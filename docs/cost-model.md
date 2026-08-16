# Cost Model

What each demo window actually costs, and the guardrails that cap it.

## Free-tier-safe by default

Every local-twin service in `docker-compose.yml` runs at zero cost — no
GCP resources are provisioned for local development.

## Cloud demo windows

`make cloud-up` provisions a minimal real-GCP footprint for a short,
timed demonstration window; `make cloud-down` tears it down and must
return spend to zero. `make cloud-up` refuses to run unless the operator
has set `GCP_BUDGET_ALERT_CONFIGURED=1` — this is a self-declared
attestation gate (an operator confirms, by their own hand, that a real
budget alert already exists on the target project before flipping the
flag), not automated enforcement: the Makefile only checks that the env
var is non-empty, it never queries GCP or verifies a budget resource
actually exists. Real, automated verification — via Terraform's `budget`
module (`infra/terraform/modules/budget/`) actually being applied against
the target project — starts in Phase 7, once the cloud demo window is
wired up.

| Service (demo window only) | Expected footprint | Notes |
|---|---|---|
| Dataflow | `--maxNumWorkers=2`, short-lived job | torn down at window end |
| Dataproc Serverless | per-job billing, no persistent cluster | |
| Cloud Composer | stood up briefly for the Phase 7 demo window, torn down after | **no free tier — bills for the environment itself, not per DAG run**; see cost caveat below |
| Cloud Run | serverless, scales to zero | minimal footprint for a short demo — collectors only run while invoked |
| Pub/Sub | demo-volume message throughput | within free-tier quota (10 GiB/month) at demo volumes |
| GCS | raw landing bucket | minimal storage for a short demo window |
| BigQuery | sandbox / on-demand queries only | no reservations purchased in Phase 0–6 |
| Dataplex, Datastream | cloud-only (no local twin) | evidenced via Terraform + recorded walkthrough, not a live persistent demo |
| Bigtable | **not stood up in cloud demo windows** — evaluated via local emulator only | per [ADR 0002](adr/0002-bigtable-vs-bigquery-hot-lookups.md): standing up a billed Bigtable cluster in an already budget-capped demo window isn't justified without a demonstrated latency requirement BigQuery can't meet |

**Cost caveat — Composer and the budget ceiling:** the budget module's
default ceiling (`infra/terraform/modules/budget/variables.tf`,
`monthly_budget_gbp`) is £10/month. Cloud Composer has no Always-Free
tier and can exceed a ceiling that small within days if left running.
The £10 default assumes short, deliberately time-boxed demo windows — a
Composer environment left running would blow through it quickly. That's
a reason to keep demo windows short and torn down promptly via
`make cloud-down`, not a reason to raise the default.

## What this repo will never do automatically

No automated coding-agent session or subagent ever runs `gcloud billing`
link/unlink, IAM policy bind/unbind, service-account key create/delete,
project create/delete, or API enable/disable. Those commands are handed
to the user to run directly, every time — see repo `CLAUDE.md`.

## Placeholder discipline

Every project ID, billing account ID, or personal email that could appear
in this file or in `infra/` is a placeholder (`<YOUR_PROJECT_ID>` etc.)
until the user fills in `.env` locally (gitignored). Nothing real is ever
committed here.
