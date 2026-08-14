# Findings — What the Engine Has Learned

A plain-language record of the research results behind the Geo-Fluid Dynamics
Engine, in the order the argument builds. Each finding names the notebook it
lives in and states its honest limits. The numbers here are from real public
data (county presidential returns, ACS demographics, certified ballot-measure
canvasses), computed by the tested `geofluid` library.

> **The through-line.** Party vote is a noisy, one-dimensional, *swappable* label.
> The durable, readable signal is **disposition** — and disposition is
> multi-dimensional. Geography describes *where* people are and is remarkably
> stable; the cleavages that move elections are *episodic*. So the engine earns
> its keep not as a crystal ball but as an instrument that **localizes** known
> forces to the unit of action, **flags where the simple story breaks**, and is
> honest about what it cannot predict.

---

## 1. Prediction of *change* is hard — and we proved it twice

The founding ambition was a "wave predictor": find where political change starts
and forecast where it spreads. Two serious attempts were **falsified on real
data**:

- **Contemporaneous conformity** (`county_influence`/`classify_nodes`): swing is
  so spatially autocorrelated that ~everyone co-moves at once — conformity can't
  separate a leader from a follower.
- **Lead-lag timing** (`spatial/leadlag`, on the 40-election 1868–2024 spine):
  the timing signal exists but is weak, spatially incoherent, and its extremes
  are tiny idiosyncratic counties, not influence hubs.

This is a result, not a failure: the *level* of the map (who's red, who's blue)
is highly predictable because it barely moves; the *change* — the only
interesting thing to forecast — is dominated by national mood, candidate effects,
and idiosyncratic human choice. A stable pattern carries little information about
what will change. *(Notebooks: `leadlag_node_roles`; see `BACKLOG.md` Module 2.)*

---

## 2. Party is a label; disposition is the signal

A century of "stable" electoral geography is an illusion of recency: over the
real span the South (Solid-Democratic for ~a century) and the Northeast
(Lincoln's Republican heartland) **swapped party labels** while their underlying
ideological dispositions stayed far more constant. The lesson for measurement:
track **disposition**, not party. The cleanest way to see disposition, stripped
of party label and candidate personality, is a **direct issue vote** — a ballot
measure.

---

## 3. False Bastions: where disposition diverges from party

A "False Bastion" is a place whose **issue vote runs ahead of its partisan lean**
— red on the surface, persuadable underneath. We find them on two independent
axes:

### Social axis — abortion (Module 3, live on the map)
Kansas (Aug 2022), Kentucky (Nov 2022), and Ohio (Nov 2023) abortion measures,
each ingested from its state's certified canvass and validated to the vote. Every
county in these red/purple states voted more pro-choice than its presidential
Democratic share. *(Module 3; the live map's dissonance overlays.)*

### Issue resistance is a stable *cross-issue* county trait
Ohio's Nov-2023 ballot carried **two** questions — abortion *and* cannabis — on
the **same 88 counties, same day**. Controlling for partisanship (the rigorous
`dissonance.issue_resistance` residual), a county's abortion resistance and its
cannabis resistance correlate **r ≈ 0.62**. Persuadability is a real, stable
trait of a *place*, not a one-issue fluke — the first county-level structure the
project found that swing never could. *Caveat:* one state; the two issues share a
"personal-liberty" flavor, so an off-cluster (e.g. economic) measure is the next
test. *(Notebooks: `issue_resistance_starter`, `issue_generality_ohio`.)*

### Economic axis — minimum wage (inverts "What's the Matter with Kansas?")
Across 10 verified statewide minimum-wage measures (2006–2020), every one passed
*above* its state's Democratic presidential share (mean **+15 points**), and the
gap is **largest where the state is reddest**: corr(partisan lean, economic
dissonance) = **−0.82**. Missouri (+31/+24), Arkansas (+27), Nebraska (+20) voted
for a raise 20–30 points beyond their presidential Democratic share; blue Colorado
(+2) and Washington (+1) sit on their partisan line. Put the economic question
*directly* on the ballot and red-state voters back it decisively — self-interest
crossing party, the opposite ideological direction from the abortion result, and
strong evidence the False-Bastion pattern is about *disposition vs. label*, not a
one-sided artifact. *Caveat:* N=10 verified subset, state-level/ecological,
selection bias (minimum wage is on the ballot mostly where it can win).
*(Notebook: `minimum_wage_economic_bastions`.)*

**Why this matters together:** disposition is multi-dimensional. A place can be
socially one way and economically another; only direct issue votes expose that
cross-pressure — and the cross-pressured places are exactly where minds are
movable. That is what the prescriptive demo turns into a targeting recommendation.

---

## 4. How change moves: geography beats similarity, education is the secondary edge

Does political change diffuse along *borders* (queen adjacency) or along
*similarity* (metro-to-metro, college-town-to-college-town)? Built a
non-geographic network (`attribute_knn_adjacency`) and raced it against geography
on residual swing (2004–2024), controlling for the fact that urbanicity, income,
age, and education all travel together:

- **Geography wins decisively** (Moran's I 0.62 vs best similarity network 0.28).
  "Ideas hop metro-to-metro" is not the story for presidential swing.
- **Among demographic axes, education leads and survives the collinearity
  control** — urbanicity's raw signal was partly *education in disguise* (they
  correlate 0.48). So if you add one non-geographic edge to a hybrid model, the
  evidence says make it **education similarity**.

*(Notebook: `diffusion_network_horse_race`; see `BACKLOG.md` Hybrid W.)*

---

## 5. Realignments *flicker*, they don't ratchet

Measuring how strongly residual swing organizes along the education network
*per election* shows the education cleavage is **episodic**: Moran's I was
near-zero through 2012 (0.02), **spiked in 2016 (0.34) and held in 2020 (0.32)**
— the Trump diploma-divide elections — then **collapsed in 2024 (0.05)**, while
geography stayed the dominant organizer throughout (0.50–0.74). The "diploma
divide" was the defining axis of the 2016/2020 *swings* specifically, not a
permanent new map; 2024's broad rightward shift was not education-patterned.

A realignment that switches on and off is precisely the regime-change signal the
unbuilt **Module 5 (systemic phase transitions)** is meant to detect — and a
caution against treating any single election's cleavage as the new permanent
structure. *(Notebook: `education_channel_over_time`.)*

---

## 8. Deep time: the Populist reservoir discharged into the New Deal

The 1868–2024 spine lets us test whether today's "Second Gilded Age" rhyme has
county-level substance. Using the third-party lens (the 1892 People's Party ran
outside the two-party system, so `dem_share_2p` is blind to it):

- **1892 Populism did NOT become 1912 Progressivism** — the Bull Moose/Debs
  county map is uncorrelated with the Populist one (r ≈ −0.08 non-South). The
  *ideas* entered both parties while the *places* that first carried them sat
  out a generation. Ideas and geography decoupled.
- **1892 Populism DID become the New Deal's surprise reservoir** — Populist
  share predicts the 1932 break from a county's own forty-year trend at
  **r = +0.38 (non-South)**, still **+0.28** against a baseline that never sees
  the 1928 Al Smith religious anomaly. Structure waited forty years for a macro
  catalyst (the Depression) plus a party willing to bid — the same
  episodic-realignment picture Module 5 sees in the education channel.
- **The 2016 echo (+0.28 non-South) is real but treacherous to read**: it is
  partly carried by silver-mining counties that became resort-economy blue
  (Aspen was Free Silver country). The 1892 bundle — economically radical,
  culturally traditional (Bryan prosecuted the Scopes trial) — maps onto
  *neither* modern party; its modern address is the False Bastion combination
  our ballot measures unbundle (minimum wage far above partisan lean, social
  measures at or below it).

*Caveats:* 1892 "other" includes small Prohibition-party totals; Southern
returns after 1890 are disenfranchisement-contaminated (reported separately,
weaker throughout, as they should be); counties are aggregates — persistence of
*places* is consistent with, but cannot prove, family transmission.
*(Notebook: `gilded_age_rhyme`.)*

---

## What it means for the product

The engine is a poor oracle and an excellent instrument. Its value is:

1. **Localization** — turning a known national force (the education cleavage, the
   abortion backlash) into a specific local action at the unit a human acts on (a
   county, a drive). *This is the prescriptive "art of the possible" demo — it
   makes no predictive claim.*
2. **Anomaly-finding** — surfacing the *residual*, the places the simple
   partisan model gets wrong (the False Bastions), because that's where the
   leverage and the surprise are.
3. **Honesty about limits** — knowing, with evidence, what spatial structure
   *can't* tell you (it can't forecast the realignment moment) is as valuable as
   what it can.

## Open questions (see `BACKLOG.md`)

- **Off-cluster generality — ANSWERED YES (2026-08-14):** across Missouri's
  eight-measure, 116-jurisdiction panel, the same-ballot 2024 abortion ×
  minimum-wage resistance correlation is **r = +0.52** — a social measure and
  an economic one, maximally off the personal-liberty cluster. The trait also
  holds within-issue across six years (minimum wage 2018×2024 **r = +0.68**),
  and is robust to baseline choice (era-matched vs 2024-only partisanship
  changes the headline numbers by <0.005). Sharpest new caveat: resistance
  coheres by ELECTORATE TYPE (general×general mean r ≈ +0.47 vs
  primary×general ≈ +0.06, while the two primary measures correlate +0.44
  with each other) — the turnout adjustment is where the 2026 prediction will
  be won or lost. *(Notebook: `mo_issue_space`.)*
- **Migration as the network:** people moving *is* the geospatial signal;
  county-to-county migration flows are a better-motivated diffusion network than
  borders or demographic similarity. Untested.
- **Module 5:** detect the realignment *event* — when the label rips loose from
  the disposition and reattaches. The deepest unsolved question here.
