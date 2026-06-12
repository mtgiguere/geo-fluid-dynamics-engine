"""Tests for Moran's I — is a county-level quantity spatially clustered?

This is Module 1's first inferential statistic: before predicting where a
wave goes, establish that waves exist — that swing on the map is clustered
beyond chance rather than scattered noise.

API note: morans_i takes a fips-INDEXED Series and the adjacency mapping and
aligns them internally. A signature taking a bare array plus an assumed
order would reopen TDD_CONTRACT.md Bug #3; this one makes misalignment
impossible to express.
"""

import pandas as pd

from geofluid.spatial.moran import morans_i

# Two separated pairs: A-B adjacent, C-D adjacent, no edges between pairs.
_PAIRS = {
    "01001": frozenset({"01003"}),
    "01003": frozenset({"01001"}),
    "29189": frozenset({"29510"}),
    "29510": frozenset({"29189"}),
}


def test_perfectly_clustered_values_give_moran_i_of_one() -> None:
    """Two adjacent pairs, each pair internally identical, pairs opposite:
    every county's neighbor average equals its own value. Hand computation
    with row-standardized W: z = (1, 1, -1, -1), z'Wz = 4, z'z = 4, S0 = 4,
    n = 4 -> I = (4/4) * (4/4) = 1.0. Perfect positive autocorrelation."""
    values = pd.Series({"01001": 1.0, "01003": 1.0, "29189": -1.0, "29510": -1.0})

    assert abs(morans_i(values, _PAIRS) - 1.0) < 1e-12


def test_perfectly_dispersed_values_give_moran_i_of_minus_one() -> None:
    """Each county's only neighbor holds the opposite value: the
    checkerboard. Hand computation: z'Wz = -4 -> I = -1.0. Perfect negative
    autocorrelation — the opposite of a wave."""
    values = pd.Series({"01001": 1.0, "01003": -1.0, "29189": 1.0, "29510": -1.0})

    assert abs(morans_i(values, _PAIRS) - (-1.0)) < 1e-12


def test_missing_values_islands_and_orphaned_counties_are_excluded() -> None:
    """The real inputs are messy: swing is NaN in 2000 and for gap counties;
    Hawaii has no neighbors; a county whose ONLY neighbor is missing has no
    one to be compared with. All three must drop out — included, an island's
    zero weight row would deflate I, and a NaN would poison the sums. The
    perfectly clustered pairs must still give exactly 1.0 after exclusion:
    - 15003: island (no neighbors) despite having a value
    - 30001: value is NaN
    - 30031: present, but its only neighbor is the NaN county
    - 56001: in the adjacency, absent from the values index entirely"""
    adjacency = {
        **_PAIRS,
        "15003": frozenset(),
        "30001": frozenset({"30031"}),
        "30031": frozenset({"30001"}),
        "56001": frozenset({"01001"}),
        "01001": _PAIRS["01001"] | {"56001"},
    }
    values = pd.Series(
        {
            "01001": 1.0,
            "01003": 1.0,
            "29189": -1.0,
            "29510": -1.0,
            "15003": 5.0,
            "30001": float("nan"),
            "30031": 2.0,
        }
    )

    assert abs(morans_i(values, adjacency) - 1.0) < 1e-12
