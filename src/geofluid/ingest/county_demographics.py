"""Ingest Census ACS county profiles into the canonical demographics panel.

The raw input is the Census Bureau API response for ACS 5-year detailed
tables: a header row of variable names followed by data rows of strings,
with geography columns "state" and "county" at the end. ACS detailed-table
variable IDs (B-tables) are stable across vintages, which is why they are
used here instead of the friendlier DP profile tables — DP variable numbers
shift from year to year and would silently break multi-vintage time series.

Like the returns ingest, this module exposes one public function whose output
satisfies the contract in tests/unit/test_county_demographics.py.
"""

import pandas as pd

# Variables that pass straight through to a canonical column (renamed).
_SIMPLE_VARS = {
    "B01003_001E": "total_population",
    "B01002_001E": "median_age",
    "B19013_001E": "median_hh_income",
    "B25077_001E": "median_home_value",
}

# Sex-by-age cells (table B01001) covering ages 65 and over: male 65-66
# through 85+ are cells 020-025, female are 044-049. Their sum over total
# population is the seniors share — one of the strongest county-level
# predictors of both turnout and partisan lean.
_AGE_CELLS_65_PLUS = [f"B01001_{i:03d}E" for i in [*range(20, 26), *range(44, 50)]]

# The canonical demographics schema, in order. Percentages are fractions in
# [0, 1], consistent with dem_share_2p in the returns panel.
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


# ACS annotation sentinels: in-band negative codes meaning "estimate not
# available" (insufficient sample, suppressed, not applicable). Documented at
# census.gov under "Notes on ACS Estimate and Annotation Values". Left as
# numbers they would silently destroy every mean, choropleth scale, and model
# fit downstream — they must become NaN at ingest.
_ACS_SENTINELS = [
    -111111111,
    -222222222,
    -333333333,
    -555555555,
    -666666666,
    -888888888,
    -999999999,
]


def _numeric(raw: "pd.Series[str]") -> "pd.Series[float]":
    """String ACS values -> numbers, with annotation sentinels as NaN."""
    values = pd.to_numeric(raw)
    return values.mask(values.isin(_ACS_SENTINELS))


def load_county_demographics(payload: list[list[str | None]], year: int) -> pd.DataFrame:
    """Transform a raw Census API county response into the demographics panel."""
    header, *rows = payload
    df = pd.DataFrame(rows, columns=header)

    out = pd.DataFrame()
    # The county FIPS join key: 2-digit state + 3-digit county, matching the
    # zero-padded 5-character key of the returns panel.
    out["fips"] = df["state"] + df["county"]
    # ACS payloads do not carry their vintage; the caller supplies it.
    out["year"] = year
    for var, name in _SIMPLE_VARS.items():
        out[name] = _numeric(df[var])
    seniors = sum(_numeric(df[cell]) for cell in _AGE_CELLS_65_PLUS)
    out["pct_65_plus"] = seniors / out["total_population"]
    # Housing tenure (table B25003): owner-occupied units over all OCCUPIED
    # units — the denominator is households, not population.
    out["pct_owner_occupied"] = _numeric(df["B25003_002E"]) / _numeric(df["B25003_001E"])
    # Educational attainment (table B15003): bachelor's, master's,
    # professional, and doctorate over the table's own universe — population
    # 25 and over. This is the variable whose quiet rise to dominance the
    # 2016 models missed (see spec, Module 4); its denominator must be the
    # adult universe, not total population.
    degrees = sum(_numeric(df[f"B15003_{i:03d}E"]) for i in range(22, 26))
    out["pct_bachelors_plus"] = degrees / _numeric(df["B15003_001E"])
    # API row order is an implementation detail; the panel is fips-ordered so
    # joins and diffs against the returns panel are deterministic.
    return out.loc[:, DEMOGRAPHICS_COLUMNS].sort_values("fips", ignore_index=True)
