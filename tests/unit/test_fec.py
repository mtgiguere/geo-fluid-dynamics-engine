"""Tests for the FEC individual-contributions ingest: political giving, dated
to the day and placed by ZIP code.

Why this is here: rooftop solar, state laws and baby names all spread from
neighbour to neighbour, but election results cannot show it (every decision
is recorded on one day, years apart). A donation is a political act with a
date and a place, so it is the first political "adoption" we can run through
the same timing model. The hypothesis under test: beliefs sort, actions
spread.

The raw input is the FEC bulk file of individual contributions for a
two-year cycle (`indiv22.zip` → `itcont.txt`), pipe-delimited, no header;
the column names come from FEC's `indiv_header_file.csv`. Dates are
MMDDYYYY. ZIP codes are 5 or 9 digits.
"""

import pandas as pd

from geofluid.ingest.fec import RAW_INDIV_COLUMNS, load_contributions

CONTRIBUTION_COLUMNS = ["cmte_id", "other_id", "zip5", "state", "date", "amount", "memo_cd"]


def _raw(rows: list[dict[str, str]]) -> pd.DataFrame:
    """Raw FEC lines, all fields as text, from compact overrides."""
    defaults = dict.fromkeys(RAW_INDIV_COLUMNS, "")
    defaults.update(
        {
            "CMTE_ID": "C00314617",
            "ENTITY_TP": "IND",
            "STATE": "MO",
            "ZIP_CODE": "641081234",
            "TRANSACTION_DT": "07012022",
            "TRANSACTION_AMT": "25",
        }
    )
    return pd.DataFrame([{**defaults, **row} for row in rows], columns=RAW_INDIV_COLUMNS)


def test_a_line_gets_a_five_digit_zip_a_date_and_an_amount() -> None:
    """A $25 gift to Planned Parenthood's federal PAC from ZIP 64108-1234 on
    July 1, 2022 becomes: ZIP "64108" (the 5 digits that place it in a
    county), date 2022-07-01, amount 25.0."""
    out = load_contributions(_raw([{}]))

    assert list(out.columns) == CONTRIBUTION_COLUMNS
    assert out.to_dict("records") == [
        {
            "cmte_id": "C00314617",
            "other_id": "",
            "zip5": "64108",
            "state": "MO",
            "date": pd.Timestamp("2022-07-01"),
            "amount": 25.0,
            "memo_cd": "",
        }
    ]


def test_only_gifts_from_individuals_count() -> None:
    """The file also carries money from organisations, PACs and party
    committees (ENTITY_TP ORG, PAC, PTY, CCM, COM, CAN). A PAC transfer is
    not a person in a ZIP code deciding to give, so it is not an adoption.
    Only ENTITY_TP "IND" rows remain."""
    raw = _raw([{}, {"ENTITY_TP": "PAC"}, {"ENTITY_TP": "ORG"}])

    out = load_contributions(raw)

    assert len(out) == 1


def test_a_gift_with_no_usable_date_is_left_out() -> None:
    """The timing model needs the day of each gift. FEC sets aside a small
    file of rows with invalid dates, and some rows have a blank one. An
    undated gift cannot be placed in time, so it is left out rather than
    stopping a 20-million-row load (the acceptance run reports how many)."""
    raw = _raw([{}, {"TRANSACTION_DT": ""}, {"TRANSACTION_DT": "13452022"}])

    out = load_contributions(raw)

    assert out["date"].tolist() == [pd.Timestamp("2022-07-01")]
