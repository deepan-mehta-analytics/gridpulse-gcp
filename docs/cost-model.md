# Cost Model

What each demo window actually costs, and the guardrails that cap it.

## Free-tier-safe by default

Every local-twin service in `docker-compose.yml` runs at zero cost — no
GCP resources are provisioned for local development.

## Cloud demo windows

`make cloud-up` provisions a minimal real-GCP footprint for a short,
timed demonstration window; `make cloud-down` tears it down and must
return spend to zero. `make cloud-up` refuses to run unless a GCP budget
alert is already configured on the target project — this is enforced in
the Makefile, not just documented.

| Service (demo window only) | Expected footprint | Notes |
|---|---|---|
| Dataflow | `--maxNumWorkers=2`, short-lived job | torn down at window end |
| Bigtable | single node | torn down at window end |
| Dataproc Serverless | per-job billing, no persistent cluster | |
| Cloud Composer | not used in demo windows — Airflow stays local | avoids Composer's persistent environment cost |
| BigQuery | sandbox / on-demand queries only | no reservations purchased in Phase 0–6 |
| Dataplex, Datastream | cloud-only (no local twin) | evidenced via Terraform + recorded walkthrough, not a live persistent demo |

## What this repo will never do automatically

No Claude session or subagent ever runs `gcloud billing` link/unlink, IAM
policy bind/unbind, service-account key create/delete, project
create/delete, or API enable/disable. Those commands are handed to the
user to run directly, every time — see repo `CLAUDE.md`.

## Placeholder discipline

Every project ID, billing account ID, or personal email that could appear
in this file or in `infra/` is a placeholder (`<YOUR_PROJECT_ID>` etc.)
until the user fills in `.env` locally (gitignored). Nothing real is ever
committed here.
