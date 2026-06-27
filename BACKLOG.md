# Backlog

Work items agreed but deliberately not started (JIT: each begins when its
trigger arrives, with its own tests). Newest decisions at top of each section.

## Product / UX

- **DONE (2026-06-13): Scoped views.** `geofluid/scope.py` (neighborhood
  expansion + catalog) ships scopes.json (nation + every state + STL/KC
  cross-border metro presets); frontend has a scope selector that filters,
  fits the camera, and recounts storyline + status. Settled principle held:
  scopes DISPLAY national statistics filtered, never recompute inside a
  boundary. Deferred sub-item still open: a "fit colors to this view" ramp
  toggle (rescaling breaks cross-scope comparison — only on request).

- **DONE (2026-06-13): Kansas dissonance map view.** Modular ballot-measure
  overlay: measures.json catalog + measure_<id>.json, a "Ballot measures"
  optgroup in the metric dropdown, dissonance coloring (baseline = 2020),
  auto-scope to the measure's state, disabled year controls, comparative
  storyline/caption. Remaining sub-items, deferred: (a) named False-Bastion
  CLASSIFICATION tiers (a continuous gap ships now; thresholds were the
  deferred classify cycle); (b) more measures (the catalog is built for it —
  append to MEASURES in the export); (c) minor: selecting a measure at
  national scope shows mostly gray (only the measure's state has data) — the
  auto-scope mitigates it, but a guard/hint could be cleaner.

- **DONE (2026-06-14): Explainer key — every view explains itself.** Every
  MetricDef + the dissonance measure now carries a required `caption` (what it
  shows, what gray means), rendered always-visible under the legend; Vitest
  pins that no view can ship without one. Closes the Chicago-misreading risk
  for all layers, not just the categorical ones. Possible future polish (not
  needed now): a dedicated "how to read this map" help panel / first-visit
  tour for the spec's broader audience.

## Science (Module 1+)

- **Module 4 (Chaos Sensor) — SEED DONE (2026-06-15).** `realignment.trend_surprise`:
  per-county residual from its own linear trend over the trailing window of
  presidential elections, extrapolated one ahead (actual − predicted). Tested
  seed-free (residual math, min-obs/missing-target exclusion, no-future-leakage).
  Showcase EDA notebook (`notebooks/realignment_1964_vs_2016.{py,ipynb}`, jupytext
  + paired executed .ipynb) over the 1868–2024 spine: 1964 reads as an almost-
  purely-REGIONAL break (median surprise 22.9pts, Moran's I 0.89, −0.58 with
  South); 2016 layers a NEW education cleavage (~0.36 with college share) on top
  of a still-regional map (~0.39) — an axis added, not swapped. The real-data run
  was itself an acceptance run: it caught + fixed a silent `read_json` FIPS
  leading-zero coercion (NaN'd the whole education axis) and corrected prose that
  overstated a clean region→education dichotomy. (Notebooks are TDD-exempt — they
  lean on the tested `geofluid` library.) STILL TO COME: spatial-coherence + axis
  detection wired into a live "surprise field" monitor (the actual Module 4
  product); the linear-trend baseline is deliberately simple (overstates landslide
  years like 1964); time-resolved education (NHGIS decennial) rather than ACS-2024
  as a static county trait.

- **Module 2 node classification — FIRST ATTEMPT FALSIFIED (2026-06-15).**
  Built `county_influence` (conformity = co-movement with neighbourhood;
  volatility) + `classify_nodes` (Buffer/Bastion/ordinary/unknown), tested.
  The real-data acceptance falsified the contemporaneous-conformity approach:
  96% "buffer", spec's Pulaski bastion → buffer, "bastions" were tiny noisy
  counties. Root cause: swing is so spatially autocorrelated that everyone
  co-moves — conformity can't separate roles. NOT wired to the map. Paths
  forward: (a) a temporal LEAD-LAG method to split Bellwether (leads) from
  Buffer (follows) — needs more elections than 7, so likely gated on the
  historical-returns extension; (b) define the Bastion via issue-resistance
  (the dissonance metric) rather than swing co-movement, which may match the
  spec's meaning better. The `county_influence` primitives stay as tested
  building blocks for whichever path we take.

- **Module 2 lead-lag retry — SECOND FALSIFICATION (2026-06-18).** Built
  `spatial/leadlag.lead_lag` (path (a) above): per-county
  `corr(own swing(t), neighbourhood(t+1)) − corr(own swing(t), neighbourhood(t−1))`
  — positive leads, negative follows. Tested seed-free (deterministic
  leader/follower construction; sparse / island / constant-series exclusions; an
  antisymmetry property), 100% branch coverage. Acceptance run on the full 40-
  election spine (`notebooks/leadlag_node_roles.{py,ipynb}`, TDD-exempt):
    - The GOOD news — timing recovers a distinction conformity could not:
      contemporaneous conformity collapses (median 0.94, 100% > 0.5, the attempt-#1
      disease), while lead-lag SPREADS (49% lead / 51% follow, std 0.13). The
      *information* is there.
    - The bad news — it's not a usable Bellwether map: signal weak (median ≈ 0);
      spatially incoherent (Moran's I ≈ −0.14, and that negativity is partly
      MECHANICAL — within a pair, if I lead you then you follow me, so the metric's
      own antisymmetry pushes neighbours to opposite signs and Moran's I isn't even
      a clean coherence test for it); and the strongest "leaders" are small,
      idiosyncratic counties (VA independent cities, Broomfield CO — created 2001 so
      its history is backfill, sparse UT/SD counties), not the metros change
      radiates from. Not a simple volatility artefact (corr ≈ 0); a mild thin-data
      pull (corr |score| vs #elections ≈ −0.22). NOT wired to the map.
  REFINED paths forward (supersede (a)): population-/metro-weighted or -restricted
  scoring (candidate hubs); a DIRECTED influence graph instead of a symmetric
  pairwise score (whose antisymmetry forces the checkerboard); or path (b), the
  issue-resistance route via the dissonance metric. `lead_lag` stays a tested
  primitive for whichever we take next.

- **Module 2 path (b) issue-resistance — FIRST POSITIVE RESULT (2026-06-24).**
  `panel/measures.build_measures_panel` (tidy `fips × measure_id` panel +
  orientation-corrected `progressive_share`) feeds two analysis notebooks
  (TDD-exempt) over the KS/KY/OH abortion + OH cannabis measures:
    - `notebooks/issue_resistance_starter.{py,ipynb}` — across the three (disjoint)
      states, the False Bastion is a near-UNIFORM offset (every county ~13–19 pts
      ahead of its Dem share on abortion; slope 0.90–0.96, big positive intercept),
      NOT a sharp county gradient (resistance-vs-partisanship corr only −0.10 to
      −0.23). Issue resistance separates measure-from-party cleanly but not
      counties-from-each-other — the same weak-localization wall swing hit.
    - `notebooks/issue_generality_ohio.{py,ipynb}` — the disjoint-geography limit
      pointed to OH's two same-ballot issues (abortion + cannabis, same 88
      counties, identical turnout). Partial correlation (residualize each issue's
      share on partisanship, then correlate residuals — the rigorous test; naive
      shared-partisanship differencing is confounded): **r ≈ 0.62**. Resistance is
      a stable CROSS-issue county trait — the first county-level structure the
      module has found, and modellable where swing was not.
  CAVEATS: one state, one ballot, N=88; abortion + cannabis share a "personal-
  liberty" flavor, so this may be libertarian-cluster generality, not fully
  general. NEXT (JIT): (1) an OFF-cluster same-ballot pair (an economic measure
  beside a social one) to test whether the generality is broad or libertarian-
  specific; (2) more multi-issue states to see if r ≈ 0.62 holds; (3) IF it holds,
  promote "issue resistance" from a notebook residual to a tested library trait
  and map it — the real Module 2 path-(b) product.

- **Prescriptive layer (spec Stage 4) — FIRST TOUCH SHIPPED (2026-06-26).**
  `targeting.build_itinerary` (tested, seed-free, 100% branch coverage) +
  `spatial/distance` turn a county issue signal + a home county into a ranked,
  classified campaign itinerary (TARGET / BASE / HARD), shipped as a PUBLIC demo
  page (`web/public/demo.html`, built by `scripts/build_targeting_demo.py`) linked
  from the live app's "The art of the possible" button. Walkthrough in `docs/DEMO.md`.
  Deliberately stage one — the pipeline and the signal are proven; the product is
  not finished. ROADMAP (the sequenced next work):
    1. **More issues/states** — each is a small loader into the existing pipeline;
       the engine is already data-source-agnostic. Unlocks targeting beyond KS.
    2. **A persuadability score that travels** — promote the issue-resistance
       residual (r ≈ 0.62 finding) to a tested per-county trait the engine can
       rank on directly, not just one measure's dissonance.
    3. **Real drive-time routing** — replace straight-line miles with a road
       network / isochrones; order the itinerary as an actual route, not a list.
    4. **In-map prescriptive mode** — fold the itinerary into the live Mapbox app
       (goal picker → highlighted targets + ranked panel), retiring the static
       demo page. Frontend logic that grows here gets Vitest (contract rule 7).
    5. **Tunable thresholds + goals** — base/target cutoffs are fixed constants
       today; expose them, and add the other organizer intents (turnout, defense)
       beyond persuasion.
    6. **Similarity-network diffusion (research)** — test whether change diffuses
       through demographic/urban-hierarchy similarity rather than geographic
       adjacency (swap W in the tested Moran/lead-lag machinery); if real, it
       reshapes both the influence model and the targeting network. See the
       "how is the wave" discussion — the open, promising lead.

- **Hybrid W**: blend queen adjacency with connectivity (commuting flows,
  broadband, media markets) per the spec's W_hybrid. Trigger: when the lag
  model's residuals show non-contiguous structure.

## NLP / text (future phase)

- **NLP stack decision — PyTorch + Hugging Face `transformers` (agreed
  2026-06-15).** When the project reaches a text/NLP phase, default to PyTorch +
  HF rather than alternatives (Matt's call; it's the right modern NLP stack and a
  deliberate portfolio signal). Candidate tasks, none scoped yet: embedding ballot-
  measure / platform / speech text to track how *ideas* (not just vote share)
  diffuse across counties; issue/topic classification feeding Module 3 dissonance
  real text instead of proxies; semantic-similarity to detect a new cleavage
  forming. Architecture is chosen once the task is pinned — **JIT: don't build
  ahead of the trigger.**
  Constraints, recorded so they aren't rediscovered:
  - Fits the no-seed TDD rule best via **inference in `eval()` mode** (deterministic
    → satisfies the reproducibility-contract rule, not seed-value snapshots).
    Embeddings / zero-shot / similarity are inference, not training.
  - If fine-tuning: test pipeline contracts (tokenization, tensor shapes, label
    maps, pre/post-processing) plus a noise-free property ("overfit a tiny batch →
    loss → ~0"), never an asserted seeded loss value.
  - Dependency/CI weight: torch is GB-scale; pin CPU-only wheels and watch
    `uv lock --check` + pip-audit. Treat model **inference as an offline build step**
    (like `scripts/export_web_data.py`), not inside the coverage-gated unit path.
  - Trigger: a defined text-analysis need (most likely real ballot-measure / platform
    text to deepen Module 3), plus the text data to ingest.

## Data

- **Ballot measures ingest — STARTER SET SCOPED + IN PROGRESS (2026-06-18).**
  County-level, per-state SoS sources; Kansas Aug 2022 done. The two Module 2
  falsifications (see Science) showed presidential swing is too synchronized/sticky
  to localize influence; Matt's hypothesis is that cleaner single-issue contests
  are the better signal (see the project memory). So this ingest is now the
  highest-leverage move — it unblocks BOTH the issue-resistance route (Module 2
  path b) AND a future lead-lag retry on single-issue contests. The decisive
  reason: influence/resistance is a *multi-observation* structure — one measure
  (N=1) has no structure to find, so we need variation across issues/states/time
  to model on (the same depth lesson the 40-election spine taught lead-lag).
  Starter set — same issue (abortion) across partisan contexts + one off-issue,
  ingested ONE AT A TIME, each test-first + a real-data acceptance run vs the
  certified statewide total (Bugs #10–12 pattern), reusing the `referendum.py`
  pattern (each state's SoS file format differs — the KS loader is KS-specific):
    1. **KS** Aug-2022 abortion (red; pro-choice won) — DONE, the anchor.
    2. **KY** Nov-2022 Amdt 2 (deep red; "NO" won, preserving rights) — DONE
       (2026-06-24). `load_ky_referendum` (KY SoS plain-text export, a distinct
       format from the KS workbook; shared `_assemble_referendum_panel` so both
       emit the canonical schema). Acceptance: all 120 counties map, panel
       matches the raw file to the vote, NO% = certified 52.35%; the 59-vote
       (0.004%) gap vs the certified canvass is a pre-certification export
       vintage artifact (Russell at 99.01% est), not a loader bug. False-Bastion
       structure confirmed (Louisville 71% / Lexington 73% NO vs rural Bell
       34% NO). NOT yet wired to the map overlay (see CONTEST DIMENSION below —
       KY is now the second measure, so combining it with KS is the JIT trigger
       for the tidy fips × measure_id schema).
    3. **OH** Nov-2023 Issue 1 (purple; pro-choice won) — DONE (2026-06-24).
       `load_oh_referendum` (SoS precinct-summary workbook: header on the 3rd row,
       both statewide issues side by side — Issue 1 abortion, Issue 2 cannabis;
       "Total"/"Percentage" summary rows excluded, the Bug #11 pattern). Acceptance:
       all 88 counties map, panel matches the certified canvass EXACTLY (YES
       2,227,384 / NO 1,695,480, delta 0/0). The ORIENTATION FLIP (YES = pro-choice
       here) drove the overlay's new `progressive_side` param so dissonance is
       signed correctly; wired to the map. Adds the 2023 time point AND a YES-side
       measure. (Issue 2 cannabis sits in the same file — a future off-issue measure,
       the MO-cannabis slot's natural substitute; not ingested yet, JIT.)
    4. **MI** Nov-2022 Prop 3 (purple/blue; passed) — the blue end of the contrast.
       Source: Michigan Bureau of Elections.
    5. **MO** Nov-2022 Amdt 3 (cannabis, red; passed) — DIFFERENT issue: tests
       whether persuadability is issue-general or issue-specific. Source: MO SoS.
       (FL/MO 2024 abortion are swappable alternates — red-state 2024 with strong
       dissonance.)
  CONTEST DIMENSION — TIDY PANEL DONE (2026-06-24): with KS + KY combined, the
  trigger arrived. `panel/measures.build_measures_panel` stacks per-measure
  referendum panels into one tidy `fips × measure_id` panel and adds
  `progressive_share` (the progressive vote's share, oriented per measure via
  `Measure.progressive_side` so it is comparable across measures — NO for the
  abortion measures, YES for a future cannabis one). Tested seed-free, 100%
  branch coverage. STILL DEFERRED (JIT — no consumer yet): the normalized measure
  METADATA table (state, date, issue); it emerges when the resistance analysis
  actually groups by those dimensions and the normalize-vs-denormalize access
  pattern is concrete. Wiring to the map overlay is per-measure (each measure
  ships its own dissonance file) and is independent of this modelling panel.
- **Historical extension** (Algara–Sharif 1868–2020): **LOADER DONE +
  VALIDATED (2026-06-15)** — `load_historical_returns` maps the dataset onto
  the canonical returns schema; free download (no guestbook), already
  FIPS-coded (authors did the boundary harmonization), read via pyreadr from
  RData. Acceptance: landmarks correct, 2020 cross-validates vs MIT at
  corr 0.9999 / 99.8% within 1pt. SPINE DONE (2026-06-15): `build_returns_spine`
  joins Algara (pre-2000) + MIT (2000+) into one validated 1868-2024 panel
  (40 elections, 116,983 county-years, national arc matches history; modern
  wins the overlap). Module 4 realignment seed now built on it (see Science →
  Module 4 Chaos Sensor). NEXT: the lead-lag node method (Module 2 retry — now
  has 40 elections of depth). NHGIS decennial demographics still future
  (pre-2005 years are returns-only; Module 4's education axis currently leans on
  static ACS-2024).
- **Midterms** (district→county crosswalks, uncontested-race handling).
  Trigger: when the hazard model demands 2-year cadence.
- **Connecticut crosswalk**: planning regions ↔ old counties, to retire the
  ACS-2021 patch. Trigger: when CT's 2021-vintage demographics become a
  problem for an analysis.

## Engineering

- **Committed data products can go stale silently** (2026-06-24 footgun): the
  deploy serves `web/public/data/*.json` as COMMITTED to git — it does NOT run
  `scripts/export_web_data.py` (which needs CENSUS_API_KEY + the gitignored raw
  data). So changing a loader wired into `MEASURES`, or the export itself,
  without regenerating + committing the affected JSON ships a stale map with no
  guard. Mitigation discipline today: after touching the export or a wired
  loader, regenerate and commit the affected products (and diff byte-for-byte
  when the change is meant to be output-preserving — see TDD_CONTRACT.md "Byte-
  Identical Regeneration"). BETTER (deferred): a CI check that the committed
  products match a fresh export — blocked on getting CENSUS_API_KEY + raw data
  into CI, which is the very reason they are committed; revisit if a stale
  product ever ships. Trigger: first stale-data incident, or a cheap way to
  pin the no-Census-key products (measures + overlays) in CI.
- **E2E only covers the Kansas measure** (2026-06-24): the Playwright suite
  selects `measure:ks_abortion_2022` and asserts its scope/caption/dissonance.
  KY is data-identical to that path (no new code), but OH exercises a NEW code
  path — `build_measure_overlay`'s `progressive_side="yes"` orientation produces
  the dissonance the map colors. That orientation is unit-tested, but nothing
  verifies OH RENDERS correctly on the built app (the Bug #8 class: unit-green ≠
  deployed-correct, lower-risk here because it is data not config). Trigger: add
  a measure E2E (or parametrize the existing one) when the next measure lands, or
  before relying on the OH overlay for outreach.
- **Mutation gate** (2026-06-13): SELF-RUNNING and VALIDATED — mutmut 3.x runs
  clean on our src layout in CI (runs #1 cron + #2 push both succeeded; the
  numbered gaps in the survivor list prove most mutants are killed, harness
  is real). The workflow now also emits survivor DIFFS (not just opaque IDs)
  to the job summary + artifact, so triage is actionable.
  FIRST RESULTS (~115 survivors, pre-sentinel-hardening run): concentrated in
  the math modules — `fit_spatial_lag` ~80, `local_morans_i` ~15,
  `load_county_returns` ~10. Hardened so far: _ACS_SENTINELS (all 7 pinned);
  SAR inferential outputs n / loglik ordering / lr_pvalue (were unasserted).
  STILL OPEN, as a TRIAGED multi-arc effort (do NOT chase 100% — equivalent
  mutants exist): (a) read the diffs from the next run and target the
  high-value SAR/Moran survivors; (b) KNOWN HARD CLASS — mutants on the
  noise parameters (sigma2 magnitude, exact lr_pvalue) resist killing under
  the no-seed rule, same root tension as SEM; may need property-based or
  constructed-residual approaches, or accept as documented equivalent-ish.
- **Git single-file-commit mystery** (TDD_CONTRACT.md OPEN INCIDENT):
  unexplained; tripwire in place. Trigger: any recurrence — capture
  evidence before repairing; consider upgrading git 2.24.

## Science honesty notes

- **PARTIALLY DONE (2026-06-13): Durbin half of the SAR honesty check.**
  `fit_spatial_lag(..., durbin=True)` adds neighbors' covariates W·X. Finding:
  rho does NOT drop controlling for neighbors' demographics (0.86→0.86 in 2008,
  slightly higher in 2016/2020) — the wave is not observable demographic
  confounding. STILL OPEN: the spatial-error model (SEM) — correlated UNOBSERVED
  shocks. Why deferred: SEM's lambda is unidentified at zero noise, so the
  noise-free recovery pattern that keeps SAR/SDM seed-free does not work; testing
  SEM needs either a property over many noise draws or an analytic special case —
  a real design problem against RED FLAG 3, not a quick add. Until SEM is done,
  describe rho as "transmission not explained by self-or-neighbor demographics,"
  not bare "contagion".
