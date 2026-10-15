# Runbook — election night and the December scorecard (2026)

The registration is frozen (`data/predictions/*_REGISTERED_2026-10-14.csv`,
tag `registration-2026-11-03`). This is the step-by-step for scoring it. Two
passes: a **provisional** scorecard from election-night counts within a day,
and the **certified** scorecard when the Board of State Canvassers signs
(early December in recent cycles). Both are published; the certified one is
what goes in `docs/FINDINGS.md` and unseals the playbooks.

Nothing here edits a registered file. The freeze guard
(`tests/unit/test_registration_frozen.py`) will fail the test suite if
anything does.

## 1. Election night (Nov 3–4): fetch the county results

The Missouri Secretary of State's results portal serves county tables the
same evening. Cloudflare blocks plain requests; the fetch script drives the
installed Chrome through Playwright, which is already set up under `web/`.

```
NODE_PATH=web/node_modules node scripts/fetch_mo_enr.cjs \
    --out data/raw --prefix enr_mo_20261103 --match amendment,referendum
```

Check the console: the first line prints the portal's own status banner
("Unofficial Results" on election night, "Official Results … Board of State
Canvassers" after certification), and each race prints its statewide YES/NO
block. Keep the race-name to measure-id mapping explicit when you parse:

| Portal race name (expected) | measure_id | progressive side |
|---|---|---|
| Constitutional Amendment No. 3 | `mo_20261103_amendment_3` | NO |
| Constitutional Amendment No. 6 | `mo_20261103_amendment_6` | YES |
| Referendum (HB 1 congressional map) | `mo_20261103_map_referendum` | NO |
| Constitutional Amendment No. 7 | `mo_20261103_amendment_7` | NO |
| Constitutional Amendment No. 8 | `mo_20261103_amendment_8` | NO |

Parse each saved text with `geofluid.ingest.referendum.parse_mo_enr_results`
and the Missouri name-to-FIPS map used in `notebooks/mo_2026_predictions.py`
(Kansas City `2938000`, St. Louis `29189`, McDonald `29119`, De Kalb
`29063`). The parser refuses any page whose counties do not sum to its
statewide block.

Nevada and Massachusetts are statewide-only calls: take the certified
statewide share from each state's election office.

## 2. Score (a notebook on the tested scorer)

Write a scoring notebook (`notebooks/mo_2026_scorecard.py`, jupytext
py:percent, TDD-exempt EDA) that leans on `geofluid.scoring`:

1. Load `mo_2026-11-03_REGISTERED_2026-10-14.csv` and the parsed results;
   `actual` = the certified share for the measure's progressive side.
2. **Relevel both** `pred_progressive_share` and `baseline_partisan_only`
   to the certified statewide share with `scoring.relevel` (turnout
   weights = the 2026 votes cast per jurisdiction), so the pattern grade is
   independent of the level grade.
3. `score_counties` → `score_summary` per measure: RMSE model vs baseline,
   skill, 90% coverage.
4. The pre-registered test: one-sided paired Wilcoxon signed-rank on
   |error_model| − |error_baseline| over all 580 Missouri rows, alpha 0.05
   (`scipy.stats.wilcoxon`, alternative="less"). Report per-measure skill
   as well.
5. `score_level` for each of the seven brackets.
6. Propositions (`propositions_2026-11-03_REGISTERED_2026-10-14.csv`):
   - coupling: `coupling_slope` of the certified Amendment 3 NO share on
     2024 Dem two-party share, `classify_coupling` against 0.797, tol 0.05;
   - spatial diagnostic: Moran's I of the relevelled Amendment 3 errors
     under queen adjacency (`geofluid.spatial.weights`, `spatial.moran`
     with permutation significance);
   - turnout-composition diagnostic: Pearson r between the relevelled
     Amendment 3 error and (2026 votes cast / 2018 votes cast) by
     jurisdiction (2018 totals from the Clean Missouri canvass contest).
7. Roll-off per measure: votes cast on the measure versus the top of the
   ticket, as the confusion measurement named in the known weaknesses.
8. Playbook grade: did the counties the sealed plans flagged as persuasion
   ground with positive headroom over-perform the partisanship baseline in
   the predicted direction?

Label every output PROVISIONAL or CERTIFIED. Execute with
`uv run jupytext --to ipynb --execute notebooks/mo_2026_scorecard.py`.

## 3. Publish

- `docs/FINDINGS.md`: a new numbered finding with the scorecard, win or
  lose, including the level misses and what they imply.
- `scripts/build_prediction_receipt.py` and `scripts/build_blueprint.py`:
  add the scorecard section (the blueprint has an empty December slot) and
  rebuild; the Playwright page tests must still pass.
- `README.md` status line.

## 4. Unseal (certified pass only)

```
# copy the ten files from the off-repo backup into data/predictions/sealed/
uv run python - <<'EOF'
import pandas as pd
from pathlib import Path
from geofluid.seal import verify_manifest
P = Path("data/predictions")
print(verify_manifest(pd.read_csv(P / "SEALED_MANIFEST_REGISTERED_2026-10-14.csv"), root=P))
EOF
```

Every row must be `ok == True`. Then remove `data/predictions/sealed/`
from `.gitignore` for the registered files (or move them to
`data/predictions/unsealed/`), commit them with the verification output in
the commit message, and reference the commit from the scorecard. Do not
regenerate the playbooks; the sealed bytes are the ones that get graded.

## 5. The dossier

Frozen prediction → public scorecard → unsealed playbook, in that order,
plus the proposal for the first client engagement (treatment and control
counties, effort log, measured lift). See `docs/MEASUREMENT_DESIGN.md` §7.

## If certification is delayed

Candidate recounts do not delay measure certification. A measure inside
Missouri's half-point recount window (the map referendum is the candidate)
could. The provisional scorecard stands, labelled, until the certified one
replaces it; nothing in the protocol depends on the date.
