"""Tests for the master panel — returns joined with demographics per county.

This is the join layer. The two ingest panels are faithful to their sources;
every geography reconciliation between them is decided HERE, explicitly,
with a test per decision. The work list came from the real-data acceptance
run of 2026-06-11 (Alaska districts, the Shannon/Oglala Lakota rename, state
unallocated-vote buckets, Connecticut's planning regions).

Join policy specified by these tests:
- left join on the returns panel (counties that vote drive the panel);
  demographics-only geographies (Puerto Rico, Kalawao) simply don't appear
- known non-joinable geographies are excluded, each for a documented reason
- ANY other county missing demographics fails loudly — silent NaN demographics
  would corrupt every downstream model fit
"""

import pandas as pd

from geofluid.panel.master import build_master_panel

# The master panel schema: returns columns, then the demographics vintage and
# value columns. "year" is the ELECTION year; "acs_vintage" is the survey year
# of the demographic context — they must never share a column name.
MASTER_COLUMNS = [
    "fips",
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


def _returns(rows: list[dict[str, object]]) -> pd.DataFrame:
    defaults: dict[str, object] = {
        "fips": "29189",
        "year": 2024,
        "dem_votes": 300,
        "rep_votes": 200,
        "other_votes": 10,
        "total_votes": 510,
        "dem_share_2p": 0.6,
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def _demographics(rows: list[dict[str, object]]) -> pd.DataFrame:
    defaults: dict[str, object] = {
        "fips": "29189",
        "year": 2023,
        "total_population": 990000,
        "median_age": 41.1,
        "pct_65_plus": 0.19,
        "median_hh_income": 81000,
        "median_home_value": 230000,
        "pct_owner_occupied": 0.71,
        "pct_bachelors_plus": 0.45,
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def test_county_year_row_gains_its_demographics() -> None:
    """The core join: a returns county-year row carries its county's
    demographic context. The demographics panel's "year" becomes
    "acs_vintage" — the election year and the survey vintage are different
    facts and must never collide in one column."""
    panel = build_master_panel(_returns([{}]), _demographics([{}]))

    assert list(panel.columns) == MASTER_COLUMNS
    assert len(panel) == 1
    row = panel.iloc[0]
    assert row["fips"] == "29189"
    assert row["year"] == 2024
    assert row["dem_share_2p"] == 0.6
    assert row["acs_vintage"] == 2023
    assert abs(row["median_age"] - 41.1) < 1e-9
    assert abs(row["pct_bachelors_plus"] - 0.45) < 1e-9
