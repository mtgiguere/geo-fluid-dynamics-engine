"""Tests for the baby-names ingest: every name given to 5 or more babies of
one sex in one state in one year, 1910-2025.

Why this is here: state laws showed the border wave and showed that part of
it is "neighbours are alike", not neighbours learning. A law is chosen by a
few hundred legislators; a baby name is chosen by millions of parents, each
copying what they see and hear. If names cross state borders the way laws
do, the wave is a mass behaviour, the kind a vote is.

The raw input is the Social Security Administration's "Popular baby names by
state" (namesbystate.zip, public domain): one headerless text file per state
(`MO.TXT`), each line `state,sex,year,name,count`, e.g. `MO,F,1910,Mary,611`.
A name given fewer than 5 times in a state-year is left out of the file for
privacy. The canonical output keys the state by its two-digit FIPS code so it
joins the county and state data.
"""

import pandas as pd
import pytest

from geofluid.ingest.names import RAW_NAME_COLUMNS, load_state_names

NAME_COLUMNS = ["name", "sex", "state_fips", "year", "births"]


def _raw(rows: list[tuple[str, str, int, str, int]]) -> pd.DataFrame:
    """Raw lines as the state files carry them."""
    return pd.DataFrame(rows, columns=RAW_NAME_COLUMNS)


def test_a_line_gets_its_state_code() -> None:
    """`MO,F,1910,Mary,611` becomes Mary, F, state_fips "29" (Missouri's
    FIPS code), 1910, 611 births."""
    out = load_state_names(_raw([("MO", "F", 1910, "Mary", 611)]))

    assert list(out.columns) == NAME_COLUMNS
    assert out.to_dict("records") == [
        {"name": "Mary", "sex": "F", "state_fips": "29", "year": 1910, "births": 611}
    ]


def test_a_postal_code_that_is_not_a_state_stops_the_load() -> None:
    """The files cover the 50 states and DC. A territory or a typo ("XX")
    would have no FIPS code, become a blank state and drop out of every
    neighbour count without a word. The load stops instead, naming it."""
    raw = _raw([("MO", "F", 1910, "Mary", 611), ("XX", "F", 1910, "Mary", 7)])

    with pytest.raises(ValueError, match="XX"):
        load_state_names(raw)
