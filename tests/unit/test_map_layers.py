"""Tests for the map layer builder — master panel slices onto county geometry.

The output is a GeoJSON FeatureCollection ready for Mapbox GL: one feature
per county, geometry from the Census cartographic boundary file, properties
carrying the metrics the map colors and the popups display.

This is the producer/consumer seam where GFIP's Bug #1 lived (model output
vs map layer column contract) — which is why the property names are spelled
out literally here, before the implementation exists.
"""

import pandas as pd
import pytest

from geofluid.map.layers import build_map_layer, export_year_metrics


def _panel(rows: list[dict[str, object]]) -> pd.DataFrame:
    defaults: dict[str, object] = {
        "fips": "29189",
        "year": 2024,
        "dem_votes": 300,
        "rep_votes": 200,
        "other_votes": 10,
        "total_votes": 510,
        "dem_share_2p": 0.6,
        "swing_dem_2p": 0.05,
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


def test_counties_without_panel_data_keep_geometry_and_flag_no_data() -> None:
    """Alaska's boroughs (excluded from the panel by policy) and any future
    no-data geography must still RENDER — a hole in the map reads as a bug to
    every user. Such features keep their geometry and get has_data=False;
    data-bearing features get has_data=True so the frontend styles on one
    flag instead of probing for missing properties."""
    layer = build_map_layer(_panel([{}]), _geojson(["29189", "02016"]), year=2024)

    by_id = {f["id"]: f for f in layer["features"]}
    assert set(by_id) == {"29189", "02016"}
    assert by_id["29189"]["properties"]["has_data"] is True
    assert by_id["02016"]["properties"]["has_data"] is False
    assert by_id["02016"]["geometry"]["type"] == "Polygon"
    assert "dem_share_2p" not in by_id["02016"]["properties"]


def test_panel_county_missing_from_geometry_fails_loudly() -> None:
    """A panel county absent from the boundary file is votes that silently
    never render — the inverse of the Alaska case and NOT a policy. The build
    must raise naming the FIPS (this is what would have caught a wrong-vintage
    boundary file, e.g. 2023 boundaries lacking Connecticut's old counties)."""
    with pytest.raises(ValueError, match=r"09001") as excinfo:
        build_map_layer(
            _panel([{}, {"fips": "09001"}]),
            _geojson(["29189"]),
            year=2024,
        )

    assert "geometry" in str(excinfo.value)


def test_layer_round_trips_through_json() -> None:
    """The layer's destination is a static .json file fetched by a browser.
    numpy scalars (int64/float64 from the pandas panel) are the classic
    json.dumps failure. The contract: dumps succeeds and the parsed result
    equals the layer — values are native Python numbers, not stringified
    stand-ins."""
    import json

    layer = build_map_layer(_panel([{}]), _geojson(["29189", "02016"]), year=2024)

    parsed = json.loads(json.dumps(layer))

    assert parsed == layer
    assert isinstance(parsed["features"][0]["properties"]["total_votes"], int)
    assert isinstance(parsed["features"][0]["properties"]["dem_share_2p"], float)


def test_year_metrics_export_is_keyed_by_fips_with_metric_names() -> None:
    """The frontend's per-year data contract: geometry ships once, metrics
    ship per year as {fips: {metric: value}} joined client-side. Same literal
    property names as the combined layer — one frontend contract, not two."""
    metrics = export_year_metrics(_panel([{}, {"fips": "01001", "dem_share_2p": 0.3}]), year=2024)

    assert set(metrics) == {"29189", "01001"}
    m = metrics["29189"]
    assert m["dem_share_2p"] == 0.6
    assert m["swing_dem_2p"] == 0.05
    assert m["total_votes"] == 510
    assert m["median_age"] == 41.1
    assert m["pct_bachelors_plus"] == 0.45
    assert "year" not in m  # the year is the filename's job, not 3,000 copies


def test_year_metrics_nan_becomes_null_for_browser_strict_json() -> None:
    """Two real counties carry NaN demographics (ACS sentinels). Python's
    json module happily WRITES literal NaN — and browser JSON.parse rejects
    it, killing the entire metrics file for one county's missing income.
    NaN must export as None (-> null), provable via allow_nan=False."""
    import json

    metrics = export_year_metrics(_panel([{"median_hh_income": float("nan")}]), year=2024)

    assert metrics["29189"]["median_hh_income"] is None
    json.dumps(metrics, allow_nan=False)  # raises if any NaN survived
