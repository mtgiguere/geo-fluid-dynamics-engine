# Backlog

Work items agreed but deliberately not started (JIT: each begins when its
trigger arrives, with its own tests). Newest decisions at top of each section.

## Product / UX

- **Scoped views — "my area," not the whole country** (2026-06-13, Matt's
  product insight): most orgs work a state, region, district, or locality
  (state-senate cluster, a House district, a media market), and the national
  map is too much. Build SCOPE as a first-class filter = a set of FIPS, with
  state (fips prefix) as one preset — the SAME mechanism serves state /
  region / district / locality. Mostly a frontend filter: everything is
  FIPS-keyed, national metrics already load in the browser, so filter
  client-side + fit camera to scope bounds + recount the storyline for the
  scope. No new export artifacts.
  KEY DECISION (settled): scoped views DISPLAY the national statistics
  filtered — they do NOT recompute spatial stats (LISA/Moran/SAR) inside the
  boundary, because border counties have real cross-state neighbors and
  severing them contradicts the engine's thesis. Dissonance is the lone
  intrinsically-scoped metric (referendum data is state-bounded by nature).
  Minor, deferred: keep the national color ramp by default (a "fit colors to
  this view" toggle only on request — rescaling breaks cross-scope
  comparison). Unlocks the Kansas dissonance view as scope=KS.
  Trigger: next UX arc / when Matt greenlights.

- **Explainer key for every map view** (2026-06-12, from a real misreading):
  Matt read wave-anchor red over Chicago as "Chicago votes Republican" — the
  layer shows clusters of *change*, and intuition does not supply that
  distinction. The interim fix (chip wording + legend caption) helps, but the
  final product needs a proper key: per-view plain-language explanations of
  what is shown, what colors mean, what gray means, and what question the
  view answers — visible without hovering, written for the spec's audience
  (policymakers, journalists, students, organizers — not statisticians).
  Trigger: before any public-facing milestone / first outside user.

## Science (Module 1+)

- **Hybrid W**: blend queen adjacency with connectivity (commuting flows,
  broadband, media markets) per the spec's W_hybrid. Trigger: when the lag
  model's residuals show non-contiguous structure.

## Data

- **Ballot measures ingest** (county-level, per-state SoS sources; Kansas
  Aug 2022 first): unlocks Module 3 dissonance/False Bastions with real
  topic votes. Trigger: after the core engine is proven on the presidential
  spine.
- **Historical extension** (Algara–Sharif 1868–2020 + NHGIS decennials):
  regime diversity for Module 4, era-similarity tests, replay depth.
  Trigger: when Module 4 work begins, or when the replay UX wants depth.
- **Midterms** (district→county crosswalks, uncontested-race handling).
  Trigger: when the hazard model demands 2-year cadence.
- **Connecticut crosswalk**: planning regions ↔ old counties, to retire the
  ACS-2021 patch. Trigger: when CT's 2021-vintage demographics become a
  problem for an analysis.

## Engineering

- **Mutation score baseline**: workflow exists but has NEVER executed
  (confirmed 2026-06-12: zero runs in three days — GitHub skips crons on
  quiet repos; see the contract's "a guardrail that has never run is
  decoration"). Predictions on record: _ACS_SENTINELS and _TOTAL_MODES
  members will survive. NEXT STEP: Matt dispatches once (Actions →
  Mutation testing → Run workflow); if the next cron also skips, move the
  schedule into a push-triggered workflow. Then read results and turn
  survivors into pinning tests.
- **Git single-file-commit mystery** (TDD_CONTRACT.md OPEN INCIDENT):
  unexplained; tripwire in place. Trigger: any recurrence — capture
  evidence before repairing; consider upgrading git 2.24.

## Science honesty notes

- **SAR vs spatial-error/Durbin comparison** (2026-06-12): the SAR rho attributes
  ALL spatial structure to transmission. A spatial error model (regionally
  correlated shocks) or Durbin terms (neighbors' demographics) would separate
  "change spreads" from "shocks cluster". Trigger: before any public claim that
  rho measures contagion.
