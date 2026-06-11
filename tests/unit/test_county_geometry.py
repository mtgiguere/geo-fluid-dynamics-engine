"""Tests for the county geometry ingest — Census boundary shapefile to GeoJSON.

The raw input is a Census cartographic boundary shapefile (cb_2021_us_county_500k).
The output is the FeatureCollection consumed by build_map_layer: feature id is
the 5-character county GEOID (our universal join key), properties carry the
county name, geometry is the polygon.

The fixture writes a real two-county shapefile to disk and converts it —
no mocks; the test exercises the actual format round-trip.
"""

from pathlib import Path

import shapefile

from geofluid.ingest.county_geometry import county_shapefile_to_geojson


def _write_shapefile(path: Path) -> None:
    with shapefile.Writer(str(path)) as w:
        w.field("GEOID", "C", size=5)
        w.field("NAME", "C", size=100)
        w.field("ALAND", "N", size=14)  # extra Census field the output must not carry
        w.poly([[(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]])
        w.record(GEOID="29189", NAME="St. Louis", ALAND=1318781340)
        w.poly([[(2.0, 2.0), (2.0, 3.0), (3.0, 3.0), (3.0, 2.0), (2.0, 2.0)]])
        w.record(GEOID="01001", NAME="Autauga", ALAND=1539634184)


def test_shapefile_converts_to_feature_collection_keyed_by_geoid(tmp_path: Path) -> None:
    """Each shape becomes a Feature whose id is the county GEOID — the same
    5-character FIPS every panel joins on — with NAME as the only property
    (metrics are the map layer's job, not the geometry's) and the polygon
    as GeoJSON geometry."""
    shp = tmp_path / "counties"
    _write_shapefile(shp)

    fc = county_shapefile_to_geojson(shp.with_suffix(".shp"))

    assert fc["type"] == "FeatureCollection"
    by_id = {f["id"]: f for f in fc["features"]}
    assert set(by_id) == {"29189", "01001"}
    stl = by_id["29189"]
    assert stl["type"] == "Feature"
    assert stl["properties"] == {"NAME": "St. Louis"}
    assert stl["geometry"]["type"] == "Polygon"
    assert stl["geometry"]["coordinates"][0][0] == (0.0, 0.0)


def test_coordinates_round_to_five_decimals(tmp_path: Path) -> None:
    """The boundary file ships full double-precision coordinates; serialized,
    that made the real 2024 layer 28 MB — most of it digits that are pure
    noise at the file's own 1:500k generalization. Five decimals is ~1.1 m
    of longitude: far beyond map precision, roughly half the bytes."""
    shp = tmp_path / "one"
    with shapefile.Writer(str(shp)) as w:
        w.field("GEOID", "C", size=5)
        w.field("NAME", "C", size=100)
        w.poly(
            [
                [
                    (-90.123456789, 38.987654321),
                    (-90.1, 39.0),
                    (-90.2, 38.9),
                    (-90.123456789, 38.987654321),
                ]
            ]
        )
        w.record(GEOID="29189", NAME="St. Louis")

    fc = county_shapefile_to_geojson(shp.with_suffix(".shp"))

    ring = fc["features"][0]["geometry"]["coordinates"][0]
    assert ring[0] == (-90.12346, 38.98765)
