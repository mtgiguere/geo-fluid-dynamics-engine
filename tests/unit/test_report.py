"""Tests for the report layer: the numbers the public pages publish.

The page builders in scripts/ only assemble HTML. Anything that decides a
number or a date a reader sees (which file is the registered one, when the
registration happened, how a chance is worded) lives here, under test, so a
page cannot quietly drift from the record it claims to show
(TDD_CONTRACT.md, Section 7).
"""

import re
from pathlib import Path

import pytest

from geofluid.report import registration_dates

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
