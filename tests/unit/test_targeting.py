"""Tests for the targeting engine — the prescriptive layer (spec Stage 4).

Every other layer answers "what is true?" — here are the votes, here is the
dissonance. This one answers "what should I DO?": given a county-level issue
signal and where the organizer lives, produce a ranked, classified itinerary
of where to campaign and where not to bother.

The decision rests on two axes per county:
  * partisan_share  — how aligned it already is with your side (2020 Dem 2-party)
  * dissonance      — progressive_share - partisan_share: how much MORE it voted
                      your way on the issue than its partisanship predicts

and sorts counties into three plain-language buckets:
  * BASE   — already yours (high partisan_share): turn them out, don't persuade
  * TARGET — red but overperformed on the issue (high dissonance): the
             persuadable "False Bastion" — your best ground
  * HARD   — red and voted its partisan lean (low dissonance): skip for now

The engine stays politics-agnostic, exactly like the loaders: it speaks in
"progressive_share" and never hardcodes an issue label. Orientation already
happened upstream (the contest panel / overlay); presentation adds the flavor.
"""

import pandas as pd

from geofluid.targeting import (
    build_itinerary,
    build_playbook,
    history_buckets,
    playbook_budget_split,
)


def _counties(rows: list[dict[str, object]]) -> pd.DataFrame:
    """A county issue frame: fips, name, progressive_share, partisan_share."""
    return pd.DataFrame(rows)


def test_red_county_with_high_dissonance_is_a_target() -> None:
    """The core move. A county that leans Republican (partisan_share 0.30, well
    below the 0.45 base line) but voted 0.55 your way on the issue has
    dissonance 0.55 - 0.30 = 0.25, far above the 0.15 target line. That is a
    persuadable False Bastion -> category 'target'. (Derived before the
    assertion.) Home is somewhere else; distances are injected."""
    counties = _counties(
        [
            {"fips": "20121", "name": "Miami", "progressive_share": 0.55, "partisan_share": 0.30},
        ]
    )

    itinerary = build_itinerary(counties, distances_mi={"20121": 39.0}, home_fips="20209")

    row = itinerary[itinerary["fips"] == "20121"].iloc[0]
    assert row["category"] == "target"
    assert abs(row["dissonance"] - 0.25) < 1e-12
    assert row["distance_mi"] == 39.0


def test_already_aligned_county_is_base_even_with_high_dissonance() -> None:
    """BASE takes precedence over TARGET. Douglas County (Lawrence/KU) is
    partisan_share 0.70 — well above the 0.45 base line — and voted 0.82 your
    way, so its dissonance is 0.12. Even if dissonance had cleared the target
    line, an already-Democratic county is your BASE: you turn it out, you don't
    spend scarce persuasion effort there. Classifying on partisanship FIRST is
    what encodes 'don't preach to the choir'."""
    counties = _counties(
        [
            {"fips": "20045", "name": "Douglas", "progressive_share": 0.82, "partisan_share": 0.70},
        ]
    )

    itinerary = build_itinerary(counties, distances_mi={"20045": 31.0}, home_fips="20209")

    assert itinerary[itinerary["fips"] == "20045"].iloc[0]["category"] == "base"


def test_red_county_voting_its_lean_is_hard_ground() -> None:
    """A county that leans Republican (partisan_share 0.25, below the base line)
    AND voted only 0.32 your way has dissonance 0.07 — below the 0.15 target
    line. It did not overperform its partisanship, so there is no persuasion
    foothold yet -> 'hard'. This is the county the tool tells you to SKIP, which
    is half its value: not wasting a volunteer's weekend on unmovable ground."""
    counties = _counties(
        [
            {"fips": "20055", "name": "Greeley", "progressive_share": 0.32, "partisan_share": 0.25},
        ]
    )

    itinerary = build_itinerary(counties, distances_mi={"20055": 300.0}, home_fips="20209")

    assert itinerary[itinerary["fips"] == "20055"].iloc[0]["category"] == "hard"


def test_targets_lead_ranked_by_dissonance_and_home_is_excluded() -> None:
    """The itinerary is an ordered to-do list, not a set. Targets come FIRST,
    ranked by dissonance descending (most persuadable ground at the top of the
    weekend), ahead of base/hard. And the organizer's own county is dropped —
    you don't drive to where you already are. Here Osage (diss 0.29) must
    outrank Miami (diss 0.23) at the top, the home county Wyandotte is absent,
    and a base county sorts behind both targets."""
    counties = _counties(
        [
            {
                "fips": "20209",
                "name": "Wyandotte",
                "progressive_share": 0.74,
                "partisan_share": 0.68,
            },
            {"fips": "20121", "name": "Miami", "progressive_share": 0.53, "partisan_share": 0.30},
            {"fips": "20139", "name": "Osage", "progressive_share": 0.56, "partisan_share": 0.27},
            {"fips": "20045", "name": "Douglas", "progressive_share": 0.82, "partisan_share": 0.70},
        ]
    )
    distances = {"20209": 0.0, "20121": 39.0, "20139": 64.0, "20045": 31.0}

    itinerary = build_itinerary(counties, distances_mi=distances, home_fips="20209")

    assert "20209" not in set(itinerary["fips"])  # home dropped
    assert list(itinerary["fips"])[:2] == ["20139", "20121"]  # Osage then Miami
    assert list(itinerary["category"])[:2] == ["target", "target"]
    assert itinerary.iloc[-1]["category"] == "base"  # Douglas sorts last


def test_county_with_no_partisan_baseline_is_excluded_not_misclassified() -> None:
    """A county with no partisan baseline (NaN partisan_share — e.g. a returns
    gap) has no defined dissonance, so it cannot be classified. It must be
    DROPPED from the itinerary, never silently bucketed: NaN >= threshold is
    False in pandas, so without a guard it would masquerade as 'hard' ground and
    a volunteer could be sent to unrankable terrain. Absence is explicit here,
    exactly as it is in swing/LISA/dissonance. Miami (valid) stays; Phantom
    (NaN) goes."""
    counties = _counties(
        [
            {"fips": "20121", "name": "Miami", "progressive_share": 0.53, "partisan_share": 0.30},
            {
                "fips": "20999",
                "name": "Phantom",
                "progressive_share": 0.40,
                "partisan_share": float("nan"),
            },
        ]
    )

    itinerary = build_itinerary(
        counties, distances_mi={"20121": 39.0, "20999": 50.0}, home_fips="20209"
    )

    assert list(itinerary["fips"]) == ["20121"]


# --- history_buckets: the bucket a county's OWN record implies ---------------
#
# build_itinerary classifies from one issue signal plus partisanship. The
# question a buyer asks is different: "how do you KNOW St. Louis County is
# turnout ground?" The answer has to be the county's record across every
# statewide measure we hold - how far it runs ahead of or behind the STATE,
# how consistently, and whether the gap shrinks when a smaller (midterm)
# crowd shows up. history_buckets turns that record plus a stated statewide
# level into a bucket, so the classification rests on certified votes and
# one explicit assumption rather than on our own forecast.


def _shares() -> tuple[pd.DataFrame, "pd.Series[float]"]:
    """Two counties x two measures, progressive shares, plus the statewide
    result of each measure. County A runs +0.10 over the state on both;
    county B runs -0.05 on both."""
    shares = pd.DataFrame(
        {"m1": [0.60, 0.45], "m2": [0.70, 0.55]},
        index=pd.Index(["A", "B"], name="fips"),
    )
    statewide = pd.Series({"m1": 0.50, "m2": 0.60})
    return shares, statewide


def test_history_mean_gap_and_expected_share_at_stated_level() -> None:
    """Derivation: A's gaps are 0.60-0.50 = +0.10 and 0.70-0.60 = +0.10, mean
    +0.10; B's are 0.45-0.50 = -0.05 and 0.55-0.60 = -0.05, mean -0.05. At a
    stated statewide level of 0.55 the expected share is level + mean gap:
    A 0.65, B 0.50."""
    shares, statewide = _shares()

    out = history_buckets(shares, statewide, level=0.55)

    assert abs(float(out["mean_gap"].loc["A"]) - 0.10) < 1e-12
    assert abs(float(out["mean_gap"].loc["B"]) - (-0.05)) < 1e-12
    assert abs(float(out["expected_share"].loc["A"]) - 0.65) < 1e-12
    assert abs(float(out["expected_share"].loc["B"]) - 0.50) < 1e-12


def test_history_bucket_from_expected_share_and_competitive_band() -> None:
    """With a competitive band of 0.08 around 0.50: expected 0.65 is above
    0.58 -> 'turnout' (already ahead: the job is showing up); 0.50 is inside
    the band -> 'persuade' (the argument decides it); a county C running
    -0.20 on both measures expects 0.55 - 0.20 = 0.35, below 0.42 -> 'hard'.
    Derived before the assertion."""
    shares, statewide = _shares()
    shares.loc["C"] = [0.30, 0.40]

    out = history_buckets(shares, statewide, level=0.55, competitive_band=0.08)

    assert out.loc["A", "bucket"] == "turnout"
    assert out.loc["B", "bucket"] == "persuade"
    assert out.loc["C", "bucket"] == "hard"


def test_history_consistency_is_share_of_measures_on_the_mean_gap_side() -> None:
    """A county that is +0.10 on one measure and -0.02 on the other has mean
    gap +0.04 but was on the plus side only 1 of 2 times -> consistency 0.5.
    County A (+0.10, +0.10) -> 1.0. gap_sd is the plain sample standard
    deviation of the gaps: A 0.0; D sd of (+0.10, -0.02) = 0.0849 (ddof=1).
    A mean gap earns trust only with high consistency and low sd."""
    shares, statewide = _shares()
    shares.loc["D"] = [0.60, 0.58]  # gaps +0.10 and -0.02

    out = history_buckets(shares, statewide, level=0.55)

    assert float(out["consistency"].loc["A"]) == 1.0
    assert float(out["consistency"].loc["D"]) == 0.5
    assert float(out["gap_sd"].loc["A"]) == 0.0
    assert abs(float(out["gap_sd"].loc["D"]) - 0.08485281374238571) < 1e-12


def test_history_midterm_penalty_from_electorate_types() -> None:
    """The turnout tell: does the county's edge shrink when the smaller
    midterm crowd shows up? With m1 a midterm measure and m2 a presidential
    one, county E (shares 0.53, 0.72) has gaps +0.03 (midterm) and +0.12
    (presidential): midterm_gap 0.03, presidential_gap 0.12, and
    midterm_penalty = presidential - midterm = +0.09 - its presidential-year
    voters are the ones who lean its way and they stay home in midterms.
    County A (+0.10 both) has penalty 0.0."""
    shares, statewide = _shares()
    shares.loc["E"] = [0.53, 0.72]
    electorate = {"m1": "midterm", "m2": "presidential"}

    out = history_buckets(shares, statewide, level=0.55, electorate=electorate)

    assert abs(float(out["midterm_gap"].loc["E"]) - 0.03) < 1e-12
    assert abs(float(out["presidential_gap"].loc["E"]) - 0.12) < 1e-12
    assert abs(float(out["midterm_penalty"].loc["E"]) - 0.09) < 1e-12
    assert abs(float(out["midterm_penalty"].loc["A"])) < 1e-12


# --- build_playbook: the (measure, side) -> plan generator -------------------
#
# The protocol (MEASUREMENT_DESIGN.md s7) wants playbooks parameterized by
# goal, never partisan: the SAME record produces the plan for whichever side
# asks. The record comes from history_buckets (fips x expected_share,
# mean_gap, midterm_penalty); the playbook orients it to the requested side,
# re-buckets, prices each county in votes, and orders the work.


def _record() -> tuple[pd.DataFrame, "pd.Series[float]"]:
    """Three counties as history_buckets would describe them for the
    progressive side, plus expected votes cast: A is comfortably ahead
    (0.65, habitual gap +0.10, a midterm penalty of 0.04), B is a toss-up
    (0.50), C is far behind (0.35, gap -0.20)."""
    record = pd.DataFrame(
        {
            "expected_share": [0.65, 0.50, 0.35],
            "mean_gap": [0.10, 0.00, -0.20],
            "midterm_penalty": [0.04, 0.00, 0.01],
        },
        index=pd.Index(["A", "B", "C"], name="fips"),
    )
    votes = pd.Series({"A": 100_000.0, "B": 50_000.0, "C": 20_000.0}, name="expected_votes")
    return record, votes


def test_playbook_orients_to_the_side_that_asks() -> None:
    """For the progressive side the record stands: A 0.65 -> turnout, B 0.50
    -> persuade, C 0.35 -> hard (band 0.08). For the other side every share
    is 1 - share and the buckets mirror: C becomes 0.65 -> turnout, A
    becomes 0.35 -> hard, B stays persuade. Same record, two plans."""
    record, votes = _record()

    prog = build_playbook(record, votes, side="progressive").set_index("fips")
    cons = build_playbook(record, votes, side="conservative").set_index("fips")

    assert list(prog.loc[["A", "B", "C"], "bucket"]) == ["turnout", "persuade", "hard"]
    assert list(cons.loc[["A", "B", "C"], "bucket"]) == ["hard", "persuade", "turnout"]
    assert abs(float(cons["expected_share"].loc["A"]) - 0.35) < 1e-12
    assert abs(float(cons["expected_share"].loc["C"]) - 0.65) < 1e-12


def test_playbook_prices_each_county_in_votes() -> None:
    """A (100,000 expected votes) for the progressive side: one point of
    movement = 1,000 votes; predicted margin (0.65 - 0.50) x 100,000 =
    +15,000; headroom = habitual gap +0.10 x 100,000 = +10,000 votes the
    record says already lean this way beyond partisanship; votes at risk in
    a midterm = penalty 0.04 x 100,000 = 4,000 supporters who skip midterms.
    For the conservative side C's numbers mirror: share 0.65 -> margin
    +3,000 on 20,000 votes; headroom -(-0.20) x 20,000 = +4,000; the midterm
    penalty flips sign to -0.01, and votes at risk floor at 0 (their crowd
    GROWS in midterms)."""
    record, votes = _record()

    prog = build_playbook(record, votes, side="progressive").set_index("fips")
    cons = build_playbook(record, votes, side="conservative").set_index("fips")

    assert abs(float(prog["votes_per_point"].loc["A"]) - 1_000.0) < 1e-6
    assert abs(float(prog["margin_votes"].loc["A"]) - 15_000.0) < 1e-6
    assert abs(float(prog["headroom_votes"].loc["A"]) - 10_000.0) < 1e-6
    assert abs(float(prog["votes_at_risk_midterm"].loc["A"]) - 4_000.0) < 1e-6
    assert abs(float(cons["margin_votes"].loc["C"]) - 3_000.0) < 1e-6
    assert abs(float(cons["headroom_votes"].loc["C"]) - 4_000.0) < 1e-6
    assert abs(float(cons["votes_at_risk_midterm"].loc["C"]) - 0.0) < 1e-6


def test_playbook_orders_persuade_by_price_then_turnout_by_risk_then_hard() -> None:
    """The plan is a ranked list. Persuade counties come first, biggest
    votes_per_point first (a point is worth more there); turnout counties
    next, most votes_at_risk_midterm first (the largest pile of supporters
    who might stay home); hard ground last. With a fourth toss-up county D
    (0.50, 80,000 votes) the order is D (800/pt) > B (500/pt) > A (turnout)
    > C (hard), and `priority` numbers them 1..4."""
    record, votes = _record()
    record.loc["D"] = [0.50, 0.00, 0.00]
    votes.loc["D"] = 80_000.0

    plan = build_playbook(record, votes, side="progressive")

    assert list(plan["fips"]) == ["D", "B", "A", "C"]
    assert list(plan["priority"]) == [1, 2, 3, 4]


def test_budget_split_weighs_reachable_votes_against_votes_at_risk() -> None:
    """The persuasion-vs-turnout split, in votes. Persuasion pool = the votes
    within reach in persuade counties: expected_votes x the competitive band
    (moving a toss-up county by the band's width): B 50,000 x 0.08 = 4,000
    and D 80,000 x 0.08 = 6,400 -> 10,400. Turnout pool = supporters at risk
    of skipping the midterm in turnout counties: A 4,000. Turnout share of
    the budget = 4,000 / 14,400 = 0.2778; persuasion gets the rest."""
    record, votes = _record()
    record.loc["D"] = [0.50, 0.00, 0.00]
    votes.loc["D"] = 80_000.0
    plan = build_playbook(record, votes, side="progressive")

    split = playbook_budget_split(plan, competitive_band=0.08)

    assert abs(float(split["persuasion_pool_votes"]) - 10_400.0) < 1e-6
    assert abs(float(split["turnout_pool_votes"]) - 4_000.0) < 1e-6
    assert abs(float(split["turnout_share"]) - 4_000 / 14_400) < 1e-12
    assert abs(float(split["persuasion_share"]) - 10_400 / 14_400) < 1e-12
