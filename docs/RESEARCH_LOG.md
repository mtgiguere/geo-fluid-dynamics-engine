# Research Log: the Questions We Asked

`FINDINGS.md` holds the results we stand behind. This log keeps a record of the
brainstorms behind them: every question we asked, what we checked, what we found,
and what is still open. Some of these turned out minor. They are kept anyway, so
nobody has to ask the same question twice, and so a talk or paper can show the
alternatives we considered and ruled out.

Entries are dated, newest first. Numbers come from the data on the stated day.
Where a number came from a quick look rather than a tested module, the entry
says so.

---

## 2026-11-07 to 2026-11-11: Is there a wave? Proving it on a known one (rooftop solar)

### Where we stand (end of 2026-11-11)

Plain version: **ideas do travel from neighbour to neighbour, and we can
measure it, as long as the data is dated finely enough.** Elections photograph
the wave too rarely to see it move. All numbers below are quick looks (scratch
EDA, one run, no confidence intervals yet), built on tested modules.

| Wave | Data | Border effect | Learning ÷ alike | Over time |
|---|---|---|---|---|
| Rooftop solar | 3.6M installs, by county and quarter, ~2000-2025 | 4-7x after each state's own clock | ~2.4-3x | (25 years only) |
| State laws | 563 laws x 50 states, 1691-2017 | ~3.4x | ~1.3-2x | Learning fell from ~2.0 before 1960 to ~1.4 since |
| Baby names | 838-1,350 names x 51 states, 1910-2025 | ~12x | ~6-10x | ~16x before 1950, ~8-10x since 2000 |

- **Border effect:** how much more likely a place is to adopt once its
  neighbours have. A shuffled map gives ~1 in every case.
- **Learning ÷ alike:** past neighbours against future neighbours, in one
  model. Future neighbours cannot be learned from, so their pull is the
  ceiling on "neighbours are alike".

What we have learned:

1. **Waves are real in all three**, and mostly forward in time (learning),
   not just look-alike neighbours.
2. **The wave is fast.** Solar neighbours are about 9 months apart, and a
   state is crossed in about 3 years. Sampling every 4 years makes about 69%
   of neighbour pairs look simultaneous. That alone explains why election
   swings looked like "everyone moves at once".
3. **Waves change over time.** They weaken but do not vanish as national media
   grows. The roads of the 1950s are not quite today's.
4. **Pushed ideas spread differently.** Model laws from a national drafting
   shop spread less along borders (2.3x against 3.6x). The salesperson and
   canvasser question has a measurable twin.

What is built (tested): `ingest.solar`, `ingest.zcta_county`, `ingest.spid`,
`ingest.names`, and the timing model `spatial.timing` (take-off, at-risk table
with yearly or quarterly steps and never-adopters, and a hazard fit with any
number of shares, a clock per wave, national or state).

Branches: `feat/solar-adoption` → `feat/spid-policy-diffusion` →
`feat/names-diffusion`, stacked, none merged. The merge waits for the
December certified pass.

Next:
- confidence intervals by resampling waves
- a within-state shuffle for solar
- the Dec 6 notebook (open list below)
- then the first political run: FEC donations, dated by day and ZIP

### The starting question

Our election data says a whole state moves at once. Ohio and Missouri counties
shift together; the neighbour-to-neighbour lead-lag was falsified twice (see
`FINDINGS.md` and BACKLOG). That makes no sense against everything we know about
ideas: language and religion have spread from person to person, and from place
to place, since the dawn of civilization. So either ideas do not travel the way
we think, or our measurements cannot see them travel.

Two reasons a measurement could miss a real wave:

- **The clock problem.** Elections are snapshots years apart. A wave that
  crosses a state between two snapshots shows up as everyone having moved at
  once (aliasing: you need to sample faster than the thing you are watching).
- **The road problem.** Ideas may travel along cities, commuting and media
  markets, not along county borders, which is the only "road" our spatial
  weights used.

### Q: Can we prove a wave on something that is not politics?

The thing that spreads is an idea, so any dated, located record of people
adopting an idea will do. Stand-ins discussed: rooftop solar, electric cars,
baby names, new technology. Matt picked **solar**. Home solar is known to spread
from neighbour to neighbour in the economics literature (Bollinger & Gillingham
2012, California; Graziano & Gillingham 2015, Connecticut). It is recorded
install by install with a date and a ZIP code, and the data is free. Facebook's
Social Connectedness Index was considered for the "roads" and dropped: no
Meta data in this project. Census commuting flows and IRS migration flows are
used instead.

**Data:** Berkeley Lab's Tracking the Sun / Distributed Solar file, 2026
edition. It has 3,995,665 installs, matching Berkeley Lab's "about 4.0
million", in 27 states plus DC. **Missouri is not in it.** A ZIP-to-county
bridge is built from the Census 2020 ZCTA-county file. Built TDD in
`ingest/solar.py` and `ingest/zcta_county.py`: 3,643,662 household installs,
1,119 counties x 112 quarters (1998-2025).

### Q: Does solar show a wave?

**Yes, and it holds up after taking out each state moving at once.**
Method (tested module `spatial/timing.py`):

1. Each county "takes off" in the first quarter it reaches a set share of its
   own final install count. Measuring a county against itself means thin data
   coverage (Texas and Maryland, about a quarter of installs with a usable ZIP)
   does not make it look late.
2. Every county is "at risk" each quarter until it takes off. We record what
   share of its neighbours took off in an earlier quarter.
3. A discrete-time hazard model (a logistic regression) estimates how much a
   neighbour having taken off raises a county's odds of taking off this
   quarter. Before that, a "clock" is taken out: one baseline per quarter
   (the national clock) or per state per quarter (the state clock).

| Clock taken out | Neighbour odds ratio (6 take-off definitions) |
|---|---|
| National only | 15-21x |
| Each state's own | **3.9-7.4x** |

About two-thirds of the raw effect is states moving at once (state programmes:
Illinois 2019, Maryland 2021). What survives is a county-to-county wave inside
states.

**Not yet tested:** whether it is more than chance (placebo shuffle), and the
alternative explanations below.

### Q: What else could make a wave, besides ideas spreading?

We should not claim we are right without ruling these out. Matt's first two
were incentive programmes moving from place to place, and installers or
salespeople moving from area to area. The full list:

1. **Policy and money below the state level.** Utility rebates and rules (a
   utility's territory is a block of neighbouring counties), city and county
   permitting, PACE loans, and electricity prices that neighbours share.
2. **Supply.** Installers opening branches; door-to-door sales and "$0 down"
   leases sold area by area; marketing bought by TV market. A salesperson is
   still a way an idea travels, but a paid one. The politics twin is the field
   office against the friend at the barbecue. We want to separate the two, not
   throw one away.
3. **Neighbours are alike.** Income, homeownership, age, sunshine and housing
   type all cluster. So does the new-construction edge: builders put solar on
   new subdivisions, and California required it on new homes from 2020.
4. **Measurement.** The file is assembled from utilities and state
   programmes. When a provider starts reporting, all its counties "appear" at
   once, which is a fake wave. Our own choices (take-off definition, ZIP to
   county) also matter.
5. **The reflection problem.** If take-off timing varies smoothly across the
   map for any reason, a county's neighbours on the early side will
   "go first" automatically.

The raw file carries the columns needed to test most of these:
`installer_name`, `self_installed`, `utility_service_territory`,
`data_provider_1`, `new_construction`, `third_party_owned`, plus price,
rebate and income.

| Explanation | Test |
|---|---|
| Utility programmes | Baseline per utility per quarter instead of per state |
| Provider starting to report | Baseline per provider; drop each provider's first quarters |
| Installers expanding | Self-installs and installers already present; does installer arrival come before take-off? |
| Door-to-door leasing | Owner-owned systems only |
| Building frontier | Drop new construction |
| Neighbours are alike | Neighbours vs lookalike counties (the 0.62 vs 0.28 test from politics) |
| Smooth gradient | **Future-neighbour placebo**: neighbours taking off LATER should not predict you |
| Chance | Shuffle take-off dates within states |
| Which road | Borders vs commuting (Census) vs migration (IRS) |

What would count as "ideas move": the wave survives the utility and provider
baselines, survives dropping leases and new builds, beats lookalikes, passes
the future-neighbour placebo, and travels commuting lines more than borders.
Every test it fails tells us what kind of wave it is, which is still a result.

### Q: How fast does the wave move?

A quick measurement (scratch EDA, 2026-11-11; to be redone in the Dec 6 solar
notebook). Take-off is at 10% of a county's final count, for 724 counties with
at least 25 installs. The 491-county version (at least 100) agrees.

- **Neighbour to neighbour: a median of ~9 months** between adjacent counties
  in the same state. Any two counties in the same state are a median of 12
  months apart.
- **A whole state: a median of ~3 years**, from its earliest-taking-off tenth
  of counties to its latest tenth.
- **Ground speed: a median of ~100-120 miles a year**, measured as the slope of
  take-off date on distance from the state's first county. Two kinds of state:
  - slow fronts: Colorado, New Jersey, Wisconsin and Maine at 20-50 miles a
    year, where distance predicts take-off strongly (r 0.5-0.9);
  - near-instant: Illinois, Maryland, Washington and Pennsylvania, which go
    within about a year, like a state programme flipping a switch.

### Q: Could the wave be real, and our political model miss it because years are too long to see the "fire burning"?

**Solar says yes, it can.** Here is the share of neighbouring pairs whose
take-offs fall between the same two snapshots, so they look simultaneous:

| How often you look | Neighbour pairs that look simultaneous |
|---|---|
| Every quarter | 11% |
| Every year | 35% |
| Every 2 years (each November election) | 53% |
| **Every 4 years (presidential)** | **~69%** |

A wave we know is there looks about 70% "everyone moves at once" through
presidential-year snapshots. Solar is a slow idea (a $20,000 decision), and
political ideas likely move faster, which would blur them even more.

The caveat: blurring explains why we cannot see a wave in election data; it
does not prove one is there. A national shock that hits everyone at once looks
the same through coarse snapshots. Telling them apart needs dated political
"adoptions".

### Q: How long does it take for panels to show up on a house? Does that change the "idea" story?

Matt's point: a neighbour may SEE the panels and ask, rather than be told.

- The file has one date per install: when the panels went up. For some
  providers it is a proxy (inspection or incentive-claim date; user guide).
  It is not the decision date, so the decision-to-roof delay cannot be
  measured from our file.
- National figures: contract to switch-on is a median of ~93 business days
  (~4-5 months) for home PV in 2024 (NREL SolarTRACE, via a secondary
  summary; the primary report is not yet checked). An older 2015 NREL study
  found a median of 53 business days from utility application to permission
  to operate. Construction itself is ~2 days; the wait is permits, inspection
  and the utility.

What follows:

- Of the ~9-month neighbour gap, roughly 4-5 months is the hardware pipeline.
  **The idea itself crosses faster than the panels show.**
- The recorded date is the moment panels become visible, which is exactly the
  right start for a "seeing" mechanism.
- **The delay-pattern test:** which delay after a neighbour's take-off predicts
  best (1, 2, 3, 4, 6 quarters)? A peak around 2-3 quarters fits
  see → decide → pipeline. A peak in the same quarter points to a shared
  shock (rebate deadline, sales blitz), not seeing.
- **Seeing vs being told:** seeing is street-scale and fades with distance;
  being told travels along social ties (commuting, migration). The roads test
  partly separates them. A ZIP-level panel gets closer to seeing distance
  (ZCTA borders are free from Census, and we already have every install's ZIP).

### Q: Is there a way to tell if a salesperson (like a political canvasser) speeds up the process?

Yes. The file names the installer on most installs (`installer_name`) and
whether the system is a lease (`third_party_owned`). The big "$0 down" lease
firms (SolarCity/Tesla, Vivint, Sunrun) sold door to door. Four tests:

1. **Arrival event study.** Date the quarter a door-to-door firm first installs
   in each county. Then ask: does adoption speed up after it arrives, compared
   with similar counties it reached later (staggered timing)?
2. **The reverse-causation check.** Firms go where demand is already growing.
   If adoption was already speeding up BEFORE the firm arrived, the firm
   followed the wave; it did not cause it. Look at the quarters before
   arrival.
3. **Selling plus seeing.** Is a sale more likely on a street, ZIP or county
   that already has panels? If salespeople work hardest where neighbours
   have already adopted, the two mechanisms add up.
4. **Wave speed by channel.** Run the neighbour hazard separately on leased
   (sold) and owned (mostly self-sought) systems. Then compare front speed
   where door-to-door firms operate with where they do not.

The politics twin is well studied. In randomized field experiments,
door-to-door canvassing raises turnout (Gerber & Green 2000), while
persuasion effects in general elections average close to zero (Kalla &
Broockman 2018). Campaign field-office placement has also been studied for
its effect on the vote. So "a salesperson speeds up turning out people who
already agree, more than changing minds" is a hypothesis solar can test
with dated, located sales.

### Q: Do waves themselves change over time? Is there an older parallel to check?

Matt's point: solar is recent. Suppose we show waves running east from Kansas
City and west from St. Louis, meeting in the middle. That might hold now and
for a few years, maybe a decade, but people and places change, so the roads
waves travel may change too. Is there an older wave (the 80s, the 90s: cable,
DirecTV, the internet) to check whether a wave pattern repeats closely, or
not at all?

**What we already have:** FINDINGS #8, where the 1892 Populist map predicts
1932. Some geographic structure lasted 40 years. Whether the ROADS (direction,
leaders, followers) last is a separate question.

**The test:** many waves over the same ground across decades. For each wave,
build a "who goes early" map (each county's take-off relative to its state),
then correlate the maps across eras. High correlation means the roads are
stable. Correlation that decays with time means the roads drift; measure how
fast, and that is the shelf life of a targeting map ("good for about N
years"). No correlation means each wave makes its own roads.

**Candidate historical waves** (availability from memory, not yet checked
except where noted):

| Era | Wave | Geography / timing | Free? |
|---|---|---|---|
| 1690s-2017 | State policy adoptions, ~700 policies (SPID, Boehmke et al.) | State, year | Yes (Harvard Dataverse) |
| 1910-now | Baby names: thousands of separate dated waves | State, year | Yes (Social Security) |
| 1952-2020 | Religion: congregations and members by denomination (RCMS) | County, ~10 yrs | Yes (ARDA) |
| 1869-2004 | Newspapers opening and closing (Gentzkow-Shapiro-Sinkinson) | County, year | Yes (ICPSR, free account) |
| 1920s-60s | Farm electrification, tractors, radios (1930), TV sets (1950/60) | County, 5-10 yr censuses | Yes (Haines county data, ICPSR) |
| 1940s-50s | TV stations arriving (Gentzkow's TV and turnout paper) | Market, dated | Replication data, likely |
| 1962-2006 | Walmart store openings (Holmes): a company wave | Store, month | Believed yes; to verify |
| 1999-2008 | Broadband: FCC high-speed providers per ZIP | ZIP, every 6 months | Likely; archive to verify |
| 1980s-90s | Cable / DirecTV | Cable launch dates in the TV & Cable Factbook | Not free as far as we know; DirecTV never published subscriber geography |

Notes:

- Baby names and state policies answer "do waves change?" most directly:
  hundreds to thousands of waves across a century.
- Religion and newspapers give county-level detail over 50+ years.
- Broadband and Walmart are mostly supply (a company arriving): twins of
  the salesperson question rather than of ideas.

**Literature head start:** Desmarais, Harden & Boehmke (2015, "Persistent
Policy Pathways") estimated which states follow which, era by era. They found
the pathways fairly persistent but changing over time, which supports the
scepticism.

### First look, 2026-11-11: state policies (SPID v1.2, scratch EDA)

Matt picked state policies to stay close to the political theme. Ingest is
tested (`ingest/spid.py`), and acceptance equals the codebook (17,823
adoptions, 724 policies). This is a quick look, not the hazard model. Each
policy's adoption order is turned into a timing percentile per state (a
non-adopter counts as last). Policies adopted by at least 10 states. Eras by
the policy's first adoption year.

**1. The border wave is real in every era, and it fades.** Bordering states
adopt closer together in time than non-bordering states:

| Era (policy first adopted) | Policies | Neighbours closer in timing by |
|---|---|---|
| 1691-1929 | 74 | 17.5% |
| 1930-1959 | 68 | 14.6% |
| 1960-1979 | 113 | 10.5% |
| 1980-1999 | 175 | 8.8% |
| 2000-2017 | 28 | 15.1% (few policies; noisy) |

(Alaska and Hawaii dropped: they were not states before 1959. Uniform Law
model acts excluded, see 3.) This matches the 2026 "From Borders to Networks"
paper: borders mattered more a century ago.

**2. The leaders persist, but they drift.** Each state's average timing per
era, correlated across eras:

| | 1691-1929 | 1930-59 | 1960-79 | 1980-99 | 2000-17 |
|---|---|---|---|---|---|
| 1691-1929 | 1 | 0.75 | 0.66 | 0.51 | 0.38 |
| 1930-59 | | 1 | 0.69 | 0.50 | 0.39 |
| 1960-79 | | | 1 | 0.66 | 0.42 |
| 1980-99 | | | | 1 | 0.59 |

Neighbouring eras (~25-30 years apart) correlate ~0.6-0.75; eras ~90 years
apart, ~0.4. **Matt's hunch holds: the map of who goes first changes, slowly.**
It never fully resets. California and New York are early in almost every
era; Mississippi and Wyoming are late in almost every era. A rough shelf
life: a "who goes early" map keeps most of its value for a generation, and
about half after a lifetime.

**3. Pushed policies spread less along borders.** Uniform Law Commission
model acts are neighbours-closer by 7.4%, the rest by 12.5% (all eras,
first run, AK/HI included). A model-law shop sends the same text to every
legislature, a network rather than a border. This is the salesperson twin
again.

Caveats, to fix in the real analysis:
- Timing percentiles, not the hazard model with a clock.
- Era is set by each policy's first year.
- The mix of policies changes by era: 75 of the ~120 policies first adopted
  after 2000 are Uniform Law acts. With them included, the 2000-17 leaders
  look unrelated to the early eras (r near 0). That is a composition
  artefact, which is why the table above excludes them.
- Policy direction (liberal vs conservative laws) changes who "leads", and
  is not yet separated.
- States not yet admitted (Arizona 1912 and others) count as late.

Next: the hazard model on SPID, with each policy's own clock and right
censoring (states not adopting by 2017). Compare against the researchers'
yearly diffusion ties, 1960-2017 (doi:10.7910/DVN/1QJCDJ).

### Second look, 2026-11-11: state policies through the hazard model

The timing model was extended for laws (tested): yearly steps; states that
never adopt stay in as "not yet" through 2017; and each law has its own
clock (baselines per law per year). The table covers 563 laws adopted by at
least 10 states: 686,126 state-years, 16,660 adoptions. Alaska and Hawaii
drop out automatically, having no land border. Scratch EDA, one run, no
confidence intervals yet.

**Odds ratio for "a bordering state has already adopted":**

| | All | 1691-1929 | 1930-59 | 1960-79 | 1980-99 | 2000-17 |
|---|---|---|---|---|---|---|
| Real borders (any time before) | 3.36 | 4.30 | 3.83 | 2.76 | 3.07 | 3.48 |
| Organic laws only | 3.57 | 4.37 | 4.03 | 2.94 | 3.29 | 4.06 |
| Uniform Law model acts only | 2.27 | 1.78 | 1.90 | 1.71 | 2.19 | 3.13 |
| Placebo: shuffled map (5 runs) | 0.94-1.10 | | | | | |

**Placebo, the fair fight:** neighbours adopting in the PAST k years (could
be learned from) against the NEXT k years (cannot be):

| Window | All | 1691-1929 | 1930-59 | 1960-79 | 1980-99 | 2000-17 |
|---|---|---|---|---|---|---|
| Past 5 years | 3.05 | 4.01 | 3.58 | 2.35 | 2.94 | 3.32 |
| Next 5 years (placebo) | 1.81 | 1.70 | 1.63 | 1.83 | 1.89 | 1.97 |
| Past 2 years | 2.84 | 4.45 | 3.15 | 2.32 | 2.59 | 2.75 |
| Next 2 years (placebo) | 2.08 | 2.26 | 1.54 | 2.18 | 2.07 | 2.44 |

What it says:

1. **Geography is real.** A shuffled map gives ~1. Real borders give ~3.
2. **The border effect has two parts.**
   - A **"neighbours are alike"** part: the future-neighbour placebo is
     ~1.6-2.4, not 1. It is steady across all eras.
   - A **forward-in-time** part, consistent with learning from neighbours:
     past beats next in every era.
3. **The forward part is what faded.** Past-to-next ratio at 5 years:
   ~2.4 before 1930, ~2.2 in 1930-59, ~1.3 in 1960-79, ~1.6 in 1980-99,
   ~1.7 in 2000-17. At 2 years: ~2.0, ~2.0, ~1.1, ~1.3, ~1.1. States
   learned from their neighbours far more before 1960; since then the
   border signal is mostly shared regional character. This fits "From
   Borders to Networks", and Matt's hunch that waves change over time.
4. **Pushed laws (model acts) spread less along borders**, confirmed in the
   hazard model: 2.27 against 3.57.

Caveats: no confidence intervals yet (bootstrap by law next); the clock is
per law per year, but not per region; statehood dates not yet handled; and
the policy mix still changes by era.

### Third look, 2026-11-11: baby names, a mass behaviour (SSA, scratch EDA)

**Q (Matt): should we try baby names too?** Yes. A law is chosen by a few
hundred legislators; a name by millions of parents copying what they see and
hear. That is closer to how a vote moves.

Ingest `geofluid.ingest.names` (tested). Acceptance: 6,696,687 rows, 51 files
(50 states + DC), 1910-2025, no duplicates, no count under 5. The state counts
summed give SSA's published #1 names: Mary/John 1910, Linda/James 1950,
Emily/Jacob 2000, Olivia/Liam 2024.

**Set-up:**
- **Wave:** each name and sex counts as one wave. The name must have been rare
  in 1910-14 (under 2% of its later peak), so we see it arrive. It must also
  peak in 1925 or later, and reach a national peak share of at least 0.1%
  (run 1) or 0.05% (run 2).
- **Take-off:** the first year the name's share of a state's births reaches
  25% (run 1) or 50% (run 2) of its national peak share. States that never
  reach that bar stay in as "not yet" through 2025.
- **Model:** same state borders, same per-wave clock, same placebos as the
  laws.

| | Run 1 (838 names) | Run 2 (1,350 names) |
|---|---|---|
| Years from the 10th to 90th percentile state reaching the bar (median name) | 10 | 10 |
| Mean gap between neighbours / any two states | 4.30 / 6.13 yrs | 4.31 / 6.02 yrs |
| Real borders, all eras | **12.7** | **11.8** |
| 1910-49 / 1950-79 / 1980-99 / 2000-25 | 15.6 / 14.1 / 10.4 / 8.0 | 16.6 / 12.1 / 10.2 / 9.6 |
| Shuffled map (3 runs) | 0.68-1.48 | 0.79-1.42 |
| Past 5 years | 12.8 | 12.5 |
| Next 5 years (placebo) | 0.60 | 0.96 |
| Past 2 / next 2 years | 11.7 / 1.36 | not run |

What it says:

1. **Names travel by border far more strongly than laws:** ~12x against
   ~3.4x. A shuffled map gives ~1.
2. **The forward part dominates.** Neighbours in the next 5 years predict
   nothing (0.6-1.0), against ~1.8 for laws. Once each name's clock is taken
   out, the border effect for names is almost all "a neighbour went first".
   It is not "neighbours are alike".
3. **It has weakened, but it is still strong:** ~16x before 1950, ~8-10x
   since 2000. National media (radio, TV, then the internet) plausibly
   flattened it without erasing it. This matches Matt's hunch: waves change
   over time.
4. **The bridge to politics:** a choice made by millions of ordinary people
   still crosses state lines like a wave in the 2000s. A wave in mass political
   behaviour is plausible. We just need dated data fine enough to see it (the
   aliasing problem).

**Caveat on the placebo (applies to the laws too).** A state adopts only once.
So a neighbour that adopts in the NEXT k years is, by construction, one that
has not adopted yet. That pushes the future-neighbour odds ratio below 1
mechanically, so the placebo understates "alike".

- For laws, the ~1.8 is therefore a floor on "alike". The reading stands, and
  if anything the "alike" share is larger.
- For names, the 0.6-1.0 means little "alike" beyond that pull. The clean
  split needs past and future shares fitted together in one model. The fitter
  takes one covariate today, so that is a tested extension (open item 13).

Other caveats: one run per setting, no confidence intervals; national clock
per name, not per region; the take-off is defined on the share of births
listed (names under 5 are suppressed, which affects small states most).

### Fourth look, 2026-11-11: learning vs alike in ONE model (solar, laws, names)

`fit_hazard` (tested: a noise-free world returns odds ratios 4 and 2
exactly) fits several neighbour shares together.

Each row is a unit at risk in one period. Three shares go in, all counted
among its known neighbours:
- **past k:** share that took off in the k periods before. These could be
  learned from.
- **next k:** share that will take off in the k periods after. These cannot
  be learned from.
- **past any:** share that took off at any time before.

Rows are kept only up to the end minus k, so every "next k" window is fully
observed. Scratch EDA, one run each, no confidence intervals.

The table compares the shares fitted alone with past k and next k fitted
together:

| Wave | Clock | Past k alone | Next k alone | Joint: past k | Joint: next k | Past ÷ next (joint) |
|---|---|---|---|---|---|---|
| Solar, k = 1 yr | state | 6.26 | 2.30 | 9.70 | 3.97 | 2.4 |
| Solar, k = 2 yr | state | 5.12 | 1.29 | 8.03 | 2.69 | 3.0 |
| Laws, k = 2 yr | per law | 2.85 | 2.08 | 3.18 | 2.38 | 1.3 |
| Laws, k = 5 yr | per law | 3.01 | 1.80 | 3.60 | 2.30 | 1.6 |
| Laws first adopted before 1960, k = 5 | per law | 3.81 | 1.66 | 4.48 | 2.20 | 2.0 |
| Laws first adopted 1960+, k = 5 | per law | 2.69 | 1.87 | 3.24 | 2.35 | 1.4 |
| Names, k = 2 yr | per name | 11.78 | 1.37 | 14.16 | 2.19 | 6.5 |
| Names, k = 5 yr | per name | 13.19 | 0.60 | 16.68 | 1.62 | 10 |
| Names first before 1960, k = 5 | per name | 18.19 | 0.75 | 24.99 | 2.06 | 12 |
| Names first 1960+, k = 5 | per name | 10.59 | 0.51 | 12.29 | 1.34 | 9 |

(For solar, the national clock gives 30-57x past. That is the "everyone at
once" inflation the state clock exists to remove, so the state clock is the
one to read.)

What it says:

1. **The drag was real.** Fitted together, every "next" odds ratio rises
   (names at 5 years: 0.60 alone → 1.62 jointly), and every "past" rises
   too. The single-share placebos understated both parts.
2. **"Next" is also not pure "alike".** If I adopt now and my neighbour then
   copies me, my neighbour's future adoption is contagion running the other
   way. So the joint "next" is an upper bound on "alike". The learning part
   is at least past ÷ next.
3. **Learning wins in all three.**
   - Names: past beats next ~6-12x.
   - Solar: ~2.4-3x, after each state's own clock.
   - Laws: ~1.3-2x. Laws are the most "alike" and the least "learned".
4. **The fade over time, corrected.**
   - Laws: the learning ratio falls from ~2.0 (before 1960) to ~1.4 (1960+).
     The direction is the same as the second look, but the fade is smaller
     than the single-share placebo suggested (that read 2.4 → 1.3-1.7).
   - Names: ~12 → ~9. Weaker, still large.
5. **For the political run:** the forward-in-time signal survives the
   fairest test we have, in a market product, a law, and a mass cultural
   choice. The question for politics is now just whether dated data is fine
   enough to see it.

### Fifth look, 2026-11-11: error bars, hot-topic laws, and shared roads

**95% intervals for the joint model**, from resampling whole waves (laws,
names; 200 reps) or whole states (solar, 1,000 reps). Windows are 5 years for
laws and names, and 1 or 2 years for solar.

| Wave | Past | Next | Past ÷ next |
|---|---|---|---|
| Solar, 1 yr, state clock | 9.7 [4.6, 25] | 4.0 [2.1, 8.8] | 2.4 [1.1, 5.9] |
| Solar, 2 yr, state clock | 8.0 [3.2, 25] | 2.7 [1.5, 5.4] | 3.0 [1.4, 6.5] |
| Laws, all | 3.60 [3.17, 4.14] | 2.30 [2.05, 2.62] | 1.56 [1.42, 1.72] |
| Laws first adopted before 1960 | 4.48 [3.43, 5.99] | 2.20 [1.75, 2.94] | 2.03 [1.66, 2.37] |
| Laws first adopted 1960+ | 3.24 [2.73, 3.83] | 2.35 [2.00, 2.72] | 1.38 [1.24, 1.54] |
| Names, all | 16.7 [14.9, 18.2] | 1.62 [1.47, 1.80] | 10.3 [9.4, 11.2] |
| Names first before 1960 | 25.0 [21.1, 29.7] | 2.06 [1.75, 2.41] | 12.2 [10.4, 14.0] |
| Names first 1960+ | 12.3 [10.7, 13.8] | 1.34 [1.16, 1.52] | 9.2 [8.2, 10.2] |

- **Learning beats alike everywhere.** Every past ÷ next interval is above 1.
  Solar's lower bound at 1 year is close to 1, because there are only ~48
  states to resample.
- **The fade in laws is real:** the before-1960 and 1960+ intervals do not
  overlap. The fade in names only just clears that bar.
- **Within-state shuffle for solar** (borders kept, counties scrambled inside
  each state, 10 runs): ~1x (0.6-1.5), against 4-7x on the real map. The wave
  runs along real neighbours, not just shared state membership.

**Q (Matt): how does "catching" solar compare with "catching" a hot-topic
idea?** The first cut is the hot-topic laws in SPID (one run, no CIs):

| Group | Laws | Past | Next | Past ÷ next |
|---|---|---|---|---|
| Abortion laws | 33 | 4.88 | 3.85 | 1.27 |
| Culture-war laws (abortion, LGBT, drugs, guns, death penalty) | 50 | 4.04 | 3.42 | 1.18 |
| All other laws | 509 | 3.56 | 2.24 | 1.59 |

Hot-topic laws cluster by region more strongly than other laws, but mostly
because neighbours are alike, not because one learns from the other. This
fits the ballot-measure findings: a broad, even offset, and a stable county
trait. Working hypothesis: **beliefs sort; actions spread.** The dated acts
that express a belief should travel like a wave: registering, giving,
volunteering, yard signs. The test is FEC donations to abortion-rights
committees from Dobbs (2022-06-24) to the Kansas vote (2022-08-02).

**Q (Matt): if solar moves St. Louis → I-70 → west, does ANY idea move the
same way?** In other words, do the roads belong to the land, or to the idea?

Test: for each pair of bordering states, the share of waves in which A went
before B. Then check whether that direction agrees across families of ideas.
Spearman correlations, 107 border pairs:

| Comparison | Agreement |
|---|---|
| Names vs names (split half: the ceiling) | 0.98 |
| Laws vs laws (split half) | 0.81 |
| Laws vs names, all years | 0.33 |
| Laws vs names, since 1960 | 0.15 |
| Names before 1960 vs after | 0.60 |
| Laws before 1960 vs after | 0.49 |
| Law topics, within one topic (split half; 6 topics with 30+ laws) | 0.25-0.52 |
| Law topics, between topics | mean 0.30 (-0.06 to 0.46) |

Who goes early differs too:
- Names: OR, WA, UT, KS, CO, ID.
- Laws: CA, MN, CT, WA, OR, IL.
- Earliness rank, laws vs names: 0.36.

What it says:

1. **Each kind of idea has very steady roads of its own.**
2. **A weak road is shared by all ideas (~0.3), and it has weakened since
   1960.**
3. **Similar ideas share roads modestly more than different ones.**
4. **Roads drift over time**, even within one family.

So solar proves the method can see a wave, but it is not the map for
politics. The best guide to how a political idea will travel is how recent
ideas of the same kind travelled.

Limits:
- This is at state level only. County roads (I-70, commuting, media
  markets) may be shared more, being physical.
- Solar could not take part. Only ~25 states have enough timed counties, and
  its take-off is relative to each county's own final count, so it is not
  comparable at state level.
- The county-level version is the next test: in Missouri, lay solar
  alongside FEC donations by ZIP.

### Sixth look, 2026-11-11: can we predict where a wave goes next?

**Q (Matt): for MPSA we need to show this can be used by an organization.**
An organization does not ask "is there a wave?". It asks: "it has caught
here and here, so where next, and where should we send people?"

**Set-up: out-of-sample.**
- Train on waves that began before 1980; test on waves that began in 1980
  or later. Nothing about a test wave is used except what was known that
  year.
- Each test wave, each year: rank the states still waiting.
- **Score 1 (pairs):** pick one waiting state that adopted that year and one
  that did not. How often is the adopter ranked higher? 50% is a coin flip.
  95% intervals come from resampling test waves.
- **Score 2 (send people to 5 states):** of the top 5 waiting states, the
  share that adopt within the next 3 years, against all waiting states
  (counted only in years the wave is moving).

Contenders:
- **Usual leaders:** how early each state went in the training waves.
- **Biggest first:** births 1980-2025, as a stand-in for population.
- **The wave:** the share of neighbours already adopted.
- **Combined:** wave + usual leaders, weighted by a hazard model fitted on
  the training waves only.

| Ranking by | Names: pairs | Names: top 5 hit | Laws: pairs | Laws: top 5 hit |
|---|---|---|---|---|
| Coin flip / random | 50.0% | 35.8% | 50.0% | 20.1% |
| Biggest first | 50.0% [48.6, 51.6] | 43.3% | 52.2% [51.2, 53.3] | 24.0% |
| Usual leaders | 60.3% [59.2, 61.6] | 53.9% | 54.0% [52.6, 55.3] | 23.9% |
| The wave | 64.0% [63.4, 64.7] | 54.7% | 54.6% [53.8, 55.3] | **27.3%** |
| Wave + usual leaders | **66.8%** [65.9, 67.8] | **56.9%** | **56.3%** [55.0, 57.6] | 26.3% |
| Adding size | 67.0% | | 56.4% | |

What it says:

1. **Waves can be forecast, out of sample.**
   - Names: picking 5 states with the model, 57% adopt within 3 years,
     against 36% at random (1.6x).
   - Laws: 27% against 20% (1.35x).
2. **The wave adds to "the usual leaders"**: +6.5 points for names [+5.8,
   +7.2] and +2.3 points for laws [+1.8, +2.8]. Knowing where the idea
   already is beats knowing only who usually goes first.
3. **Size barely matters**, once the wave and the usual leaders are known.
4. **Laws are much harder to call than names**: about 56% against 67%. That
   matches the earlier finding that laws travel less by learning and more by
   "alike". An idea that is mostly regional character is harder to call from
   its neighbours. How much a topic's wave can be trusted is itself something
   to measure, and that measurement is the specialist's job.

Caveats:
- Scratch EDA; the pick-5 score is one run.
- "Usual leaders" uses the same family's training waves (names for names,
  laws for laws), which is the "each idea has its own roads" lesson applied.
- A single 1980 split.
- When this goes on the public page, the scoring moves into the tested
  library.

### Political twins, and the bridge back to politics

Each alternative explanation has a political twin: state programmes ↔ state
parties and ballot campaigns; installers ↔ field offices and canvassers; TV
markets ↔ ad buys; data providers ↔ reporting changes. Panels have a twin too:
**yard signs and bumper stickers**, a visible sign that a neighbour adopted an
idea.

Elections have the most extreme pipeline there is: every decision is
"installed" on the same day. So even a perfect person-to-person wave in
opinions is recorded as simultaneous. That is a second reason the data says
"the whole state moves at once", on top of the 4-year gap.

Candidate dated political "adoptions", to run through the solar pipeline:

- **FEC individual contributions:** a date and a ZIP per donation, free bulk
  data. Conduit reporting (ActBlue, WinRed) may itemize small donations; to be
  verified.
- **Monthly party registration** by county, in states that register by party.
- **GDELT daily news** at county level, for the information side (planned for
  Dec 13).

### Side questions from the same sessions

- **GDELT is not statewide only.** An earlier claim of ours was wrong. Events
  carry ADM1 and ADM2 (US county) codes plus latitude and longitude. Raw files
  are free every 15 minutes. BigQuery has a free monthly allowance (about 1 TB
  per month, from general knowledge, not checked) and costs about $6.25/TB
  after that. The GKG is the expensive part (2015 alone is over 2.5 TB). A
  cost and density pilot runs early in the Dec 13 work.
- **Speed of work.** Downloads and ingests take a day, not a week. Schedules
  were compressed accordingly (see `docs/TODO_2027.md`).

### Open, in rough order (Dec 6 solar notebook)

1. Placebo shuffle within states: DONE 2026-11-11 (~1x against 4-7x real; fifth look)
2. Future-neighbour placebo: DONE 2026-11-11 (fourth look; past ÷ next ~2.4-3x on the state clock). Next: within-state shuffle, bootstrap
3. Provider and utility baselines
4. Delay-pattern test (which lag predicts best)
5. Drop leases / new construction; self-installs
6. Salesperson tests: arrival event study, pre-arrival trend, selling plus seeing, leased vs owned
7. Neighbours vs lookalikes
8. Roads: borders vs commuting vs migration
9. The clock test: rerun the hazard model with solar sampled every 4 years
10. ZIP-level panel
11. First political run: FEC donations through the same pipeline
12. Do waves change over time? "Who goes early" maps correlated across eras: baby names / SPID first (many waves), then RCMS religion and newspapers (county level)
13. Joint past + future neighbour model: DONE 2026-11-11 (`fit_hazard`, fourth look). The window shares are computed in scratch code; promote them into `at_risk_table` (tested) when the Dec 6 notebook needs them
14. Bootstrap intervals by wave (law, name) for the era tables: DONE 2026-11-11 (fifth look)
15. County-level shared roads in Missouri: solar vs FEC donations by ZIP (does I-70 carry both?)
16. Hot-topic actions vs beliefs: FEC abortion-rights giving, Dobbs to the Kansas vote, through the joint model
17. Wave prediction test (Nov 25 TODO): DONE 2026-11-11 (sixth look). Next: other split years; move the scoring into the tested library for the public page
