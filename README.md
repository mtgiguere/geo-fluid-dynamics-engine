# Geo-Fluid Dynamics Engine

**Live map: https://mtgiguere.github.io/geo-fluid-dynamics-engine/**
· [The blueprint](https://mtgiguere.github.io/geo-fluid-dynamics-engine/blueprint.html)
· [The November receipt](https://mtgiguere.github.io/geo-fluid-dynamics-engine/forecast.html)
· [The art of the possible](https://mtgiguere.github.io/geo-fluid-dynamics-engine/demo.html)

Do ideas travel across the ground the way forests do? This is an open
instrument for finding out, using the one human idea with free, certified,
county-by-county measurements repeated for 150 years: the vote. It reads
certified election returns and ballot-measure results, measures how a
county's vote on an *issue* diverges from its *party* label, tests whether
change moves neighbor to neighbor, and turns what survives testing into a
plan a campaign can act on and a prediction that can be graded.

## Where it stands (October 2026)

**A pre-registered prediction is frozen and waiting for November 3, 2026.**
County-by-county predictions for Missouri's five statewide ballot measures,
plus statewide calls for Nevada and Massachusetts, were committed on
2026-10-14 under the tag `registration-2026-11-03`, with the statistical
test, two diagnostics on the engine itself, and the sealed campaign
playbooks' fingerprints. A guard test fails the suite if any registered file
changes. The scorecard, win or lose, is published after certification. See
[`data/predictions/README.md`](data/predictions/README.md) and the
[runbook](docs/RUNBOOK_2026.md).

**What the research found** is in [`docs/FINDINGS.md`](docs/FINDINGS.md),
in the order the argument built, losses included:

- Two attempts to find where political change *starts* were falsified on
  real data. Counties move together; there is no first domino.
- Party is a label; disposition is the signal. Direct issue votes expose it.
- "False Bastions": places whose issue vote runs ahead of their party, on the
  social axis (abortion) and the economic one (minimum wage, strongest in the
  reddest states). Persuadability is a stable trait of a place (Ohio
  r = 0.62 across issues; Missouri 0.52 across issues, 0.68 across years).
- Geography beats demographic similarity as the organizer of change
  (Moran's I 0.62 vs 0.28); education is the secondary edge.
- Realignments flicker (the education cleavage lit in 2016–2020, faded 2024).
- For predicting a new measure, partisanship alone is a strong baseline
  (3.69 pp county error); the pooled ideal point lost to it (3.80); the
  same-issue residual beat it (3.39) — only where the history truly rhymes.
- Deep time: the 1892 Populist vote predicted the 1932 New Deal break forty
  years later (r = +0.38), the same dormant-then-activated structure seen in
  modern European persistence studies.

**What's live.** The interactive map (results, swing, wave anchors, six
demographic layers, ballot-measure dissonance for Kansas, Kentucky, Ohio;
scoped focus; a play-the-decades time-lapse). Three public pages built from
data by scripts: the blueprint (the whole arc with the notebooks' own
figures), the November receipt (the registered predictions explained for
volunteers and decision-makers, with a plan priced in votes and a budget
calculator), and the art of the possible (one volunteer's weekend itinerary
from real Kansas data).

**Modules, by status.** Wave Predictor: measuring tools built, the "wave"
reframed as a flock. Gravity Engine: influence hubs falsified; issue
resistance found instead. Friction & Dissonance: live. Chaos & Anomaly
Sensor: seed built (trend surprise). Phase Transition: not started; one
order parameter registered. The original spec is
`docs/geo-fluid-dynamics-engine.docx`; the forward research design is
[`docs/MEASUREMENT_DESIGN.md`](docs/MEASUREMENT_DESIGN.md).

## Documentation map

| If you want to… | Read |
|---|---|
| understand what was learned | [`docs/FINDINGS.md`](docs/FINDINGS.md) |
| see the November predictions and how they'll be graded | [`data/predictions/README.md`](data/predictions/README.md), the receipt page |
| run election night and the December scorecard | [`docs/RUNBOOK_2026.md`](docs/RUNBOOK_2026.md) |
| bring your own state or issue (no programming) | [`docs/BRING_YOUR_OWN_STATE.md`](docs/BRING_YOUR_OWN_STATE.md) |
| write the loader for a new state (programming) | [`docs/ADD_A_STATE.md`](docs/ADD_A_STATE.md) |
| know where every raw file comes from | [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) |
| understand the research design and the 2026 protocol | [`docs/MEASUREMENT_DESIGN.md`](docs/MEASUREMENT_DESIGN.md) |
| give a five-minute demo | [`docs/DEMO.md`](docs/DEMO.md) |
| contribute | [`CONTRIBUTING.md`](CONTRIBUTING.md), then [`TDD_CONTRACT.md`](TDD_CONTRACT.md) |
| see what's deferred and why | [`BACKLOG.md`](BACKLOG.md) |
| navigate the code | [`CLAUDE.md`](CLAUDE.md) (layout and commands) |

## Quick start

```
uv sync                                # Python dependencies (lockfile)
git config core.hooksPath .githooks   # one-time: the pre-commit gate
uv run pytest                          # 100+ tests, no raw data needed
```

The test suite runs without any raw data. Everything below needs the
git-ignored inputs described in [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md).

**The map, locally**

```
export CENSUS_API_KEY=...                       # free key from api.census.gov
uv run python scripts/export_web_data.py        # -> web/public/data/*.json
cd web && cp .env.example .env.local            # add a Mapbox public token
npm install && npm run dev                      # http://localhost:5173
```

**The pages**

```
uv run python scripts/build_targeting_demo.py       # demo.html (Kansas itinerary)
uv run python scripts/build_prediction_receipt.py   # forecast.html (from data/predictions)
uv run python scripts/build_blueprint.py            # blueprint.html (figures from notebooks)
```

**The research notebooks** (jupytext percent scripts paired with executed
notebooks; exploratory, built on the tested library)

```
uv run jupytext --to ipynb --execute notebooks/mo_2026_predictions.py
```

**Election night** (Missouri's results portal, through the installed Chrome)

```
NODE_PATH=web/node_modules node scripts/fetch_mo_enr.cjs --out data/raw --prefix enr_mo_20261103
```

## How it's built

Strict test-driven development under a binding contract
([`TDD_CONTRACT.md`](TDD_CONTRACT.md)): one failing test at a time, no code
without a test that demanded it, no random seeds in numerical tests, and
every loader of real data must reproduce its state's certified totals before
anything downstream may use it. CI repeats the gates on Linux with branch
coverage ≥ 90%, dependency audit, CodeQL, mutation testing as a watchdog,
and a Playwright end-to-end gate against the production build before every
deploy.

## What it is not

Not a poll, not a voter file, not an oracle. It never says anything about an
individual, never estimates a map for an issue a state has not voted on, and
never predicts without writing the prediction down first. The limits are
stated next to every finding on purpose.

## License

See `LICENSE` (to be chosen by the author; the intent is a permissive
open-source license).
