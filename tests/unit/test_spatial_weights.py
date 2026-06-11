"""Tests for spatial adjacency and weights — Module 1's foundation.

The Wave Predictor and Gravity Engine both run on a spatial weights matrix W
built from county adjacency. This file is the contract for that machinery.

Ordering note: TDD_CONTRACT.md Bug #3 (FIPS sort order) lived exactly here in
the prior project. Every matrix test uses an explicit fips->value mapping —
never an array literal whose order silently encodes an assumption.
"""

from typing import Any

from geofluid.spatial.weights import county_adjacency


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
