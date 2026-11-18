# Geo-Fluid Dynamics Engine

Strategic civic simulator: descriptive → predictive → prescriptive analytics for how
ideas move across geography, using certified election returns and ballot measures.
Live: https://mtgiguere.github.io/geo-fluid-dynamics-engine/

## Where to look first

- **Status and results:** `README.md` ("Where it stands").
- **What has been learned, losses included:** `docs/FINDINGS.md`.
- **Research questions asked and answered, dated:** `docs/RESEARCH_LOG.md`.
- **Research design and the 2026 protocol:** `docs/MEASUREMENT_DESIGN.md`.
- **Dated plan to MPSA (April 1-4, 2027):** `docs/TODO_2027.md`.
- **Deferred work, each with its trigger:** `BACKLOG.md`.
- **Original spec:** `docs/geo-fluid-dynamics-engine.docx`.

Modules: (1) Wave Predictor: spatial tools and the timing/hazard model built.
(2) Gravity Engine: influence hubs falsified twice; issue resistance found
instead. (3) Friction & Dissonance: live. (4) Chaos & Anomaly: seed
(`realignment.trend_surprise`). (5) Phase Transition: one order parameter
registered. Prescriptive layer: `targeting`.

## Non-negotiable: `TDD_CONTRACT.md` before writing any code

1. One test at a time. CONFIRM RED before writing any implementation.
2. Minimum code to GREEN. No code exists without a failing test demanding it.
3. No conditional guards in tests, no seed-specific assertions, never
   `is True` / `is False` against pandas/numpy values.
4. Long comments explaining scientific method are a feature: the audience
   includes policymakers, journalists and students.
5. Every ingest module's definition of done includes a real-data acceptance
   run against externally certified totals.
6. When CI diverges from local, diff the actual inputs first, and ask Matt
   for the failing log early.
7. E2E verifies integration, never logic. Page logic gets Vitest (or moves
   into the tested Python library); page-builder scripts only assemble.
8. After structural git operations, check `git ls-files | wc -l` against the
   expected count before pushing.
9. Stochastic/numerical code is verified without seeds (contract Section 4).
10. Write the derivation into the test docstring BEFORE the assertion.
11. A guardrail that has never run is decoration: schedule its first run.
12. A handed-over PR is final; further work goes to a new branch.
13. Never pipe `pytest` through `tail` (or any filter) in a gate chain: the
    pipe's exit code hides a failure. Run pytest as its own step.

Notebooks (`notebooks/`) are TDD-exempt EDA but must lean on the tested library.

## Pre-commit sequence (enforced by `.githooks/pre-commit`)

```
uv run ruff check .
uv run ruff format .    # if this changes files, re-run ruff check
uv run pytest
```

One-time per clone: `git config core.hooksPath .githooks`.

## Commands

- `uv sync`, `uv run pytest`, `uv run mypy` (strict)
- `CENSUS_API_KEY=... uv run python scripts/export_web_data.py`: rebuild the map's
  data products into `web/public/data/` (needs the gitignored raw data under `data/raw/`)
- `uv run jupytext --to ipynb --execute notebooks/<name>.py`: execute a notebook
- Frontend (in `web/`): `npm test` (Vitest), `npx playwright test` (E2E against the
  production build), `npm run dev` (local at :5173)

CI: `qa.yml` delegates to `mtgiguere/qa_pipeline` (ruff, mypy, pytest with branch
coverage ≥ 90%, pip-audit; Vitest + typecheck/build; CodeQL). `ci.yml`: gitleaks and
`uv lock --check`. `deploy.yml`: Playwright E2E gates every deploy. `mutation.yml`:
mutmut on pushes to main (Linux only), report-only survivor diffs.

## Layout

- `src/geofluid/ingest/`: raw public data → canonical panels. `county_returns` (MIT
  2000–2024), `historical_returns` (Algara–Sharif, 1868+), `county_demographics` (ACS),
  `county_geometry` (cb_2021), `referendum` (per-state ballot-measure loaders incl.
  `parse_mo_canvass`, `parse_mo_enr_results`; loaders stay politics-agnostic), `solar`
  (LBNL installs → county-quarter panel) + `zcta_county`, `spid` (policy adoption
  years), `names` (SSA baby names by state), `fec` (individual contributions by ZIP/day)
- `src/geofluid/panel/`: `master` (returns + demographics + swing), `spine` (1868–2024),
  `measures` (tidy `fips × measure_id` with orientation-corrected `progressive_share`)
- `src/geofluid/spatial/`: `weights` (queen adjacency, W, `attribute_knn_adjacency`),
  `moran` (global I, LISA), `lag` (SAR, `durbin=True`), `timing` (take-off, at-risk table,
  neighbour hazard), `distance`, `influence` + `leadlag` (tested, falsified on real data)
- `src/geofluid/catalog`: the 271-measure ballot catalog (`data/catalog/`)
- `src/geofluid/dissonance`: issue-vs-party gap, `issue_resistance`
- `src/geofluid/targeting`: `build_itinerary`, `history_buckets`, `build_playbook`,
  `playbook_budget_split`
- `src/geofluid/scoring`: the scorecard (county error, skill vs party-only baseline,
  coverage, `relevel`, `score_level`, coupling)
- `src/geofluid/seal`: seal-then-reveal manifests for the 2026 playbooks
- `src/geofluid/realignment`, `src/geofluid/scope`
- `src/geofluid/map/`: `layers` (GeoJSON + per-year metrics), `svg` (`project_rings`,
  shared by every page builder), `waves` (wave-player frames, hand-offs, chance hand-offs)
- `scripts/`: `export_web_data.py` (map data), page builders (`build_targeting_demo`,
  `build_prediction_receipt`, `build_blueprint`, `build_wave_player`),
  `register_predictions.py` (DRAFT → REGISTERED freeze), `fetch_inputs.py` (raw inputs
  vs the registered manifest), `fetch_mo_enr.cjs` (election-night MO results),
  `assemble_measure_catalog.py`
- `data/predictions/`: the 2026 pre-registration. **Never edit a `*_REGISTERED_*` file**;
  the freeze-guard test enforces it. Tags: `registration-2026-11-03`,
  `registration-supplement-2026-11-02`
- `notebooks/`: jupytext py:percent + executed `.ipynb`; each finding is summarized in
  `docs/FINDINGS.md`; `mo_2026_scorecard` grades the registration
- `web/`: Vite + TS + Mapbox app (`src/`), E2E in `e2e/`; `public/` holds the static
  pages (`demo.html`, `forecast.html`, `blueprint.html`, `waves.html`) and their tested
  logic (`calc.js`, `waves.js`)
- `tests/unit/`: one test file per module
- `docs/`: also `RELATED_WORK.md`, `FAQ.md`, `RUNBOOK_2026.md`, `BRING_YOUR_OWN_STATE.md`,
  `ADD_A_STATE.md`, `DATA_SOURCES.md`, `DEMO.md`
