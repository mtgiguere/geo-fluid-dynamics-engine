"""Tests for the county-returns ingest — the canonical county-year panel.

The raw input format is the MIT Election Data + Science Lab county presidential
returns file (`countypres_2000-2020.csv`): one row per (year, county, candidate,
vote mode), with columns including year, state, county_fips, party, and
candidatevotes.

The canonical output is one row per (fips, year). It is the panel that every
downstream consumer — the descriptive map, the wave replay, the diffusion models —
reads. This file is the contract for that panel: column names, dtypes, and
semantics are specified here, in tests, before any implementation exists
(see TDD_CONTRACT.md, Bug #1 — column-name drift between producer and consumer).
"""

import pandas as pd

from geofluid.ingest.county_returns import load_county_returns

# The canonical panel schema. Deliberately written out literally here rather than
# imported from the implementation — a test that imports the constant it checks
# can never catch the constant changing.
PANEL_COLUMNS = [
    "fips",
    "year",
    "dem_votes",
    "rep_votes",
    "other_votes",
    "total_votes",
    "dem_share_2p",
]


def _raw_rows(rows: list[dict[str, object]]) -> pd.DataFrame:
    """Build a raw MIT-format returns frame from compact row overrides."""
    defaults: dict[str, object] = {
        "year": 2020,
        "state": "MISSOURI",
        "state_po": "MO",
        "county_name": "ST LOUIS",
        "county_fips": "29189",
        "office": "US PRESIDENT",
        "candidate": "CANDIDATE",
        "party": "DEMOCRAT",
        "candidatevotes": 0,
        "totalvotes": 0,
        "mode": "TOTAL",
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def test_single_county_year_produces_one_panel_row_with_two_party_share() -> None:
    """Specifies the core panel contract: one row per county-year; votes
    aggregated into dem/rep/other blocs; total_votes counts every ballot cast
    for any candidate; dem_share_2p is the TWO-PARTY share — third parties are
    in the total but excluded from the share denominator. 300 D / 100 R / 50 L
    must yield dem_share_2p = 300 / 400 = 0.75, not 300 / 450.
    """
    raw = _raw_rows(
        [
            {"party": "DEMOCRAT", "candidatevotes": 300},
            {"party": "REPUBLICAN", "candidatevotes": 100},
            {"party": "LIBERTARIAN", "candidatevotes": 50},
        ]
    )

    panel = load_county_returns(raw)

    assert list(panel.columns) == PANEL_COLUMNS
    assert len(panel) == 1
    row = panel.iloc[0]
    assert row["fips"] == "29189"
    assert row["year"] == 2020
    assert row["dem_votes"] == 300
    assert row["rep_votes"] == 100
    assert row["other_votes"] == 50
    assert row["total_votes"] == 450
    assert abs(row["dem_share_2p"] - 0.75) < 1e-9


def test_fips_is_zero_padded_five_char_string_from_numeric_input() -> None:
    """The raw file stores county_fips as a number (1001.0 for Autauga, AL)
    because missing values elsewhere force the column to float dtype. The panel
    fips must be the canonical 5-character zero-padded string ("01001") — it is
    the join key for every geometry and demographic dataset downstream, and a
    "1001.0"/"01001" mismatch would silently drop the join."""
    raw = _raw_rows(
        [
            {
                "county_fips": 1001.0,
                "state": "ALABAMA",
                "county_name": "AUTAUGA",
                "party": "REPUBLICAN",
                "candidatevotes": 7,
            }
        ]
    )

    panel = load_county_returns(raw)

    assert panel.iloc[0]["fips"] == "01001"


def test_rows_without_county_fips_are_excluded() -> None:
    """The raw file contains rows that are not counties — statewide "FEDERAL
    PRECINCT" rows for overseas absentee ballots have no county_fips. A county
    panel cannot represent them, so they are excluded. The alternative
    failure modes are both worse: crashing on NaN, or fabricating a FIPS that
    would join against nothing."""
    raw = _raw_rows(
        [
            {"county_fips": 29189.0, "party": "DEMOCRAT", "candidatevotes": 10},
            {
                "county_fips": float("nan"),
                "county_name": "FEDERAL PRECINCT",
                "state": "CONNECTICUT",
                "party": "DEMOCRAT",
                "candidatevotes": 5,
            },
        ]
    )

    panel = load_county_returns(raw)

    assert list(panel["fips"]) == ["29189"]
