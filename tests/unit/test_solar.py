"""Tests for the rooftop-solar ingest — the "known wave" the engine is tested on.

Why solar is here at all: our election data says a whole state moves at once,
which is what a wave looks like when it is photographed only once every few
years. Home solar is an idea that is KNOWN to spread person to person (a
neighbour's panels make you more likely to buy your own), and it is recorded
install by install, with a date and a ZIP code. If the engine can see a wave
in solar, we have a working wave detector to point back at politics.

The raw input is Lawrence Berkeley National Laboratory's public data file
(Tracking the Sun / Distributed Solar, 2026 edition: one row per PV system,
81 columns; `installation_date`, `zip_code`, `state`, `customer_segment` are
the four this module reads). The canonical output is one row per install.
This file is the contract for that table (TDD_CONTRACT.md, Bug #1: written
here before any implementation exists).
"""

import pandas as pd

from geofluid.ingest.solar import county_adoption_panel, load_solar_installs

# The canonical schema, written out literally rather than imported from the
# implementation: a test that imports the constant it checks can never catch
# the constant changing.
INSTALL_COLUMNS = ["state", "zip5", "install_date", "residential"]
PANEL_COLUMNS = ["fips", "quarter", "new_installs", "cumulative_installs"]


def _raw_rows(rows: list[dict[str, object]]) -> pd.DataFrame:
    """Build a raw LBNL-format frame from compact row overrides. Every column
    arrives as text, the way the loader reads the file (dtype=str)."""
    defaults: dict[str, object] = {
        "data_provider_1": "California Public Utilities Commission",
        "installation_date": "2015-10-26T00:00:00.000000000",
        "zip_code": "93004",
        "state": "CA",
        "customer_segment": "RES_SF",
        "PV_system_size_DC": "6.5",
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def test_one_raw_row_becomes_one_install_with_the_canonical_columns() -> None:
    """The core contract: one PV system in, one install row out, with the
    four canonical columns in order. The raw timestamp
    "2015-10-26T00:00:00.000000000" is a calendar date at midnight, so the
    install_date is 2015-10-26. RES_SF (single-family home) is residential.
    """
    installs = load_solar_installs(_raw_rows([{}]))

    assert list(installs.columns) == INSTALL_COLUMNS
    assert len(installs) == 1
    row = installs.iloc[0]
    assert row["state"] == "CA"
    assert row["zip5"] == "93004"
    assert row["install_date"] == pd.Timestamp("2015-10-26")
    assert bool(row["residential"])


def test_float_formatted_zip_loses_its_trailing_point_zero() -> None:
    """Real-data quirk: about 2.2 million California rows (and ~1,200 Florida
    rows) store the ZIP as a float's text, "93004.0". The ZIP is the integer
    part, "93004"; keeping ".0" would make every California install fail the
    ZIP-to-county join and drop out of the panel."""
    installs = load_solar_installs(_raw_rows([{"zip_code": "93004.0"}]))

    assert installs.iloc[0]["zip5"] == "93004"


def test_zip_plus_four_keeps_only_the_five_digit_zip() -> None:
    """The user guide says zip_code is "+4, when applicable". Real rows carry
    it two ways: hyphenated ("87122-1184", ~74,000 New Mexico and other rows)
    and run together as nine digits ("846632587", Utah). Both are ZIP 87122 /
    84663 plus a four-digit suffix; the panel works at five digits."""
    installs = load_solar_installs(
        _raw_rows([{"zip_code": "87122-1184"}, {"zip_code": "846632587"}])
    )

    assert installs["zip5"].tolist() == ["87122", "84663"]


def test_four_digit_zip_gets_its_lost_leading_zero_back() -> None:
    """New England and New Jersey ZIPs start with 0 (Connecticut 06xxx).
    About 248,000 rows lost that zero when the ZIP was once stored as a
    number: Connecticut's "6033" is ZIP 06033. Padding on the left to five
    digits restores it."""
    installs = load_solar_installs(_raw_rows([{"zip_code": "6033", "state": "CT"}]))

    assert installs.iloc[0]["zip5"] == "06033"


def test_padding_spaces_around_the_zip_are_trimmed() -> None:
    """Real rows carry padding: Illinois " 61801" (leading space), Arizona
    "85621       " (trailing spaces), and one Illinois "61821" followed by a
    non-breaking space. Untrimmed, " 61801" would become " 6180" at five
    characters, a ZIP that does not exist."""
    installs = load_solar_installs(
        _raw_rows([{"zip_code": " 61801"}, {"zip_code": "85621       "}, {"zip_code": "61821\xa0"}])
    )

    assert installs["zip5"].tolist() == ["61801", "85621", "61821"]


def test_unusable_zip_becomes_missing_but_the_install_is_kept() -> None:
    """Values that are not a ZIP: "-1" (the file's missing-value code,
    ~233,000 rows, mostly Texas and Maryland), "redacted", "Multiple", "0",
    "7.2", a three-digit "301", a six-digit "852485" (ambiguous: which five?),
    and "inois 60446" (a spilled city field). Each becomes a missing ZIP
    (NA), never a guessed one. The install row itself is kept: it still
    counts toward its state's total, and only the ZIP-level panel skips it.
    Nine rows in, nine rows out, nine missing ZIPs."""
    junk = ["-1", "redacted", "Multiple", "0", "7.2", "301", "852485", "inois 60446", ""]
    installs = load_solar_installs(_raw_rows([{"zip_code": z} for z in junk]))

    assert len(installs) == len(junk)
    assert installs["zip5"].isna().all()


def test_residential_means_a_household_segment_and_unknown_is_not() -> None:
    """The idea we track is a HOUSEHOLD choosing solar. The raw segments are
    RES (838,715 rows), RES_SF single-family (2,866,948), RES_MF
    multi-family (166,452): all residential. COM, NON-RES, AGRICULTURAL,
    GOV, SCHOOL, OTHER TAX-EXEMPT are organisations, and "-1" or a blank
    segment is unknown. Unknown is not residential: residential is a
    True/False column with no missing values, so a count of households
    never silently includes or drops an unknown row.

    The text may arrive as pandas' string type (pandas 3 reading dtype=str,
    where a missing value already tests False) or as plain Python objects
    (pandas 2, or any other reader, where it tests None). The contract holds
    for both, so both are fed in."""
    segments = ["RES", "RES_SF", "RES_MF", "COM", "NON-RES", "AGRICULTURAL", "-1", None]
    raw = _raw_rows([{"customer_segment": s} for s in segments])
    raw_as_objects = raw.astype(object)

    for frame in (raw, raw_as_objects):
        installs = load_solar_installs(frame)
        assert installs["residential"].tolist() == [True, True, True] + [False] * 5
        assert installs["residential"].dtype == bool


def _installs(rows: list[dict[str, object]]) -> pd.DataFrame:
    """Build a canonical install table (the loader's output) from overrides."""
    defaults: dict[str, object] = {
        "state": "MO",
        "zip5": "63101",
        "install_date": pd.Timestamp("2015-11-15"),
        "residential": True,
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


# ZIP -> county lookup (geofluid.ingest.zcta_county output): 63101 is in St.
# Louis city (29510), 63017 in St. Charles County (29183).
_LOOKUP = pd.DataFrame({"zip5": ["63101", "63017"], "fips": ["29510", "29183"]})


def test_panel_counts_new_and_cumulative_household_installs_per_county_quarter() -> None:
    """The adoption panel: one row per (county, quarter), with that quarter's
    new household installs and the running total. Two homes in ZIP 63101
    (St. Louis city, 29510) install on 2015-11-15 (Q4 2015, which starts
    2015-10-01) and 2016-02-03 (Q1 2016, starting 2016-01-01): new 1 then 1,
    cumulative 1 then 2. A quarter is labelled by its first day."""
    installs = _installs([{}, {"install_date": pd.Timestamp("2016-02-03")}])

    panel = county_adoption_panel(installs, _LOOKUP)

    assert list(panel.columns) == PANEL_COLUMNS
    assert panel.to_dict("records") == [
        {
            "fips": "29510",
            "quarter": pd.Timestamp("2015-10-01"),
            "new_installs": 1,
            "cumulative_installs": 1,
        },
        {
            "fips": "29510",
            "quarter": pd.Timestamp("2016-01-01"),
            "new_installs": 1,
            "cumulative_installs": 2,
        },
    ]


def test_panel_counts_only_household_installs() -> None:
    """The idea tracked is a household choosing solar. A school or business
    install in the same county and quarter (residential False) is not
    counted: one home plus one business in Q4 2015 gives new_installs 1."""
    installs = _installs([{}, {"residential": False}])

    panel = county_adoption_panel(installs, _LOOKUP)

    assert panel["new_installs"].tolist() == [1]


def test_quiet_quarters_are_rows_with_zero_new_installs() -> None:
    """The timing model reads WHEN a county takes off, so quiet quarters must
    be rows, not gaps: every county gets every quarter of the panel's span
    (first to last install quarter across ALL counties), zero-filled.

    Fixture: St. Louis city (29510) installs in Q4 2015 and Q2 2016; St.
    Charles (29183, ZIP 63017) only in Q1 2016. Span: Q4 2015 .. Q2 2016,
    three quarters, so 2 counties x 3 quarters = 6 rows.
      29183: new 0, 1, 0  -> cumulative 0, 1, 1
      29510: new 1, 0, 1  -> cumulative 1, 1, 2
    Rows sorted by county, then quarter."""
    installs = _installs(
        [
            {},
            {"install_date": pd.Timestamp("2016-05-20")},
            {"zip5": "63017", "install_date": pd.Timestamp("2016-02-03")},
        ]
    )

    panel = county_adoption_panel(installs, _LOOKUP)

    assert panel["fips"].tolist() == ["29183"] * 3 + ["29510"] * 3
    assert (
        panel["quarter"].tolist()
        == [pd.Timestamp("2015-10-01"), pd.Timestamp("2016-01-01"), pd.Timestamp("2016-04-01")] * 2
    )
    assert panel["new_installs"].tolist() == [0, 1, 0, 1, 0, 1]
    assert panel["cumulative_installs"].tolist() == [0, 1, 1, 1, 1, 2]


def test_an_install_whose_zip_lands_in_another_state_is_not_counted() -> None:
    """Real-data acceptance finding (2026-11-10): 2,102 of 3,753,597 matched
    installs (0.056%) have a ZIP whose county is in a different state from
    the install's own state field, mostly 1,803 DC-labelled installs on ZIPs
    whose land is mainly in Maryland, the rest typos (California installs on
    Hawaii ZIPs). The two fields disagree, so the county is not trusted and
    the install is left out of the county panel.

    Fixture: a California-labelled install on Missouri ZIP 63101 (county
    29510, state FIPS 29 = MO) is dropped; the Missouri-labelled one at the
    same ZIP is kept: new_installs 1, not 2."""
    installs = _installs([{}, {"state": "CA"}])

    panel = county_adoption_panel(installs, _LOOKUP)

    assert panel["new_installs"].tolist() == [1]
