"""Build GeoJSON map layers from master panel slices.

The producer/consumer seam between the analysis panels and the Mapbox
frontend. Property names are the frontend's contract, specified in
tests/unit/test_map_layers.py before this implementation existed.
"""

from typing import Any

import pandas as pd

# Panel columns carried into feature properties for coloring and popups.
_METRIC_COLUMNS = [
    "year",
    "dem_votes",
    "rep_votes",
    "other_votes",
    "total_votes",
    "dem_share_2p",
    "acs_vintage",
    "total_population",
    "median_age",
    "pct_65_plus",
    "median_hh_income",
    "median_home_value",
    "pct_owner_occupied",
    "pct_bachelors_plus",
]


def build_map_layer(
    panel: pd.DataFrame, county_geojson: dict[str, Any], year: int
) -> dict[str, Any]:
    """One feature per county: geometry from the boundary file, properties
    from the master panel's rows for the requested election year."""
    sliced = panel[panel["year"] == year]
    by_fips: dict[str, dict[str, Any]] = {
        str(row["fips"]): {col: row[col] for col in _METRIC_COLUMNS}
        for row in sliced.to_dict("records")
    }

    features = []
    for feature in county_geojson["features"]:
        out = dict(feature)
        out["properties"] = {**feature["properties"], **by_fips[str(feature["id"])]}
        features.append(out)
    return {"type": "FeatureCollection", "features": features}
