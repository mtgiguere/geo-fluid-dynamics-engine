"""Tests for the ZIP-to-county lookup.

Solar installs (and much other non-election data) are located by ZIP code,
while the engine's map, adjacency and "roads" (commuting, migration) are
counties. The bridge is the Census 2020 ZCTA-to-county relationship file
(`tab20_zcta520_county20_natl.txt`, pipe-delimited): one row per piece of a
ZIP Code Tabulation Area that falls inside a county, with that piece's land
area (AREALAND_PART). The output is one row per ZIP with the single county it
is assigned to. This file is the contract for that lookup.
"""

import pandas as pd

from geofluid.ingest.zcta_county import zip_to_county

LOOKUP_COLUMNS = ["zip5", "fips"]


def _rel_rows(rows: list[dict[str, object]]) -> pd.DataFrame:
    """Build a raw relationship-file frame (all text, as read with dtype=str)."""
    defaults: dict[str, object] = {
        "GEOID_ZCTA5_20": "63101",
        "GEOID_COUNTY_20": "29510",
        "NAMELSAD_COUNTY_20": "St. Louis city",
        "AREALAND_PART": "1000",
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def test_a_zip_inside_one_county_maps_to_that_county() -> None:
    """The simple case: ZCTA 63101 lies wholly inside St. Louis city (29510),
    so the lookup has one row, 63101 -> 29510, with the canonical columns."""
    lookup = zip_to_county(_rel_rows([{}]))

    assert list(lookup.columns) == LOOKUP_COLUMNS
    assert lookup.to_dict("records") == [{"zip5": "63101", "fips": "29510"}]


def test_a_zip_crossing_a_county_line_goes_to_the_county_with_most_of_its_land() -> None:
    """About 10,000 of the 33,791 ZIP areas cross a county line. Each is
    assigned whole to the county holding the largest share of its LAND
    (AREALAND_PART). ZCTA 63017 here has 900 square metres of land in St.
    Louis County (29189) and 7,000 in St. Charles County (29183): 7,000 > 900,
    so 63017 -> 29183. One row per ZIP, never one per piece. The file is read
    as text, and as text "900" sorts above "7000", so land area must be
    compared as a number or the wrong county wins."""
    rel = _rel_rows(
        [
            {"GEOID_ZCTA5_20": "63017", "GEOID_COUNTY_20": "29189", "AREALAND_PART": "900"},
            {"GEOID_ZCTA5_20": "63017", "GEOID_COUNTY_20": "29183", "AREALAND_PART": "7000"},
        ]
    )

    lookup = zip_to_county(rel)

    assert lookup.to_dict("records") == [{"zip5": "63017", "fips": "29183"}]


def test_county_land_outside_every_zip_area_is_not_a_zip() -> None:
    """Real-data quirk: the file's first rows have a blank GEOID_ZCTA5_20
    (Baldwin County AL, 339,765,765 square metres of land that lie in no
    ZIP Code Tabulation Area). Such a row says nothing about any ZIP. It is
    dropped, not kept as a ZIP that is missing (NaN), which would otherwise
    "win" a county if its land was large. One real ZIP in, one row out."""
    rel = _rel_rows(
        [
            {"GEOID_ZCTA5_20": None, "GEOID_COUNTY_20": "01003", "AREALAND_PART": "339765765"},
            {},
        ]
    )

    lookup = zip_to_county(rel)

    assert lookup.to_dict("records") == [{"zip5": "63101", "fips": "29510"}]
