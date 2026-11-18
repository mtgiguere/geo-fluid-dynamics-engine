# The Engineering Contract

Binding for every session, human or Claude, on library and shipped code.
The goal is a project that is still trustworthy and easy to change years from
now: every number it publishes traces back to a tested function, and every
function exists because a test demanded it.

Each rule below was learned the hard way, here or in this project's two
predecessors. The stories are in git history (this file before 2026-11-18);
what stays is the rule. Code comments cite rules by their number (Bug #3,
RED FLAG 3); the index at the end keeps those citations meaningful.

---

## 1. The cycle

```
1. Write ONE test. It describes behaviour you want, not code you will write.
2. Run it. CONFIRM RED, and that it fails for the reason you expect.
3. Write the minimum code to pass it. Not one line more.
4. Run it. CONFIRM GREEN.
5. Refactor if needed; run the suite again.
6. Commit. The message describes the behaviour added.
```

- **One test at a time means one.** Two new tests blur which behaviour is
  missing when RED fires.
- **Bug fix:** first a test that reproduces the bug (RED), then the fix. The
  test stays forever.
- **An edge case you think of mid-implementation:** stop, write its test, run it.
- **Immediately GREEN is information.** Either the behaviour was already
  guaranteed (keep the test: it turns a coincidence into a guarantee), or an
  earlier cycle over-built. A run of immediately-GREEN tests means the second.
- **Derive in the docstring before the assertion.** Write the hand-math into
  the test's docstring first, then the expected value. Arithmetic done in the
  head after the fixture is written has been wrong twice.

## 2. Just-in-time

Write only the code a currently failing test demands. If you cannot point to
the failing test that needs a function, the function does not belong yet.
Speculative public functions are API surface you must maintain and that
callers use wrong. Start from what the consumer wants: the right design is
usually one public function with private steps, not a pipeline of public steps
the caller must chain in the right order.

## 3. What a test must not do (the red flags)

| # | Red flag | Instead |
|---|---|---|
| 1 | `pytest.skip("not implemented")` stub | Write the real test; let it fail |
| 2 | Conditional guard: `if len(result) > 0: assert ...` | Design the fixture so the result is never empty |
| 3 | Seed-specific assertion (`rng(42)` then a copied value) | Section 4: constructions, recovery, properties |
| 4 | `is True` / `is False` on pandas or numpy values | `== True`, `bool(...)`, or compare the value |
| 5 | Test named for the mechanism (`test_uses_groupby`) | Name the behaviour |
| 6 | Test written after the function | That is test-after; delete and redo the cycle |
| 7 | A function no failing test demanded | Section 2 |
| 8 | A public function only one private caller uses | Make it private or inline it |

A good test: a specific, deterministic input; one call; one exact expected
output or exact error. Coverage says which lines ran, not which behaviours
were checked. A test that cannot fail is documentation, not verification;
mutation testing exists to find those.

## 4. Stochastic and numerical code: verified without seeds

1. **Deterministic construction.** Find an input where chance has no room to
   act (a county adjacent to every other one has pseudo p-value exactly 1.0
   under any permutation).
2. **Noise-free recovery.** Build data from known parameters with no error
   term and demand the parameters back (SAR: y = (I - ρW)⁻¹Xβ).
3. **Properties.** Invariances and identities as Hypothesis properties
   (location-scale invariance of Moran's I; mean of local I equals global I;
   a uniform field's area-weighted mean is the field value).
4. **Reproducibility, not seed values.** Two identically seeded injected
   generators must give identical output. A published analysis may record its
   seed so the map can be re-derived. What is banned is asserting the number
   seed 42 happened to produce.

## 5. Real data falsifies your model of the world

Fixtures and implementation share the same imagination, so strict TDD alone
cannot catch a wrong idea of what the file looks like.

- **Every loader's definition of done includes a real-data acceptance run**
  against externally certified facts (official statewide or national totals).
  Every discrepancy becomes a RED test whose fixture reproduces the real row
  pattern in miniature.
- **Spot checks validate only the cells you check.** When provenance matters,
  diff the whole file against the authoritative source.
- **Guard loudly before any pivot or groupby** that could receive NaN keys.
  Aggregations silently drop NaN groups; a mapping failure must raise and
  name what failed to map.
- **Absence is explicit.** Zero ballots is not an observation; a missing
  prior election is NaN, not a shorter calendar.
- **Output-preserving refactors are proven by regeneration.** Rebuild the
  affected data products and confirm they are byte-identical.
- **Executing a notebook on real data is an acceptance run too.** Notebooks
  are exempt from test-first, not from honesty against the data.

## 6. Where meaning lives

Loaders stay politics-agnostic: they report raw yes/no and never decide which
side is "progressive." Orientation is an explicit input, named once per
consumer (`Measure.progressive_side`, the overlay's `progressive_side`). The
tell that this rule was broken: a source with flipped polarity needs a new
code path instead of a new config value.

## 7. Where the discipline reaches

- **Library and shipped code** (`src/geofluid/`, page logic): full contract.
- **Frontend: E2E verifies integration, never logic** ("the Frontend Line").
  Pure page logic (formatters, expression builders, calculators) lives in
  modules with Vitest contracts. Playwright proves the built app works at the
  real deploy path and that the pages connect.
- **Page-builder scripts** follow the same line: logic that computes a number
  a page publishes moves into the tested library; the script only assembles.
- **Notebooks / EDA are TDD-exempt.** They call tested library functions; new
  analytical capability arrives as a tested library function first. A bug
  fixed inside a notebook needs a regression test only if the same hazard
  exists in shipped code.

## 8. Changing an existing test

Legitimate only when the external contract changed (an API, file format or
standard): say so in the test docstring and the commit message. Changing a
test because the code you want to write doesn't satisfy it is deleting the
specification. Never.

## 9. Gates and guardrails

```
uv run ruff check .
uv run ruff format .    # if it changes files, re-run ruff check
uv run pytest           # its own step: never piped through tail or any filter
```

- `.githooks/pre-commit` enforces this (`git config core.hooksPath .githooks`
  once per clone). CI repeats it with mypy strict, branch coverage ≥ 90%,
  pip-audit and CodeQL; Playwright gates every deploy; mutation testing runs
  on every push to main as the watchdog for tests that cannot fail.
- **A rule violated once gets promoted to a mechanism.** Written rules get
  skipped; CI catches after the push; a hook cannot be skipped silently.
- **A guardrail that has never run is decoration.** Schedule its first
  verified execution as part of installing it.

## 10. Git and pull requests

- After structural git operations (stash across branches, conflicted pops,
  merges), check `git ls-files | wc -l` against the expected count before
  pushing. A single-file commit once deleted 42 files from main; the cause was
  never found. Prefer committing work in progress over stashing across
  branches.
- **A handed-over PR is final.** Further work goes to a new branch.

## 11. Debugging

- When CI and local disagree, list and diff the actual inputs (env vars,
  tokens, data, versions) before forming a theory.
- Ask Matt for the failing log early. One pasted log beats three guesses.
- Error messages must carry identifiers (URL, FIPS, file). If a failure cannot
  name its subject, fix the capture first.

## 12. Comments are for every reader

The audience includes policymakers, journalists and students. Long comments
that explain scientific method (what is done, why this approach, what the
result means, its limits, what was rejected) are a feature. A lint rule that
fights this is configured away, with the reason written down.

---

## Index of cited numbers

Kept so citations in code and tests still point somewhere.

| Cited as | Rule |
|---|---|
| Bug #1 | Column-name drift between producer and consumer: write the shared schema as a test before either side |
| Bug #2 | Empty input must keep its columns; never KeyError on an empty frame |
| Bug #3 | Align by key (FIPS), never by position or assumed sort order |
| Bug #4 | RED FLAG 4: no `is True` on numpy/pandas values |
| Bug #5 | Hollow tests behind conditional guards (RED FLAG 2); mutation testing watches for them |
| Bug #8 | Blank map at the deploy path: why Playwright gates every deploy at the real base path |
| Bugs #10–12 | Real data falsified the fixtures (pseudo-candidate rows, coexisting total and sub-mode rows, zero-vote placeholders): Section 5 |
| Bug #11 pattern | Summary and total rows coexist with the detail rows; summing both double counts |
| RED FLAG n | Section 3 table |
| The Frontend Line | Section 7 |
| OPEN INCIDENT | Section 10 (single-file commit) |
