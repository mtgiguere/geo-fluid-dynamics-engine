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
import pytest

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


def test_swing_is_change_in_two_party_share_since_previous_election() -> None:
    """Specifies the wave quantity: swing_dem_2p is this election's two-party
    share minus the SAME county's share in the immediately preceding election.
    A county going 0.40 -> 0.55 swung +0.15 toward the Democrats. The first
    election a county appears in has no previous share: swing is missing
    (NaN), never zero — zero means "no movement", which is a real claim."""
    panel = build_master_panel(
        _returns(
            [
                {"year": 2016, "dem_votes": 400, "rep_votes": 600, "dem_share_2p": 0.4},
                {"year": 2020, "dem_votes": 550, "rep_votes": 450, "dem_share_2p": 0.55},
            ]
        ),
        _demographics([{}]),
    )

    by_year = panel.set_index("year")
    assert pd.isna(by_year.loc[2016, "swing_dem_2p"])
    assert abs(by_year.loc[2020, "swing_dem_2p"] - 0.15) < 1e-9


def test_shannon_county_old_fips_harmonizes_to_oglala_lakota() -> None:
    """Shannon County SD was renamed Oglala Lakota County in 2015 (46113 ->
    46102). The MIT returns file is internally inconsistent: it uses the OLD
    code in 2000-2012 and again in 2024, the new code in 2016/2020. Without
    harmonization the county's time series fractures into two phantom
    counties, each missing demographics half the time. All 46113 rows become
    46102 in the master panel."""
    panel = build_master_panel(
        _returns([{"fips": "46113", "year": 2024}]),
        _demographics([{"fips": "46102", "median_age": 26.4}]),
    )

    assert list(panel["fips"]) == ["46102"]
    assert abs(panel.iloc[0]["median_age"] - 26.4) < 1e-9


def test_alaska_districts_and_state_buckets_are_excluded() -> None:
    """Two geographies can never join and are excluded by policy, not error:

    Alaska (02xxx) reports elections by legislative district while every
    demographic dataset uses boroughs — no county-level crosswalk exists, so
    Alaska is analyzed statewide, never at "county" level.

    State-level buckets (FIPS XX000, e.g. New York's 36000 holding 124,288
    unallocated 2024 absentee votes) are real votes but map to no county.

    Both exclusions are silent BY DOCUMENTED POLICY — unlike any other
    unmatched county, which must fail loudly (next test)."""
    panel = build_master_panel(
        _returns(
            [
                {"fips": "02010", "year": 2024},
                {"fips": "36000", "year": 2024},
                {"fips": "29189", "year": 2024},
            ]
        ),
        _demographics([{}]),
    )

    assert list(panel["fips"]) == ["29189"]


def test_unexplained_missing_demographics_fails_loudly_naming_the_counties() -> None:
    """Any county outside the documented exclusions that lacks demographics
    is a data defect, not a policy: a left join would hand every downstream
    model NaN covariates that pandas happily propagates. The build must raise
    and NAME the offending counties, so the failure is diagnosable from the
    message alone. (Connecticut 2024 against an ACS vintage >= 2022 trips
    this by design — resolving CT is the caller's explicit decision.)"""
    with pytest.raises(ValueError, match=r"09001.*09003") as excinfo:
        build_master_panel(
            _returns(
                [
                    {"fips": "09001", "year": 2024},
                    {"fips": "09003", "year": 2024},
                    {"fips": "29189", "year": 2024},
                ]
            ),
            _demographics([{}]),
        )

    assert "demographics" in str(excinfo.value)


def test_panel_is_sorted_by_fips_then_year_after_recoding() -> None:
    """The recode (46113 -> 46102) changes a county's sort position: a panel
    that inherits the returns frame's order is no longer FIPS-ordered after
    harmonization. The master panel must re-sort so downstream serialization
    and diffs stay deterministic. Expected order written out explicitly."""
    panel = build_master_panel(
        _returns(
            [
                {"fips": "46103", "year": 2020},
                {"fips": "46113", "year": 2024},  # recodes to 46102 — sorts FIRST
            ]
        ),
        _demographics([{"fips": "46103"}, {"fips": "46102"}]),
    )

    assert list(zip(panel["fips"], panel["year"], strict=True)) == [
        ("46102", 2024),
        ("46103", 2020),
    ]


def test_merged_jurisdiction_votes_aggregate_into_absorbing_county() -> None:
    """Found by the fail-fast in the real master panel build: Bedford City VA
    (51515) was an independent city with real votes 2000-2012, then merged
    into Bedford County (51019) in 2013. Harmonizing to current geography
    means its votes JOIN the county's votes — the recode must aggregate the
    two rows into one, recomputing the two-party share, never emit duplicate
    (fips, year) rows."""
    panel = build_master_panel(
        _returns(
            [
                {
                    "fips": "51515",
                    "year": 2000,
                    "dem_votes": 1000,
                    "rep_votes": 2000,
                    "other_votes": 100,
                    "total_votes": 3100,
                    "dem_share_2p": 1000 / 3000,
                },
                {
                    "fips": "51019",
                    "year": 2000,
                    "dem_votes": 4000,
                    "rep_votes": 8000,
                    "other_votes": 200,
                    "total_votes": 12200,
                    "dem_share_2p": 4000 / 12000,
                },
            ]
        ),
        _demographics([{"fips": "51019"}]),
    )

    assert len(panel) == 1
    row = panel.iloc[0]
    assert row["fips"] == "51019"
    assert row["dem_votes"] == 5000
    assert row["rep_votes"] == 10000
    assert row["other_votes"] == 300
    assert row["total_votes"] == 15300
    assert abs(row["dem_share_2p"] - 5000 / 15000) < 1e-9


def test_demographics_only_geographies_do_not_appear() -> None:
    """ACS covers geographies that cast no presidential vote — Puerto Rico's
    78 municipios, Kalawao's 43 residents folded into Maui's returns. They
    must not appear as vote-less rows in the master panel; the returns side
    drives membership."""
    panel = build_master_panel(
        _returns([{}]),
        _demographics([{}, {"fips": "72031"}, {"fips": "15005"}]),
    )

    assert list(panel["fips"]) == ["29189"]
