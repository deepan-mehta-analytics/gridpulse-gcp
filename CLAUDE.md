# GridPulse — Project Instructions

Extends `~/.claude/CLAUDE.md`. Read that first; these are additions and
repo-specific emphases, not a replacement.

## Non-negotiable guardrails

- No Claude session or subagent ever runs `gcloud billing` link/unlink,
  IAM policy bind/unbind, service-account key create/delete, project
  create/delete, or API enable/disable — in any phase, regardless of
  confirmation given in chat. Hand the exact command to the user to run
  themselves via `!<command>`.
- Any file under `infra/`, `docs/cost-model.md`, or `.env.example` that
  could carry a real GCP project ID, billing account ID, or personal email
  ships with placeholder values only, in the same commit that creates it —
  this repo is public.
- `make cloud-up` refuses to run without a configured budget alert.
  `make cloud-down` must return spend to zero after every demo window.

## Repo-specific conventions

- Default GCP region: `europe-west2`.
- Python 3.11+, Terraform 1.6+.
- No Kubernetes anywhere in this repo.
- Dockerfiles (from Phase 1 onward, under `ingest/collectors/`): comments
  on their own line before the instruction, never trailing — BuildKit
  parses a trailing `#` on `ENV`/`ARG`/`LABEL` as content and aborts the
  build.
- Dataplex and Datastream have no local emulator twin — those modules are
  evidenced by Terraform plus a recorded walkthrough only; log this under
  Limitations, don't paper over it.
- `docs/exam-guide-map.md` is the source of truth for which PDE v4.2
  sub-objective each module serves — update its status column as modules
  land.
