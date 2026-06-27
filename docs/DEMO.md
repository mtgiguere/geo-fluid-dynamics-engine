# Demo Walkthrough — Geo-Fluid Dynamics Engine

A clean, click-by-click script for showing the engine to someone in ~5 minutes:
what to click, what it shows, what to say, and why it matters. Written for a
live demo (e.g. an interview), but it doubles as the "how to read this" guide.

**The one-sentence pitch:**
> We got curious whether the same public election data behind a map could answer
> a question the map can't: where should an organizer actually *go*? This is the
> result — it turns the data into a plain-English plan: which counties to campaign
> in, in what order, and which to skip.

**The arc to keep in your head** (this is the whole story — each stage is a
question we wanted the data to answer, building on the one before):

| Stage | The question it answers |
|-------|-------------------------|
| **Descriptive** | *What happened?* |
| **Diagnostic** | *Where is something surprising?* |
| **Predictive** | *Is that surprise a reliable signal?* |
| **Prescriptive** | *So what do I do about it?* |

The demo walks top to bottom and lands on the last row.

---

## Links

- **Live map:** https://mtgiguere.github.io/geo-fluid-dynamics-engine/
- **The prescriptive demo:** the **🧭 "The art of the possible"** button in the app header
  (or directly: `…/demo.html`). It is a public page — no login — so you can send
  the link or screen-share it.

> Everything below is real: real certified election returns, real Census
> demographics, computed by tested code. Nothing in the demo is mocked.

---

## The 5-minute flow (recommended)

The **demo page tells the whole arc on its own** and is bulletproof (no live
dependencies). The live map is the "…and it's a real running system" opener.
If you're short on time or the venue's network is shaky, **just open the demo
page** — it stands alone.

### 0 · Open the live map (≈45 sec) — establish it's real

Open the live map. While it paints:

> "This is deployed, live, and interactive — every U.S. county, real election
> data back to 1868. Let me start with the map view, then show you the question
> we wanted to chase from there."

- **Metric dropdown → "Two-party result"** (the default). Colored map.
- **Click any county** → a popup with its result and demographics.
- **Metric dropdown → "Swing since last election"**, then hit **▶ Play** for a
  second or two — the decades animate.

> "That's the map view — accurate, and genuinely useful. But if your job is to
> *decide where to go*, it leaves you to work that out yourself. That's the part
> we got curious about."

### 1 · The diagnostic view (≈45 sec) — the surprise

- **Metric dropdown → "Ballot measures" group → "Kansas: Abortion rights
  (Aug 2022)."** The map auto-zooms to Kansas and recolors.

> "August 2022 — Kansas, a deep-red state, votes to *protect* abortion rights
> and shocks everyone. This layer isn't the result; it's the **gap** between how
> each county votes its *party* and how it voted its *conscience*. Blue = voted
> more pro-choice than its partisanship predicts. We call those **False
> Bastions** — red on the surface, persuadable underneath."

That's the diagnostic. Now the turn.

### 2 · The knockout — click 🧭 "The art of the possible" (≈3 min)

> "But this is *still a map*. Watch what happens when we make it tell you what
> to do."

Click the **🧭 "The art of the possible"** button. The demo page opens. Scroll through
its three acts — you've just previewed Acts 1–2 on the live map, so move quickly
to **Act 3**, where the payoff is.

**Act 3 — "You live in Kansas City. Here's your Saturday."**

This is the screen to linger on. Point at the **map + the ranked list side by
side**:

- **The map:** amber counties = go here (persuadable), slate = your base, grey =
  skip. The pulsing dot is "you" (Kansas City).
- **The list = marching orders.** Read a couple aloud:
  - *"Leavenworth County — **14 miles** away — voted 59% to protect rights in a
    county only 39% Democratic. **+20 points** of conscience over party. That's
    your easy first stop."*
  - *"Osage County — **+29 points**, the strongest persuadable county in range."*
- **Hover a row or a county** — they're **linked**: the county lights up on the
  map and everything else dims. *"Hover any stop and it shows you where to
  drive."*
- **Point at the "Skip your base" line:** *"Johnson, Douglas, Shawnee — already
  with you. The tool tells you NOT to waste a Saturday there. Knowing where not
  to go is half the value."*

> "So instead of a map I have to interpret, I have a route: start in Leavenworth,
> then work the ring south and west. Ranked by persuadability, ordered by drive
> time, with the reason in plain English."

**Then the proof it's predictive** (scroll to the Act 2 callout if you skipped
it, or just say it):

> "Fair question: is this just an abortion map? No. In Ohio, the same 88 counties
> voted on *two* different things the same day — abortion and cannabis. The
> counties that broke from their party on one broke on the other too —
> correlation **0.62**, with partisanship held constant. **Persuadability is a
> stable trait of a place.** That's what makes this a prediction, not a
> coincidence."

### 3 · The honest close (≈45 sec) — the reason to hire you

> "I want to be straight about what this is: it's **stage one**. One issue, one
> state, fixed thresholds. What I've proven is the *pipeline* — descriptive to
> diagnostic to predictive to a prescriptive recommendation a volunteer can act
> on — and that the signal underneath it is real and generalizes.
>
> What's next is the fun part: more issues and states, a persuadability score
> that travels, drive-time routing, and turning this into a live mode inside the
> map. That's the work I'd love to do with you."

---

## Cheat-sheet — the real numbers

**Kansas Aug-2022 abortion (the demo's data).** Statewide the "NO" (pro-choice)
side won ~59% — our panel matches the certified Secretary-of-State canvass to
the vote. Home county: **Wyandotte (Kansas City, KS)**.

The ranked itinerary the page shows (target counties, by persuasion leverage):

| Stop | County | Drive | Conscience-over-party |
|-----:|--------|------:|----------------------:|
| 1 | Osage | 61 mi | **+29 pts** |
| 2 | Franklin | 47 mi | +26 pts |
| 3 | Jackson | 61 mi | +23 pts |
| 4 | Miami | 37 mi | +23 pts |
| 5 | Jefferson | 35 mi | +22 pts |
| 6 | **Leavenworth** | **14 mi** | +20 pts |
| 7 | Doniphan | 53 mi | +18 pts |
| 8 | Atchison | 41 mi | +17 pts |

**Skip (your base):** Johnson (69% pro-choice), Douglas (82%), Shawnee (66%).

**Classification across Kansas:** 81 persuadable targets · 4 base · 19 hard
ground (of 105 counties; your home county is excluded).

**The predictive proof:** Ohio Nov-2023, abortion (Issue 1) vs cannabis
(Issue 2), same 88 counties, same ballot — partial correlation **r ≈ 0.62**
(controlling for partisanship). Persuadability is a stable cross-issue trait.

---

## Questions you should expect (and honest answers)

**"Isn't this just showing me Democratic-leaning counties?"**
> No — the opposite. It deliberately sets your base aside. A target is a county
> that voted *against* its partisanship — Republican by the numbers, but
> persuadable on the issue. The whole point is finding voters your party map
> would tell you to ignore.

**"Does this generalize beyond abortion?"**
> That's the Ohio result — r ≈ 0.62 across two unrelated issues on the same
> counties. The honest caveat: it's one state, and abortion and cannabis both
> have a 'personal-liberty' flavor, so the next test is an *off-cluster* measure
> (say, an economic one). But the first generalization test came back positive.

**"What about predicting waves — where change spreads from?"**
> We tested that and it mostly *didn't* hold: in presidential voting, change is
> one national tide hitting everywhere at once, not a wave that ripples
> county-to-county. We have the analysis. That negative result is *why* the tool
> targets persuadable *places* instead of chasing phantom wavefronts — good
> prediction starts with refusing to predict what you can't. (There's a promising
> open idea: that change may diffuse through *similarity* networks — big metro to
> big metro — rather than geographic adjacency. That's on the roadmap.)

**"How current / where's the data from?"**
> Public records: county presidential returns (1868–2024), Census ACS
> demographics, and certified Secretary-of-State ballot-measure canvasses. Every
> ingest is validated against the official statewide totals before it ships.

**"Is the math trustworthy?"**
> It's built test-first — the classification, the distances, the statistics all
> have tests written before the code, no seed-fishing, and the deployed app is
> gated by an end-to-end test that runs the real build in a real browser. When a
> model failed (two earlier attempts at the influence question), we *recorded the
> falsification* rather than burying it.

**"Could this scale to all 50 states / other contests?"**
> Yes — the architecture is built for it. Each state's data is a small loader
> feeding one canonical pipeline; the prescriptive engine is data-source-agnostic.
> Adding a state is data work, not a rebuild. That's stage two.

---

## If you only have 60 seconds

Open `…/demo.html`, scroll to **Act 3**, and say:

> "Same public election data behind any map — but turned into a route. It hands
> a Kansas City volunteer a weekend plan — drive to Leavenworth first, 14 miles,
> these folks vote their conscience over their party; skip Johnson County, they're
> already with you. Ranked, reasoned, and it's proven to generalize across issues.
> That's the leap from *what happened* to *what to do* — and it's stage one."
