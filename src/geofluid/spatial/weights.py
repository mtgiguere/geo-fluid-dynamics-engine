"""County adjacency and spatial weights — the substrate of Modules 1 and 2.

Adjacency is computed by shared-vertex detection: in a topologically
consistent boundary file (Census cartographic boundaries are), two counties
share a border if and only if they share boundary vertices. This is queen
contiguity — corner-touching counties count as neighbors — the standard
choice for county-level spatial analysis, and it requires no geometry
library: just hashing vertices, which handles all 3,234 counties in seconds.
"""

from collections import defaultdict
from typing import Any


def _vertices(geometry: dict[str, Any]) -> list[tuple[float, float]]:
    """All boundary vertices of a Polygon or MultiPolygon."""
    if geometry["type"] == "Polygon":
        polygons = [geometry["coordinates"]]
    else:  # MultiPolygon
        polygons = geometry["coordinates"]
    return [tuple(point) for polygon in polygons for ring in polygon for point in ring]


def county_adjacency(county_geojson: dict[str, Any]) -> dict[str, frozenset[str]]:
    """Queen-contiguity neighbors for every county in the boundary file.

    Every county appears in the result — islands (Hawaii, Nantucket) map to
    an empty set. Dropping them from the keys would silently shrink the
    weights matrix and misalign every index built on it.
    """
    counties_at_vertex: defaultdict[tuple[float, float], set[str]] = defaultdict(set)
    fips_list: list[str] = []
    for feature in county_geojson["features"]:
        fips = str(feature["id"])
        fips_list.append(fips)
        for vertex in _vertices(feature["geometry"]):
            counties_at_vertex[vertex].add(fips)

    neighbors: dict[str, set[str]] = {fips: set() for fips in fips_list}
    for sharing in counties_at_vertex.values():
        for fips in sharing:
            neighbors[fips].update(sharing - {fips})
    return {fips: frozenset(found) for fips, found in neighbors.items()}
