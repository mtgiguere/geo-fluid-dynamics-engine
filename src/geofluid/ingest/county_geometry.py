"""Ingest Census cartographic boundary shapefiles into county GeoJSON.

The cb_2021 vintage is deliberate: it carries Connecticut's old counties
(matching the returns geography), Oglala Lakota under its current 46102
code, and Bedford already merged — the same harmonized world as the master
panel. A newer vintage would reintroduce the CT planning-region mismatch.
"""

from pathlib import Path
from typing import Any

import shapefile


def _round_coords(value: Any) -> Any:
    """Recursively round coordinate tuples to 5 decimals (~1.1 m of
    longitude). The source file is generalized to 1:500k, so the digits
    beyond that are pure noise — and roughly half the serialized bytes
    of the real layer (28 MB before rounding)."""
    if isinstance(value, float):
        return round(value, 5)
    if isinstance(value, (tuple, list)):
        return tuple(_round_coords(v) for v in value)
    return value


def county_shapefile_to_geojson(shp_path: str | Path) -> dict[str, Any]:
    """Convert a Census county boundary shapefile to a FeatureCollection.

    Feature id is the county GEOID — the 5-character FIPS every panel joins
    on. NAME is the only property carried; metrics belong to the map layer,
    and the rest of the Census fields (areas, LSAD codes) are dead weight in
    a file the browser downloads.
    """
    features = []
    with shapefile.Reader(str(shp_path)) as reader:
        for shape_record in reader.iterShapeRecords():
            record = shape_record.record.as_dict()
            geometry = dict(shape_record.shape.__geo_interface__)
            geometry["coordinates"] = _round_coords(geometry["coordinates"])
            features.append(
                {
                    "type": "Feature",
                    "id": record["GEOID"],
                    "properties": {"NAME": record["NAME"]},
                    "geometry": geometry,
                }
            )
    return {"type": "FeatureCollection", "features": features}
