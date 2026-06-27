"""Tests for spatial adjacency and weights — Module 1's foundation.

The Wave Predictor and Gravity Engine both run on a spatial weights matrix W
built from county adjacency. This file is the contract for that machinery.

Ordering note: TDD_CONTRACT.md Bug #3 (FIPS sort order) lived exactly here in
the prior project. Every matrix test uses an explicit fips->value mapping —
never an array literal whose order silently encodes an assumption.
"""

from typing import Any

import numpy as np
import pandas as pd
from hypothesis import given
from hypothesis import strategies as st

from geofluid.spatial.weights import (
    attribute_knn_adjacency,
    county_adjacency,
    spatial_weights,
)


def _square(fips: str, x: float, y: float, size: float = 1.0) -> dict[str, Any]:
    """A unit square county with lower-left corner at (x, y)."""
    return {
        "type": "Feature",
        "id": fips,
        "properties": {"NAME": f"County {fips}", "fips": fips},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[(x, y), (x + size, y), (x + size, y + size), (x, y + size), (x, y)]],
        },
    }


def _fc(features: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": features}


def test_counties_sharing_a_border_are_adjacent_and_islands_are_present() -> None:
    """Two squares sharing an edge are neighbors (symmetrically). A county
    with no shared boundary — Hawaii, Nantucket — must still APPEAR in the
    adjacency with an empty neighbor set: dropping islands from the keys
    would silently shrink the weights matrix and misalign every index."""
    fc = _fc(
        [
            _square("29189", 0.0, 0.0),
            _square("29510", 1.0, 0.0),  # shares the x=1 edge with 29189
            _square("15003", 5.0, 5.0),  # island: touches nothing
        ]
    )

    adjacency = county_adjacency(fc)

    assert adjacency == {
        "29189": frozenset({"29510"}),
        "29510": frozenset({"29189"}),
        "15003": frozenset(),
    }


def test_corner_touching_counties_are_neighbors_queen_contiguity() -> None:
    """The contiguity rule is QUEEN: sharing a single point makes neighbors.
    This is the Four Corners case (Arizona/Colorado/New Mexico/Utah meet at
    one point) and the standard choice for county-level spatial analysis —
    influence does not require a drivable border. Pinned here so a future
    switch to rook contiguity is a visible contract change."""
    fc = _fc(
        [
            _square("04001", 0.0, 0.0),  # corner at (1, 1)
            _square("08083", 1.0, 1.0),  # corner at (1, 1) — diagonal touch
        ]
    )

    adjacency = county_adjacency(fc)

    assert adjacency["04001"] == frozenset({"08083"})
    assert adjacency["08083"] == frozenset({"04001"})


def test_weights_matrix_is_row_standardized_and_sorted_by_fips() -> None:
    """The W contract: rows/columns aligned to SORTED fips (returned alongside
    the matrix, never assumed), each row standardized to sum to 1 across the
    county's neighbors, islands all-zero. Expected weights are written as an
    explicit (from, to) -> value mapping — Bug #3 in TDD_CONTRACT.md was an
    array literal whose order silently disagreed with the implementation."""
    adjacency = {
        "29189": frozenset({"01001", "29510"}),
        "29510": frozenset({"29189"}),
        "01001": frozenset({"29189"}),
        "15003": frozenset(),  # island
    }

    matrix, order = spatial_weights(adjacency)

    assert order == ["01001", "15003", "29189", "29510"]
    assert matrix.shape == (4, 4)
    # 01001 neighbors {29189} -> full weight to it; 29189 neighbors two
    # counties -> 0.5 each; 29510 -> full weight to 29189; 15003 -> nothing.
    expected = {
        ("01001", "29189"): 1.0,
        ("29189", "01001"): 0.5,
        ("29189", "29510"): 0.5,
        ("29510", "29189"): 1.0,
    }
    for i, source in enumerate(order):
        for j, target in enumerate(order):
            assert matrix[i, j] == expected.get((source, target), 0.0), (source, target)


@st.composite
def _adjacencies(draw: st.DrawFn) -> dict[str, frozenset[str]]:
    """Random symmetric adjacency over 1-12 counties (any edge set)."""
    n = draw(st.integers(min_value=1, max_value=12))
    fips = [f"{i:05d}" for i in range(n)]
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    chosen: set[tuple[int, int]] = draw(st.sets(st.sampled_from(pairs))) if pairs else set()
    neighbors: dict[str, set[str]] = {f: set() for f in fips}
    for i, j in chosen:
        neighbors[fips[i]].add(fips[j])
        neighbors[fips[j]].add(fips[i])
    return {f: frozenset(s) for f, s in neighbors.items()}


@given(adjacency=_adjacencies(), value=st.floats(-1e6, 1e6, allow_nan=False))
def test_spatial_lag_of_constant_field_is_that_constant(
    adjacency: dict[str, frozenset[str]], value: float
) -> None:
    """Property: W @ (a constant field) returns the constant for every county
    with neighbors, and exactly zero for islands — for ANY adjacency and any
    value. "The average of my neighbors' x, when everyone's x is c, is c" is
    what row standardization MEANS; if the normalization is wrong anywhere,
    some county's lag will not be c. (Same property family as the GFIP
    area-weighted-mean test in TDD_CONTRACT.md.)"""
    matrix, order = spatial_weights(adjacency)

    lag = matrix @ np.full(len(order), value)

    for i, fips in enumerate(order):
        if adjacency[fips]:
            assert abs(lag[i] - value) < 1e-9 * max(1.0, abs(value))
        else:
            assert lag[i] == 0.0


@given(adjacency=_adjacencies())
def test_weights_diagonal_is_zero_and_nonzero_pattern_is_symmetric(
    adjacency: dict[str, frozenset[str]],
) -> None:
    """Property: no county influences itself through W (zero diagonal), and
    the nonzero PATTERN is symmetric for symmetric adjacency — the weights
    differ (row standardization), but i touching j must mean j touches i."""
    matrix, order = spatial_weights(adjacency)

    n = len(order)
    for i in range(n):
        assert matrix[i, i] == 0.0
        for j in range(n):
            assert (matrix[i, j] > 0) == (matrix[j, i] > 0)


# --- Attribute-similarity adjacency (Module 2 path: who-resembles-whom) -------
#
# A second, NON-geographic network: counties are neighbours when they are close
# in standardized DEMOGRAPHIC feature space (density, education, age, ...), not
# when they share a border. It returns the same dict[fips, frozenset[fips]] as
# county_adjacency, so it drops straight into morans_i / local_morans_i — letting
# us ask whether political change co-moves along SIMILARITY rather than geography,
# and (the confound to respect) which demographic axis carries that co-movement.


def test_attribute_knn_adjacency_links_nearest_in_feature_space() -> None:
    """Counties become neighbours by nearness in standardized feature space.
    A single feature places six counties in two tight clusters — A,B,C at 0,1,2
    and D,E,F at 10,11,12 — so each county's k=2 nearest are its own
    cluster-mates and NO edge crosses between clusters. z-scoring is a monotonic
    affine map on one feature, so it preserves these orderings: A(0)'s two
    nearest are B(1) and C(2). (Derived before the assertion.)"""
    features = pd.DataFrame(
        {"x": [0.0, 1.0, 2.0, 10.0, 11.0, 12.0]},
        index=["A", "B", "C", "D", "E", "F"],
    )

    adjacency = attribute_knn_adjacency(features, k=2)

    assert adjacency["A"] == frozenset({"B", "C"})
    assert adjacency["D"] == frozenset({"E", "F"})
    left = {"A", "B", "C"}
    for fips in left:
        assert adjacency[fips] <= left  # no cross-cluster edges


def test_attribute_knn_adjacency_gives_each_county_k_neighbours_excluding_itself() -> None:
    """Every county gets exactly k neighbours and never lists itself. (Regression
    guard on the completed kNN builder — immediately GREEN.)"""
    features = pd.DataFrame({"x": [0.0, 1.0, 2.0, 3.0, 4.0]}, index=["A", "B", "C", "D", "E"])

    adjacency = attribute_knn_adjacency(features, k=3)

    for fips, neighbours in adjacency.items():
        assert len(neighbours) == 3
        assert fips not in neighbours


def test_attribute_knn_adjacency_is_invariant_to_feature_scale_and_shift() -> None:
    """THE load-bearing property for a fair multi-feature distance: because each
    column is z-scored, rescaling or shifting a feature (density in people/sq-mi
    vs /sq-km, a column with a huge offset) must yield the SAME network. So a
    high-magnitude variable cannot dominate a [0,1] one by units alone — z-score
    is invariant to per-column affine maps, so the standardized distances, hence
    the neighbours, are identical. (Regression guard — immediately GREEN.)"""
    base = pd.DataFrame(
        {"x": [0.0, 1.0, 2.0, 10.0, 11.0, 12.0], "y": [5.0, 5.0, 5.0, 9.0, 9.0, 9.0]},
        index=["A", "B", "C", "D", "E", "F"],
    )
    scaled = pd.DataFrame(
        {"x": base["x"] * 1000.0 + 7.0, "y": base["y"] * 0.001 - 3.0},
        index=base.index,
    )

    assert attribute_knn_adjacency(base, k=2) == attribute_knn_adjacency(scaled, k=2)


def test_attribute_knn_adjacency_ignores_a_constant_feature() -> None:
    """A feature identical for every county carries no information and must not
    break the distance (no divide-by-zero on its zero variance): the network is
    decided by the informative feature alone. (Guards the std==0 handling.)"""
    df = pd.DataFrame(
        {"x": [0.0, 1.0, 2.0, 10.0, 11.0, 12.0], "flat": [3.0] * 6},
        index=["A", "B", "C", "D", "E", "F"],
    )

    assert attribute_knn_adjacency(df, k=2) == attribute_knn_adjacency(df[["x"]], k=2)
