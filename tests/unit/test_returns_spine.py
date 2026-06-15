"""Tests for the returns spine — one 1868-2024 panel from two sources.

The Algara-Sharif historical loader (1868-2020) and the MIT loader
(2000-2024) produce the SAME canonical schema. The spine stitches them into
one panel: the modern MIT source is authoritative from its first year (2000)
onward — it's the source we validate against and the one with demographics —
so the historical source fills only the years BEFORE the cutover. The
overlap is resolved in MIT's favour, never double-counted.
"""

import pandas as pd

from geofluid.panel.spine import build_returns_spine

_COLUMNS = ["fips", "year", "dem_votes", "rep_votes", "other_votes", "total_votes", "dem_share_2p"]


def _panel(rows: list[dict[str, object]]) -> pd.DataFrame:
    defaults: dict[str, object] = {
        "fips": "01001",
        "year": 1996,
        "dem_votes": 100,
        "rep_votes": 100,
        "other_votes": 0,
        "total_votes": 200,
        "dem_share_2p": 0.5,
    }
    return pd.DataFrame([{**defaults, **r} for r in rows], columns=_COLUMNS)


def test_modern_source_wins_the_overlap_no_double_count() -> None:
    """A county present in both sources at 2000 takes the MODERN row, not the
    historical one — and appears once. Historical supplies pre-2000 only.
    Historical 2000 has dem 100; modern 2000 has dem 999; the spine's 2000
    must read 999 and there must be exactly one 2000 row."""
    historical = _panel(
        [
            {"year": 1996, "dem_votes": 60},
            {"year": 2000, "dem_votes": 100},  # overlap — must be overridden
            {"year": 2020, "dem_votes": 100},  # overlap — must be overridden
        ]
    )
    modern = _panel(
        [
            {"year": 2000, "dem_votes": 999},
            {"year": 2020, "dem_votes": 500},
            {"year": 2024, "dem_votes": 400},
        ]
    )

    spine = build_returns_spine(historical, modern, cutover_year=2000)

    assert list(spine.columns) == _COLUMNS
    by_year = spine[spine["fips"] == "01001"].set_index("year")
    assert list(by_year.index) == [1996, 2000, 2020, 2024]
    assert by_year.loc[2000, "dem_votes"] == 999  # modern won the overlap
    assert by_year.loc[1996, "dem_votes"] == 60  # historical kept pre-cutover


def test_defunct_and_new_counties_both_survive_sorted() -> None:
    """A county only in the historical source (a defunct/merged county that
    stopped reporting before 2000) and a county only in the modern source
    both appear, in (fips, year) order."""
    historical = _panel([{"fips": "51780", "year": 1900, "dem_votes": 7}])  # defunct
    modern = _panel([{"fips": "29510", "year": 2024, "dem_votes": 9}])

    spine = build_returns_spine(historical, modern, cutover_year=2000)

    assert list(zip(spine["fips"], spine["year"], strict=True)) == [
        ("29510", 2024),
        ("51780", 1900),
    ]
