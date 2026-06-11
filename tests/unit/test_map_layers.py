"""Tests for the map layer builder — master panel slices onto county geometry.

The output is a GeoJSON FeatureCollection ready for Mapbox GL: one feature
per county, geometry from the Census cartographic boundary file, properties
carrying the metrics the map colors and the popups display.

This is the producer/consumer seam where GFIP's Bug #1 lived (model output
vs map layer column contract) — which is why the property names are spelled
out literally here, before the implementation exists.
"""

import pandas as pd

from geofluid.map.layers import build_map_layer


def _panel(rows: list[dict[str, object]]) -> pd.DataFrame:
    defaults: dict[str, object] = {
        "fips": "29189",
        "year": 2024,
        "dem_votes": 300,
        "rep_votes": 200,
        "other_votes": 10,
        "total_votes": 510,
        "dem_share_2p": 0.6,
        "acs_vintage": 2023,
        "total_population": 990000,
        "median_age": 41.1,
        "pct_65_plus": 0.19,
        "median_hh_income": 81000,
        "median_home_value": 230000,
        "pct_owner_occupied": 0.71,
        "pct_bachelors_plus": 0.45,
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def _geojson(fips_ids: list[str]) -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": f,
                "properties": {"NAME": f"County {f}"},
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 0], [0, 0]]]},
            }
            for f in fips_ids
        ],
    }


def test_features_gain_panel_metrics_for_the_requested_year() -> None:
    """The core layer contract: each feature keeps its id and geometry and
    gains the panel metrics for the requested election year under literal,
    frontend-facing property names. The panel may hold many years; only the
    requested year's values appear."""
    panel = _panel(
        [
            {"year": 2020, "dem_share_2p": 0.55},
            {"year": 2024, "dem_share_2p": 0.6},
        ]
    )

    layer = build_map_layer(panel, _geojson(["29189"]), year=2024)

    assert layer["type"] == "FeatureCollection"
    features = layer["features"]
    assert len(features) == 1
    feature = features[0]
    assert feature["id"] == "29189"
    assert feature["geometry"]["type"] == "Polygon"
    props = feature["properties"]
    assert props["dem_share_2p"] == 0.6
    assert props["total_votes"] == 510
    assert props["total_population"] == 990000
    assert props["median_age"] == 41.1
    assert props["pct_65_plus"] == 0.19
    assert props["median_hh_income"] == 81000
    assert props["median_home_value"] == 230000
    assert props["pct_owner_occupied"] == 0.71
    assert props["pct_bachelors_plus"] == 0.45
    assert props["year"] == 2024
