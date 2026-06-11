# Geo-Fluid Dynamics Engine

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

## Development

This project is built with strict test-driven development. **`TDD_CONTRACT.md` is
binding** — read it before contributing. Every function exists because a failing test
demanded it, and the commit history shows the RED → GREEN sequence.

```
uv sync          # install dependencies
uv run pytest    # run the test suite
```
