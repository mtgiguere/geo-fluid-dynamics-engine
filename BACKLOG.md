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
