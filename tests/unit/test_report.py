"""Tests for the report layer: the numbers the public pages publish.

The page builders in scripts/ only assemble HTML. Anything that decides a
number or a date a reader sees (which file is the registered one, when the
registration happened, how a chance is worded) lives here, under test, so a
page cannot quietly drift from the record it claims to show
(TDD_CONTRACT.md, Section 7).
"""

import re
from pathlib import Path

import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

from geofluid.report import (
    latest_prediction_file,
    measure_call,
    reader_percent,
    registration_dates,
)

# The frozen 2026 registration (never edited; test_registration_frozen guards it).
PRED = Path(__file__).resolve().parents[2] / "data" / "predictions"


def test_registration_date_is_the_first_hash_file_and_later_ones_are_supplements(
    tmp_path: Path,
) -> None:
    """Hash files dated 2026-10-14, 2026-10-15 and 2026-11-02 (written out of
    order): the registration happened on the FIRST date, 2026-10-14; the
    other two are dated supplements, oldest first. Reading the newest file as
    "the" registration date moved the blueprint's date with every supplement."""
    for day in ("2026-11-02", "2026-10-14", "2026-10-15"):
        (tmp_path / f"REGISTERED_SHA256_{day}.csv").write_text("file,sha256\n")

    first, supplements = registration_dates(tmp_path)

    assert first == "2026-10-14"
    assert supplements == ["2026-10-15", "2026-11-02"]


def test_registration_dates_with_no_hash_file_names_the_directory(tmp_path: Path) -> None:
    """An empty predictions folder has no registration to report. That must
    fail loudly and name the folder searched, not surface as a bare
    IndexError (Section 11: a failure names its subject)."""
    with pytest.raises(FileNotFoundError, match=re.escape(str(tmp_path))):
        registration_dates(tmp_path)


def test_golden_the_2026_registration_is_dated_october_14() -> None:
    """Golden number, read from the frozen data/predictions/ folder: the
    registration tag registration-2026-11-03 is commit 6149dfc of 2026-10-14;
    the outside-review supplement followed on 2026-10-15 and the pre-vote
    supplement (tag registration-supplement-2026-11-02) on 2026-11-02."""
    assert registration_dates(PRED) == ("2026-10-14", ["2026-10-15", "2026-11-02"])


def test_a_registered_file_wins_over_a_newer_draft(tmp_path: Path) -> None:
    """A draft dated 2026-10-20 and a registration dated 2026-10-14: the page
    shows the REGISTERED file even though the draft is newer, because only
    the registered numbers are the record that gets graded."""
    (tmp_path / "mo_REGISTERED_2026-10-14.csv").write_text("x")
    (tmp_path / "mo_DRAFT_2026-10-20.csv").write_text("x")

    path, status = latest_prediction_file(tmp_path, "mo")

    assert (path.name, status) == ("mo_REGISTERED_2026-10-14.csv", "REGISTERED")


def test_before_registration_the_newest_draft_is_shown_and_labelled_draft(
    tmp_path: Path,
) -> None:
    """Drafts of 2026-10-01 and 2026-10-09 and nothing registered: the page
    shows the 2026-10-09 draft and labels it DRAFT, so a reader can never
    mistake a working number for the frozen record."""
    (tmp_path / "mo_DRAFT_2026-10-01.csv").write_text("x")
    (tmp_path / "mo_DRAFT_2026-10-09.csv").write_text("x")

    path, status = latest_prediction_file(tmp_path, "mo")

    assert (path.name, status) == ("mo_DRAFT_2026-10-09.csv", "DRAFT")


def test_no_file_for_a_prefix_names_the_prefix_and_folder(tmp_path: Path) -> None:
    """Neither a registered file nor a draft for "mo": the error names both
    the prefix and the folder searched (Section 11)."""
    with pytest.raises(FileNotFoundError, match=rf"mo.*{re.escape(str(tmp_path))}"):
        latest_prediction_file(tmp_path, "mo")


def test_an_ordinary_chance_reads_as_a_whole_percent() -> None:
    """0.42 is printed as "42%": whole points, no false precision."""
    assert reader_percent(0.42) == "42%"


def test_extreme_chances_are_never_printed_as_certain() -> None:
    """0.001 and 0.999 would print as "0%" and "100%", which claim a
    certainty no forecast has. They read "under 1%" and "over 99%"."""
    assert (reader_percent(0.001), reader_percent(0.999)) == ("under 1%", "over 99%")


@given(st.floats(min_value=0.0, max_value=1.0))
def test_no_chance_from_zero_to_one_prints_as_zero_or_a_hundred(p: float) -> None:
    """Property over every chance in [0, 1]: the words "0%" and "100%" never
    appear. Rounding is where this breaks: the thresholds must sit on the
    rounded value, not on p, or a chance of exactly 0.005 rounds to "0%"."""
    assert reader_percent(p) not in ("0%", "100%")


def _one_measure(shares: list[float], low: float, central: float, high: float) -> pd.DataFrame:
    """Prediction rows for one measure, as the registered file lays them out:
    the statewide bracket repeated on every county row."""
    return pd.DataFrame(
        {
            "fips": [f"2900{i}" for i in range(len(shares))],
            "pred_progressive_share": shares,
            "level_low": low,
            "level_central": central,
            "level_high": high,
        }
    )


def test_a_measure_call_reports_the_bracket_and_the_counties_its_side_wins() -> None:
    """Three counties at 0.60, 0.40 and 0.55 under a 0.45 / 0.52 / 0.58
    bracket: the call is the bracket as registered, and the tracked side is
    expected to carry 2 of the 3 counties (those above one half)."""
    call = measure_call(_one_measure([0.60, 0.40, 0.55], 0.45, 0.52, 0.58))

    assert (call.low, call.central, call.high) == (0.45, 0.52, 0.58)
    assert (call.counties_won, call.n_counties) == (2, 3)


def test_a_measure_call_carries_the_chance_now_and_after_one_point() -> None:
    """Bracket 0.48355 / 0.50 / 0.52. A central call of exactly one half is a
    coin flip: chance now 0.5. The tail facing 50 is the lower one, so
    sd = (0.50 - 0.48355) / 1.645 = 0.01; one statewide point the tracked
    side's way puts the call one sd above 50: Phi(1) = 0.8413447."""
    call = measure_call(_one_measure([0.5], 0.48355, 0.50, 0.52))

    assert call.chance_now == pytest.approx(0.5)
    assert call.chance_plus_one == pytest.approx(0.8413447, abs=1e-6)


@pytest.mark.parametrize(
    ("measure_id", "published"),
    [
        ("mo_20261103_amendment_3", ("55", "48", "59", 11, "90%", "94%")),
        ("mo_20261103_amendment_6", ("62", "50", "70", 105, "95%", "96%")),
        ("mo_20261103_map_referendum", ("53", "46", "60", 12, "76%", "83%")),
        ("mo_20261103_amendment_7", ("58", "50", "68", 116, "95%", "97%")),
        ("mo_20261103_amendment_8", ("36", "28", "45", 0, "1%", "1%")),
    ],
)
def test_golden_the_receipt_cards_match_the_registered_file(
    measure_id: str, published: tuple[str, str, str, int, str, str]
) -> None:
    """Golden numbers: each card on the live November receipt (forecast.html,
    built 2026-10-15) as a reader sees it, recomputed from the frozen
    registered file: central, low, high (of every 100 votes), counties won
    of 116, chance now, chance after one point. If the page logic drifts from
    the record, this fails."""
    rows = pd.read_csv(PRED / "mo_2026-11-03_REGISTERED_2026-10-14.csv", dtype={"fips": str})
    call = measure_call(rows[rows["measure_id"] == measure_id])

    seen = (
        f"{call.central * 100:.0f}",
        f"{call.low * 100:.0f}",
        f"{call.high * 100:.0f}",
        call.counties_won,
        reader_percent(call.chance_now),
        reader_percent(call.chance_plus_one),
    )
    assert (seen, call.n_counties) == (published, 116)
