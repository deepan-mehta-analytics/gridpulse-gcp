# GridPulse — Project Status

Ecosystem snapshot for this repo. Updated after every meaningful session.

## Current phase
Phase 0 — Scaffolding (README, directory tree, exam-guide map, data-sources
doc, docker-compose/Makefile, Terraform skeleton, CI, ADRs, this file).

## Phase status

| Phase | Status | Notes |
|---|---|---|
| 0 — Scaffolding | ✅ Done | this session |
| 1 — Stream ingest → bronze/silver (local) | ⏳ Pending | |
| 2 — Bitemporal restatement engine + tests | ⏳ Pending | |
| 3 — Batch backfill, BigLake/Iceberg, gold marts | ⏳ Pending | |
| 4 — Governance (Dataplex, DLP, policy tags) | ⏳ Pending | |
| 5 — BQML forecasting/classification, embeddings | ⏳ Pending | |
| 6 — Agent tiers + eval harness | ⏳ Pending | |
| 7 — Cloud demo window | ⏳ Pending | |

## Last commit
6f991b2 docs: add ADRs for bitemporal model, Bigtable comparison, and masking

## Metrics
No results yet — Phase 0 has no runnable pipeline. See README Results
section for the five metrics that will populate here.

## Known gaps
Dataplex and Datastream have no local emulator twin (cloud-only, evidenced
via Terraform + recorded walkthrough). ENTSO-E token not yet requested.
Conversational Analytics API pricing not yet re-verified (preview-era).
