# Ballot-measure catalog

Step 1 of `docs/MEASUREMENT_DESIGN.md`: statewide **metadata** for every
catalogued measure across five topic corpora (abortion, marriage, cannabis,
labor, healthcare), 1996–2025. No county data lives here — this catalog's
job is to expose the **overlap structure** (same-ballot pairs, repeated
measures, repeat geographies) that decides which county-level ingests buy
identification for the ideal-point/severity model.

## Files

- `ballot_measures.csv` — the unified catalog, one row per measure.
  `progressive_side` says which vote is the progressive one (the
  orientation convention shared with `geofluid.ingest.referendum`);
  `severity_note` is a researcher's characterization of extremity, a
  *prior* — estimated cutpoints replace it once the model exists.
- `DESIGN_MATRIX.md` — auto-generated overlap summary: cross-topic
  same-ballot pairs (severity identifiers) and repeat geographies
  (drift anchors). This is the county-ingest priority list.
- `sources/<topic>.json` — the per-corpus research output the CSV is
  assembled from.

Regenerate with `uv run python scripts/assemble_measure_catalog.py`.

## Provenance and honesty notes

- Compiled 2026-08-10 by parallel research agents working from
  **Ballotpedia** (each measure's `source_url`), cross-checked against
  NCSL's database; dates and yes-percentages were verified per measure,
  and unverifiable facts were recorded as `null` (e.g. AR 2024 Issue 3,
  whose votes were never counted by court order).
- `yes_pct` is the certified YES share to one decimal. Watch two
  conventions: Illinois 2014 (advisory) reports shares of *all ballots
  cast* (yes+no < 100%), and Maine 2012 is stated as yes/(yes+no) where
  Ballotpedia prints the blank-inclusive share.
- **This is metadata, not an ingest.** Nothing here has passed the
  contract's certified-total acceptance bar (Bugs #10–12); each measure
  that gets county-level treatment goes through the `referendum.py`
  loader pattern with its own acceptance run at that point.
- Coverage is the five priority corpora — not every measure ever voted.
  Topics are assigned by corpus; a handful of measures could arguably
  carry two tags (e.g. tobacco-tax-funded Medicaid expansions), and the
  first corpus in assembly order wins.
