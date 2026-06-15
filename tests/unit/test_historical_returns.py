"""Tests for the historical returns ingest — Algara & Sharif 1868-2020.

The Algara-Sharif "Partisanship & Nationalization" dataset (Harvard Dataverse
doi:10.7910/DVN/DGUMFI) ships county presidential returns back to 1868,
ALREADY FIPS-coded with county-lifespan metadata — the authors did the
150-year boundary harmonization. The raw object `pres_elections_release`
(read from RData via pyreadr in the export layer) has one row per county-year
with democratic_raw_votes / republican_raw_votes / raw_county_vote_totals.

This loader maps it onto the SAME canonical schema as load_county_returns,
so the whole downstream pipeline (master panel, swing, LISA) works unchanged
over 150 years. The modern MIT source (2000-2024) stays authoritative for
its years; Algara fills 1868-1996, and the 2000-2020 overlap is the
cross-source validation (Algara 2020 two-party matches MIT to a tenth of a
point — see the acceptance run).
"""

import pandas as pd

from geofluid.ingest.historical_returns import load_historical_returns

# The canonical schema, written out literally (identical to the returns panel
# so the two sources concatenate into one 1868-2024 spine).
PANEL_COLUMNS = [
    "fips",
    "year",
    "dem_votes",
    "rep_votes",
    "other_votes",
    "total_votes",
    "dem_share_2p",
]


def _raw(rows: list[dict[str, object]]) -> pd.DataFrame:
    defaults: dict[str, object] = {
        "election_year": 1936.0,
        "fips": "01001",
        "office": "PRES",
        "democratic_raw_votes": 400.0,
        "republican_raw_votes": 500.0,
        "raw_county_vote_totals": 950.0,
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def test_maps_algara_rows_to_the_canonical_returns_schema() -> None:
    """One county-year: dem 400, rep 500, total 950 -> other_votes 50
    (total minus the two parties), dem_share_2p = 400/900 = 0.4444, year an
    integer, votes int64. Same columns as the MIT returns panel."""
    panel = load_historical_returns(_raw([{}]))

    assert list(panel.columns) == PANEL_COLUMNS
    row = panel.iloc[0]
    assert row["fips"] == "01001"
    assert row["year"] == 1936
    assert row["dem_votes"] == 400
    assert row["rep_votes"] == 500
    assert row["other_votes"] == 50
    assert row["total_votes"] == 950
    assert abs(row["dem_share_2p"] - 400 / 900) < 1e-9
    for col in ["dem_votes", "rep_votes", "other_votes", "total_votes"]:
        assert pd.api.types.is_integer_dtype(panel[col]), col


def test_rows_without_two_party_votes_are_excluded() -> None:
    """A county-year with missing dem/rep votes (a county that did not yet
    exist, or no recorded returns — 88 such rows in the real file) has no
    two-party share and is dropped, not fabricated as zero."""
    raw = _raw(
        [
            {"fips": "01001", "democratic_raw_votes": float("nan")},
            {"fips": "01003", "democratic_raw_votes": 300.0, "republican_raw_votes": 200.0},
        ]
    )

    panel = load_historical_returns(raw)

    assert list(panel["fips"]) == ["01003"]


def test_sorted_by_fips_then_year_with_integer_years() -> None:
    """Deterministic (fips, year) order regardless of input order; the float
    election_year (1936.0) becomes an integer 1936."""
    raw = _raw(
        [
            {"fips": "29510", "election_year": 2020.0},
            {"fips": "01001", "election_year": 1872.0},
            {"fips": "01001", "election_year": 1868.0},
        ]
    )

    panel = load_historical_returns(raw)

    assert list(zip(panel["fips"], panel["year"], strict=True)) == [
        ("01001", 1868),
        ("01001", 1872),
        ("29510", 2020),
    ]
    assert pd.api.types.is_integer_dtype(panel["year"])
