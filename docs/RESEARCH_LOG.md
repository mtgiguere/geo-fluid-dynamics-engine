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

1. Placebo shuffle within states (is 3.9-7.4x more than chance?)
2. Future-neighbour placebo
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
