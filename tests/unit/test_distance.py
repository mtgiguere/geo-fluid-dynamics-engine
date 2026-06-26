"""Tests for spatial distance helpers — drive-distance for the targeting engine.

The prescriptive layer ranks where an organizer should drive; that needs miles
between counties. Two small, error-prone pieces worth testing in isolation
(great-circle math is easy to get subtly wrong — radians, axis order):

  * bounding_box_center(geometry) -> (lon, lat): a cheap, honest stand-in for a
    county's location — the midpoint of its bounding box, enough to rank
    drive-distance without a true area centroid.
  * haversine_miles(a, b): great-circle miles between two (lon, lat) points.
"""

import math

from geofluid.spatial.distance import bounding_box_center, haversine_miles


def _square(cx: float, cy: float, half: float) -> dict[str, object]:
    """A GeoJSON Polygon square centered at (cx, cy), closing vertex repeated
    as real GeoJSON rings do."""
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [cx - half, cy - half],
                [cx + half, cy - half],
                [cx + half, cy + half],
                [cx - half, cy + half],
                [cx - half, cy - half],
            ]
        ],
    }


def test_bounding_box_center_of_a_square_is_its_center() -> None:
    """The bbox center is robust to GeoJSON's repeated closing vertex (which
    biases a naive vertex mean). A square centered at (-95.0, 38.5) with
    half-width 0.5 must return exactly (-95.0, 38.5)."""
    center = bounding_box_center(_square(-95.0, 38.5, 0.5))
    assert center == (-95.0, 38.5)


def test_bounding_box_center_handles_multipolygon() -> None:
    """Counties with islands/exclaves arrive as MultiPolygon. The bbox must
    span ALL parts: a part near (0,0) and a part near (10,10) give a bounding
    box [0,10]x[0,10], center (5, 5)."""
    geom = {
        "type": "MultiPolygon",
        "coordinates": [
            _square(0.0, 0.0, 1.0)["coordinates"],
            _square(10.0, 10.0, 1.0)["coordinates"],
        ],
    }
    assert bounding_box_center(geom) == (5.0, 5.0)


def test_haversine_zero_for_identical_points() -> None:
    """A point is zero miles from itself."""
    assert haversine_miles((-94.6, 39.1), (-94.6, 39.1)) == 0.0


def test_haversine_one_degree_of_latitude_is_about_69_miles() -> None:
    """A degree of latitude is ~69.09 statute miles anywhere on the globe
    (a meridian is a great circle). (0,0)->(0,1) must land within half a mile
    of 69.09 — the check that the radians conversion and Earth radius are
    right, without pinning an over-precise value."""
    assert math.isclose(haversine_miles((0.0, 0.0), (0.0, 1.0)), 69.09, abs_tol=0.5)


def test_haversine_is_symmetric() -> None:
    """Distance a->b equals b->a (Kansas City to Wichita, roughly)."""
    a, b = (-94.6, 39.1), (-97.3, 37.7)
    assert math.isclose(haversine_miles(a, b), haversine_miles(b, a), rel_tol=1e-12)
