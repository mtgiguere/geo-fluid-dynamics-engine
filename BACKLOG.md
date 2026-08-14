# Backlog

Work items agreed but deliberately not started (JIT: each begins when its
trigger arrives, with its own tests). Newest decisions at top of each section.

> **North star for the coming year (2026-08-10):** an exhaustive, honest check
> of the founding question — how ideas move across the map — built on the
> ballot-measure measurement design (`docs/MEASUREMENT_DESIGN.md`), with an eye
> to presenting at **Geo Week 2027** or another geospatial/political-data venue.

## Product / UX

- **DONE (2026-08-14): "Bring Your Own State" lay explainer.**
  `docs/BRING_YOUR_OWN_STATE.md` — plain-language, zero-jargon walkthrough of
  what it takes to use the engine for a new state/issue (five ingredients;
  only the loader is technical; the certified-total acceptance run framed as
  a "built-in lie detector"; the Nebraska repeal-the-repeal orientation trap;
  the honest Georgia answer: no initiative process → no direct-vote signal →
  the tool refuses to guess). Death penalty worked as the example (NE/CA/OK
  2016 all have real county data — a natural future corpus, incl. the CA
  same-ballot competing pair). DEFERRED: a public web version of this
  explainer alongside demo.html (same audience as the planned deep-time
  "rabbit hole" page; both are post-registration work).

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

> The narrative across these findings is consolidated in `docs/FINDINGS.md`.

- **2026 PRE-REGISTERED PREDICTION EXPERIMENT — COMMITTED, CLOCK RUNNING
  (2026-08-10).** Full protocol in `docs/MEASUREMENT_DESIGN.md` §7; researched
  ballot landscape in `data/catalog/upcoming_2026.json`. Predict county-level
  results for Nov 3 2026 measures and commit the predictions to main BEFORE the
  election (git = notary): **MO Amendment 3** (repeal of 2024's abortion
  amendment — same counties, 51.6% baseline, harsher cutpoint, midterm
  electorate; the marquee), **NV Question 6** (identical text to 2024's 64.4% —
  fixed cutpoint, isolates drift+turnout; calibration control), **MA Question 8**
  (repeal of the operating rec-cannabis market; 2016 baseline 53.7%); stretch:
  SD Amendment I + state-level VA/ID calls. Sequenced work with hard deadlines:
    1. MO SoS county-level files — **DONE for the four historical elections
       (2026-08-12)**: official canvass PDFs in `data/raw/` (Nov 2024, Nov
       2018, Aug 2018, Aug 2020); scoping parse of Nov 2024 Amendment 3
       reproduced the certified 51.60% exactly (117 jurisdictions: 114
       counties + St. Louis City + **Kansas City reported as its own
       jurisdiction spanning four counties — an explicit loader design
       decision, the AK-districts class of geography question**).
       STILL OPEN (Matt's do-out): **Aug 2026 primary county-level results
       once MO certifies (~Sept 2026)** — the 2026-electorate calibration
       set; unofficial county data earlier if the researcher finds it.
       NV/MA past files if we pursue those at county level.
    2. Loaders test-first, one at a time, each with certified-total acceptance
       (Bugs #10–12). **MO LOADER DONE (2026-08-14)**:
       `ingest/referendum.parse_mo_canvass` + `load_mo_referendum` (pdfplumber),
       tested RED-first (canonical panel, comma numbers, multi-page sections,
       Total-row integrity check, loud unknown-jurisdiction guard). Acceptance:
       ALL EIGHT contests across the four canvasses match certified statewide
       values to the decimal (2024 Amdt 3 51.60 / Prop A 57.57; 2018 Prop B
       62.34 / Amdt 2 65.59 / Amdt 3 31.50 / Prop C 43.57; Aug-2018 Prop A
       32.53; Aug-2020 Amdt 2 53.27), 116 jurisdictions each. Mapping policy:
       Kansas City carries MIT's place-code convention "2938000" (spans four
       counties; MIT presidential returns report KC separately too, so a KC
       partisan baseline exists); canvass name aliases: "St. Louis"→29189,
       "McDonald"→29119.
    3. Prediction notebook (TDD-exempt EDA on tested library parts): county
       positions from past measures + partisanship, explicit turnout
       assumption + sensitivity, severity as a stated bracket. SCOPE WIDENED
       (2026-08-14): predict EVERY MO November measure incl. the low-salience
       referrals (Amdt 7 prosperity fund, Amdt 8 sheriffs — roll-off and
       status-quo-bias modeling, humbler intervals; the anti-cherry-picking
       move) and any litigation additions.
    4. **Registration commit by 2026-10-15** — frozen thereafter (amendments =
       new dated file; the old one still gets scored). PLUS (2026-08-14): the
       parameterized PLAYBOOK generator — (measure, side) → org plan built on
       build_itinerary + pooled resistance + the electorate-type turnout
       split — drafted with the predictions, dated, committed SEALED;
       protocol in MEASUREMENT_DESIGN.md §7.
    5. November/December: ingest certified results, score BOTH products
       (predictions: per-county error, interval calibration, skill vs
       partisanship-only baseline; playbooks: did flagged TARGET counties
       carry the claimed headroom?), postmortem into FINDINGS.md win or lose,
       then UNSEAL playbooks and assemble the viability dossier (receipt →
       scorecard → playbook) → the Geo Week 2027 centerpiece and the pitch
       to real organizations.
  WATCH: MO ballot litigation (redistricting referendum + initiative-protection
  amendment, both rejected by the SoS on 2026-08-04 and in court) could add
  November measures; recheck the ballot in September.

- **INTERNATIONALIZATION — SCOPED, POST-REGISTRATION (2026-08-14).** The
  engine's objects (geographic units × direct issue votes × partisan baseline
  × time) are country-agnostic; two targets chosen, both JIT-gated on the
  2026 registration shipping first:
  (a) **Switzerland as the estimator's validation bench** — quarterly national
  referenda since 1848, ~600+ votes at municipality level (swissvotes.ch /
  BFS, machine-readable), same topics revisited for decades: the densest
  county×measure×time matrix on Earth. Validate the ideal-point/cutpoint
  estimator where identification is easy before trusting it on sparse US data.
  (b) **Mexico as the first foreign loader** — INE municipal-level data,
  morena's 2018 realignment as a trend_surprise showcase, consultas populares
  (with their quorum/turnout quirks documented); doubles as Matt's Year-0
  geography. KNOWN REWORK: the partisan baseline must generalize from
  two-party share to party-bloc/left-right composites (multiparty systems) —
  the biggest engineering lift; boundary crosswalks per country; and the
  free-and-fair prerequisite is a documented data-quality gate (the same rule
  that quarantined the post-1890 US South in the rhyme notebook).

- **CAMPAIGN MONEY AS A MEASURE-LEVEL COVARIATE — SCOPED (2026-08-14).**
  Today spending is an acknowledged confound absorbed into estimated cutpoints
  (MEASUREMENT_DESIGN.md honest limits). Upgrade path:
  (1) enrich the catalog with `support_spend` / `oppose_spend` columns — a
  research-agent job; Ballotpedia summarizes committee spending on the very
  pages our `source_url` column already cites (state ethics filings for
  depth). (2) Then the decomposition becomes testable: does money shift
  outcomes BEYOND what severity + county positions predict, and is it
  asymmetric (the Gerber finding: one-sided NO money defeats measures far
  more effectively than YES money passes them — PG&E's Prop 16 lost 400:1
  outspent; Prop 22 won at $200M; both belong in the test)? Level shift vs
  county-gradient shape change is also testable with our machinery.
  (3) For the 2026 marquee: Missouri Ethics Commission quarterly + 8-day
  filings let us watch Amendment 3 war chests build in real time — the
  registered prediction states its spending assumption explicitly, and the
  postmortem grades it. HONESTY GATE: spending is endogenous (money chases
  close races); we measure and control, we do not claim clean causality.

- **DEEP-TIME ARC OPENED — Gilded Age rhyme test DONE (2026-08-14).**
  `notebooks/gilded_age_rhyme.{py,ipynb}` (TDD-exempt, on the 1868–2024 spine):
  1892 Populist share (third-party lens — `dem_share_2p` is blind to Weaver)
  does NOT correlate with 1912 Progressivism (r ≈ −0.08) but predicts the 1932
  New Deal break at r = +0.38 non-South (+0.28 with a 1928-free baseline: the
  Al Smith anomaly explains part, not all). The reservoir discharged in 1932;
  1936 re-target ≈ 0 for the mechanical re-baselining reason documented in the
  notebook. 2016 echo +0.28 but silver-county-confounded. Summarized in
  FINDINGS.md §8. NEXT in the arc (JIT, after the 2026 registration): (a)
  county-level historical REFERENDA — prohibition (the only complete
  rise-AND-fall idea wave, 1880s→1919→1933 repeal) and women's suffrage
  (repeat-vote states) — scoping is a catalog-agent job; (b) NHGIS decennial
  demographics (long-deferred, now doubly justified) to separate
  persistence-of-people from replacement-of-people; (c) a public "rabbit hole"
  explainer page telling the Populist→New Deal reservoir story for lay readers
  (demo.html pattern; candidate second act for the Geo Week narrative).

- **Ballot-measure measurement design — DOCUMENTED, NOT BUILT (2026-08-10).**
  `docs/MEASUREMENT_DESIGN.md` is the full design: county ideal points ×
  measure cutpoints (IRT — severity *estimated*, not hand-coded;
  `progressive_side` is its one-bit degenerate case), identification via
  overlap structure (same-ballot pairs → severity; repeated measures → drift;
  demographics controlled from ACS; diffusion = spatially structured residual,
  tested with Moran's I on estimator residuals), ex-ante prediction via
  content→cutpoint placement (brackets + severity-slider product shape), and
  topic dimensionality as a *tested hypothesis* (our False Bastions already
  imply ≥2 axes; is r≈0.62 within-cluster or general?). Build order with JIT
  triggers is in the doc: (1) statewide catalog + design matrix — DONE
  (2026-08-10, see Data section); (2) measure metadata table — DONE
  (2026-08-10): `geofluid.catalog.load_measure_catalog`, tested (schema,
  dtypes, unique-id + closed-vocabulary validation, 100% branch) with a
  real-data acceptance test against certified KS/OH landmarks;
  (3) targeted county ingests by identification value (priority corpora:
  marriage amendments 2004–2012, Medicaid-expansion initiatives, cannabis
  wave, FL/MO minimum-wage county cuts); (4) the estimator — gated on matrix
  connectivity, seed-free per contract; (5) residual-diffusion test; (6) NLP
  content→cutpoint. Supersedes nothing — it *sequences* the open Module 2
  path-b and economic-bastion items below.

- **Issue-resistance trait PROMOTED to tested library (2026-06-28).**
  `dissonance.issue_resistance` is the partisanship-controlled residual (OLS of
  progressive on partisan share — the rigorous "defies its partisan peers", vs the
  raw dissonance gap the map/targeting engine still use); the Ohio generality
  notebook now calls it. STILL OPEN (path-b step toward the product): aggregate it
  ACROSS measures into one per-county persuadability score (only Ohio has
  overlapping measures today — waits on more same-geography measures), then
  optionally rank the targeting engine on the aggregate trait instead of
  single-measure raw dissonance (a deliberate deploy change, not yet warranted).

- **Economic-axis False Bastions — STATE-LEVEL CUT DONE (2026-06-28).**
  `notebooks/minimum_wage_economic_bastions.{py,ipynb}` (TDD-exempt): 10 verified
  statewide minimum-wage measures (2006–2020) vs each state's presidential partisan
  lean (our county returns). Economic dissonance = Yes share − Dem two-party share.
  Finding: every measure passed ABOVE its partisan lean (mean +15pts); corr(lean,
  dissonance) = −0.82 — poorest, reddest states (MO, AR, NE) crossed party hardest
  for a raise (+20–31pts), blue states sit on their line. Inverts "What's the
  Matter with Kansas": the abortion False-Bastion pattern on the economic axis,
  pointing the other ideological direction. CAVEATS: N=10 verified subset,
  state-level/ecological, selection bias, static income. NEXT (JIT): the
  within-state COUNTY cut — ingest Florida 2020 (Amendment 2) and/or Missouri 2018
  (Prop B) via the `referendum` loader pattern (Matt grabs the SoS file) to show
  the county-level gradient AND add a genuinely off-cluster economic measure to the
  issue-generality test.

- **Education channel is EPISODIC — TEMPORAL CUT DONE (2026-06-28).**
  `notebooks/education_channel_over_time.{py,ipynb}` (TDD-exempt; uses
  `attribute_knn_adjacency` + `morans_i`): global Moran's I of residual swing per
  election under geographic vs demographic-similarity networks. Education's
  organizing power of swing: 0.13 (2004/08) → 0.02 (2012) → 0.34 (2016) →
  0.32 (2020) → 0.05 (2024); geography steady 0.50–0.74 throughout. The
  diploma-divide was the defining axis of the 2016/2020 SWINGS, not a permanent
  remap — it flickered off in 2024 (a broad, non-education-patterned shift). This
  strengthens the Module 5 (phase transition) case: realignments are episodic
  regime events to detect, not a monotonic trend. Caveat: static modern
  demographics applied to all years; time-resolved NHGIS demographics would
  sharpen it.

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
  - PARTIALLY DONE (2026-06-28): step (3)'s building block shipped —
    `dissonance.issue_resistance` is the tested per-measure trait (OLS residual of
    progressive on partisan share; the rigorous "defies its partisan peers", vs
    the raw dissonance gap the map/targeting engine still use). The generality
    notebook now calls it. STILL OPEN: aggregate it ACROSS measures into a single
    per-county persuadability score (only Ohio has overlapping measures today, so
    this waits on more same-geography measures — steps 1/2), then optionally rank
    the targeting engine on the aggregate trait instead of single-measure raw
    dissonance (a deliberate deploy change, not yet warranted).

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
    6. **Similarity-network diffusion (research) — FIRST CUT DONE (2026-06-28).**
       `spatial/weights.attribute_knn_adjacency` (tested) builds a non-geographic
       network from demographic similarity, drop-in to the Moran/lead-lag
       machinery. Horse-race EDA (`notebooks/diffusion_network_horse_race.{py,
       ipynb}`) over residual swing (county swing − national mean), 2004–2024:
       **geography decisively wins** (Moran's I 0.62 vs best demographic net 0.28,
       education 0.17) — similarity does NOT beat borders for presidential swing,
       so "ideas hop metro-to-metro" is not the story and swapping networks does
       not rescue the falsified lead-lag. BUT among demographic axes **education
       leads and survives the collinearity control** (Layer-2 unique variation:
       education 0.08 > income/urbanicity/age); urbanicity was partly education in
       disguise (corr 0.48). NEXT: permutation significance; per-year (1964/2016
       likely differ); k-sensitivity; and feed the result into Hybrid W below.

- **Hybrid W**: blend queen adjacency with connectivity per the spec's W_hybrid.
  Trigger: when the lag model's residuals show non-contiguous structure. NOW
  EVIDENCE-BACKED (2026-06-28): the diffusion horse-race says keep geography as
  the backbone and add ONE non-geographic edge — **education similarity** (it
  carried the most co-movement beyond geography and survived controlling for
  income/urbanicity/age). `attribute_knn_adjacency` is the constructor; a hybrid
  would blend it with `county_adjacency` (e.g. row-normalized convex combination).

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
  - TRIGGER NOW HAS A SHAPE (2026-08-10): content→cutpoint prediction — embed
    ballot-measure text, learn the mapping to estimated severity cutpoints from
    past measures, place NEW measures ex ante (`docs/MEASUREMENT_DESIGN.md` §3).
    Still JIT: fires only after the estimator produces ex-post cutpoints to
    train on (build-order step 6).

## Data

- **Ballot-measure CATALOG — DONE (2026-08-10).** Step 1 of
  `docs/MEASUREMENT_DESIGN.md` shipped: `data/catalog/ballot_measures.csv` —
  **271 statewide measures, 1996–2025**, across the five priority corpora
  (cannabis 74, labor 58, marriage 45, abortion 44, healthcare 50), each
  Ballotpedia-verified (state, date, election type, yes_pct, outcome,
  progressive_side, severity note, same-ballot companions, source URL).
  `data/catalog/DESIGN_MATRIX.md` (auto-generated by
  `scripts/assemble_measure_catalog.py`) computes the overlap structure:
  **59 same-ballot multi-measure ballots, 50 of them CROSS-TOPIC** (vs. the
  single Ohio 2023 pair all prior analysis rested on), and **59 repeat
  state-topic geographies**. Standout identification assets: NE 2024 (5
  measures incl. COMPETING abortion amendments), SD 2006 (abortion ban +
  marriage + cannabis same ballot), WA 1998 (abortion + cannabis + minimum
  wage), CO 2006 (4 measures incl. opposed marriage pair), MO 2018/2024,
  FL 2024 (abortion + cannabis, both 60%-threshold failures). NEXT (step 3
  of the build order, after the metadata table): pick the first county-level
  ingests FROM the design matrix — each a per-state SoS loader with
  certified-total acceptance (Bugs #10–12), one at a time.

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
