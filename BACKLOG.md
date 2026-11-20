# Backlog

Open work only: agreed, deliberately not started, each with the trigger that
starts it (just-in-time; every item arrives with its own tests). Finished work
lives in `docs/FINDINGS.md` (what was learned), `docs/RESEARCH_LOG.md` (what
was asked and checked) and git history (this file before 2026-11-18 holds the
build narratives). Dated deadlines to MPSA (April 1-4, 2027) are in
`docs/TODO_2027.md`.

## The 2026 registration: finishing it

- **Certified scorecard, unseal, grade, publish.** When Missouri certifies
  (expected Dec 8-15): re-fetch, re-run `notebooks/mo_2026_scorecard.py`, unseal
  and verify the ten playbooks (`seal.verify_manifest`), grade them, write the
  FINDINGS entry (wins and misses), update the README status and rebuild the
  receipt page (`forecast.html`) around the result. Steps: `docs/RUNBOOK_2026.md`.
- **Aug 2026 canvass PDF cross-check.** When the SoS finally posts
  `ActualResults-August42026.pdf`, check it against the ENR-portal panel.

## Science

- **Neighbours in the forecast (the spatial-lag model).** The 2026 Amendment 3
  misses cluster on the map (Moran's I 0.33): neighbouring counties carry
  information the registered model left out. `spatial/lag` already fits SAR.
  Trigger: the method bake-off (below); first cut is the Feb 14 stretch item.

- **Information environment: heat, explanation, wording, money** (Matt,
  2026-11-04; the "obscurity" question). The engine may be missing what voters
  knew when they reached the question. In 2026 every Missouri measure moved
  toward No against our call, and the two big level misses (Amdt 8, Prop A)
  were the quiet ones; roll-off ranks the measures in the same order as the
  level misses (n = 5, a lead, not a finding). Gap carried over between two
  Missouri votes on the same issue: abortion 2024→2026 79% (r 0.74), minimum
  wage 2018→2024 62% (0.68), Clean Missouri 2018→2020 repeal 30% (0.44),
  unrelated pair 34% (0.31).
  - Data: official ballot text (MO fair-ballot language; catalog measures where
    available); committee spending (Missouri Ethics Commission; Ballotpedia
    summaries; other states' portals); news volume per measure per week
    (GDELT); search interest by media market (Google Trends).
  - Features, all measured BEFORE the vote: reading level, negations, length,
    YES = change vs keep, number of subjects, loaded words; later a text
    embedding (the NLP phase).
  - Tests across the 271-measure catalog: (a) does gap persistence rise with
    heat? (b) do quiet or confusingly worded measures drift toward No from
    their partisan expectation? (c) does the engine's edge over party alone
    shrink on obscure measures (voters fall back on party cues)? (d) does money
    shift outcomes beyond severity and county positions, and asymmetrically
    (one-sided No money)? Spending is endogenous: measure and control, never
    claim clean causality. Roll-off is the after-the-vote check on the score.
  - Payoff: the engine knows in advance how far to trust itself (tight ranges
    on hot, explained measures; party plus a No lean and wide ranges on quiet
    ones). For a campaign: on a quiet measure, explaining what YES means may be
    worth more than persuading.
  Trigger: now, alongside the bake-off; Missouri 2026 is the first case study.

- **Engine method bake-off: analogs vs averages vs trendlines** (2026-11-04).
  Choose the next registration's method by honest backtest, never by tuning on
  the answer key. Candidates, fit on the ~21 certified MO measures 2018-2026
  (`county_receipts_mo`): (1) single best analog, the 2026 method, as control;
  (2) flat average of past gaps (reference); (3) similarity-weighted ensemble
  (topic, severity, electorate); (4) county trendlines of measure gaps, pure vs
  damped, midterm and presidential electorates apart, slopes shrunk toward
  neighbours and state; (5) demographic fallback when no close analog exists
  (the Amdt 6 lesson); (6) bracket width from history, widening with analog
  distance, plus a tested "when in doubt, vote No" offset. Level and pattern
  uncertainty sized separately (2026 ranges held 65% against a claimed 90%).
  Protocol: rolling origin (through 2022 → 2024; through 2024 → 2026), scored
  with `geofluid.scoring` relevel-then-RMSE plus coverage; n is small, so this
  is method selection, not proof. New library code is test-first. Trigger:
  certified 2026 results; the 2024 origin can start now.

- **Solar wave, the remaining steps** (ingest and timing model done). (3) The
  roads: borders vs Census commuting vs IRS migration vs TV media markets (no
  Facebook data). (4) The clock test: sample solar every four years, as
  elections do; if the wave disappears, that explains "no first domino".
  (5) Back to politics: the same detector on GDELT daily county coverage and
  dated local-option adoptions. Trigger: now (Dec 6 in the to-do).

- **Module 5: measure the order parameter before claiming a detector.**
  From data we hold: (1) issue-party coupling over time (registered for
  2026; provisional result: Amdt 3 HOLD, slope 0.77 vs 0.80); (2) dispersion
  of `issue_resistance`
  across counties per measure; (3) landslide-county share on the 1868-2024
  spine; (4) the midterm-penalty distribution. Institutional-legitimacy inputs
  (official turnover, concession behaviour, referee-override laws, rejection
  language) need new ingests and NLP. Score the 2026 governance measures
  (Amdt 6, the map referendum) as behavioural data points. Claim stays bounded:
  "we measure the coupling every cycle", never "we will call the moment".
  Trigger: after the certified scorecard; first deliverable a notebook for 1-3.

- **Persuadability as one per-county score.** Aggregate `issue_resistance`
  across measures into a single trait, then optionally rank the targeting
  engine on it instead of one measure's raw dissonance (a deliberate deploy
  change). Missouri 2026 says it is mostly issue-specific (cross-measure median
  r 0.09; same issue 0.68-0.74), so aggregate within issue families first.
  Trigger: the bake-off's similarity weights.

- **Economic False Bastions, the county cut.** Missouri 2018 Prop B (minimum
  wage) is already parsed by `parse_mo_canvass`; Florida 2020 Amendment 2
  would add a second state. Shows the county gradient behind the state-level
  −0.82 (which overstates; the residual is the honest version).
  Trigger: the paper outline (Jan 10) if Finding 3 needs the county view.

- **Measurement design, build-order steps 3-6** (`docs/MEASUREMENT_DESIGN.md`):
  (3) targeted county ingests chosen from `data/catalog/DESIGN_MATRIX.md` by
  identification value (marriage 2004-2012, Medicaid expansion, cannabis,
  minimum wage; NE 2024, SD 2006, WA 1998, CO 2006, FL 2024 as overlap assets);
  (4) the ideal-point × cutpoint estimator, gated on matrix connectivity,
  seed-free; (5) residual-diffusion test; (6) NLP content → cutpoint.
  Trigger: each step's predecessor.

- **Module 4: the live surprise-field monitor.** `trend_surprise` plus spatial
  coherence and axis detection; a better baseline than linear trend (it
  overstates landslide years). GDELT is a candidate input.
  Trigger: when Module 4 is scoped (after MPSA).

- **Module 2, refined paths.** Influence hubs were falsified twice. Open:
  population- or metro-weighted scoring; a directed influence graph instead of
  the antisymmetric pairwise score; and Matt's leading-signal hypothesis
  (midterms, specials and ballot measures are a denser series than
  presidential swing). Trigger: a high-frequency political series (GDELT, the
  bake-off's Aug + Nov measure series).

- **Hybrid W.** Geography as the backbone plus one non-geographic edge,
  education similarity (`attribute_knn_adjacency` blended with
  `county_adjacency`). Also open from the horse race: permutation significance
  and k-sensitivity. Trigger: when lag-model residuals show non-contiguous
  structure.

- **SEM half of the SAR honesty check.** The Durbin half is done (ρ holds
  controlling for neighbours' demographics). The spatial-error model is
  unidentified at zero noise, so the seed-free recovery pattern fails; it
  needs a property over noise draws or an analytic special case. Until then,
  describe ρ as "transmission not explained by own or neighbours'
  demographics", not bare "contagion".

- **Deep time, next.** County-level historical referenda (prohibition, the one
  complete rise-and-fall idea wave; women's suffrage), NHGIS decennial
  demographics (separates persistence of people from replacement of people;
  also sharpens the education-channel and Module 4 results), and a public
  "rabbit hole" page on the Populist → New Deal story. Trigger: after MPSA.

- **Internationalization.** Mexico is a portability demo for MPSA, deliberately
  small: one loader matching INE's certified totals, one map (Dec 6 in the
  to-do). Beyond the demo: Switzerland as the estimator's validation bench
  (municipal referenda since 1848); a multiparty partisan baseline (party-bloc
  or left-right composites); per-country boundary crosswalks; a documented
  free-and-fair data-quality gate. Trigger: after MPSA.

- **Non-political domains** (e.g. real estate). The analytical core is
  domain-agnostic; a pilot needs one loader to `fips × period × value`, a
  generic outcome name and a neutral map view. Monthly data suits the
  lead-lag machinery better than elections. Parked; first deliverable would
  be a notebook, not a product.

## NLP / text

- **GDELT** (free worldwide news catalog, themes and tone, every 15 minutes,
  BigQuery). Uses: the information-environment layer, Module 4, the aliasing
  hypothesis, Mexico. Check before trusting: coverage is not opinion; tone is
  dictionary-based and non-English text is machine translated; geocoding is
  often city or state, so county resolution needs an acceptance test against
  known events; BigQuery's free tier needs partition-filtered, costed queries.
  Trigger: the information-environment data step (Dec 13).
- **Stack: PyTorch + Hugging Face** (agreed 2026-06-15). Inference in `eval()`
  mode satisfies the reproducibility contract; fine-tuning tests pipeline
  contracts plus "overfit a tiny batch → loss near 0", never a seeded loss
  value. Pin CPU-only wheels; run inference as an offline build step, outside
  the coverage-gated unit path. First jobs: ballot-text features and
  content → cutpoint. Trigger: the information-environment features.

## Data

- **Ballot-measure ingests still on the starter list:** Michigan 2022 Prop 3
  (the blue end of the abortion contrast); Missouri 2022 Amendment 3
  (cannabis). Trigger: when a test needs them.
- **Midterms** (district → county crosswalks, uncontested races). Trigger:
  when the hazard model needs a two-year cadence.
- **Connecticut crosswalk** (planning regions ↔ old counties, retiring the
  ACS-2021 patch). Trigger: when CT demographics matter to an analysis.

## Product / UX

- **Public pages:** the wave story page (Nov 28 in the to-do); a web version
  of `BRING_YOUR_OWN_STATE.md`; link the wave player from the app once
  reviewed.
- **Prescriptive roadmap:** real drive-time routing; an in-map prescriptive
  mode (retiring the static demo page); tunable thresholds and goals
  (turnout, defense, not just persuasion).
- **Map polish:** named False-Bastion tiers; a hint when a measure is shown at
  national scope; a "fit colours to this view" toggle (only on request); a
  first-visit "how to read this map" panel.

## Engineering

- **E2E covers only the Kansas measure.** Ohio's YES orientation is
  unit-tested but not checked on the built app. Trigger: the next measure on
  the map, or before relying on the Ohio overlay for outreach.
- **Committed data products can go stale silently.** The deploy serves the
  committed `web/public/data/*.json`; it does not run the export. After
  touching the export or a wired loader, regenerate and commit (byte-diff when
  output-preserving). Better: a CI check for the products that need no Census
  key. Trigger: first stale-data incident.
- **Mutation survivors.** Triage the high-value SAR and Moran survivors from
  the diffs; noise-parameter mutants resist killing under the no-seed rule
  (same root as SEM) and may be documented as equivalent. Do not chase 100%.
- **Single-file-commit mystery** (contract Section 10): unexplained; the
  `git ls-files` tripwire is in place. On recurrence, capture evidence before
  repairing.
