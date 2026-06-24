"""Tests for the cross-measure contest panel — the fips x measure_id schema.

Module 2 path (b), the issue-resistance route, needs to model a county's
persuadability ACROSS ballot measures, not within one (N=1 has no structure —
the same depth lesson the 40-election spine taught lead-lag). This panel stacks
the per-measure referendum panels (each from a load_*_referendum loader) into
one tidy frame keyed (measure_id, fips), and adds progressive_share: the
progressive vote's share, ORIENTED so it is comparable across measures
whatever ballot side carried the progressive position (abortion measures: a NO
vote preserved rights; a cannabis legalization measure: a YES vote).
"""

import pandas as pd
import pytest

from geofluid.panel.measures import Measure, build_measures_panel


def _panel(rows: list[tuple[str, int, int]]) -> pd.DataFrame:
    """A canonical referendum panel (as load_*_referendum emits) from
    (fips, yes_votes, no_votes) triples."""
    df = pd.DataFrame(rows, columns=["fips", "yes_votes", "no_votes"])
    df["total_votes"] = df["yes_votes"] + df["no_votes"]
    df["no_share"] = df["no_votes"] / df["total_votes"]
    return df


def test_combines_two_measures_with_orientation_corrected_progressive_share() -> None:
    """Two measures stack into one tidy fips x measure_id panel, sorted by
    (measure_id, fips). progressive_share is the PROGRESSIVE side's share of
    the two-way vote: for an abortion measure NO is progressive, so county
    20001 (yes 30 / no 70, no_share 0.70) has progressive_share 70/100 = 0.70;
    for a cannabis measure YES is progressive, so county 29001 (yes 60 / no 40)
    has progressive_share 60/100 = 0.60 (= 1 - no_share). Derived here before
    the assertions. Inputs are passed out of measure order to prove the sort."""
    abortion = Measure(
        measure_id="ks_abortion_2022",
        progressive_side="no",
        panel=_panel([("20001", 30, 70)]),
    )
    cannabis = Measure(
        measure_id="mo_cannabis_2022",
        progressive_side="yes",
        panel=_panel([("29001", 60, 40)]),
    )

    tidy = build_measures_panel([cannabis, abortion])

    assert list(tidy.columns) == [
        "measure_id",
        "fips",
        "yes_votes",
        "no_votes",
        "total_votes",
        "no_share",
        "progressive_share",
    ]
    assert list(zip(tidy["measure_id"], tidy["fips"], strict=True)) == [
        ("ks_abortion_2022", "20001"),
        ("mo_cannabis_2022", "29001"),
    ]
    assert abs(tidy.iloc[0]["progressive_share"] - 0.70) < 1e-12
    assert abs(tidy.iloc[1]["progressive_share"] - 0.60) < 1e-12


def test_progressive_side_must_be_yes_or_no() -> None:
    """progressive_side is the whole point of this panel — the orientation that
    makes progressive_share comparable across measures. A typo ('No', 'n', '')
    must raise at construction, naming the bad value, never silently fall
    through to one side and invert the axis for an entire measure (a plausible-
    looking but wrong progressive_share is exactly the silent scientific error
    this project guards against)."""
    with pytest.raises(ValueError, match="No"):
        Measure(
            measure_id="ks_abortion_2022",
            progressive_side="No",
            panel=_panel([("20001", 30, 70)]),
        )
