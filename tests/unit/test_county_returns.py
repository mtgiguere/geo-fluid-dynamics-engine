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


def test_votes_are_summed_across_vote_mode_rows() -> None:
    """From 2020 onward the raw file splits a county's votes across mode rows
    (ELECTION DAY, ABSENTEE, PROVISIONAL, ...). The panel must sum them:
    DEM 100 on election day plus DEM 40 absentee is dem_votes = 140, still in
    a single county-year row."""
    raw = _raw_rows(
        [
            {"party": "DEMOCRAT", "candidatevotes": 100, "mode": "ELECTION DAY"},
            {"party": "DEMOCRAT", "candidatevotes": 40, "mode": "ABSENTEE"},
            {"party": "REPUBLICAN", "candidatevotes": 60, "mode": "ELECTION DAY"},
        ]
    )

    panel = load_county_returns(raw)

    assert len(panel) == 1
    assert panel.iloc[0]["dem_votes"] == 140
    assert panel.iloc[0]["rep_votes"] == 60


def test_panel_is_sorted_by_fips_then_year_with_integer_years() -> None:
    """The panel must come out in deterministic (fips, year) order regardless
    of raw row order, and year must stay an integer (a float year like 2016.0
    would corrupt every "support in year t" lookup downstream). The explicit
    expected list — not a re-sort of the output — specifies the order
    (TDD_CONTRACT.md Bug #3: the assertion must not share the implementation's
    assumptions)."""
    raw = _raw_rows(
        [
            {"county_fips": "29510", "year": 2020, "party": "DEMOCRAT", "candidatevotes": 5},
            {"county_fips": "01001", "year": 2020, "party": "DEMOCRAT", "candidatevotes": 5},
            {"county_fips": "29510", "year": 2016, "party": "DEMOCRAT", "candidatevotes": 5},
        ]
    )

    panel = load_county_returns(raw)

    assert list(zip(panel["fips"], panel["year"], strict=True)) == [
        ("01001", 2020),
        ("29510", 2016),
        ("29510", 2020),
    ]
    assert pd.api.types.is_integer_dtype(panel["year"])


def test_empty_input_yields_empty_panel_with_canonical_columns() -> None:
    """Zero raw rows (e.g. a filter that matched nothing) must yield a panel
    with zero rows but ALL canonical columns. Downstream consumers select
    columns before checking length; an empty frame without the columns is the
    exact KeyError class of TDD_CONTRACT.md Bug #2."""
    # One default row, then slice to zero rows: an empty frame that still has
    # the raw columns, which is what "no matching records" actually looks like.
    raw = _raw_rows([{}]).iloc[0:0]

    panel = load_county_returns(raw)

    assert list(panel.columns) == PANEL_COLUMNS
    assert len(panel) == 0


def test_pseudo_candidate_total_rows_are_not_votes() -> None:
    """Discovered in the real 2024 file (Wisconsin, Vermont, West Virginia,
    Wyoming): a pseudo-candidate row "TOTAL VOTES CAST" with party=NaN carries
    the county's reported turnout. It is bookkeeping, not a candidate — counting
    it would double total_votes (Milwaukee: 464,107 phantom votes into
    other_votes). Rows without a party are excluded."""
    raw = _raw_rows(
        [
            {"party": "DEMOCRAT", "candidatevotes": 316292, "mode": "<NA>"},
            {"party": "REPUBLICAN", "candidatevotes": 138022, "mode": "<NA>"},
            {
                "candidate": "TOTAL VOTES CAST",
                "party": float("nan"),
                "candidatevotes": 464107,
                "mode": "<NA>",
            },
        ]
    )

    panel = load_county_returns(raw)

    assert panel.iloc[0]["total_votes"] == 316292 + 138022
    assert panel.iloc[0]["other_votes"] == 0


def test_total_mode_rows_take_precedence_over_sub_mode_rows() -> None:
    """Discovered in the real 2024 file (Texas, Arizona, Iowa, ...): a county
    can report authoritative TOTAL VOTES rows ALONGSIDE early-voting sub-mode
    rows (whose votes are already inside the totals) and stray unattributed
    rows. Harris County, TX would over-count by 4.5x if all rows were summed.
    When total-mode rows carry the county's votes, they alone are the truth."""
    raw = _raw_rows(
        [
            {"party": "DEMOCRAT", "candidatevotes": 800, "mode": "TOTAL VOTES"},
            {"party": "REPUBLICAN", "candidatevotes": 700, "mode": "TOTAL VOTES"},
            # early-vote subset, already contained in the TOTAL VOTES rows
            {"party": "DEMOCRAT", "candidatevotes": 600, "mode": "EARLY VOTING"},
            # stray unattributed bulk row (real example: 2.69M "OTHER" votes
            # in a county with 1.56M actual ballots)
            {"party": "OTHER", "candidatevotes": 2000, "mode": "<NA>"},
        ]
    )

    panel = load_county_returns(raw)

    row = panel.iloc[0]
    assert row["dem_votes"] == 800
    assert row["rep_votes"] == 700
    assert row["other_votes"] == 0
    assert row["total_votes"] == 1500
