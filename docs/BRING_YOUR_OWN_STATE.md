# Bring Your Own State (and Your Own Issue)

*A plain-language guide to what it actually takes. No computer skills assumed.*

You've seen the Missouri demo: a map that finds the counties where people
vote differently on an **issue** than their **party label** predicts — the
places where minds are actually reachable. Now suppose you live in Georgia,
Arizona, or Idaho, and your issue is something else entirely — say, the
death penalty. What has to happen?

Short version: **five ingredients, and only one of them needs a programmer.**

---

## Ingredient 1: Your state must have actually voted on the issue

This tool doesn't read minds and it doesn't use polls. It reads **real
ballots** — those questions at the bottom of your ballot ("Amendment 3,"
"Proposition A") where you vote on an *issue* directly, with no candidate
attached. That direct vote is the only place a county's true position shows
up separated from its party habit.

So the first step costs nothing and takes ten minutes: check whether your
state has voted on your issue. Ballotpedia (a free encyclopedia of every
ballot measure) is the place to look, and this project keeps a research
catalog of 271 measures across five topics as a starting point.

**The death penalty, checked for real:** there IS ballot history —

- **Nebraska 2016**: the legislature *abolished* the death penalty; citizens
  petitioned it onto the ballot, and 61% voted to bring it back.
- **California 2016**: two competing measures on the *same day* — one to
  repeal the death penalty (failed), one to speed up executions (passed).
- **Oklahoma 2016**: 66% voted to write the death penalty into the state
  constitution.

**The catch, checked for real:** only about half the states let citizens put
questions on the ballot. **Arizona and Idaho do. Georgia does not** — Georgia
only votes on questions its legislature chooses to refer, and it has never
referred the death penalty. So the Arizonan can't map death-penalty
sentiment *in Arizona* either (no Arizona vote exists), but Oklahoma and
Nebraska — similar red-leaning states — offer the nearest real evidence. The
Georgian's honest answer is harder: for that issue, in that state, the
direct-vote signal simply doesn't exist yet. **No vote, no signal — the tool
refuses to guess, and that refusal is a feature.** A tool that "estimated"
Georgia's county-level death-penalty map from demographics would be exactly
the kind of confident fiction this project was built to replace.

## Ingredient 2: The county-by-county results file

Every state's election office (usually the Secretary of State) publishes
official results broken down by county. Finding that file is citizen work,
not programmer work: go to the state election website, find the election,
download whatever they offer. PDF is fine — Missouri only offered PDFs, and
they turned out to be the cleanest data any state has given this project.

Time: an afternoon, most of it spent navigating a government website.

## Ingredient 3: The party baseline (already done — for every county in America)

To measure "this county votes differently on the issue than its party label
predicts," you need the party label part. That's presidential election
results by county, and the project already carries them — every county,
every election, 2000–2024 (and back to 1868 for the historical work). If
your state has counties, this ingredient is already on the shelf.

## Ingredient 4: The translator (the one technical step)

Here's the honest part: every state formats its results file differently.
Kansas publishes a spreadsheet with quirks, Kentucky a text file, Ohio a
workbook with the header on the third row, Missouri a PDF. Someone technical
has to write a small "translator" (we call it a loader) that reads your
state's format into the standard form the engine understands.

Two things a lay person should know about this step:

- **It's days, not months.** The Missouri translator — including the
  discovery that Kansas City reports separately from its four counties —
  was built and verified in a day.
- **It has a built-in lie detector.** Every translator must reproduce the
  state's own certified statewide totals exactly before its output is used
  for anything. Missouri's reproduced all eight measures to the decimal.
  If the translation is off by even one county, it fails loudly and no map
  gets made. You don't have to trust the programmer; you can check the
  one number yourself.

## Ingredient 5: A human decision — which side is which

The engine is politics-agnostic; it needs to be told which side of your
measure is which, and this is trickier than it sounds. In Kansas 2022, voting
**NO** was the pro-choice vote. In Ohio 2023, voting **YES** was. And the
death penalty is the trap in its purest form: in Nebraska 2016, the ballot
asked whether to **repeal the repeal** — a voter *against* the death penalty
had to vote "Retain." Get this one human judgment wrong and every map is
perfectly, silently backwards. It's the one step that demands someone who
understands the measure, not the software.

---

## Then what do you get?

Once those five ingredients exist, the rest is automatic — the same products
you saw in the Missouri demo:

- **The dissonance map**: every county colored by how far its issue vote ran
  ahead of (or behind) its party label. The surprising counties — red places
  well ahead of their label — are the **False Bastions**: written off by the
  party map, reachable in reality.
- **The itinerary**: given a home base, a ranked plan — which counties are
  persuadable TARGETs, which are BASE (turn out, don't persuade), which are
  HARD (skip), with drive distances.

And if your state voted on *several* issues (like Missouri's eight), the
engine can pool them: Missouri showed that a county that defies its label on
one issue tends to defy it on others (a wage measure predicts an abortion
measure), so every past vote sharpens the picture for the next one.

## What it will never tell you

- **Individuals.** Everything is county-level. "This county is reachable" is
  a statement about a place, never about your neighbor.
- **Issues nobody voted on.** No measure, no signal (see Georgia, above).
- **The future, unaccountably.** The project's rule for predictions is that
  they get written down *in public, before* the election, and scored after —
  that experiment is running right now for Missouri's November 2026 ballot.

## The whole thing on one napkin

| Step | Who | Effort |
|---|---|---|
| 1. Has your state voted on your issue? | You, on Ballotpedia | minutes |
| 2. Download the county results file | You, on your state's election site | an afternoon |
| 3. Party baseline | Already on the shelf | none |
| 4. The translator + its lie detector | A programmer | days |
| 5. Which side is which | A human who understands the measure | one careful decision |
| The map and the itinerary | The engine | automatic |
