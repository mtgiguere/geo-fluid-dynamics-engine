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
