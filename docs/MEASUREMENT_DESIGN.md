# Measurement Design — From Vote Shares to Moving Ideas

The agreed research design for the ballot-measure phase, written down (2026-08-10)
*before* any code, per JIT discipline: this document is the contract for what gets
built and in what order. It answers four questions raised in design discussion:
how to compare measures that differ in extremity, how to tell a measure's
properties apart from an electorate changing, how to predict before results
exist, and how many ideological dimensions the topic space actually has.

> **The ambition that shapes the year.** If the coming year's work can honestly
> claim "we exhaustively checked how ideas move across the map" — every claim
> calibrated on past data and falsifiable on future votes — the result is a
> presentable body of work (target: Geo Week 2027, or another geospatial /
> political-data venue). "Exhaustive" means: catalog *everything*, ingest
> *selectively* by identification value, and grade every prediction after the
> fact.

---

## 1. The measurement model: county positions × measure cutpoints

Not all measures on a topic are created equal: an outright abortion ban, a
defund-Planned-Parenthood measure, and an enshrine-choice amendment are all
"the same topic" at very different extremity. The framework that handles this
is **ideal-point estimation** (item-response theory, IRT — the same machinery
behind legislative NOMINATE scores and standardized-test calibration):

- Each **county** occupies a position (its *ideal point*) on a latent
  ideological dimension. This is the durable object we want to track over time
  — it is "disposition" from `FINDINGS.md`, made quantitative.
- Each **measure** has a *cutpoint* (severity/difficulty) on the same
  dimension: where it splits the electorate. A ban cuts far from where
  defunding cuts; an enshrine-rights measure cuts from the other side.
- Testing analogy: counties are students, measures are exam questions,
  severity is question difficulty. Which questions a county "passes" locates
  it far more precisely than any single yes/no.

Two design commitments:

- **Severity is estimated from data, not hand-assigned.** Measures order
  themselves by where they cut the electorate (if support for the ban implies
  support for defunding but not vice versa, the ban's cutpoint is revealed as
  more extreme). Hand-coded −1↔+1 scores are subjective; estimated cutpoints
  are falsifiable. Hand-coding survives only as priors/anchors where data is
  sparse.
- The existing `Measure.progressive_side` orientation flag is the **one-bit
  degenerate version** of this model (direction without extremity); the
  continuous cutpoint is its generalization, extending a seam the schema
  already has. We also hold an advantage over roll-call applications: we
  observe **continuous county vote share** per measure, not binary votes.

## 2. Identification: the overlap structure does the work

From a single measure, its severity, electorate drift, demographic change, and
neighbor influence are **observationally equivalent** — no statistic can
separate them. Identification comes from *which measures appear where and
when*; each kind of overlap kills one confound:

- **Same ballot, different measures → identifies severity.** Ohio Nov-2023
  (Issue 1 abortion + Issue 2 cannabis, identical electorate, same day) is the
  template: demographics, turnout, mood all frozen, so differences are measure
  properties. Severity is identified *cross-sectionally*, never by comparing
  across years.
- **Same measure, different times → identifies drift.** Colorado's personhood
  trio (2008/2010/2014, essentially the same maximal measure: 73→70→65% NO) is
  the mirror image: cutpoint fixed by construction, so movement is electorate
  change. Repeated measures are **anchor items** (the exam-equating trick).
  South Dakota 2006 (near-total ban) vs 2008 (ban-with-exceptions) is a
  deliberate *severity ladder* — both kinds of repeats are gold.
- **Demographic change is observed, so it is controlled, not inferred
  around.** With the ACS panel, decompose any county's movement into
  *composition* (its people changed) vs *persuasion* (the same people moved) —
  the same honesty pattern as the SAR Durbin check.
- **Neighbor influence is the spatially structured residual — the quarry, not
  a nuisance.** Severity is one number per measure (no geography); diffusion
  moves counties *differentially with spatial pattern*. Fit positions +
  cutpoints, then run Moran's I on the residuals (existing machinery, new
  object). Spatially coherent residuals = the Module 1 wave, cleanly
  separated; flat residuals = no detectable contagion beyond composition and
  drift — also worth knowing.

The formal requirement: the county × measure × time matrix must be
**connected** (some measures share ballots, some repeat, geographies overlap)
— the way NOMINATE bridges legislators across years via members serving in
both. A pile of one-off measures in disjoint states never separates severity
from drift, however large. **This turns "exhaustive ingest" into a design
problem: overlap structure, not volume, buys identification.**

## 3. Prediction without a crystal ball

The naive version is circular ("severity comes from the results we're
predicting"). The escape: severity is estimated two ways at two times.

- **Ex-post**: results locate where a measure actually cut — this calibrates
  the historical scale (using results for *past* measures is not circular).
- **Ex-ante**: a *new* measure is placed on the already-built scale from its
  **content** — provisions are readable features (total ban / exceptions /
  defunding / criminal penalty / enshrine-rights), and past measures give both
  content and estimated cutpoints to learn the mapping from. (This is the most
  concrete trigger yet for the parked NLP phase: embed measure text, predict
  cutpoint — still JIT.)

Why this is less fragile than it sounds:

1. **Most predictive power is not in the cutpoint.** County positions, drift,
   and demographics are all estimated from data we already have; a new measure
   contributes exactly one unknown scalar against a fully mapped landscape.
2. **Brackets are honest forecasts.** "More severe than KY Amdt 2 (failed
   47.6%), less severe than a total ban" already yields a falsifiable interval
   per county — ordinal placement beats a defended decimal.
3. **The uncertainty is a product.** The prescriptive shape may be a
   *severity slider*: the county map as a function of severity, showing which
   counties flip along the way — "how far can we push before losing county X"
   is the actual question a measure-drafting campaign faces.

The loop closes the house way: ex-ante placement → results → ex-post estimate
→ the gap is measured model error, every election a fresh falsification test.
(Election night itself: the first counties reporting pin the cutpoint; the
model then predicts the rest.)

## 4. Topics and dimensionality: the taxonomy is a hypothesis

Measures get **topic tags at ingest**, but how many latent dimensions the
space has is *tested, not decreed*. Candidate clusters (from the ballot-measure
record):

| Cluster | Examples | Note |
|---|---|---|
| Economic / redistributive | minimum wage, taxes, Medicaid expansion | our −0.82 economic-bastion axis |
| Cultural / moral | abortion, marriage amendments | the classic social axis |
| Personal liberty / vice | cannabis, gambling, death penalty, guns | the r≈0.62 pair lives here — generality still untested |
| Governance / rules-of-the-game | redistricting, term limits, RCV, voter ID | scrambles partisan alignment |
| Environment / land use | conservation bonds, energy mandates | |
| Labor | right-to-work, paid leave, gig classification | |

Education is a policy *area*, not an axis: bonds/funding are economic in
disguise; vouchers/curriculum are cultural in disguise — tag it, expect it to
decompose. Our own findings already imply **≥ 2 dimensions**: poor red
counties sit *right* on abortion and *left* on minimum wage — an off-diagonal
position is what makes False Bastions possible at all. The open r≈0.62
generality question becomes precise here: does resistance correlate *within*
the liberty cluster only, or *across* clusters?

## 5. Ingest strategy: catalog first, county files by identification value

Statewide catalogs (NCSL ballot-measure database, Ballotpedia) are cheap and
exhaustive; **county-level results are the expensive bespoke part** (one SoS
loader per state-format, per the `referendum.py` pattern, each with a
certified-total acceptance run — Bugs #10–12). So:

1. **Catalog** every statewide measure: state, date, topic tag, direction,
   result, text link, election type (primary/general/odd-year).
2. **Mark the overlap structure**: same-ballot pairs, repeated measures,
   severity ladders, repeat geographies. This design matrix *is* the ingest
   priority list.
3. **Ingest county files in identification-value order.** Priority corpora,
   pre-registered here:
   - **Same-sex marriage amendments, 2004–2012** — the temporal anchor: ~30
     states on nearly the same cultural measure, several repeats, spanning the
     fastest documented opinion reversal; a known dramatic answer to validate
     against.
   - **Medicaid expansion by initiative (ID/UT/NE/MO/OK, 2017–2020)** — the
     economic red-state set beside minimum wage.
   - **Cannabis wave, 2012–2024** — the liberty cluster; tests the r≈0.62
     generality within- vs across-cluster.
   - **Minimum-wage county cuts (FL 2020 Amdt 2 / MO 2018 Prop B)** — already
     queued in BACKLOG; now doubly justified (county-level economic gradient +
     off-cluster same-ballot potential).

## 6. Honest limits, stated up front

- **Electorate composition ≠ opinion change.** An August-primary electorate
  (KS 2022) is not a November one; election type is a mandatory control, and
  within-place-over-time claims carry turnout caveats until modeled.
- **Ecological inference.** County positions are aggregates; "a county that
  defunds but won't jail doctors" is a distribution of voters straddling two
  cutpoints. Never phrase findings as individual psychology.
- **Wording and campaign spending are absorbed into cutpoints.** We cannot
  separate "harsher text" from "better-funded opposition" and will not claim
  to.
- **Identification is only as good as matrix density.** With today's four
  measures we have one same-ballot pair and zero repeats — this is a design
  for what to ingest, not something estimable yet.

## 7. The 2026 pre-registration experiment (added 2026-08-10)

Section 3's falsification loop, made concrete and dated: predict
county-level results for a slate of November 3, 2026 measures, **commit
the predictions to main before the election** (git history is the
notary), then score them against certified results and publish the
postmortem in `FINDINGS.md` — win or lose. Researched 2026 landscape:
`data/catalog/upcoming_2026.json`.

**The slate:**

1. **Missouri Amendment 3 (marquee).** The legislature's repeal of
   2024's reproductive-rights amendment: same counties, known 51.6%
   baseline, a *harsher* cutpoint asked in the opposite direction, on a
   midterm electorate — the severity-shift-vs-drift machinery, live.
   Full per-county predicted progressive share with intervals.
2. **Nevada Question 6 (calibration control).** Identical text to
   2024's 64.4% first passage — the cutpoint held fixed by
   construction, so error isolates drift + turnout.
3. **Massachusetts Question 8.** First-ever attempt to repeal an
   operating recreational-cannabis market; direct reversal of 2016
   Question 4 (53.7% yes) — repeat geography, known baseline.
4. Stretch: SD Amendment I (Medicaid rollback; third straight SD
   healthcare vote), and state-level-only calls on VA/ID (first-ever
   abortion votes there; no county baseline of our own yet).

**Calibration assets no forecaster usually gets:** Missouri's Aug 4,
2026 primary already produced county-level results on an actual 2026
electorate (parks tax ~82% yes; initiative-restriction Amendment 4
rejected ~80-20; income-tax phaseout rejected ~83-17), and Oklahoma's
June 2026 standalone special (minimum wage REJECTED ~56-44 after a
decade of red-state wins) is the sharpest election-type/turnout data
point in the catalog.

**Protocol (the honesty rules):**

- Predictions ship as a committed CSV (county, predicted progressive
  share, interval) plus a methods statement: explicit turnout
  assumption with reported sensitivity, severity placement as a stated
  bracket (the estimator will not be trained across enough measures by
  October), and the partisanship-only baseline we claim to beat.
- **Registered means frozen.** After the registration commit, the file
  is never edited; new information yields a new dated file and the old
  one stands and gets scored.
- Grading: per-county error, interval calibration, and skill vs the
  partisanship-only baseline. Results go in `FINDINGS.md` regardless of
  outcome — a public miss with a good postmortem is still the method
  working.
- Known risks, stated now: midterm turnout composition is the dominant
  error source; the MO ballot may still gain measures via pending
  litigation (redistricting referendum, initiative-protection
  amendment); one cycle is evidence, not proof.

**Deadlines:** registration commit on main by **2026-10-15**; election
**2026-11-03**; postmortem after certification (Dec 2026) — feeding the
Geo Week 2027 story: *pre-registered, out-of-sample, scored in public.*

## Build order (JIT triggers)

1. **Statewide catalog + design matrix** — trigger: arrived (this document).
   No county data needed; sources are public catalogs.
2. **Measure metadata table** (topic, direction, election type, later
   severity) — the long-deferred normalize decision finally has its consumer.
3. **Targeted county ingests** per the design matrix, one at a time,
   test-first, certified-total acceptance each.
4. **The estimator** (positions + cutpoints) — trigger: the ingested matrix is
   connected with enough pairs/repeats to identify (revisit the threshold when
   the catalog shows what's available). Seed-free testing via deterministic
   constructions and noise-free recovery, per contract.
5. **Residual-diffusion test** (Moran's I on estimator residuals) — the
   exhaustive geo-fluid claim itself.
6. **Content→cutpoint prediction** (the NLP trigger) — after ex-post cutpoints
   exist to train on.
