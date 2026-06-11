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
    "swing_dem_2p",
    "acs_vintage",
    "total_population",
    "median_age",
    "pct_65_plus",
    "median_hh_income",
    "median_home_value",
    "pct_owner_occupied",
    "pct_bachelors_plus",
]


def export_year_metrics(panel: pd.DataFrame, year: int) -> dict[str, dict[str, Any]]:
    """The frontend's per-year data product: {fips: {metric: value}}.

    Geometry ships once and is cacheable; these files are small (~300 KB)
    and fetched per year as the user scrubs time. Property names match the
    combined layer — one frontend contract, not two. The year itself is the
    filename's job, not 3,000 redundant copies.
    """
    sliced = panel[panel["year"] == year]
    columns = [c for c in _METRIC_COLUMNS if c != "year"]
    # NaN (ACS sentinel demographics) must become None -> JSON null. Python's
    # json module happily writes literal NaN, which browser JSON.parse rejects
    # — one county's missing income would kill the whole file client-side.
    return {
        str(row["fips"]): {col: None if pd.isna(row[col]) else row[col] for col in columns}
        for row in sliced.to_dict("records")
    }


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
        # Geographies outside the panel (Alaska, by documented policy) still
        # render — a hole in the map reads as a bug. has_data is the single
        # flag the frontend styles on.
        metrics = by_fips.get(str(feature["id"]))
        if metrics is None:
            out["properties"] = {**feature["properties"], "has_data": False}
        else:
            out["properties"] = {**feature["properties"], **metrics, "has_data": True}
        features.append(out)

    # The inverse of the no-data case is NOT a policy: a panel county absent
    # from the boundary file is votes that silently never render. Raise,
    # naming the FIPS — this catches a wrong-vintage boundary file at build
    # time instead of as an invisible hole in production.
    geometry_ids = {str(f["id"]) for f in county_geojson["features"]}
    undrawable = sorted(set(by_fips) - geometry_ids)
    if undrawable:
        raise ValueError(f"Panel counties missing from geometry: {undrawable}")
    return {"type": "FeatureCollection", "features": features}
