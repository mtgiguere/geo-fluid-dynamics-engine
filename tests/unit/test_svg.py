"""Tests for the inline-SVG projection shared by the public page builders.

Three builders draw county choropleths as self-contained SVG. The projection
(equirectangular with a cos(latitude) aspect correction, 1000 units wide) is
pure arithmetic that was duplicated across untested scripts; here it lives
once, under test, and the scripts call it.
"""

import math

from geofluid.map.svg import project_rings


def test_unit_square_projects_to_the_full_width_with_aspect_correction() -> None:
    """One ring, the square lon 0..1 x lat 0..1. Width is fixed at 1000, so
    px(0) = 0 and px(1) = 1000. Height = 1000 * dlat / (dlon * cos(midlat))
    with midlat 0.5 degrees -> 1000 / cos(0.5 deg) = 1000.038...; y runs
    downward so py(1) = 0 and py(0) = height. The path visits the ring's
    points in order and closes with Z; coordinates are rounded to 0.1.
    The bounding-box centroid is the box centre: (500.0, height/2)."""
    rings = {"X": [[[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]]]}

    paths, centroids, height = project_rings(rings)

    expected_height = 1000 / math.cos(math.radians(0.5))
    assert abs(height - expected_height) < 1e-9
    assert paths["X"] == "M0.0,1000.0L1000.0,1000.0L1000.0,0.0L0.0,0.0L0.0,1000.0Z"
    assert centroids["X"] == (500.0, 500.0)
