"""Tests for local Moran's I (LISA) — which counties anchor the wave.

Global I says clustering exists; the local decomposition says WHERE. Each
county gets its own statistic I_i (its contribution to the global pattern)
and a quadrant label: a high value among high neighbors is a wave core,
a low value among high neighbors is a hole in the wave, and so on.

Same API discipline as the global statistic: fips-indexed Series in,
fips-indexed results out, alignment internal.
"""

import pandas as pd
from hypothesis import assume, given
from hypothesis import strategies as st

from geofluid.spatial.moran import (
    local_morans_by_year,
    local_morans_i,
    morans_i,
    significant_quadrants,
)

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


def test_local_moran_by_year_carries_permutation_p_values() -> None:
    """The export path needs per-year p-values: by_year forwards the
    permutation arguments and the tidy frame gains p_value, bounded by the
    pseudo-p floor 1/(permutations+1) and 1.0 — for any rng."""
    panel = pd.DataFrame(
        [
            {"fips": f, "year": 2020, "swing_dem_2p": v}
            for f, v in [("01001", 1.0), ("01003", 1.5), ("29189", -1.0), ("29510", -2.0)]
        ]
    )

    tidy = local_morans_by_year(panel, _PAIRS, value_column="swing_dem_2p", permutations=9)

    assert list(tidy.columns) == ["fips", "year", "i_local", "quadrant", "p_value"]
    assert ((tidy["p_value"] >= 0.1) & (tidy["p_value"] <= 1.0)).all()


_RING_FIPS = ["01001", "01003", "29189", "29510", "46102", "56001"]
_RING = {
    f: frozenset({_RING_FIPS[(i - 1) % 6], _RING_FIPS[(i + 1) % 6]})
    for i, f in enumerate(_RING_FIPS)
}


def test_fully_connected_county_has_pseudo_p_of_exactly_one() -> None:
    """Conditional permutation holds a county's own value fixed and permutes
    everyone else's across the other locations. A county adjacent to ALL
    other counties therefore sees the same neighbor mean under every
    permutation — its simulated I_i always equals the observed one, so the
    pseudo p-value is exactly (nperm + 1)/(nperm + 1) = 1.0, deterministically,
    for ANY rng. This is the no-seed test of the permutation machinery
    (TDD_CONTRACT.md RED FLAG 3: seed-specific assertions are banned)."""
    star = {
        "29189": frozenset({"01001", "01003", "29510"}),  # connected to all
        "01001": frozenset({"29189"}),
        "01003": frozenset({"29189"}),
        "29510": frozenset({"29189"}),
    }
    values = pd.Series({"29189": -2.0, "01001": 2.0, "01003": 3.0, "29510": 3.0})

    local = local_morans_i(values, star, permutations=99)

    assert local["p_value"]["29189"] == 1.0
    # The spokes have one neighbor each drawn from three candidates; their
    # p-values are random but must respect the pseudo-p bounds.
    for fips in ["01001", "01003", "29510"]:
        assert 1 / 100 <= local["p_value"][fips] <= 1.0


def test_same_generator_seed_reproduces_identical_p_values() -> None:
    """The reproducibility contract: an injected, identically-seeded
    Generator yields identical p-values. This asserts DETERMINISM of the
    machinery, not any seed-specific data value — the distinction RED FLAG 3
    draws. Published findings must be re-runnable."""
    import numpy as np

    values = pd.Series({"01001": 1.0, "01003": 1.5, "29189": -1.0, "29510": -2.0})

    first = local_morans_i(values, _PAIRS, permutations=49, rng=np.random.default_rng(7))
    second = local_morans_i(values, _PAIRS, permutations=49, rng=np.random.default_rng(7))

    assert first["p_value"].equals(second["p_value"])


def test_significant_quadrants_masks_labels_that_could_be_chance() -> None:
    """The map-honesty rule: a quadrant label is only painted when the
    clustering beats chance at the chosen alpha. Counties failing the test
    keep their row and i_local but lose the label (None -> gray on the map
    via the existing null path). Constructed p-values, no randomness."""
    lisa = pd.DataFrame(
        {
            "i_local": [3.0, 0.4, -1.2],
            "quadrant": ["high-high", "low-low", "low-high"],
            "p_value": [0.01, 0.30, 0.05],
        },
        index=pd.Index(["01001", "29189", "29510"], name="fips"),
    )

    masked = significant_quadrants(lisa, alpha=0.05)

    assert masked["quadrant"].tolist() == ["high-high", None, "low-high"]  # 0.05 <= alpha
    assert masked["i_local"].tolist() == [3.0, 0.4, -1.2]  # values untouched
    assert lisa["quadrant"].tolist()[1] == "low-low"  # input not mutated


def test_local_moran_by_year_returns_tidy_per_county_year_frame() -> None:
    """The panel-shaped wrapper the export pipeline consumes: one LISA run
    per election year over the chosen column, returned tidy (fips, year,
    i_local, quadrant). Counties whose value is missing that year (swing in
    a county's first appearance) simply have no row for that year — absence,
    not a fabricated label."""
    panel = pd.DataFrame(
        [
            # 2020: clustered pairs (+ around 01xxx, - around 29xxx)
            {"fips": "01001", "year": 2020, "swing_dem_2p": 1.0},
            {"fips": "01003", "year": 2020, "swing_dem_2p": 1.0},
            {"fips": "29189", "year": 2020, "swing_dem_2p": -1.0},
            {"fips": "29510", "year": 2020, "swing_dem_2p": -1.0},
            # 2024: 29189 has no swing (NaN); others flip sign
            {"fips": "01001", "year": 2024, "swing_dem_2p": -1.0},
            {"fips": "01003", "year": 2024, "swing_dem_2p": -2.0},
            {"fips": "29189", "year": 2024, "swing_dem_2p": float("nan")},
            {"fips": "29510", "year": 2024, "swing_dem_2p": 3.0},
        ]
    )

    tidy = local_morans_by_year(panel, _PAIRS, value_column="swing_dem_2p")

    assert list(tidy.columns) == ["fips", "year", "i_local", "quadrant"]
    by_key = tidy.set_index(["fips", "year"])
    assert by_key.loc[("01001", 2020), "quadrant"] == "high-high"
    assert by_key.loc[("29189", 2020), "quadrant"] == "low-low"
    # 2024: 29189 is NaN -> no row for it, and its pair partner 29510 is
    # orphaned -> also no row. Only the 01xxx pair remains — and a lone pair
    # is measured against its own mean (-1.5), making it perfectly DISPERSED:
    # 01001 (-1.0) sits above that mean with a below-mean neighbor.
    # (First drafted as "low-low"; the implementation was right and the
    # hand-math wrong — exclusion changes the reference mean.)
    assert ("29189", 2024) not in by_key.index
    assert ("29510", 2024) not in by_key.index
    assert by_key.loc[("01001", 2024), "quadrant"] == "high-low"
    assert by_key.loc[("01003", 2024), "quadrant"] == "low-high"


@given(raw=st.lists(st.floats(-100, 100, allow_nan=False), min_size=6, max_size=6))
def test_mean_of_local_statistics_equals_global_moran_i(raw: list[float]) -> None:
    """Property: with row-standardized W and no islands, S0 = n and the
    global statistic decomposes exactly: I = mean(I_i). This is the theorem
    that makes the LISA a DECOMPOSITION rather than a separate metric — if
    the two implementations ever drift apart (different exclusion, different
    centering), this property snaps."""
    values = pd.Series(dict(zip(_RING_FIPS, raw, strict=True)))
    assume(float(values.var()) > 1e-6)

    local = local_morans_i(values, _RING)

    assert abs(float(local["i_local"].mean()) - morans_i(values, _RING)) < 1e-9
