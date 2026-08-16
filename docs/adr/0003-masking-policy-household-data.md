# ADR 0003: Masking Policy for Household Smart-Meter Data

## Status
Accepted

## Context
The London Datastore smart-meter dataset (`docs/data-sources.md`) contains
half-hourly consumption for ~5,500 real households. This is not
anonymous data by construction: a household's half-hourly load shape
encodes occupancy patterns — when people wake up, leave for work, cook,
sleep — which is a well-documented re-identification vector in the smart-
meter privacy literature. This is a genuine privacy risk, not a
hypothetical one invoked to justify using DLP for the exam checklist.

## Decision
Apply Cloud DLP profiling to the household dataset specifically (not
uniformly across every dataset in the warehouse — the BMU/generation-mix
data has no comparable individual-level privacy exposure and is not
masked). Where DLP profiling flags quasi-identifying load-shape patterns:

- Apply BigQuery policy tags to household-identifying columns, restricting
  column-level access to roles that have a specific, documented need.
- Aggregate to a minimum k-anonymity threshold (k chosen and justified in
  `govern/dlp/` once Phase 4 implements this — not fixed here, since the
  right k depends on the actual cohort size and re-identification risk
  measured against the real dataset, not guessed in advance) before any
  household-level data is exposed to a broader audience than the
  governance-scoped role.
- The synthetic operational Postgres schema (fleet/asset/maintenance data)
  is explicitly exempt from this ADR's masking policy, since it contains
  no real individuals and is labelled synthetic everywhere it appears.

## Consequences
**Positive:** governance work in this repo defends a real, articulable
risk — useful both as an honest engineering decision and as a stronger
portfolio artifact than "we added DLP because the exam guide mentions it."
**Negative:** k-anonymity aggregation reduces the resolution of any
analysis or ML feature built directly on household-level load shapes;
downstream forecasting/clustering work (Phase 5) must account for this
reduced resolution when interpreting results.

## Alternatives rejected
- **No masking (use the dataset as published)** — rejected; the dataset's
  own documentation and the smart-meter privacy literature both treat
  half-hourly household load curves as identifying, so ignoring that here
  would be dishonest given the repo's own claim to modeling this
  seriously (exam §4.1, §1.1).
- **Blanket masking applied identically to every dataset in the
  warehouse** — rejected; BMU/generation/carbon-intensity data has no
  comparable individual-level exposure, and masking it identically would
  be governance-by-reflex rather than governance grounded in an actual
  risk assessment, which is the point of this ADR.
