# Contributing

Thank you for looking. This project is small, open, and built under a strict
discipline that is the reason its numbers can be trusted. The discipline is
not optional for contributions.

## Before anything else

Read `TDD_CONTRACT.md`. It is binding and it is evidence-based: every rule
in it exists because of a real bug in an earlier attempt at this exact
project. The short version:

1. One failing test at a time. Run it. See it fail. Then write the minimum
   code that makes it pass.
2. No code exists without a failing test that demanded it. Guard branches
   included.
3. Numerical code is verified without random seeds: deterministic
   constructions, noise-free recovery worlds, invariance properties.
4. Write the derivation into the test docstring before the assertion.
5. Every loader of real data reproduces its state's certified totals before
   anything downstream may use it.
6. Notebooks under `notebooks/` are exploratory and TDD-exempt, but they may
   only call the tested library for real computation.

## Setup

```
uv sync
git config core.hooksPath .githooks     # the pre-commit gate: ruff check, ruff format --check, pytest
uv run pytest
cd web && npm install && npm test       # Vitest for frontend logic
```

The pre-commit hook refuses a commit that fails lint, format, or tests.
CI (`qa.yml`) repeats those gates on Linux with branch coverage ≥ 90%,
`pip-audit`, CodeQL, and the Playwright E2E gate against the production
build before any deploy. Mutation testing runs on main as a watchdog for
hollow tests.

## What a good pull request looks like

- One concern. A loader, a finding, a page, a fix.
- The RED → GREEN sequence visible in the commits or the description.
- For a new state loader: the fixture-based unit tests, plus the acceptance
  run against certified statewide totals pasted into the PR. See
  `docs/ADD_A_STATE.md`.
- For a finding: the notebook (`.py` percent script and its executed
  `.ipynb`), and a paragraph in `docs/FINDINGS.md` with the honest limits.
- For a page: built by a script from data, not hand-edited HTML, and
  covered by a Playwright test that checks integration only.
- Docs updated: `CLAUDE.md` layout, `BACKLOG.md` if it closes or opens an
  item.

## What will be declined

- Code without a test that failed first.
- Seeds in tests, conditional guards in tests, `is True` / `is False`
  against pandas or numpy values.
- Any edit to a `data/predictions/*_REGISTERED_*` file. The freeze guard
  fails the suite on it; the protocol is that a revision is a new dated
  file.
- Claims in prose that the numbers do not support. The findings document
  prints the losses next to the wins on purpose.

## Where to start

- `docs/BRING_YOUR_OWN_STATE.md` — the lay guide to what a new state needs.
- `docs/ADD_A_STATE.md` — the programmer's companion: schema, loader
  pattern, acceptance, catalog entry.
- `docs/DATA_SOURCES.md` — where every raw file comes from.
- `BACKLOG.md` — agreed, deferred work, each item with the trigger that
  would start it. Items without a trigger are not started.

## Conduct

Be kind, be specific, show the test. Political data attracts strong
opinions; this repository has exactly one: the number has to be right and
the limits have to be stated.
