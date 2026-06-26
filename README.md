# Geo-Fluid Dynamics Engine

**Live map: https://mtgiguere.github.io/geo-fluid-dynamics-engine/**

A strategic civic simulator. Where current civic-data platforms produce static heatmaps
of who agrees with you today, this engine models how ideas *move* — across counties,
along human networks, over years — and predicts where they will go next.

Built in four stages:

1. **Descriptive** — an interactive map of historical county-level voting, turnout,
   and demographics. Who are the people, and how have they voted?
2. **Historical replay** — scrub through decades and watch waves of political change
   propagate across the map. The same machinery that renders the replay is the
   backtesting harness for the models.
3. **Predictive** — geo-temporal diffusion (survival analysis over hybrid spatial
   weights), network influence (Spatial Durbin spillovers), friction detection
   (wombling, dissonance indices), and regime-change sensing.
4. **Prescriptive** — ranked, region-aware targeting recommendations.

### Status

Stages 1–2 are **live on the deployed map**, the first predictive layers are in,
and there is now a **first prescriptive demo** (Stage 4) — see below.

- Map views: election result, swing since last election, **wave anchors** (local
  spatial clustering of swing, permutation-significant), six demographic layers, and
  **ballot-measure dissonance** (issue vote vs. partisan lean — the "False Bastion"),
  now spanning three abortion measures across both ballot polarities (Kansas Aug
  2022, Kentucky Nov 2022, Ohio Issue 1 Nov 2023).
- **Scoped focus**: narrow to any state or a cross-border metro (St. Louis, Kansas
  City) — the map is meant for organizers working one area, not just the nation.
- **Play** the seven presidential elections (2000–2024) as a time-lapse.
- **Every view explains itself**: an always-visible plain-language caption says what
  the colors mean and what gray means — written for organizers, not statisticians.
- **"Where do I go?" — a prescriptive demo** (the 🧭 button in the app header):
  the leap from *what happened* to *what to do*. For a chosen issue and home
  county it produces a ranked, plain-language campaign itinerary — which counties
  to canvass (persuadable "False Bastions"), in what order, with drive distances,
  and which to skip (your base, your dead ends). A guided three-act walkthrough is
  in [`docs/DEMO.md`](docs/DEMO.md).

Under the hood, the analytical core includes Moran's I and LISA (with permutation
significance), a maximum-likelihood spatial-lag (SAR) model — with a Spatial Durbin
honesty check confirming the spatial signal survives controlling for neighbors'
demographics — and the dissonance metric. The county returns now reach back to
**1868** (a 40-election spine, 1868–2024), and the first seed of the chaos/anomaly
sensor (spec Module 4) is built on it: a per-county *trend-surprise* that detects
realignments, walked through in the
[1964-vs-2016 analysis notebook](notebooks/realignment_1964_vs_2016.ipynb) — 1964 was
an almost-purely-regional break, 2016 added a new education cleavage. Network influence
(Module 2) saw two approaches falsified on real data (contemporaneous conformity, then
a lead-lag timing signal); the current route reframes influence as *issue resistance* —
a county's persuadability on single-issue ballot measures versus its partisan identity —
built on a growing multi-state measure set and a cross-measure contest panel, and it
found its first positive result (issue resistance is a stable cross-issue county trait,
partial correlation ≈ 0.62 in Ohio). That trait is what the prescriptive demo turns into
a targeting recommendation. The phase-transition detector (Module 5) is not yet built —
see `BACKLOG.md`.

## Development

This project is built with strict test-driven development. **`TDD_CONTRACT.md` is
binding** — read it before contributing. Every function exists because a failing test
demanded it, and the commit history shows the RED → GREEN sequence.

```
uv sync                                # install dependencies
git config core.hooksPath .githooks   # one-time: pre-commit gate (check/format/tests)
uv run pytest                          # run the test suite
```

## Running the map

```
# one-time data export (needs CENSUS_API_KEY in the environment, the MIT
# returns CSV and cb_2021 5m boundary shapefile under data/raw/)
uv run python scripts/export_web_data.py

cd web
cp .env.example .env.local   # add your Mapbox public token
npm install
npm run dev                  # http://localhost:5173
```
