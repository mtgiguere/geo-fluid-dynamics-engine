"""Tests for local Moran's I (LISA) — which counties anchor the wave.

Global I says clustering exists; the local decomposition says WHERE. Each
county gets its own statistic I_i (its contribution to the global pattern)
and a quadrant label: a high value among high neighbors is a wave core,
a low value among high neighbors is a hole in the wave, and so on.

Same API discipline as the global statistic: fips-indexed Series in,
fips-indexed results out, alignment internal.
"""

import pandas as pd

from geofluid.spatial.moran import local_morans_i

_PAIRS = {
    "01001": frozenset({"01003"}),
    "01003": frozenset({"01001"}),
    "29189": frozenset({"29510"}),
    "29510": frozenset({"29189"}),
}


def test_local_values_hand_computed_for_perfect_clustering() -> None:
    """Pairs (+1, +1) and (-1, -1): z = (1, 1, -1, -1), m2 = z'z/n = 1, each
    county's neighbor lag equals its own value, so I_i = z_i * lag_i / m2 = 1
    for every county. The result is a fips-indexed Series."""
    values = pd.Series({"01001": 1.0, "01003": 1.0, "29189": -1.0, "29510": -1.0})

    local = local_morans_i(values, _PAIRS)

    assert isinstance(local["i_local"], pd.Series)
    assert sorted(local["i_local"].index) == ["01001", "01003", "29189", "29510"]
    for fips in ["01001", "01003", "29189", "29510"]:
        assert abs(local["i_local"][fips] - 1.0) < 1e-12


def test_quadrant_labels_classify_cores_and_outliers() -> None:
    """The LISA quadrants, on a hand-built star: center county at -2
    surrounded by +2/+3/+3 neighbors. Mean is 1.5, so the center is below
    average among above-average neighbors -> "low-high" (a hole in a wave);
    each spoke is above average with a below-average neighborhood (their
    only neighbor is the center) -> "high-low" (defiant outliers). The
    clustered-pairs fixture yields "high-high" and "low-low" cores."""
    star = {
        "29189": frozenset({"01001", "01003", "29510"}),
        "01001": frozenset({"29189"}),
        "01003": frozenset({"29189"}),
        "29510": frozenset({"29189"}),
    }
    values = pd.Series({"29189": -2.0, "01001": 2.0, "01003": 3.0, "29510": 3.0})

    local = local_morans_i(values, star)

    assert local["quadrant"]["29189"] == "low-high"
    assert local["quadrant"]["01001"] == "high-low"
    assert local["quadrant"]["01003"] == "high-low"
    assert local["quadrant"]["29510"] == "high-low"

    pairs_values = pd.Series({"01001": 1.0, "01003": 1.0, "29189": -1.0, "29510": -1.0})
    pairs_local = local_morans_i(pairs_values, _PAIRS)
    assert pairs_local["quadrant"]["01001"] == "high-high"
    assert pairs_local["quadrant"]["29189"] == "low-low"
