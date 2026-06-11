"""Tests for the county-demographics ingest — the ACS county profile panel.

The raw input is the U.S. Census Bureau API response format for ACS 5-year
detailed tables (api.census.gov/data/{year}/acs/acs5): a JSON array whose
first element is a header row of variable names and whose remaining elements
are data rows of strings (or null), ending with the geography columns
"state" and "county".

The canonical output is one row per county with human-readable column names —
the demographic covariates the descriptive map displays and the predictive
modules consume. As with the returns panel, this file is the contract:
schema and semantics are specified here before any implementation exists.
"""

from geofluid.ingest.county_demographics import load_county_demographics

# The canonical demographics schema, written out literally (a test that
# imports the constant it checks can never catch the constant changing).
# Percentages are fractions in [0, 1], consistent with dem_share_2p.
DEMOGRAPHICS_COLUMNS = [
    "fips",
    "year",
    "total_population",
    "median_age",
    "pct_65_plus",
    "median_hh_income",
    "median_home_value",
    "pct_owner_occupied",
    "pct_bachelors_plus",
]

# Sex-by-age cells (table B01001) for the 65-and-over population:
# male 65-66 ... 85+ are cells 020-025, female 65-66 ... 85+ are 044-049.
_AGE_CELLS_65_PLUS = [f"B01001_{i:03d}E" for i in [*range(20, 26), *range(44, 50)]]


def _payload(rows: list[dict[str, str | None]]) -> list[list[str | None]]:
    """Build a raw Census-API-shaped payload (header + string rows) from
    compact per-county overrides."""
    defaults: dict[str, str | None] = {
        "NAME": "St. Louis County, Missouri",
        "B01003_001E": "990414",  # total population
        "B01002_001E": "41.1",  # median age
        "B19013_001E": "75000",  # median household income
        "B25077_001E": "230000",  # median home value
        # 65+ sex-by-age cells: 12 cells of 1000 -> 12,000 people 65+
        **dict.fromkeys(_AGE_CELLS_65_PLUS, "1000"),
        "B25003_001E": "400000",  # occupied housing units
        "B25003_002E": "280000",  # ... of which owner-occupied
        "B15003_001E": "700000",  # population 25 and over
        "B15003_022E": "140000",  # bachelor's
        "B15003_023E": "56000",  # master's
        "B15003_024E": "14000",  # professional degree
        "B15003_025E": "7000",  # doctorate
        "state": "29",
        "county": "189",
    }
    header = list(defaults)
    return [header, *[[{**defaults, **row}[k] for k in header] for row in rows]]


def test_single_county_payload_yields_fips_and_numeric_simple_columns() -> None:
    """Specifies the geography key and the pass-through variables: fips is the
    5-character state+county concatenation, year is the ACS vintage passed by
    the caller (the payload itself does not carry it), and the simple ACS
    variables arrive as strings but must come out numeric."""
    payload = _payload([{}])

    df = load_county_demographics(payload, year=2023)

    assert len(df) == 1
    row = df.iloc[0]
    assert row["fips"] == "29189"
    assert row["year"] == 2023
    assert row["total_population"] == 990414
    assert abs(row["median_age"] - 41.1) < 1e-9
    assert row["median_hh_income"] == 75000
    assert row["median_home_value"] == 230000
