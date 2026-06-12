# Backlog

Work items agreed but deliberately not started (JIT: each begins when its
trigger arrives, with its own tests). Newest decisions at top of each section.

## Product / UX

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

- **Spatial lag / Durbin regression**: how far does a neighbor's swing travel
  after demographics have said their piece. Trigger: next science arc.
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

- **Mutation score baseline**: first mutmut run (nightly workflow exists;
  predictions on record: _ACS_SENTINELS and _TOTAL_MODES members will
  survive). Trigger: first completed nightly run — read results, turn
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
