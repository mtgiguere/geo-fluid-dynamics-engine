# The TDD Contract
## Why We Do Test-Driven Development — Evidence From This Codebase

This document exists because of a deliberate experiment.

During the development of the Geo-Fluid Dynamics Engine, Claude was given significant
autonomy and explicitly allowed to use TAD (Test-After Development) instead of TDD.
The results were analyzed in a systematic retrospective. What follows is the evidence —
not theory, not best practice citations, but specific bugs, specific tests, and specific
lines of code from this project that prove why TDD is not optional.

**If you are a new Claude Code session starting work on this project: read this first.**
**If you are inclined to skip TDD "just this once": re-read this.**

---

## What TAD Looks Like (What We Did Wrong)

TAD means: design in your head → write implementation → write tests that confirm
what you just wrote → push.

The tests look fine. They pass. Coverage looks good. But something is wrong:
**the tests are asking "does this code do what I just wrote?" not "does this code do
what it SHOULD do?"** That is a completely different question.

Here is the evidence from this project.

---

## Bug #1: Column Name Drift (adoption_prob → adoption_probability)

**What happened:**

`SurvivalDiffusionModel.get_adoption_frontier()` was implemented and returned a column
named `adoption_prob`. Separately, `frontier_map.build_layer()` was implemented expecting
a column named `adoption_probability`. Both were tested individually and both passed.

When CI wired them together via the API test, it crashed:
```
ValueError: Missing required columns: ['on_frontier', 'adoption_probability']
```

**Why TAD caused it:**

I wrote `get_adoption_frontier()` and tested it knowing I named the column `adoption_prob`.
I wrote `frontier_map.build_layer()` and tested it knowing I expected `adoption_probability`.
Both tests confirmed what I just coded. Neither test specified the contract between them.

**What TDD would have done:**

Write this test first, before implementing either function:
```python
def test_frontier_output_is_consumable_by_frontier_map():
    frontier = model.get_adoption_frontier()
    # This test specifies the contract between two functions
    result = frontier_map.build_layer(frontier)
    assert result["type"] == "FeatureCollection"
```

That test would fail immediately on the first implementation attempt because the column
name would be wrong. The contract would be specified before either function was written.

---

## Bug #2: Empty DataFrame KeyError (node_classifier)

**What happened:**

`classify_nodes()` was called with an empty adoption_events DataFrame.
`pd.DataFrame([])` with an empty list produces a DataFrame with **zero columns**, not
zero rows with the expected columns. So `adoption_events["topic_id"]` raised `KeyError`.

CI output:
```
KeyError: 'topic_id'
modules/gravity_engine/processing/node_classifier.py:87
```

**Why TAD caused it:**

I wrote `_compute_county_stats()` and tested it with non-empty adoption_events.
The happy path worked. I never asked "what does an empty adoption_events look like?"
because I was thinking about the implementation I just wrote, not the contract.

**What TDD would have done:**

Before writing a single line of `_compute_county_stats()`, write this test:
```python
def test_classify_nodes_with_no_adopters_for_topic():
    """Topic 2 has no adopters — function must not crash."""
    ae = _make_adoption_events({}, topic_id=2)  # empty dict → empty DataFrame
    result = classify_nodes(panel, out_c, in_c, fips_index, ae, topic_id=2)
    assert result["node_type"].isin(NODE_TYPES).all()
```

Watch it fail. Then write the guard. The bug never ships.

---

## Bug #3: FIPS Sort Order (The Comment That Lied)

**What happened:**

In `test_spatial_weights.py`, the test comment read:
```python
fips_order = sorted(panel["fips"].unique())
sup_vec = np.array(support)   # ordered: 29169, 29183, 29189 alphabetically
```

The comment said alphabetically. The code used `support` which was in **insertion order**
`[29169, 29189, 29183]`. The test had been wrong since it was written. CI found it:

```
assert np.float64(0.15000000000000002) < 1e-06
```

**Why TAD caused it:**

I wrote the test knowing the implementation sorts alphabetically. I wrote the assertion
knowing what I intended. I wrote the comment to remind myself. Then I wrote the wrong code
in the assertion because I was thinking about `support` in the order I created it, not in
the order the implementation would use it.

**What TDD would have done:**

Write the test first with an explicit mapping that makes the expected output unambiguous:
```python
fips_to_support = {"29169": 0.3, "29189": 0.6, "29183": 0.9}
fips_order = sorted(panel["fips"].unique())
sup_vec = np.array([fips_to_support[f] for f in fips_order])
```

The explicit mapping cannot lie. The comment can.

---

## Bug #4: The np.True_ Identity Check

**What happened:**

Three tests in `test_rolloff.py` failed with:
```
assert np.True_ is True   →   AssertionError
assert np.False_ is False →   AssertionError
```

**Why TAD caused it:**

I was thinking about boolean logic when I wrote the tests. I knew the implementation
would produce True/False values. I used `is True` because that's what you write when
you're thinking "this should be True." I wasn't thinking about what pandas actually
returns — numpy scalars, not Python singletons.

**What TDD would have done:**

If you write the test first and actually RUN it to confirm it fails (the RED step),
you immediately discover that the implementation doesn't exist yet, and you think carefully
about what the assertion syntax should be. The RED step forces you to think about the
assertion before the implementation.

The correct pattern — never use `is True` or `is False` with pandas/numpy values:
```python
assert result["is_false_bastion"]        # truthiness check — works with np.bool_
assert not result["is_false_bastion"]
assert result["is_false_bastion"] == True  # value equality — not identity
```

---

## Bug #5: Eight Hollow Tests That Cannot Fail

**What happened:**

The retrospective analysis found 8 tests with conditional guards that let the
core assertion bypass entirely. The test runs, it passes, coverage is counted.
But the thing being tested is never actually verified.

Example:
```python
def test_wombling_value_equals_support_difference():
    """With support [0.8, 0.3], wombling_value should be 0.5."""
    ...
    if len(result) > 0:           # ← hollow guard
        assert abs(result.iloc[0]["wombling_value"] - 0.5) < 1e-6
```

If `result` is empty — because the adjacency detection has a bug — this test passes.
The bug ships. The test reported 100% on this line.

**Why TAD caused it:**

I knew the implementation sometimes returns empty results for edge cases. I added the
guard to avoid flaky tests. But I was protecting the implementation from the test,
which is exactly backwards. Tests are supposed to catch bugs. Guards prevent that.

**What TDD would have done:**

Write the test first. It specifies that for two adjacent polygons with supports 0.8
and 0.3, the output must be non-empty and must have wombling_value ≈ 0.5. Full stop.
```python
def test_wombling_value_equals_support_difference():
    gdf = _make_adjacent_counties()
    W = np.array([[0, 1], [1, 0]], dtype=float)
    support = pd.Series({"A": 0.8, "B": 0.3})
    result = lattice_wombling(gdf, support, W, ["A", "B"])
    assert len(result) == 1, "Two adjacent counties must produce one boundary"
    assert abs(result.iloc[0]["wombling_value"] - 0.5) < 1e-6
```

No guard. If the function doesn't detect the boundary, the test fails loudly.

---

## What 100% Coverage Actually Means

Coverage tells you which lines were **executed**. It does not tell you which behaviors
were **verified**.

Example: `compute_ifs(0.5, 0.5)` achieves 100% line coverage of `compute_ifs`.
It does not test:
- `compute_ifs(float('nan'), 0.5)` → returns NaN silently
- `compute_ifs(-0.1, 0.5)` → `np.clip` handles it, but was that specified?
- `compute_ifs(0.0, 0.5)` → geometric mean property, verified?
- `compute_ifs(1.0, 1.0)` → what does full-danger look like?

86% coverage with TAD ≠ 86% of behavior verified.
70% coverage with TDD > 86% coverage with TAD.

The number that matters is: **what fraction of the behavioral contract is specified
in tests before the code is written?**

---

## The Actual TDD Discipline — Not Theory, Instructions

### The Sequence (Non-Negotiable)

```
1. Write one test. It must describe behavior you want, not code you will write.
2. Run the test. CONFIRM IT FAILS (RED). If it passes, the test is wrong.
3. Write the minimum code to make it pass. Not more.
4. Run the test. CONFIRM IT PASSES (GREEN).
5. Refactor if needed. Run tests again.
6. Commit. The commit message describes the behavior added, not the code written.
7. Repeat.
```

The RED step is not optional. If you skip it, you are doing TAD.

### Pre-Commit — Run the Linters Locally First

CI catching a linter error is not a minor inconvenience. It means you pushed
broken code, wasted pipeline minutes, and added a noise commit ("fix lint") to
the history. The fix is simple: run the linters before committing, not after.

```bash
# Before every commit — Python
uv run ruff check .
uv run pytest --no-header -q

# Before every commit — R (when analysis/ files changed)
Rscript --vanilla -e "lintr::lint_package()"
```

If any of these fail, do not commit. Fix the issue first.

### Comments Are for Every Reader — Not Just Developers

This project is deliberately public. Its audience is not only software engineers.
It includes policymakers, researchers, journalists, students, and anyone who cares
about freshwater and human welfare. The code should be legible to a motivated
non-developer who is willing to read carefully.

**This means: long, explanatory comments are a feature, not a code smell.**

When implementing scientific methodology — a hypothesis test, a model specification,
a data transformation decision — write a comment that explains:
- What the code is doing in plain language
- WHY this approach was chosen
- What the expected result means
- What the limitation is
- What alternative was considered and rejected

```r
# H7 requires a fundamentally different empirical approach from H1-H6.
# The mechanism operates over 10-30 year horizons:
#   - Countries deplete aquifers today for agriculture
#   - 10-20 years later, groundwater runs out
#   - Agriculture collapses, food prices rise, instability follows
#
# The correct test: controlling for baseline income, do countries with faster
# aquifer depletion achieve lower SUBSEQUENT economic performance?
```

This is not over-commenting. This is open science. A UN analyst, a journalist,
or a student should be able to read this and understand what we are testing and why.

**Linters that fight this goal should be configured away — not obeyed.**

`commented_code_linter` (R) is disabled in `.lintr` because it would flag
methodological commentary as violations. The linter serves the project, not the
other way around. When a lint rule conflicts with the project's purpose, disable
the rule and document why.

### Red Flag Signals — Stop and Fix Before Proceeding

If you find yourself writing any of the following, you are not doing TDD:

```python
# RED FLAG 1: Skip guard without confirmed implementation
pytest.skip("not implemented")  # wrong — this is the TDD stub; DON'T add the code yet

# RED FLAG 2: Conditional guard hiding assertion
if len(result) > 0:
    assert something  # wrong — design fixture so result is always non-empty

# RED FLAG 3: Seed-specific assertion
rng = np.random.default_rng(42)  # wrong — use property-based testing for algorithms
assert some_trend_holds()         #        or construct data so the property is guaranteed

# RED FLAG 4: Identity check with pandas/numpy
assert result["col"] is True     # wrong — always
assert result["col"] is False    # wrong — always

# RED FLAG 5: Test name that describes implementation
def test_calls_psycopg2_connect():  # wrong — tests describe behavior not mechanism
def test_uses_groupby():

# RED FLAG 6: Test written after the function it tests
# (you wrote parse(), then wrote test_parse() — that is TAD)
```

### What a Good Test Looks Like

A good test is written **before the implementation** and specifies:
1. Given this specific, deterministic input
2. When this function is called
3. Then this exact output is produced (or this exact error is raised)

```python
def test_adoption_year_is_first_crossing():
    """Specifies: the adoption year is the FIRST year support crosses the threshold.
    Not the last. Not any year. The first."""
    support = pd.DataFrame({
        "fips": ["29169"] * 4,
        "topic_id": [1] * 4,
        "year": [2012, 2016, 2020, 2024],
        "support_pct": [0.40, 0.48, 0.52, 0.58],
    })
    events = compute_adoption_events(support, topic_id=1, threshold_pct=0.50)
    row = events[events["fips"] == "29169"].iloc[0]
    assert row["first_adoption_year"] == 2020  # not 2024; not 2016
```

This test was written before the implementation. It fails before the implementation.
It specifies exactly one thing. It has no guards. It has no seeds. It has one expected value.

### Using Hypothesis for Algorithmic Code

For mathematical functions (IFS, CCI, spatial weights, survival probability),
seed-based testing is always wrong. Use Hypothesis:

```python
from hypothesis import given, strategies as st

@given(
    cci=st.floats(0.0, 1.0, allow_nan=False),
    ili=st.floats(0.0, 1.0, allow_nan=False),
)
def test_ifs_always_in_0_1(cci, ili):
    """Property: IFS is always in [0, 1] for valid inputs."""
    assert 0.0 <= compute_ifs(cci, ili) <= 1.0
```

Hypothesis will find the edge cases you didn't think of.

### Property Tests Emerge Naturally From Strict TDD

You do not always need Hypothesis to write a property test. When you ask
"what must be true about this output regardless of the specific input?" — you are
already thinking in properties. Strict TDD surfaces this naturally.

During GFIP Phase 1 GRACE ingest development, the spatial aggregation test was written as:

```python
def test_load_grace_area_weighted_mean_of_constant_equals_that_constant():
    """Property: area-weighted mean of a spatially uniform field must equal the field value.
    This holds regardless of country shape or latitude.
    """
    for value in [-3.5, 0.0, 2.8]:
        ds = _make_dataset(value=value)
        result = load_grace(ds, shapes)
        assert abs(result.iloc[0]["grace_lwe_anomaly_cm"] - value) < 1e-6
```

This test was not designed. It emerged from asking "what must always be true about
area-weighted mean?" — the answer is: a uniform field must return the field value.
That property is independent of grid resolution, country shape, or latitude.

If the cos(lat) weights were wrong, this test would catch it for any input value.
A seed-based test (`assert result == 1.847...`) would only catch it for that one case.

**The pattern:** When testing mathematical or spatial functions, ask:
- What invariant must hold for all valid inputs?
- What relationship must be preserved regardless of the specific values?
- What property would be violated if my algorithm is wrong?

That question — not the specific expected output — is the test. It is more powerful
than any hand-calculated expected value, and it emerges naturally from strict TDD
because strict TDD forces you to think about behavior before implementation.

### When a Test Is Immediately GREEN — That Is Also Information

During GFIP Phase 1 development, two tests passed without driving any code change:
- Year column is integer dtype (pivot preserves int64 automatically)
- Tiny country with no grid cells gets NaN (weighted mean of empty mask = NaN naturally)

When a test you write is immediately GREEN, it means one of two things:
1. The behavior was already guaranteed by your implementation choice — the test
   is still valuable as a regression guard, confirming the guarantee is real.
2. The test is redundant — it confirms something another test already covers.

In strict TDD, an immediately GREEN test is not a failure. It is the process telling
you something about your implementation that you could not have known without running
it. Write the test. See GREEN. Note the reason. Move on.

---

## The Conversation You Will Have

At some point you will think:

> "This is a simple function. I know exactly what it does. Writing the test first
> is just busywork. I'll write the test after — it'll be faster."

That is exactly what happened in this project. Every time. The function that felt
simple had a bug. The test written after documented the bug. CI found it later.

The bugs above were not from complex functions. They were from:
- A column being named `adoption_prob` instead of `adoption_probability`
- An empty DataFrame having zero columns instead of zero rows
- A comment that said "alphabetically" while the code did insertion order
- A boolean being `np.True_` instead of `True`

None of these required deep thinking to get right. All of them required writing the
test first so the contract was specified before the code was written.

---

## The Standing Instruction for This Project

**For every new function added to this codebase:**

1. Write the test in the test file. Run pytest. Confirm RED.
2. Write the implementation. Run pytest. Confirm GREEN.
3. Then and only then, open a PR.

**For every bug fix:**
1. Write a test that reproduces the bug. Confirm RED.
2. Fix the bug. Confirm GREEN.
3. The test stays in the suite permanently.

**For every edge case you think of while implementing:**
1. Stop implementing. Write the edge case test first.
2. Run it. Confirm RED (or discover the implementation already handles it).
3. Continue.

This is not about discipline or methodology. This is about the specific, documented
bugs in this codebase that would not exist if we had done this.

---

## Summary of Evidence

| Bug | How Found | TDD Prevention |
|-----|-----------|----------------|
| `adoption_prob` vs `adoption_probability` | CI failure after PR merge | Interface contract test written before either function |
| Empty DataFrame KeyError in node_classifier | CI failure | Test with empty adoption_events before implementation |
| FIPS sort order mismatch | CI failure | Explicit mapping in test rather than `np.array(support)` |
| `np.True_ is True` assertion failure | CI failure | RED step forces you to think about assertion syntax |
| 8 hollow tests with conditional guards | Manual retrospective | No guards — design fixture to guarantee non-empty result |
| 20+ seed-dependent assertions | Manual retrospective | Hypothesis property tests |
| Column naming inconsistency (node types) | Manual retrospective | Enum defined in test file before any implementation |
| Blank map on GitHub Pages (BASE_URL prefix missing) | Human opened deployed URL | Playwright E2E test runs against actual built app at real deployment path |

Bugs #1–#7 were caught by CI or by a human reviewing. Bug #8 was caught by a human opening
a browser against the live deployment.
**Tests that don't catch bugs are documentation, not verification.**

---

## Groundshift Examples — Evidence From This Codebase

*Added after the first full TDD development arc on Groundshift. These examples are from
real sessions on this project, not the GFIP predecessor. They are here because future
Claude Code sessions need concrete examples from this codebase, not just the prior one.*

---

### Bug #9 (Groundshift): The Silent threat_tier — How a Test Can Have the Same Bug as the Code

**What happened:**

`make_plugin` in `tests/unit/conftest.py` accepted a `threat_tier` parameter and passed it
to `PluginMetadata`. But when constructing `SuitabilityModifier`, the implementation was:

```python
metadata={}
```

The `threat_tier` from `PluginMetadata` was never copied into `SuitabilityModifier.metadata`.
The aggregator reads `metadata["threat_tier"]` to route modifiers into the correct tier.
With `metadata={}`, every plugin was routed as `"stress"` tier regardless of its declared tier.

The existing tests all passed. They were testing the wrong thing — they exercised the
aggregation formula, but with stress-tier routing for all plugins, even existential ones.
An existential plugin that should have applied Liebig's ceiling (`min(envelope, factor)`)
was instead applying the stress formula (`envelope × factor`).

**Why TDD almost didn't catch it:**

The test was written **after** the conftest was written, confirming the behavior of the code
that already existed. Because the conftest bug was in the test infrastructure itself, even
TDD-style tests inherited the bug. The test was asking "does this code do what I just wrote?"
rather than "does this code do what it should do?"

**What caught it:**

A codebase review during session onboarding found the mismatch between the `PluginMetadata`
field and the hardcoded `metadata={}`. A regression test was written first:

```python
def test_existential_tier_plugin_applies_liebig_ceiling_not_multiplicative(make_plugin):
    # existential factor=0.3, envelope=0.8:
    #   correct (existential): min(0.8, 0.3) = 0.3
    #   wrong   (stress bug):  0.8 × 0.3    = 0.24
    registry = PluginRegistry()
    registry.register(make_plugin("p1", factor=0.3, probability=1.0, threat_tier="existential"))
    result = Scorer(registry).run(_da(0.8), REGION, TIME_RANGE, CROP_PROFILE)
    assert float(result.score.mean()) == pytest.approx(0.3)
```

**That test was RED.** The conftest bug was confirmed. Then the fix was written: copy
`threat_tier` and `custom_weight` from `PluginMetadata` into `SuitabilityModifier.metadata`.

**The lesson for this codebase:**

`SuitabilityModifier.metadata` **must** contain `"threat_tier"` (and `"custom_weight"` if
the tier is `"custom"`). These are how the aggregator routes. If they are missing or
wrong, the aggregator silently falls back to stress-tier routing. This is not a graceful
fallback — it is silent scientific error that produces plausible-but-wrong output.

The fix is documented in `tests/unit/conftest.py`. The regression test
`test_existential_tier_plugin_applies_liebig_ceiling_not_multiplicative` must never be
removed — it is the only test that would catch this class of routing bug.

---

### Observation #1 (Groundshift): An Immediately GREEN Test Is Information

During calibration anchor development, a test was written for the case where an anchor
is completely outside the run region — the clip returns empty and `mean()` produces `NaN`:

```python
def test_score_anchors_no_alert_when_anchor_outside_result_extent():
    anchor = _anchor("origin_center", 100.0, 80.0, 110.0, 85.0)
    results = score_anchors(_make_result(), [anchor])
    assert results[0].alert_triggered is False
```

This test passed immediately without any code change. The reason: in Python,
`NaN < 0.70` evaluates to `False`. The alert condition `expected_min is not None and mean_score < expected_min`
was already NaN-safe by language semantics, not by any defensive code.

**This is not a failed TDD step — it is TDD doing its job.** The test confirmed a
behavioral guarantee that could not have been known without running it. The test stays
in the suite as a regression guard. If someone later adds a `math.isnan` check that
accidentally changes this behavior, the test will catch it.

This is also why the RED step matters: writing the test and *running it* to see GREEN
is different from writing the test and *assuming* it will be GREEN. Assumptions are often
wrong. Python's NaN comparison semantics are subtle enough that many developers would
expect `NaN < 0.70` to raise rather than return False. The test proved the behavior.

---

### Observation #2 (Groundshift): The RED Step Reveals Design Gaps

When the CLI integration test was written:
```python
args = parser.parse_args(["run", "--crop", "coffee", "--region", "ethiopia", "--phase", "describe"])
```

The RED step revealed: `FileNotFoundError: coffee.yaml not found`. Only `coffee_arabica.yaml`
existed. The test did not fail for the expected reason (`ImportError: run_describe`).

This is RED step discipline paying off. The test failed for a design reason that needed
a decision: does `--crop coffee` mean arabica? Is arabica the default? Should `coffee_arabica`
be the canonical ID? The decision was made (yes, `coffee` means arabica), a `coffee.yaml`
alias was created, and then the test failed for the correct reason before implementation
proceeded.

If the test had been written after the implementation (TAD), the developer would have
written `--crop coffee_arabica` to match the file that existed, and `--crop coffee` would
have been a silent gap. The RED step forced the interface question into the open.

---

### Process Rule (Groundshift): ruff format Is Not Optional

`ruff check` catches code quality issues. `ruff format` enforces consistent code style.
Both must pass before every commit. The pre-commit sequence is always:

```bash
ruff check .
ruff format .
pytest
```

Running only `ruff check` and skipping `ruff format` will result in formatting drift that
accumulates across commits and forces manual cleanup. This happened multiple times in
early Groundshift sessions. The fix is mechanical: always run both, always in that order.

If `ruff format` changes any files, re-run `ruff check` to confirm no new issues were
introduced. Then commit.

---

### Observation #3 (Groundshift): The 14-Test Cascade — TDD Catches Breaking Changes Instantly

When `DescribePhaseRunner.run()` changed its return type from `SuitabilityResult` to
`DescribeResult`, 14 tests failed at once — precisely identifying every call site that
needed updating.

```
FAILED tests/integration/test_describe_phase_smoke.py::test_pipeline_returns_suitability_result
FAILED tests/integration/test_describe_phase_smoke.py::test_score_is_a_dataarray
FAILED tests/integration/test_describe_phase_smoke.py::test_confidence_is_a_dataarray
... (14 total)
```

Without the test suite, this breaking change would have been silent until runtime — or
worse, produced wrong output without crashing (the old `.score` attribute would have
thrown an `AttributeError` on the `DescribeResult` object, but only when that code path
was exercised by a real run).

The cascade also made the fix mechanical: each failing test told you exactly what
attribute access needed to change (`result.score` → `result.suitability.score`).
No guessing, no grepping, no fear that you missed a call site.

**The lesson for this codebase:**

Breaking interface changes are not dangerous when there is a test suite. They are
*only* dangerous without one. TDD means breaking changes are caught at commit time
(seconds) instead of deploy time (minutes or hours later, under real data conditions).

This pattern will recur when `PredictPhaseRunner` is added (it will return
`PredictResult`, not `SuitabilityResult`). The same cascade will happen and be just
as easy to fix.

---

### Process Rule (Groundshift): Fix Code Smells Immediately

During a retrospective on the imagery pipeline, two instances of defensive `getattr`
were found in `cli.py`:

```python
if getattr(args, "source", "worldclim") == "era5":  # should be: if args.source == "era5":
if getattr(args, "imagery", None) == "sentinel2":   # should be: if args.imagery == "sentinel2":
```

Both arguments are always set by the argparse parser (with defaults). The `getattr`
pattern implied mistrust of the parser that wasn't justified and obscured intent.

These were fixed immediately — not deferred to "next session" or "when we get a chance."
Small code smells deferred are code smells forgotten. Fix them at the retrospective
when they are fresh, not later when they are invisible.

---

### Updated Summary of Evidence

| Bug / Observation | How Found | TDD Prevention |
|---|---|---|
| `adoption_prob` vs `adoption_probability` (GFIP) | CI failure after PR merge | Interface contract test before either function |
| Empty DataFrame KeyError in node_classifier (GFIP) | CI failure | Test with empty input before implementation |
| FIPS sort order mismatch (GFIP) | CI failure | Explicit mapping in test, not array literal |
| `np.True_ is True` assertion failure (GFIP) | CI failure | RED step forces assertion syntax thought |
| 8 hollow tests with conditional guards (GFIP) | Manual retrospective | No guards — design fixture to guarantee result |
| 20+ seed-dependent assertions (GFIP) | Manual retrospective | Hypothesis property tests |
| Column naming inconsistency (GFIP) | Manual retrospective | Enum defined in test before any implementation |
| Blank map on GitHub Pages (GFIP) | Human opened deployed URL | Playwright E2E test runs against real deployment |
| Silent `threat_tier` routing bug (Groundshift) | Codebase review + regression test | Test specifies existential-vs-stress tier outcome before fix |
| `--crop coffee` vs `coffee_arabica.yaml` (Groundshift) | RED step revealed wrong failure reason | RED step forces interface question before implementation |
| NaN anchor alert (Groundshift) | Immediately GREEN | Confirmed Python NaN comparison semantics as guarantee |
| `DescribeResult` return type change (Groundshift) | 14-test cascade at commit time | Precise failure list; fixed in minutes with no missed call sites |
| Defensive `getattr` in CLI (Groundshift) | Retrospective code review | Fixed immediately; deferred smells become invisible smells |
| "TOTAL VOTES CAST" pseudo-candidate doubled Milwaukee (GFDE) | Real-data acceptance run | RED test reproducing the real row pattern before the fix |
| TOTAL rows + sub-mode rows coexist; Harris County 4.5× (GFDE) | Real-data acceptance run | Same — fixtures modeled on the real file, not imagination |
| Zero-vote placeholder TOTAL rows zeroed four states (GFDE) | Real-data acceptance run | RED before refining the precedence rule |

---

*This document was written after the fact as an honest retrospective.*
*Its purpose is to prevent future sessions from repeating the same patterns.*
*The evidence in it is real. The bugs were real. The fixes were real.*
*Do the work in the right order.*

---

## Bug #8: The Blank Map — What E2E Tests Would Have Caught

This bug is different from #1–#7. It was not a logic error in a function. It was a
**deployment configuration error** — the kind no unit test can see, because unit tests
run against components in isolation, not against an actual built app served from a real URL.

When GFIP was deployed to GitHub Pages at
`https://mtgiguere.github.io/global_freshwater_intelligence_project/`, the dashboard loaded
but the map was blank and all panels showed no data. Every fetch for JSON was returning 404.
The cause:

Static JSON files were being fetched with paths beginning with `/`:
```typescript
const url = `/data/global-risk.json`
```

GitHub Pages serves the app at the sub-path `/global_freshwater_intelligence_project/`.
An absolute `/data/...` path resolves from the domain root — which 404s. The files were
actually at `/global_freshwater_intelligence_project/data/...`.

The fix was to prefix all static paths with `import.meta.env.BASE_URL` — a Vite variable
set to the deployment sub-path at build time:
```typescript
const url = `${import.meta.env.BASE_URL}data/global-risk.json`
```

**Why no existing test caught it:**

- Unit tests mock `fetch`. The mock does not care what path is requested.
- Vitest/RTL runs in jsdom, not in a built app with a real URL structure.
- TypeScript compiles correctly regardless of what string is inside the backtick.
- CI passed: 177 Python tests green · 43 frontend tests green · 97% coverage · zero lint errors.

Then the map was blank the first time a human opened the deployed URL.

**What an E2E test would have done:**

An E2E test runs the production build, serves it from a real HTTP server at the actual
deployment path, launches a real browser, and navigates to the URL. It mocks nothing.
It exercises the full stack: Vite build → `BASE_URL` injection → browser fetch → real HTTP
response → component render. The test would fail at the first canvas visibility check
because the canvas never receives data — before any human opens a browser.

---

## The E2E Testing Gap

**What GFIP has:**
- 177 Python unit/integration tests (strict TDD)
- 43 React unit tests (Vitest + RTL)
- 97% line coverage

**What GFIP does not have:**
- Any test that runs against the actual built app in an actual browser

These are fundamentally different verification levels. Unit tests verify that individual
functions satisfy their contracts. E2E tests verify that the **integrated system** — built,
bundled, served at its real URL — works for a real user completing a real task.

Bugs #1–#7 are unit-level failures. Bug #8 is a deployment-level failure.
No amount of unit test coverage can prevent it, because it lives in the gap between
"this component has a correct implementation" and "this app works when deployed to this URL."

### The Right Tool: Playwright

Playwright is the correct E2E testing tool for this stack. It:
- Runs real Chromium, Firefox, and WebKit — not a DOM simulation
- Installs alongside Vitest without conflict: `npm install -D @playwright/test`
- Tests both the local dev server and the production build (set `baseURL` per environment)
- Waits reliably on network requests, DOM elements, and canvas rendering
- Produces a video recording and screenshots on failure — the most useful artefact
  for diagnosing deployment bugs, because it shows exactly what a browser saw

Configure it with a `playwright.config.ts` at the `dashboard/` root alongside
`vite.config.ts`. The two runners are invoked separately (`npx playwright test` vs
`npm test`) and do not interfere.

### Golden Path Scenarios for GFIP

A golden path test covers the most important thing a user would try to do. For GFIP,
there are six. Each should be one Playwright test.

**1. Map loads with coloured countries**
```typescript
test('map renders with coloured countries on load', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('canvas')).toBeVisible({ timeout: 10_000 })
  await expect(page.getByText(/countries loaded/)).toBeVisible()
})
```
*What this catches:* BASE_URL path bug, CORS failures, blank-canvas rendering failures,
broken static JSON fetches. If this test had existed, Bug #8 would have been caught in CI
before any human opened the deployed URL.

**2. Click a country — info bar appears**
```typescript
test('clicking a country shows its name and CRS score', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('canvas')).toBeVisible({ timeout: 10_000 })
  await page.locator('canvas').click({ position: { x: 480, y: 240 } })
  await expect(page.getByText(/CRS:/)).toBeVisible()
})
```
*What this catches:* GeoJSON click handler, numericToIso3 lookup, risk data join.

**3. Country Deep Dive — chart renders with real data**
```typescript
test('Country Deep Dive shows a time-series chart', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Country Deep Dive' }).click()
  // Recharts renders SVG paths — at least one path means data arrived
  await expect(page.locator('.recharts-line-curve').first()).toBeVisible({ timeout: 10_000 })
})
```
*What this catches:* country detail fetch, chart data format, Recharts rendering.

**4. ML Futures — forecast scores appear**
```typescript
test('ML Futures shows three score bars for the default country', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'ML Futures' }).click()
  await expect(page.getByText('Water Scarcity Forecast')).toBeVisible({ timeout: 10_000 })
  await expect(page.getByText('Political Instability Forecast')).toBeVisible()
  await expect(page.getByText('Displacement Pressure Forecast')).toBeVisible()
})
```
*What this catches:* prediction endpoint fetch, score bar rendering, is_trained banner logic.

**5. Outcomes Explorer — all seven hypothesis cards appear**
```typescript
test('Outcomes Explorer renders all seven hypothesis cards', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Outcomes Explorer' }).click()
  for (const h of ['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7']) {
    await expect(page.getByRole('heading', { name: new RegExp(`^${h}`) }))
      .toBeVisible({ timeout: 10_000 })
  }
})
```
*What this catches:* hypotheses endpoint, card rendering, insights text display.

**6. Country search — type to select, panel updates**
```typescript
test('searching for a country and selecting it updates the deep dive', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Country Deep Dive' }).click()
  await page.getByPlaceholder(/search/i).fill('Kenya')
  await page.getByText('Kenya').first().click()
  await expect(page.getByText(/Kenya/)).toBeVisible()
})
```
*What this catches:* CountrySearch autocomplete, country selection state, panel re-render.

### When to Run E2E Tests

E2E tests are slower than unit tests (seconds per test vs milliseconds). The right cadence:

- **CI on pushes to `main`**: run after the unit test suite passes — not on every feature
  branch commit, where they would slow the development feedback loop.
- **Before any deployment**: run `npx playwright test` locally after `npm run build`
  before pushing changes to `vite.config.ts`, `client.ts`, or GitHub Actions workflows.
- **After any configuration change**: `BASE_URL`, `VITE_BASE_PATH`, CSP headers, or
  sub-path routing — any of these can produce Bug #8-class failures that only E2E catches.

The unit test suite remains the fast development feedback loop. E2E tests are the
deployment gate. Both are required; neither replaces the other.

### The Lesson

> 177 unit tests + 43 component tests + 97% coverage + zero lint errors
> = a completely passing CI suite
> = a blank map when the first user opens the deployed URL.
>
> Coverage measures which lines were executed. It does not measure whether the app
> works for a person using a browser. Those are different questions. Both must be asked.

---

## Just-In-Time Programming — The Other Half of the Discipline

TDD tells you *how* to build. Just-In-Time (JIT) programming tells you *what* to build
and *when*. Together they are the same discipline from two angles.

**The JIT rule:**

> Write only the code that a currently failing test demands.
> Do not write code for needs that do not yet exist.

This sounds obvious. It is not practiced. Here is what violating it looks like:

```python
# VIOLATION: writing a helper "because it might be useful later"
def filter_variables(df, variables):   # no test demands this as a public function
    ...                                # it exists because I imagined a future caller

def validate_schema(df):               # same — planned upfront, not test-driven
    ...
```

Both functions were written during the GFIP AQUASTAT batch approach because the
developer anticipated they would be needed. No test demanded them as public functions.
The strict TDD pass eliminated both — not because they were wrong, but because they
were *premature*.

**The tell:**

If you are about to write a function and you cannot point to a currently failing test
that demands it — stop. The function does not belong yet.

When the need arrives, a test will fail. That failing test is your permission to write
the function. Not before.

**Why this matters:**

Every speculative public function is API surface that has to be maintained, tested,
documented, and kept consistent with the rest of the codebase. Speculative functions
that never get called are pure cost. Speculative functions that *do* get called but
were designed for an imagined use case often get called *wrong*.

JIT is not laziness. It is the discipline of trusting that the tests will tell you
what to build, in the order you need to build it.

**The connection to TDD:**

TDD enforces JIT automatically. You cannot write speculative code and have it be tested,
because the test is supposed to come first. If you find yourself writing code before the
test, you are violating both TDD and JIT simultaneously.

The sequence "write test → write minimum code → repeat" *is* just-in-time programming.
The "minimum code" step is JIT: not one line more than the failing test requires.

**A RED FLAG specific to JIT violations:**

```python
# RED FLAG 7: Function with no failing test demanding it
def _compute_auxiliary_stats(df):   # who called this? what test failed without it?
    ...

# RED FLAG 8: Public function that is only called by one private function
def parse_raw_csv(path):            # if only load_aquastat() calls this, it should
    ...                             # be private or inlined — no external test demands it
```

---

## What We Learned: Batch TDD vs Strict TDD

This section documents a deliberate experiment run during GFIP Phase 1 development.
The same module (AQUASTAT ingest) was written twice: once with batch TDD ("tests-first
design") and once with strict TDD (one test, RED, minimum code, GREEN, repeat).

### The experiment

**Batch approach:** All 17 tests written at once. RED confirmed once as a batch (ImportError).
Full implementation written at once. GREEN confirmed.

**Strict TDD:** One test at a time. RED confirmed individually. Minimum code to pass that
one test. GREEN confirmed. Next test.

### What changed

| | Batch | Strict TDD |
|---|---|---|
| Public functions | 5 | 1 |
| Lines of implementation | 52 | 27 |
| Tests | 17 | 8 |
| Branch coverage | 99% | 100% |

### Why the designs diverged

**1. Starting from consumer behavior collapses the API.**

Batch approach started from "what functions do I need?" and produced 5 public functions:
`parse_raw_csv`, `filter_variables`, `pivot_to_wide`, `map_country_codes`, `validate_schema`.

Strict TDD started from "what does the consumer want?" and produced 1 public function:
`load_aquastat`. The internal steps became private implementation details.

The consumer cannot call the pipeline steps in the wrong order. They cannot forget to call
`validate_schema`. The function guarantees its output is valid. The batch API could not.

**2. Error handling location is driven by the test, not by habit.**

Batch approach: `map_country_codes` returned NaN silently. `validate_schema` caught it
downstream. Two public functions the consumer had to remember to chain.

Strict TDD: The test said "load_aquastat raises if any country cannot be mapped." So the
check lives inside `load_aquastat`. Fail-fast, co-located with the failure, impossible to skip.

**3. Some planned functions never needed to exist.**

`validate_schema` was a public function in the batch approach because it was planned upfront.
No test ever demanded it as a public function. Strict TDD never created it.

**4. One test was immediately GREEN — and that is information.**

The year-is-integer test passed without any code change. In the batch approach this could not
be known, so a defensive cast was written anyway. Strict TDD revealed the cast was unnecessary.
When a test you write is immediately GREEN, the behavior was already guaranteed. This is not
a failure of TDD — it is TDD giving you information about your implementation.

**5. Fewer tests, but higher quality.**

17 tests → 8 tests. The batch approach tested each internal function separately. When those
functions are private, those tests verify implementation mechanics, not behavior. The 8 strict
TDD tests each verify one consumer-visible behavior. All 8 drove a code change or confirmed
a behavioral guarantee.

### The lesson

> "Tests-first design" produces the design you planned.
> Strict TDD produces the design the behavior demands.
>
> They are not the same design. The strict TDD design is simpler, better encapsulated,
> and has fewer failure modes — not because the developer was smarter, but because
> each test forced the question: "what is the minimum interface that satisfies this
> one behavior?" The answer is always simpler than what you planned.

---

## Methodological Notes — Data Limitations Discovered During EDA

These are not engineering bugs. They are scientific observations about the data that
shape how the Phase 3 analysis must be designed and interpreted.

### Annual Averages Mask Seasonal Water Stress

**Discovery (Phase 2 EDA):**
The primary exposure variable — `renewable_freshwater_percap` from AQUASTAT — is an
annual average. This makes countries like India, Pakistan, and the Sahel *appear*
adequately watered when they are effectively bone-dry for 6–9 months of the year.

**The mechanism:**
Monsoon climates receive the majority of annual precipitation in a 60–90 day window.
When the monsoon arrives, the ground is baked hard from months of heat. Water runs off
as floods rather than infiltrating to recharge aquifers. The annual "total" looks fine.
The lived reality is severe seasonal scarcity for most of the year.

**Why this matters for each hypothesis:**
- H1–H4: Cross-sectional correlations between freshwater and human outcomes are
  artificially weakened because the annual average misclassifies seasonally-arid
  countries as water-secure.
- H7 (groundwater): Monsoon countries are among the heaviest aquifer extractors
  precisely *because* surface water is seasonally unreliable. GRACE data reveals
  the depletion that annual averages hide.

**What this means for Phase 3:**
1. Annual freshwater per capita is a necessary but insufficient exposure variable.
2. Fixed effects panel regression partially addresses this by controlling for
   time-invariant country characteristics (including climate type).
3. The SPEI (Standardised Precipitation-Evapotranspiration Index) from CMIP6/WorldClim
   data captures drought duration and intensity at monthly resolution and should be
   included as a supplementary exposure variable in Phase 3 models.
4. A `seasonal_aridity_flag` (see below) should be computed and used as a moderating
   variable — effects of freshwater stress may be stronger in seasonally arid countries.

### The Seasonal Aridity Flag — Plan

**Definition:** A country-year is seasonally arid if it experiences more than 6 months
per year with average precipitation below 50mm (roughly 1.6mm/day — the standard
meteorological dry month threshold).

**Data source:** WorldClim 2.1 — 30-year average monthly precipitation at 2.5 arc-minute
resolution, available as free GeoTIFF downloads at worldclim.org.

**Implementation plan:**
1. Download 12 monthly precipitation GeoTIFFs from WorldClim 2.1.
2. Aggregate each raster to country level (area-weighted mean, same approach as GRACE).
3. For each country: count months where monthly_precip_mm < 50.
4. Output variables:
   - `dry_months_count` — integer 0–12, number of months below threshold
   - `seasonal_aridity_flag` — boolean, True if dry_months_count > 6
5. Add both to the Master Panel as static country-level features (WorldClim is a
   long-term climatological average, not time-varying — join on iso3 only, not year).

**Expected findings:**
Countries flagged: most of MENA, Sahel, Horn of Africa, Pakistan, northwestern India,
Central Asia, northern Mexico, southwestern USA, parts of Brazil (Nordeste), Australia
(interior). These are exactly the countries where the annual freshwater average
misrepresents lived water scarcity.

**Phase 3 moderation analysis:**
Run regressions separately for `seasonal_aridity_flag == True` and `== False`.
The hypothesis is that H1–H5 effect sizes will be significantly larger in the
seasonally-arid group — because in these countries, a reduction in annual freshwater
represents a reduction in an already marginal and unreliable supply, not just a
reduction from abundance.

---

## Geo-Fluid Dynamics Engine Examples — Evidence From the Rebuild

*Added 2026-06-11 after the first development arc of the GFDE rebuild (the returns and
demographics ingest modules). The contract above was written from GFIP and Groundshift
evidence; this section records what the rebuild itself taught. The headline lesson is
new: strict TDD with fixtures was followed to the letter — and the loader was still
wrong three ways, because the fixtures encoded a model of the world that the world
did not match.*

---

### Bugs #10–#12 (GFDE): Three Correct Implementations of a Wrong World-Model

**What happened:**

`load_county_returns` was built in six strict TDD cycles. Every test was written first,
every RED confirmed, no guards, no seeds, 100% branch coverage, mypy strict clean.
Then the real 94,409-row MIT county returns file was run through it, and the panel was
wrong in three distinct ways:

1. **Bug #10 — the pseudo-candidate.** Wisconsin/Vermont/West Virginia/Wyoming 2024
   carry a row `candidate="TOTAL VOTES CAST", party=NaN` holding the county's reported
   turnout. The loader mapped NaN party into `other_votes`: Milwaukee County reported
   918,421 total votes instead of 454,314 — exactly doubled.
2. **Bug #11 — total-mode rows coexist with sub-mode rows.** Texas 2024 (and Utah 2020)
   report a county's complete `TOTAL VOTES` count AND the early-vote breakdown alongside
   it, plus stray unattributed bulk rows. Summing everything gave Harris County 7.0M
   votes against 1.56M actual ballots — a 4.5× over-count.
3. **Bug #12 — zero-vote placeholder totals.** The obvious fix for #11 ("when TOTAL rows
   exist, use only them") would have silently zeroed Arkansas, Louisiana, Oklahoma, and
   Pennsylvania, whose 2024 TOTAL rows are zero-vote placeholders with the real count in
   the sub-mode rows.

**Why strict TDD did not catch them:**

The fixtures were invented from a reasonable mental model: one row per candidate per
mode, modes partition the vote. The tests verified the code against that model
perfectly. But the tests could only encode row patterns the developer knew existed.
The failure mode is not TAD's "does the code do what I just wrote?" — it is
"does the world look like what I imagined?" No amount of test-first discipline answers
that question, because the test and the implementation share the same imagination.

**What caught them:**

A real-data acceptance run: load the actual file, compare aggregates against externally
certified facts (national vote totals per election), and investigate every discrepancy.
Each discrepancy became a RED test whose fixture reproduces the *real* row pattern in
miniature (Milwaukee's pseudo-candidate, Harris County's coexisting modes, Arkansas's
zero placeholders). Then the fix. The final panel matches certified national results
for all seven elections, 2000–2024.

**The rule this adds to the discipline:**

> Fixtures specify the contract. Real data falsifies your model of the world.
> For every ingest module, a real-data acceptance run against externally verifiable
> facts is part of the definition of done — not extra credit. Validate aggregates
> against certified or published values, and treat every discrepancy as a RED test
> waiting to be written.

A corollary from the same arc: **spot checks validate only the cells you check.**
A mirror of the dataset passed spot checks (known counties, known years) while carrying
an off-by-one FIPS shift that corrupted ~146 county-years in other states. Structural
corruption needs structural comparison — when provenance matters, diff the whole file
against the authoritative source, not samples of it.

---

### Observation (GFDE): Converting Accidental Behavior Into Specified Behavior

The acceptance run found 6 county-years silently absent from the panel (Alaska's
placeholder "DISTRICT 99", a Kansas City pseudo-FIPS, defunct Bedford City VA) — all
all-zero placeholder entities dropped as a *side effect* of the Bug #12 fix. The
behavior was correct and entirely accidental.

The response was a test specifying the behavior (`zero ballots is not an observation`),
expected and confirmed immediately GREEN. Accidental correctness is a liability — the
next refactor can remove it without any test noticing. The immediately-GREEN test is
the cheapest possible insurance: it converts a coincidence into a guarantee.

---

### Process Rule (GFDE): When the World Changes, Changing the Test Is Legitimate

Mid-arc, the Census API began rejecting keyless requests (a 2025 policy change,
confirmed live: an HTML "Missing Key" page returned with HTTP 200). The existing test
specified the exact request URL without a key; the URL builder now needed one.

The existing test was *modified* — expected URL updated to include `&key=` — rather
than a new test added beside it. This is legitimate exactly when the **external
contract itself changed**, and it must be visible: the commit message and the test
docstring both record the external cause. The line being drawn:

- Changing a test because the API/file format/standard it specifies changed: correct.
  Document the cause in the test and the commit.
- Changing a test because the implementation you want to write doesn't satisfy it:
  that is deleting the specification to fit the code. Never.

---

### Process Rule (GFDE): One Test at a Time Means One

During the demographics arc, two tests were added in a single edit (sort order +
null handling) because the second "was obviously going to be immediately GREEN."
It was — and that is luck, not discipline. The prediction could have been wrong, and
with two new failing tests the RED step no longer tells you *which* behavior is
unimplemented; failure reasons blur. The cadence exists precisely so every RED has
one unambiguous cause. The violation was disclosed in the commit message; the rule
stands: one test, one RED, one GREEN, one commit.
