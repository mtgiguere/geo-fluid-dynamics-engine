"""The targeting engine — the prescriptive layer (spec Stage 4).

Turns a county-level issue signal into an organizer's itinerary: where to
campaign, in what order, and where not to bother. This is the leap from a map
that shows *what is* to a tool that says *what to do*.

Each county is scored on two axes and sorted into a plain-language bucket:

  * partisan_share — how aligned it already is with your side (the presidential
    Democratic two-party share is the usual baseline)
  * dissonance = progressive_share - partisan_share — how much MORE it voted
    your way on the issue than its partisanship predicts

  BASE   — already yours (partisan_share at/above the base line): turn them out,
           don't spend persuasion effort here
  TARGET — red but overperformed on the issue (dissonance at/above the target
           line): the persuadable "False Bastion", your best ground
  HARD   — red and voted close to its partisan lean: skip for now

The engine is politics-agnostic, like the ingest loaders: it speaks only in
progressive_share / dissonance and never hardcodes an issue or a side.
Orientation happened upstream; plain-language flavor belongs to presentation.
"""

from collections.abc import Mapping

import pandas as pd

# Itinerary order: persuadable targets first, then your base, then hard ground.
_CATEGORY_RANK = {"target": 0, "base": 1, "hard": 2}
# Playbook order: persuade (the argument decides it), turnout (show up), hard.
_PLAYBOOK_RANK = {"persuade": 0, "turnout": 1, "hard": 2}


def build_itinerary(
    counties: pd.DataFrame,
    distances_mi: Mapping[str, float],
    home_fips: str,
    *,
    base_partisan_min: float = 0.45,
    target_dissonance_min: float = 0.15,
) -> pd.DataFrame:
    """Rank and classify counties into a campaign itinerary.

    `counties` carries fips, name, progressive_share, partisan_share.
    `distances_mi` maps fips to miles from the organizer's home county.
    Returns the itinerary with a category, the dissonance, and the distance.
    """
    out = counties[counties["fips"] != home_fips].copy()  # you don't drive to yourself
    out["dissonance"] = out["progressive_share"] - out["partisan_share"]
    out["distance_mi"] = out["fips"].map(dict(distances_mi))

    # A county with no defined dissonance (missing issue or partisan baseline)
    # cannot be classified — drop it explicitly. Without this, NaN >= threshold
    # is False in pandas, so it would silently masquerade as 'hard' ground and a
    # volunteer could be routed to unrankable terrain. Absence is explicit.
    out = out[out["dissonance"].notna()]

    # Classify on partisanship FIRST: an already-aligned county is your BASE
    # (turn out, don't persuade) whatever its dissonance — "don't preach to the
    # choir". Only among the not-yet-yours counties does dissonance separate the
    # persuadable TARGETs from the HARD ground.
    is_base = out["partisan_share"] >= base_partisan_min
    is_target = ~is_base & (out["dissonance"] >= target_dissonance_min)
    out["category"] = "hard"
    out.loc[is_base, "category"] = "base"
    out.loc[is_target, "category"] = "target"

    # An itinerary is ordered: targets first (best persuasion leverage at the top
    # of the weekend), ranked by dissonance; base and hard follow. _CATEGORY_RANK
    # orders the buckets, dissonance breaks ties within.
    out["_rank"] = out["category"].map(_CATEGORY_RANK)
    return out.sort_values(
        ["_rank", "dissonance"], ascending=[True, False], ignore_index=True
    ).drop(columns="_rank")


def history_buckets(
    shares: pd.DataFrame,
    statewide: "pd.Series[float]",
    level: float,
    *,
    competitive_band: float = 0.08,
    electorate: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """What a county's OWN voting record implies about it, given one stated
    statewide level.

    `shares` is fips x measure (progressive share per county per past
    measure); `statewide` is the statewide progressive share of each measure.
    The gap is county minus state, measure by measure: the county's habitual
    distance from Missouri (or any state) as a whole. `expected_share` is the
    stated `level` plus the county's mean gap - "if the state lands at 55,
    this county's record says it lands here". Everything except `level` is a
    certified vote; `level` is the one explicit assumption.
    """
    gaps = shares.sub(statewide.reindex(shares.columns), axis=1)
    out = pd.DataFrame(index=shares.index)
    out["mean_gap"] = gaps.mean(axis=1)
    # Trust in the mean gap: how often the county was on the same side of the
    # state as its average says (1.0 = every time), and how spread out the
    # gaps are. A +0.04 built from +0.10 and -0.02 is not "ahead".
    same_side = gaps.gt(0).eq(out["mean_gap"].gt(0), axis=0)
    out["consistency"] = same_side.mean(axis=1)
    out["gap_sd"] = gaps.std(axis=1, ddof=1)
    out["expected_share"] = level + out["mean_gap"]

    # The turnout tell. If `electorate` labels each measure "midterm" or
    # "presidential", split the gap by crowd: a county whose edge is bigger
    # in presidential years than in midterms has supporters who show up only
    # for the big one - its problem is turnout, and midterm_penalty (the
    # presidential gap minus the midterm gap) is the size of that problem.
    if electorate is not None:
        kind = pd.Series(dict(electorate)).reindex(shares.columns)
        for name in ("midterm", "presidential"):
            cols = list(kind.index[kind == name])
            out[f"{name}_gap"] = gaps[cols].mean(axis=1) if cols else float("nan")
        out["midterm_penalty"] = out["presidential_gap"] - out["midterm_gap"]

    # The bucket is the expected share read against 0.50 with a band of
    # genuine competitiveness around it: clearly ahead -> turnout (the job
    # is showing up), inside the band -> persuade (the argument decides it),
    # clearly behind -> hard. The band is the caller's stated tolerance.
    out["bucket"] = "persuade"
    out.loc[out["expected_share"] >= 0.5 + competitive_band, "bucket"] = "turnout"
    out.loc[out["expected_share"] <= 0.5 - competitive_band, "bucket"] = "hard"
    return out


def build_playbook(
    record: pd.DataFrame,
    expected_votes: "pd.Series[float]",
    side: str,
    *,
    competitive_band: float = 0.08,
) -> pd.DataFrame:
    """The plan for one (measure, side), from the county record alone.

    `record` is history_buckets' output for the PROGRESSIVE side of the
    measure (fips x expected_share, mean_gap, midterm_penalty); `side` is
    "progressive" or "conservative". The generator never takes a position:
    it orients the record to whoever asks (the other side's expected share
    is 1 - share, its gap is the negative) and re-buckets with the same
    competitive band, so the two plans are exact mirrors of one record.
    """
    if side not in ("progressive", "conservative"):
        raise ValueError(f"side must be 'progressive' or 'conservative', got {side!r}")
    flip = side == "conservative"
    out = pd.DataFrame(index=record.index)
    out["expected_share"] = 1 - record["expected_share"] if flip else record["expected_share"]
    out["mean_gap"] = -record["mean_gap"] if flip else record["mean_gap"]
    penalty = -record["midterm_penalty"] if flip else record["midterm_penalty"]

    # Price the county in votes, because a budget is spent in votes, not
    # shares: what one point of movement buys, the predicted margin, the
    # votes the record says already lean this way beyond partisanship, and
    # the supporters who skip midterms (a penalty below zero means this
    # side's crowd grows in midterms - nothing at risk).
    votes = expected_votes.reindex(record.index)
    out["expected_votes"] = votes
    out["votes_per_point"] = votes / 100
    out["margin_votes"] = (out["expected_share"] - 0.5) * votes
    out["headroom_votes"] = out["mean_gap"] * votes
    out["votes_at_risk_midterm"] = penalty.clip(lower=0) * votes
    out["bucket"] = "persuade"
    out.loc[out["expected_share"] >= 0.5 + competitive_band, "bucket"] = "turnout"
    out.loc[out["expected_share"] <= 0.5 - competitive_band, "bucket"] = "hard"

    # The plan is a ranked list: persuade ground first, where a point buys
    # the most votes; then turnout ground, largest pile of at-risk supporters
    # first; hard ground last. _PLAYBOOK_RANK orders the buckets, the bucket's
    # own currency breaks ties.
    out["_rank"] = out["bucket"].map(_PLAYBOOK_RANK)
    out["_key"] = out["votes_per_point"]
    is_turnout = out["bucket"] == "turnout"
    out.loc[is_turnout, "_key"] = out.loc[is_turnout, "votes_at_risk_midterm"]
    out = out.sort_values(["_rank", "_key"], ascending=[True, False]).drop(
        columns=["_rank", "_key"]
    )
    out["priority"] = range(1, len(out) + 1)
    return out.reset_index()


def playbook_budget_split(
    plan: pd.DataFrame, *, competitive_band: float = 0.08
) -> "pd.Series[float]":
    """How to split a budget between persuasion and turnout, in votes.

    Two pools, both in votes so they can be compared: the persuasion pool is
    what is within reach in persuade counties - expected votes times the
    competitive band (moving a toss-up county across the band's width); the
    turnout pool is the supporters at risk of skipping the midterm in turnout
    counties. The shares are each pool's fraction of the two together. A
    heuristic, stated in the open: it says where the votes are, not what to
    say to get them.
    """
    persuade = plan[plan["bucket"] == "persuade"]
    turnout = plan[plan["bucket"] == "turnout"]
    persuasion_pool = float((persuade["expected_votes"] * competitive_band).sum())
    turnout_pool = float(turnout["votes_at_risk_midterm"].sum())
    total = persuasion_pool + turnout_pool
    return pd.Series(
        {
            "persuasion_pool_votes": persuasion_pool,
            "turnout_pool_votes": turnout_pool,
            "persuasion_share": persuasion_pool / total if total else float("nan"),
            "turnout_share": turnout_pool / total if total else float("nan"),
        }
    )
