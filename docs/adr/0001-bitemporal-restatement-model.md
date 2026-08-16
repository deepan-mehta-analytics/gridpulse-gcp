# ADR 0001: Bitemporal Restatement Model for Settlement Data

## Status
Accepted

## Context
GB electricity settlement periods are published, then republished, multiple
times over roughly four months via a sequence of reconciliation runs
(II → SF → R1 → R2 → RF). Each run can move the imbalance price for the
same settlement period by a material amount — see the worked example in
the README's Architecture section (82.4 → 79.1 → 80.6 → 80.9 across four
runs for one 30-minute period).

Two naive approaches were considered and rejected:

- **Overwrite-in-place.** The warehouse always reflects the latest known
  value. Simple, but destroys the audit trail — a forecast trained six
  months ago against "the R2 value" can no longer be reproduced, because
  that row no longer exists in that form. Fails any exam-guide requirement
  around data validation and reproducibility (§1.2).
- **Blind append.** Every publication is inserted as a new row with no
  structure distinguishing versions from each other. Answers "what was the
  imbalance price for this period" differently depending on which rows a
  query happens to pick up — effectively non-deterministic without very
  careful, easy-to-get-wrong query discipline pushed onto every consumer.

## Decision
Model three temporal dimensions as first-class, separate columns on every
bronze/silver row:

- `event_time` — the settlement period the data describes (never changes
  across republications of the same period)
- `published_at` — when this specific version was published by Elexon
- `settlement_run` — which run produced this version (`II`, `SF`, `R1`,
  `R2`, `RF`)

Bronze retains every published version — no overwrites, no deletes. Silver
applies a `MERGE` keyed on `(natural key, settlement_run)`, producing one
row per run per period. A `current_state` view in gold selects the latest
`settlement_run` per period for consumers who just want "the current
answer." As-of queries reconstruct any past belief state by filtering
`published_at <= <as-of timestamp>` and taking the latest run known as of
that timestamp.

## Consequences

**Positive:**
- Full audit trail — any historical forecast or report is exactly
  reproducible against the run that was current when it was built.
- Genuinely demonstrates late-arriving data, allowed lateness, and ACID
  trade-off decisions (exam §1.2, §2.2) against real data instead of
  synthetic toy examples.
- Restatement drift (how far T+0 estimates move by T+4m) becomes a
  first-class, queryable metric — one of the Results-section metrics this
  repo tracks.

**Negative / costs accepted:**
- Storage cost — bronze/silver grow with every republication, not just
  every new period. Mitigated by BigQuery's low per-GB storage cost and
  GCS lifecycle tiering on raw landing.
- Query complexity — consumers who only want "the current answer" must use
  the `current_state` view rather than querying silver directly; this is
  documented, not left implicit.
- Beam pipeline complexity — windowing and allowed-lateness tuning must
  account for the fact that a "late" record isn't malformed data, it's an
  expected, scheduled reconciliation run (measured lag, not guessed).

## Alternatives rejected
- **Overwrite-in-place** — rejected, destroys audit trail (see Context).
- **Blind append with no run/version structure** — rejected, produces
  non-deterministic query results (see Context).
- **Slowly Changing Dimension Type 2 on the settlement fact table** —
  considered; rejected as the primary model because SCD2's `valid_from`/
  `valid_to` framing is designed for dimension attribute changes, not for
  a fact value being republished under a fully-specified version key. SCD2
  is used elsewhere in this repo (Phase 3 gold dims) where it fits, but
  not here.
