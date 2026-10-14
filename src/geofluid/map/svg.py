"""Inline-SVG projection for the public pages' county choropleths.

Equirectangular with a cos(mid-latitude) aspect correction, 1000 units wide,
y pointing down: good enough for a single state at a glance, dependency-free,
and identical across every page that draws one. Shared here so the arithmetic
is under test once instead of copied into three untested build scripts.
"""

import math
from collections.abc import Mapping

Ring = list[tuple[float, float]]
MultiPolygon = list[list[Ring]]  # polygons -> rings -> (lon, lat) points


def project_rings(
    rings: Mapping[str, MultiPolygon], *, width: float = 1000.0
) -> tuple[dict[str, str], dict[str, tuple[float, float]], float]:
    """Project MultiPolygon rings (lon, lat) keyed by id into SVG path strings.

    Returns (paths, centroids, height): `paths` maps id -> "M..L..Z" path
    data; `centroids` maps id -> the bounding-box centre in SVG units (where
    a marker goes); `height` is the viewBox height that keeps the aspect
    honest at the rings' mid-latitude. Coordinates are rounded to 0.1.
    """
    pts = [p for parts in rings.values() for poly in parts for ring in poly for p in ring]
    lon0, lon1 = min(p[0] for p in pts), max(p[0] for p in pts)
    lat0, lat1 = min(p[1] for p in pts), max(p[1] for p in pts)
    kx = math.cos(math.radians((lat0 + lat1) / 2))
    height = width * (lat1 - lat0) / ((lon1 - lon0) * kx)

    def px(lon: float) -> float:
        return round((lon - lon0) / (lon1 - lon0) * width, 1)

    def py(lat: float) -> float:
        return round((lat1 - lat) / (lat1 - lat0) * height, 1)

    paths: dict[str, str] = {}
    centroids: dict[str, tuple[float, float]] = {}
    for fid, parts in rings.items():
        segs = []
        for poly in parts:
            for ring in poly:
                segs.append(
                    "".join(
                        f"{'M' if i == 0 else 'L'}{px(p[0])},{py(p[1])}" for i, p in enumerate(ring)
                    )
                    + "Z"
                )
        paths[fid] = "".join(segs)
        own = [p for poly in parts for ring in poly for p in ring]
        cx = (px(min(p[0] for p in own)) + px(max(p[0] for p in own))) / 2
        cy = (py(min(p[1] for p in own)) + py(max(p[1] for p in own))) / 2
        centroids[fid] = (round(cx, 1), round(cy, 1))
    return paths, centroids, height
