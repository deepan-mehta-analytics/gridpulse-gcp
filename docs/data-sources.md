# Data Sources

## Elexon Insights (BMRS)
- **Content:** GB generation, demand, imbalance prices — half-hourly,
  including all settlement reconciliation runs
- **Access:** Public REST API, no API key required
- **Cadence:** Per settlement period, republished across II/SF/R1/R2/RF
  runs over the following ~4 months
- **Payload shape:** JSON, one record per BMU per settlement period per run
- **Licence:** BMRS Data Licence — attribution required
- **Attribution string (verbatim, required on every derived output):**
  `Contains BMRS data © Elexon Limited, copyright and database right.`
- **Rate limits:** documented per-endpoint on the Elexon Insights portal —
  confirm before high-frequency polling in Phase 1

## Elexon IRIS
- **Content:** Near-real-time push of the same BMRS datasets, files
  arriving within seconds of publication
- **Access:** Free, requires account registration, no special hardware
- **Cadence:** Push, near-instant on publication
- **Payload shape:** File drop (format per IRIS docs, confirm in Phase 1)
- **Licence:** Same as BMRS — attribution required
- **Rate limits:** N/A (push model)

## NESO Carbon Intensity API
- **Content:** GB carbon intensity — actual and forecast
- **Access:** Public REST API, no key
- **Cadence:** Half-hourly
- **Payload shape:** JSON
- **Licence:** Open
- **Rate limits:** none documented as of 2026-08-16 — confirm on integration

## Open-Meteo
- **Content:** Weather actuals and forecast
- **Access:** Public REST API, no key
- **Cadence:** Hourly (varies by endpoint)
- **Payload shape:** JSON
- **Licence:** Free for non-commercial use — this repo is a portfolio/study
  project, confirm this qualifies before any commercial framing
- **Rate limits:** documented per Open-Meteo's fair-use policy

## EIA API v2
- **Content:** US hourly demand and interchange by balancing authority
- **Access:** Free API key, issued instantly on signup
- **Cadence:** Hourly
- **Payload shape:** JSON
- **Licence:** US Government open data
- **Rate limits:** per EIA's published API quota
- **Phase note:** secondary source — scope cross-market schema unification,
  do not build against it in Phase 0/1

## ENTSO-E Transparency Platform
- **Content:** EU load, generation, prices
- **Access:** Free token — requires emailing `transparency@entsoe.eu`,
  ~3 business days turnaround
- **Cadence:** Varies by dataset, generally hourly/quarter-hourly
- **Payload shape:** XML (ENTSO-E's own schema)
- **Licence:** ENTSO-E terms of use
- **Rate limits:** per ENTSO-E's published quota
- **Phase note:** secondary source; request the token early given lead
  time, but do not block Phase 0/1 on it

## OSUKED Power Station Dictionary
- **Content:** BMU ↔ plant ↔ owner mapping
- **Access:** Public GitHub repository
- **Cadence:** Static/periodically updated reference data
- **Payload shape:** CSV/JSON per the OSUKED repo
- **Licence:** MIT

## London Datastore — Smart Meter Energy Consumption
- **Content:** Half-hourly consumption for ~5,500 real London households
- **Access:** Public download, London Datastore
- **Cadence:** Static historical dataset
- **Payload shape:** CSV
- **Licence:** Dataset-specific — read and record the exact licence terms
  from the London Datastore page before use
- **Governance note:** this is the repo's governance centrepiece — household
  load curves are re-identifiable via occupancy-pattern leakage. DLP
  profiling, policy-tag masking, and k-anonymity thresholds are applied
  here specifically because of that real risk (see ADR 0003), not by
  reflex.

## Elexon circulars / market notices
- **Content:** Unstructured operational text (market notices, circulars)
- **Access:** Public
- **Cadence:** As published
- **Payload shape:** HTML/PDF documents
- **Licence:** Attribution required (same as BMRS)
- **Use:** source corpus for the Tier 2 Market Context RAG agent

## Synthetic data (the one exception)

A small operational Postgres schema (fleet/asset/maintenance reference
data) is synthetic, generated to exercise CDC and PII-handling patterns
where no suitable open dataset exists. **Labelled as synthetic everywhere
it appears** — table comments, this doc, and the README Dataset section.
