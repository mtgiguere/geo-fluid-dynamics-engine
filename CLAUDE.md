# Geo-Fluid Dynamics Engine

Strategic civic simulator: descriptive → predictive → prescriptive analytics for how
political ideas move across geography. Five planned modules: Wave Predictor (geo-temporal
diffusion), Gravity Engine (network influence), Friction & Dissonance Mapper, Chaos &
Anomaly Sensor, Systemic Phase Transition detector.
Full spec: `docs/geo-fluid-dynamics-engine.docx`. Deployed: https://mtgiguere.github.io/geo-fluid-dynamics-engine/

## What's built (as of 2026-06-15)

The descriptive map and the first analytical layers are live and deployed
(https://mtgiguere.github.io/geo-fluid-dynamics-engine/):

- **Data spine** (`ingest/` → `panel/master`): county presidential returns 2000–2024
  (MIT) joined to ACS demographics on a harmonized FIPS key; `swing_dem_2p` and LISA
  quadrants merged in. County geometry from Census cb_2021.
- **Historical spine** (`ingest/historical_returns` + `panel/spine`): returns
  extended back to **1868** (Algara–Sharif, pre-2000) joined to MIT (2000+) into one
  validated 40-election panel (1868–2024, ~117k county-years; modern source wins the
  overlap; cross-validates vs MIT at corr 0.9999 in 2020). Demographics remain 2000+
  (NHGIS decennial is future).
- **Module 1 (Wave Predictor), core built**: `spatial/weights` (queen adjacency +
  row-standardized W), `spatial/moran` (global Moran's I, LISA with permutation
  significance), `spatial/lag` (SAR maximum-likelihood spatial-lag model, ρ, with a
  `durbin=True` honesty check — ρ survives controlling for neighbors' demographics).
  Still to come: the survival/hazard *timing* model, hybrid W, and the spatial-error
  (SEM) half of the honesty check (hard under the no-seed rule — see BACKLOG).
- **Module 3 (Friction & Dissonance), live**: `dissonance` (issue-vs-party gap) and
  the Kansas Aug-2022 ballot-measure overlay, shipped as a map view (the "False
  Bastions"). Still to come: wombling, roll-off, False-Bastion classification tiers,
  more ballot measures (the overlay catalog is modular — append to `MEASURES`).
- **Frontend** (`web/`, Vite + TS + Mapbox GL): map views for result, swing, wave
  anchors, six demographics, and ballot-measure dissonance; scoped focus
  (nation / any state / cross-border metro presets); play-the-decades time-lapse;
  plain-language storyline; and an always-visible explainer caption on every view.
  Data products are static JSON built by `scripts/export_web_data.py`.
- **Tooling**: self-running mutation gate (validated on Linux CI; emits survivor
  diffs), the pre-commit hook, and the Playwright E2E deploy gate.
- **Module 4 (Chaos & Anomaly Sensor), seed built**: `realignment.trend_surprise`
  — each county's residual from its own linear trend, extrapolated one election
  ahead (the realignment signal). Demonstrated in an analysis notebook (`notebooks/`,
  1964 vs 2016) on the 1868–2024 spine: 1964 ≈ purely regional, 2016 adds an
  education cleavage. Still to come: the live surprise-field monitor (magnitude +
  spatial coherence + axis) that is the actual Module 4 product.
- **Module 2 (Gravity Engine), first attempt falsified**: `county_influence` +
  `classify_nodes` primitives are tested, but contemporaneous-conformity
  node-classification was falsified on real data (swing is so autocorrelated that
  everyone co-moves). Lead-lag retry now unblocked by the 40-election spine.
- **Module 5 (Systemic Phase Transition)**: not started. See `BACKLOG.md` for
  sequenced next work and open design questions.

## Non-negotiable: read TDD_CONTRACT.md before writing any code

This project is built with strict TDD + JIT programming. The contract is evidence-based —
it documents real bugs from the previous attempt at this exact project. The short version:

1. One test at a time. Run it. CONFIRM RED before writing any implementation.
2. Write the minimum code to GREEN. No code exists without a failing test demanding it.
3. No conditional guards in tests. No seed-specific assertions. Never `is True` /
   `is False` against pandas/numpy values.
4. Long explanatory comments on scientific methodology are a feature, not a smell —
   the audience includes policymakers, journalists, and students.
5. Fixtures specify the contract; real data falsifies your model of the world. Every
   ingest module's definition of done includes a real-data acceptance run validated
   against externally certified facts (see the contract's GFDE Bugs #10–#12).
6. When CI diverges from local, diff the actual inputs (env vars, tokens, data,
   versions) before hypothesizing — and ask Matt for the failing log early; one
   pasted log beats three speculative CI runs.
7. E2E verifies integration, never logic. The moment frontend code accumulates pure
   logic (formatters, expression builders), it gets Vitest contract tests.
8. After structural git operations (stash across branches), verify
   `git ls-files | wc -l` against the expected count before pushing — see the
   contract's OPEN INCIDENT on the single-file commit.
9. Stochastic/numerical code is verified WITHOUT seeds: deterministic
   constructions, noise-free recovery worlds, invariance properties, and a
   reproducibility (not seed-value) contract — see the contract's "Verifying
   Stochastic and Numerical Machinery" section before writing any such test.
10. Write the derivation into the test docstring BEFORE the assertion —
    hand-math done in the head after the fixture has been wrong twice.
11. A guardrail that has never run is decoration: schedule its first verified
    execution as part of installing it.
12. A handed-over PR is final; further work goes to a new branch.
13. Never pipe `pytest` through `tail` (or any filter) in a `&&` gate chain —
    the pipe's exit code masks a test failure and lets a red commit through
    (it did once; the pre-commit hook caught it). Run pytest as its own step.

## Pre-commit sequence (before every commit)

```
uv run ruff check .
uv run ruff format .    # if this changes files, re-run ruff check
uv run pytest
```

This is enforced mechanically by `.githooks/pre-commit`. One-time setup per clone:

```
git config core.hooksPath .githooks
```

(Added after a commit skipped the format step and CI caught the drift —
the contract's "ruff format is not optional" rule, demonstrated live.)

## Commands

- `uv sync` — install dependencies
- `uv run pytest` — run the test suite
- `uv run mypy` — strict type checking
- `CENSUS_API_KEY=... uv run python scripts/export_web_data.py` — rebuild the
  frontend's static data products into `web/public/data/` (needs the gitignored
  MIT returns CSV + cb_2021 shapefiles + KS measure workbook under `data/raw/`)
- `uv run jupytext --to ipynb --execute notebooks/<name>.py` — execute an analysis
  notebook into its paired `.ipynb` with rendered outputs (needs the gitignored raw
  data under `data/raw/`; notebooks are TDD-exempt EDA)
- Frontend (in `web/`): `npm test` (Vitest), `npx playwright test` (E2E against the
  production build), `npm run dev` (local at :5173)

CI gates (`.github/workflows/ci.yml`): gitleaks → ruff check → ruff format --check →
mypy → pytest with branch coverage ≥ 90% → pip-audit → uv lock --check, plus a web
job (npm ci + typecheck/build). Deployment (`deploy.yml`): Playwright E2E against the
production build at the real Pages base path gates every deploy. Mutation testing
(`mutation.yml`): runs on every push to main touching code (+ weekly backstop +
dispatch), report-only — emits survivor diffs to the job summary/artifact; the
watchdog for hollow tests. (mutmut only runs on Linux CI — it refuses on Windows.)

## Layout

- `src/geofluid/ingest/` — raw public data → canonical panels (`county_returns`,
  `county_demographics`, `county_geometry`, `referendum`, `historical_returns`)
- `src/geofluid/panel/master` — joins returns + demographics into the master panel
  (FIPS-harmonized; adds swing); `panel/spine` — joins historical + MIT returns into
  the 1868–2024 panel
- `src/geofluid/spatial/` — `weights` (adjacency + W), `moran` (global I, LISA,
  permutation significance), `lag` (SAR model)
- `src/geofluid/dissonance` — issue-vs-party gap + ballot-measure overlay
- `src/geofluid/realignment` — `trend_surprise` (Module 4 seed: per-county residual
  from its own trend)
- `src/geofluid/scope` — geographic scope catalog + cross-border neighborhood expansion
- `src/geofluid/map/layers` — GeoJSON layer + per-year metrics export shaping
- `scripts/export_web_data.py` — thin orchestration → `web/public/data/*.json`
- `notebooks/` — exploratory analysis (jupytext py:percent + paired executed .ipynb);
  EDA that leans on the tested `geofluid` library, **TDD-exempt** (see TDD_CONTRACT.md)
- `web/` — Vite + TS + Mapbox frontend (`src/metrics.ts`, `src/scope.ts`,
  `src/measure.ts`; `e2e/` Playwright)
- `tests/unit/` — Python unit tests (one file per module)
- `TDD_CONTRACT.md` — the development contract; binding for every session
- `BACKLOG.md` — agreed-but-deferred work, each item with its JIT trigger
