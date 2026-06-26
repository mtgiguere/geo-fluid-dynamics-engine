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

from geofluid.targeting import build_itinerary


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
