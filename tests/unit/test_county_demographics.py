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

import pandas as pd

from geofluid.ingest.county_demographics import acs5_county_url, load_county_demographics

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
    header: list[str | None] = list(defaults)
    return [header, *[[{**defaults, **row}[str(k)] for k in header] for row in rows]]


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


def test_pct_65_plus_is_sum_of_senior_age_cells_over_total_population() -> None:
    """Specifies the seniors share: the twelve B01001 sex-by-age cells for 65+
    (male and female: 65-66, 67-69, 70-74, 75-79, 80-84, 85+) summed and
    divided by total population, as a fraction. 12 cells of 1,000 in a county
    of 120,000 people is exactly 0.10."""
    payload = _payload([{"B01003_001E": "120000"}])

    df = load_county_demographics(payload, year=2023)

    assert abs(df.iloc[0]["pct_65_plus"] - 0.10) < 1e-9


def test_pct_owner_occupied_is_owner_units_over_occupied_units() -> None:
    """Specifies the housing-tenure share: owner-occupied units (B25003_002)
    over ALL occupied units (B25003_001) — the denominator is households, not
    population. 280,000 of 400,000 occupied units is exactly 0.70."""
    payload = _payload([{}])

    df = load_county_demographics(payload, year=2023)

    assert abs(df.iloc[0]["pct_owner_occupied"] - 0.70) < 1e-9


def test_pct_bachelors_plus_sums_four_degree_cells_over_adults_25_plus() -> None:
    """Specifies the education share: bachelor's + master's + professional +
    doctorate (B15003 cells 022-025) over the population 25 and over
    (B15003_001) — the table's own universe, NOT total population. The 2016
    lesson in the project spec is exactly this variable; getting its
    denominator wrong would distort the engine's most important covariate.
    (140,000 + 56,000 + 14,000 + 7,000) / 700,000 = 0.31."""
    payload = _payload([{}])

    df = load_county_demographics(payload, year=2023)

    assert abs(df.iloc[0]["pct_bachelors_plus"] - 0.31) < 1e-9


def test_panel_columns_match_canonical_schema_in_order() -> None:
    """The full demographics contract: exactly these columns, in this order.
    Downstream code (map layers, model feature matrices) may select by
    position when serializing — schema order is part of the contract, exactly
    as with the returns panel."""
    payload = _payload([{}])

    df = load_county_demographics(payload, year=2023)

    assert list(df.columns) == DEMOGRAPHICS_COLUMNS


def test_acs_sentinel_values_become_nan_not_numbers() -> None:
    """ACS encodes "median cannot be computed" (insufficient sample, e.g.
    Kalawao County's ~80 residents) as the in-band sentinel -666666666.
    Treated as a number it would silently destroy every mean, scale, and
    model fit downstream. Sentinels must come out as NaN — and NaN must not
    infect the county's other, valid columns."""
    payload = _payload([{"B25077_001E": "-666666666", "B19013_001E": "-666666666"}])

    df = load_county_demographics(payload, year=2023)

    row = df.iloc[0]
    assert pd.isna(row["median_home_value"])
    assert pd.isna(row["median_hh_income"])
    assert abs(row["median_age"] - 41.1) < 1e-9  # valid columns untouched


def test_panel_is_sorted_by_fips_regardless_of_payload_order() -> None:
    """Census API row order is an implementation detail of the API. The panel
    must come out in fips order so joins and diffs against the returns panel
    are deterministic."""
    payload = _payload(
        [
            {"state": "29", "county": "510"},
            {"state": "01", "county": "001"},
            {"state": "29", "county": "189"},
        ]
    )

    df = load_county_demographics(payload, year=2023)

    assert list(df["fips"]) == ["01001", "29189", "29510"]


def test_null_payload_values_become_nan() -> None:
    """The API returns JSON null for some county-variable combinations.
    Nulls must become NaN in numeric columns, not crash the parse and not
    infect other columns."""
    payload = _payload([{"B19013_001E": None}])

    df = load_county_demographics(payload, year=2023)

    row = df.iloc[0]
    assert pd.isna(row["median_hh_income"])
    assert row["total_population"] == 990414


def test_acs5_county_url_requests_every_needed_variable_for_all_counties() -> None:
    """The fetch URL is part of the ingest contract: every variable the
    transform consumes must be requested, for every county, at the requested
    vintage, with the API key (mandatory for all Census API requests since
    2025 — confirmed live: keyless requests return an HTML "Missing Key"
    page with HTTP 200). Spelled out literally so a silently dropped
    variable cannot hide behind a constant shared with the implementation."""
    url = acs5_county_url(2023, api_key="TESTKEY123")

    assert url == (
        "https://api.census.gov/data/2023/acs/acs5"
        "?get=NAME,B01003_001E,B01002_001E,B19013_001E,B25077_001E,"
        "B01001_020E,B01001_021E,B01001_022E,B01001_023E,B01001_024E,B01001_025E,"
        "B01001_044E,B01001_045E,B01001_046E,B01001_047E,B01001_048E,B01001_049E,"
        "B25003_001E,B25003_002E,"
        "B15003_001E,B15003_022E,B15003_023E,B15003_024E,B15003_025E"
        "&for=county:*&key=TESTKEY123"
    )
