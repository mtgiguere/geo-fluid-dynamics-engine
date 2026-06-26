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
