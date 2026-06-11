"""Ingest Census cartographic boundary shapefiles into county GeoJSON.

The cb_2021 vintage is deliberate: it carries Connecticut's old counties
(matching the returns geography), Oglala Lakota under its current 46102
code, and Bedford already merged — the same harmonized world as the master
panel. A newer vintage would reintroduce the CT planning-region mismatch.
"""

from pathlib import Path
from typing import Any

import shapefile


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
            features.append(
                {
                    "type": "Feature",
                    "id": record["GEOID"],
                    "properties": {"NAME": record["NAME"]},
                    "geometry": shape_record.shape.__geo_interface__,
                }
            )
    return {"type": "FeatureCollection", "features": features}
