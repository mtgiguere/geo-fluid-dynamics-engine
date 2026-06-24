"""Tests for the referendum ingest — issue votes, the engine's real fuel.

First source: the Kansas SoS official precinct file for the August 2022
constitutional amendment (the abortion referendum). Format: one row per
(County, Precinct, Candidate) where Candidate is the string
'Amendment, Constitutional - "YES"' or '... - "NO"', votes as numbers,
counties by NAME (no FIPS — the name->fips mapping comes from our own
boundary file).

Semantics note, explicit because it inverts intuition: for this measure
"NO" was the vote to PRESERVE abortion rights (the amendment would have
removed them). The panel carries raw yes/no and no_share; downstream
analysis decides which side maps to which politics, per measure.
"""

from pathlib import Path

import pandas as pd
import pytest

from geofluid.ingest.referendum import (
    load_ks_referendum,
    load_ks_referendum_workbook,
    load_ky_referendum,
)

_NAME_TO_FIPS = {"ALLEN": "20001", "JOHNSON": "20091"}


def _raw(rows: list[dict[str, object]]) -> pd.DataFrame:
    defaults: dict[str, object] = {
        "County": "Allen",
        "Precinct": "Carlyle Township",
        "Race": "Constitutional Amendment",
        "Candidate": 'Amendment, Constitutional - "YES"',
        "Party": float("nan"),
        "Votes": 0.0,
        "VTD": "000010",
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def test_precincts_aggregate_to_county_with_no_share() -> None:
    """The county referendum panel: precinct rows sum per county per side;
    no_share = NO / (YES + NO). Allen: YES 66 + 54 = 120, NO 48 + 22 = 70,
    no_share = 70 / 190 (derived here, before the assertion was written).
    Counties arrive as names and leave as FIPS, sorted."""
    raw = _raw(
        [
            {"Votes": 66.0},
            {"Candidate": 'Amendment, Constitutional - "NO"', "Votes": 48.0},
            {"Precinct": "Cottage Grove", "Votes": 54.0},
            {
                "Precinct": "Cottage Grove",
                "Candidate": 'Amendment, Constitutional - "NO"',
                "Votes": 22.0,
            },
            {"County": "Johnson", "Votes": 100.0},
            {
                "County": "Johnson",
                "Candidate": 'Amendment, Constitutional - "NO"',
                "Votes": 300.0,
            },
        ]
    )

    panel = load_ks_referendum(raw, _NAME_TO_FIPS)

    assert list(panel.columns) == ["fips", "yes_votes", "no_votes", "total_votes", "no_share"]
    assert list(panel["fips"]) == ["20001", "20091"]
    allen = panel.iloc[0]
    assert allen["yes_votes"] == 120
    assert allen["no_votes"] == 70
    assert allen["total_votes"] == 190
    assert abs(allen["no_share"] - 70 / 190) < 1e-12
    assert abs(panel.iloc[1]["no_share"] - 0.75) < 1e-12


def test_unknown_county_name_fails_loudly() -> None:
    """A county name that maps to no FIPS is a join defect (misspelling,
    wrong state, format drift) — silent dropping would shrink the panel
    invisibly. Raise, naming the county."""
    raw = _raw([{"County": "Gotham", "Votes": 5.0}])

    with pytest.raises(ValueError, match="GOTHAM"):
        load_ks_referendum(raw, _NAME_TO_FIPS)


def test_unexpected_candidate_label_fails_loudly() -> None:
    """A referendum has exactly two sides. A third candidate string means
    the format changed (write-ins, a new race mixed in) — never a silent
    'other' bucket."""
    raw = _raw([{"Candidate": "Amendment, Constitutional - ABSTAIN", "Votes": 5.0}])

    with pytest.raises(ValueError, match="ABSTAIN"):
        load_ks_referendum(raw, _NAME_TO_FIPS)


def _write_ks_workbook(path: Path) -> None:
    """Write a workbook reproducing the real Kansas SoS structure: a long
    main sheet for most counties, plus a wide per-county sheet for a big
    county — two 'Constitutional Amendment' columns whose Yes/No identity is
    declared in a data row, preceded by a junk 'NON' row (as Johnson/Sedgwick/
    Wyandotte actually are)."""
    main = pd.DataFrame(
        {
            "County": ["Allen", "Allen"],
            "Precinct": ["Carlyle", "Carlyle"],
            "Race": ["Constitutional Amendment", "Constitutional Amendment"],
            "Candidate": [
                'Amendment, Constitutional - "YES"',
                'Amendment, Constitutional - "NO"',
            ],
            "Party": [None, None],
            "Votes": [66.0, 48.0],
            "VTD": ["000010", "000010"],
        }
    )
    # Wide sheet: header dedup gives the ".1" suffix; rows 0-1 are the NON
    # junk row and the Yes/No marker row; precinct vote rows follow.
    # Real sheets end with a "COUNTY TOTALS" row (precinct code ZZZ) that is
    # the SoS's authoritative county figure — and in Shawnee and Wyandotte it
    # EXCEEDS the precinct sum, because it includes provisional/advance votes
    # not attributed to any precinct line. Here the precincts sum to 365/467
    # but the official total is 370/470 (5 yes + 3 no provisional). The panel
    # must report the official 370/470, not the precinct sum.
    johnson = pd.DataFrame(
        {
            "PRECINCT CODE": [None, None, 1, 2, "ZZZ"],
            "PRECINCT NAME": [None, None, "Aubry 01", "Aubry 02", "COUNTY TOTALS"],
            "Constitutional Amendment": ["NON", "Yes", 52, 313, 370],
            "Constitutional Amendment.1": ["NON", "No", 68, 399, 470],
        }
    )
    with pd.ExcelWriter(path) as writer:
        main.to_excel(writer, sheet_name="OfficialPrecinctLevelResults", index=False)
        johnson.to_excel(writer, sheet_name="JOHNSON", index=False)


def test_workbook_merges_long_main_sheet_and_wide_county_sheets(tmp_path: Path) -> None:
    """The real file splits its four largest counties into separate WIDE
    sheets (Johnson, Sedgwick, Shawnee, Wyandotte) — discovered when the
    acceptance run captured only 52% of the certified NO vote. The workbook
    reader must fold those back in, using each wide sheet's official COUNTY
    TOTALS row (Johnson YES 370 / NO 470 — which includes provisional votes
    beyond the 365/467 precinct sum), alongside Allen from the long main
    sheet (precinct-summed, since the main sheet has no totals rows)."""
    path = tmp_path / "ks.xlsx"
    _write_ks_workbook(path)

    panel = load_ks_referendum_workbook(path, _NAME_TO_FIPS)

    assert list(panel["fips"]) == ["20001", "20091"]
    johnson = panel[panel["fips"] == "20091"].iloc[0]
    assert johnson["yes_votes"] == 370
    assert johnson["no_votes"] == 470
    allen = panel[panel["fips"] == "20001"].iloc[0]
    assert allen["yes_votes"] == 66
    assert allen["no_votes"] == 48


# --- Kentucky Nov-2022 Amendment 2 ("No Right To Abortion") -----------------
#
# A SECOND source in a DIFFERENT format. The Kentucky State Board of Elections
# publishes a plain-text export, not the precinct workbook Kansas uses: a title
# line, then per county a name line ("<X> County"), a "<pct>% Est. Vote Counted"
# line, a "Choices / Total Votes / % Votes" tab-separated header, and one "Yes"
# and one "No" row (whose order varies county to county). The KY loader is
# KY-specific (each state's SoS format differs) but emits the SAME canonical
# panel as Kansas, so the dissonance layer consumes both identically.
#
# Semantics, again inverting intuition: Amendment 2 would have declared NO right
# to abortion in the state constitution. "NO" DEFEATED it — so "NO" is the
# abortion-rights-preserving side, exactly as in Kansas. The panel stays
# politics-agnostic; no_share is the comparable metric.

_KY_NAME_TO_FIPS = {"ADAIR": "21001", "ALLEN": "21003", "ANDERSON": "21005"}

_KY_TITLE = "2022 Kentucky Amendment 2 - No Right To Abortion Election Results"


def _write_ky_file(path: Path, blocks: str) -> None:
    """Write a miniature of the real KY State Board of Elections text export:
    the title line, then the given per-county blocks verbatim. The real file
    uses CRLF; we write LF and rely on the loader's line splitting to absorb
    both (the real CRLF file is the acceptance-run check)."""
    path.write_text(_KY_TITLE + "\n" + blocks)


def test_ky_single_county_parses_to_canonical_row(tmp_path: Path) -> None:
    """One KY county block -> one canonical referendum row, identical in shape
    to the Kansas panel. The vote count is read from the 'Total Votes' column
    BY the Yes/No label (never the percent column, which is the source's own
    rounding). Adair-style block, Yes 60 / No 40: total 100,
    no_share = 40 / 100 = 0.40 (derived here before the assertion). The county
    name 'Adair County' normalizes to 'ADAIR' to join the boundary-file FIPS
    map (Census NAME uppercased, no 'County' suffix), and votes are int64."""
    path = tmp_path / "ky.txt"
    _write_ky_file(
        path,
        "Adair County\n"
        "100% Est. Vote Counted\n"
        "Choices\tTotal Votes\t% Votes\n"
        "Yes\t60\t60.0%\n"
        "No\t40\t40.0%\n",
    )

    panel = load_ky_referendum(path, _KY_NAME_TO_FIPS)

    assert list(panel.columns) == ["fips", "yes_votes", "no_votes", "total_votes", "no_share"]
    assert len(panel) == 1
    row = panel.iloc[0]
    assert row["fips"] == "21001"
    assert row["yes_votes"] == 60
    assert row["no_votes"] == 40
    assert row["total_votes"] == 100
    assert abs(row["no_share"] - 0.40) < 1e-12
    assert panel["yes_votes"].dtype == "int64"


def test_ky_assigns_votes_by_label_not_row_order(tmp_path: Path) -> None:
    """In the real file the Yes/No rows are NOT in a fixed order — some
    counties (Bourbon, Boyle, Woodford) list No first. Votes must be assigned
    by the row's LABEL, never its position. Here Anderson lists No (50) before
    Yes (30): yes_votes must be 30 and no_votes 50, not the reverse."""
    path = tmp_path / "ky.txt"
    _write_ky_file(
        path,
        "Anderson County\n"
        "100% Est. Vote Counted\n"
        "Choices\tTotal Votes\t% Votes\n"
        "No\t50\t62.5%\n"
        "Yes\t30\t37.5%\n",
    )

    panel = load_ky_referendum(path, _KY_NAME_TO_FIPS)

    row = panel.iloc[0]
    assert row["fips"] == "21005"
    assert row["yes_votes"] == 30
    assert row["no_votes"] == 50


def test_ky_parses_thousands_separators(tmp_path: Path) -> None:
    """The export formats vote counts with thousands separators (Boone really
    reads 'Yes 22,540'). The loader must read 22,540 as the integer 22540, not
    choke on the comma. Yes 22,540 / No 21,581 (Boone's real figures):
    total 44,121, no_share = 21581 / 44121 (derived before the assertion)."""
    path = tmp_path / "ky.txt"
    _write_ky_file(
        path,
        "Adair County\n"
        "100% Est. Vote Counted\n"
        "Choices\tTotal Votes\t% Votes\n"
        "Yes\t22,540\t51.1%\n"
        "No\t21,581\t48.9%\n",
    )

    panel = load_ky_referendum(path, _KY_NAME_TO_FIPS)

    row = panel.iloc[0]
    assert row["yes_votes"] == 22540
    assert row["no_votes"] == 21581
    assert row["total_votes"] == 44121
    assert abs(row["no_share"] - 21581 / 44121) < 1e-12


def test_ky_multiple_counties_one_row_each_sorted_by_fips(tmp_path: Path) -> None:
    """Each county block becomes exactly one panel row, and the panel is sorted
    by FIPS ascending regardless of the file's order. The file here lists Allen
    (21003) before Adair (21001); the panel must come back [21001, 21003], one
    row apiece — so an index built on this panel aligns with every other
    FIPS-sorted product."""
    path = tmp_path / "ky.txt"
    _write_ky_file(
        path,
        "Allen County\n"
        "100% Est. Vote Counted\n"
        "Choices\tTotal Votes\t% Votes\n"
        "Yes\t10\t50.0%\n"
        "No\t10\t50.0%\n"
        "Adair County\n"
        "100% Est. Vote Counted\n"
        "Choices\tTotal Votes\t% Votes\n"
        "Yes\t7\t70.0%\n"
        "No\t3\t30.0%\n",
    )

    panel = load_ky_referendum(path, _KY_NAME_TO_FIPS)

    assert list(panel["fips"]) == ["21001", "21003"]
    assert list(panel["yes_votes"]) == [7, 10]


def test_ky_unknown_county_name_fails_loudly(tmp_path: Path) -> None:
    """A county name that maps to no FIPS is a join defect (misspelling, a new
    independent city, format drift) — silent dropping would shrink the panel
    invisibly. Raise, naming the offending county, exactly as the Kansas loader
    does. 'Fayette' is omitted from the test map to force the failure."""
    path = tmp_path / "ky.txt"
    _write_ky_file(
        path,
        "Fayette County\n"
        "100% Est. Vote Counted\n"
        "Choices\tTotal Votes\t% Votes\n"
        "Yes\t5\t50.0%\n"
        "No\t5\t50.0%\n",
    )

    with pytest.raises(ValueError, match="FAYETTE"):
        load_ky_referendum(path, _KY_NAME_TO_FIPS)


def test_ky_county_missing_a_side_fails_loudly(tmp_path: Path) -> None:
    """A referendum has exactly two sides. A county block reporting only a Yes
    (or only a No) is format drift — a dropped row, a parse slip — and must
    raise, naming the county. Otherwise the pivot pads the missing side to a
    phantom 0, producing a no_share that looks real but is fabricated. Adair
    here has a Yes and no No."""
    path = tmp_path / "ky.txt"
    _write_ky_file(
        path,
        "Adair County\n100% Est. Vote Counted\nChoices\tTotal Votes\t% Votes\nYes\t60\t100.0%\n",
    )

    with pytest.raises(ValueError, match="ADAIR"):
        load_ky_referendum(path, _KY_NAME_TO_FIPS)
