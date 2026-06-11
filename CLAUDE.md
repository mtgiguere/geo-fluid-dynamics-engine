# Geo-Fluid Dynamics Engine

Strategic civic simulator: descriptive → predictive → prescriptive analytics for how
political ideas move across geography. Five planned modules: Wave Predictor (geo-temporal
diffusion), Gravity Engine (network influence), Friction & Dissonance Mapper, Chaos &
Anomaly Sensor, Systemic Phase Transition detector.
Full spec: `docs/geo-fluid-dynamics-engine.docx`.

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

## Pre-commit sequence (before every commit)

```
uv run ruff check .
uv run ruff format .    # if this changes files, re-run ruff check
uv run pytest
```

## Commands

- `uv sync` — install dependencies
- `uv run pytest` — run the test suite
- `uv run mypy` — strict type checking

CI gates (`.github/workflows/ci.yml`): gitleaks → ruff check → ruff format --check →
mypy → pytest with branch coverage ≥ 90% → pip-audit → uv lock --check.

## Layout

- `src/geofluid/` — the package (src layout)
- `tests/unit/` — unit tests
- `TDD_CONTRACT.md` — the development contract; binding for every session
