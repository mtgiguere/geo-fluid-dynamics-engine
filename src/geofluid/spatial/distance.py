"""Great-circle distance between counties — for the targeting engine's routing.

The prescriptive layer tells an organizer how far each candidate county is, so
"drive 39 miles south" can sit next to "a persuadable False Bastion." Two small
helpers: a cheap bounding-box stand-in for a county's location, and the
great-circle miles between two such points.
"""

import math
from typing import Any

_EARTH_RADIUS_MILES = 3958.7613  # mean Earth radius in statute miles


def _walk_coords(coords: Any) -> "tuple[list[float], list[float]]":
    """Collect all (lon, lat) vertices from an arbitrarily nested GeoJSON
    coordinate array into parallel lon/lat lists."""
    lons: list[float] = []
    lats: list[float] = []
    if coords and isinstance(coords[0], (int, float)):
        lons.append(coords[0])
        lats.append(coords[1])
    else:
        for part in coords:
            sub_lons, sub_lats = _walk_coords(part)
            lons.extend(sub_lons)
            lats.extend(sub_lats)
    return lons, lats


def bounding_box_center(geometry: dict[str, Any]) -> tuple[float, float]:
    """The midpoint of a geometry's bounding box, as (lon, lat).

    A deliberately cheap stand-in for a county's location — enough to rank
    drive-distance without computing a true area centroid, and robust to
    GeoJSON's repeated closing vertex (which would bias a naive vertex mean).
    Spans every ring/part, so MultiPolygon counties (islands, exclaves) are
    bounded whole.
    """
    lons, lats = _walk_coords(geometry["coordinates"])
    return (min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2


def haversine_miles(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle distance in statute miles between two (lon, lat) points."""
    lon1, lat1 = math.radians(a[0]), math.radians(a[1])
    lon2, lat2 = math.radians(b[0]), math.radians(b[1])
    d_lat, d_lon = lat2 - lat1, lon2 - lon1
    h = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    return _EARTH_RADIUS_MILES * 2 * math.asin(math.sqrt(h))
