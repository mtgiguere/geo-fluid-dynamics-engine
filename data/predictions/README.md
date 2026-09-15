# Pre-registered predictions

The receipts for the 2026 experiment (`docs/MEASUREMENT_DESIGN.md` §7):
county-level predictions for statewide ballot measures, committed to `main`
BEFORE the election so that git history is the notary, then scored in public
after certification.

## Files

- `mo_2026-11-03_DRAFT_<date>.csv` — working drafts produced by
  `notebooks/mo_2026_predictions.py`. Drafts may be regenerated freely.
- `mo_2026-11-03_REGISTERED_<date>.csv` — the frozen registration (to be
  committed by **2026-10-15**). **Never edited after the commit.** New
  information yields a new dated file; every registered file still gets
  scored.
- `statewide_only_2026-11-03_DRAFT_<date>.csv` — level-only calls with
  brackets for measures where we hold no county file (NV Question 6, MA
  Question 8; decided 2026-09-15). Same freeze rules; scored on the level
  criteria only.
- `county_receipts_mo_DRAFT_<date>.csv` — the receipt cards' data: one row
  per jurisdiction per certified Missouri measure (21 measures, 2018–2026):
  `county_share`, `statewide_share`, `gap` (county minus state, on the
  progressive side), `electorate` type. Every row is checkable against the
  Secretary of State.
- `county_record_buckets_mo_DRAFT_<date>.csv` — `targeting.history_buckets`
  applied to each jurisdiction's record on the 13 general-election measures
  at the Amendment 3 bracket middle: `mean_gap`, `consistency`, `gap_sd`,
  `midterm_gap`, `presidential_gap`, `midterm_penalty`, `expected_share`,
  `bucket` (turnout / persuade / hard), plus `abortion_2024_gap` and
  `bucket_amdt3_at_level` from the same-issue record alone. This is how the
  TURNOUT / PERSUADE / SKIP labels are justified from votes rather than from
  our own forecast.
- `propositions_2026-11-03_DRAFT_<date>.csv` — registered structural
  propositions scored alongside the predictions: currently the Module 5
  order-parameter call that the 2026 Amendment 3 vote is at least as
  party-coupled as 2024's (partisan slope, logit scale; STEEPEN / HOLD /
  RELAX with the ex-ante call and scoring rule written down).
- Sealed playbooks (the prescriptive half) will live alongside, per the
  protocol's seal-then-reveal rule.

## Columns

| column | meaning |
|---|---|
| `measure_id` | catalog-style id, e.g. `mo_20261103_amendment_3` |
| `ballot` | the ballot line in words |
| `progressive_side` | which answer (`yes`/`no`) the prediction's share refers to — the orientation convention shared with `geofluid.ingest.referendum` and the catalog |
| `fips` | county FIPS; `29510` St. Louis City; `2938000` Kansas City (MIT place-code convention — KC reports as its own jurisdiction spanning four counties) |
| `county` | jurisdiction name |
| `dem_two_party_2024` | the partisan baseline used (MIT presidential returns) |
| `pred_progressive_share` | the registered central prediction: share of the two-way vote going to `progressive_side` |
| `pred_low_90`, `pred_high_90` | 90% interval — the wider of (a) the level bracket carried through the county pattern and (b) ±1.645 × the backtest's pattern RMSE around the central prediction |
| `level_low`, `level_central`, `level_high` | the ex-ante statewide bracket the county predictions are conditioned on |
| `analogs` | past measures whose partisanship slope and (shrunk) residual generate the county pattern |
| `turnout_weights` | which election's county turnout shares aggregate counties to the statewide level |
| `pred_central_2024_turnout_weights` | the central prediction re-levelled with 2024 presidential county turnout shares (sensitivity) |
| `baseline_partisan_only` | the partisanship-only prediction at the same statewide level — the baseline the registered model claims to beat |

## Scoring (after certification)

1. **Level**: certified statewide progressive share vs `level_central`, and
   whether it fell inside `[level_low, level_high]`.
2. **Pattern**: per-county absolute error and RMSE of `pred_progressive_share`
   vs certified, against `baseline_partisan_only` — both re-levelled to the
   certified statewide share so the comparison isolates county skill.
3. **Calibration**: fraction of counties whose certified share fell inside
   `[pred_low_90, pred_high_90]` (target ≈ 90%).

Results go in `docs/FINDINGS.md` win or lose.
