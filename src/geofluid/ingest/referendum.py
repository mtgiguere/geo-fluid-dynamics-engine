"""Ingest official referendum results into a county panel.

Referendums are the engine's purest fuel: actual county-level votes on
TOPICS (abortion, marijuana, wages) rather than parties — the data Module 3
needs to measure the gap between a county's partisan identity and its issue
behavior. First source: the Kansas SoS precinct file for the August 2022
constitutional amendment.

Semantics: the panel carries raw yes/no plus no_share and stays agnostic
about politics. For Kansas 2022 specifically, "NO" preserved abortion
rights — which side is "liberal" is a per-measure fact that belongs to the
analysis layer, never hardcoded here.
"""

from collections.abc import Mapping
from pathlib import Path

import pandas as pd

_SIDE_BY_CANDIDATE_SUFFIX = {'"YES"': "yes_votes", '"NO"': "no_votes"}

# The Kansas SoS workbook keeps most counties in one long sheet and splits
# its four largest into separate WIDE sheets (one column per side, the Yes/No
# labels declared in a data row). This is the main long sheet's name; every
# other sheet is a wide per-county sheet keyed by the county name.
_KS_MAIN_SHEET = "OfficialPrecinctLevelResults"
_AMENDMENT_COLUMN_PREFIX = "Constitutional Amendment"


def _side(candidate: str) -> str:
    """Map the official candidate string to a referendum side, loudly."""
    for suffix, side in _SIDE_BY_CANDIDATE_SUFFIX.items():
        if candidate.strip().endswith(suffix):
            return side
    raise ValueError(f"Unexpected referendum candidate label: {candidate!r}")


def load_ks_referendum(raw: pd.DataFrame, county_fips: Mapping[str, str]) -> pd.DataFrame:
    """Aggregate the Kansas precinct file to the county referendum panel.

    Counties arrive as names; the caller supplies the name->FIPS mapping
    (built from the project boundary file). Unknown names and unexpected
    candidate labels raise — silent dropping would shrink the panel
    invisibly, and a referendum has exactly two sides.
    """
    df = raw.loc[:, ["County", "Candidate", "Votes"]].copy()
    df["side"] = df["Candidate"].map(_side)

    names = df["County"].str.upper()
    unknown = sorted(set(names) - set(county_fips))
    if unknown:
        raise ValueError(f"County names with no FIPS mapping: {unknown}")
    df["fips"] = names.map(dict(county_fips))

    panel = (
        df.pivot_table(index="fips", columns="side", values="Votes", aggfunc="sum", fill_value=0)
        .reindex(columns=["yes_votes", "no_votes"], fill_value=0)
        .reset_index()
    )
    panel[["yes_votes", "no_votes"]] = panel[["yes_votes", "no_votes"]].astype("int64")
    panel["total_votes"] = panel["yes_votes"] + panel["no_votes"]
    panel["no_share"] = panel["no_votes"] / panel["total_votes"]
    return panel.sort_values("fips", ignore_index=True).loc[
        :, ["fips", "yes_votes", "no_votes", "total_votes", "no_share"]
    ]


def _wide_county_sheet_to_long(county_name: str, sheet: pd.DataFrame) -> pd.DataFrame:
    """Normalize one wide per-county sheet into the long (County, Candidate,
    Votes) shape the aggregator consumes.

    The two vote columns both start with "Constitutional Amendment"; which is
    Yes and which is No is declared in the data row whose two cells read
    YES/NO (a leading "NON" junk row precedes it in most counties). The
    county's count is taken from the sheet's own "COUNTY TOTALS" row, which is
    the SoS's authoritative figure — in Shawnee and Wyandotte it EXCEEDS the
    precinct sum because it includes provisional/advance votes not attributed
    to any precinct line, so summing precincts would silently drop real votes.
    """
    value_cols = [c for c in sheet.columns if str(c).startswith(_AMENDMENT_COLUMN_PREFIX)]
    side_label: dict[object, str] = {}
    for i in range(len(sheet)):
        cells = {str(sheet[c].iloc[i]).strip().upper() for c in value_cols}
        if cells == {"YES", "NO"}:
            side_label = {c: str(sheet[c].iloc[i]).strip().upper() for c in value_cols}
            break
    if not side_label:
        raise ValueError(f"No YES/NO marker row found in wide sheet for {county_name!r}")

    names = sheet["PRECINCT NAME"].astype(str).str.strip().str.upper()
    totals_rows = sheet[names == "COUNTY TOTALS"]
    if len(totals_rows) != 1:
        raise ValueError(
            f"Expected exactly one COUNTY TOTALS row in {county_name!r}, found {len(totals_rows)}"
        )
    totals = totals_rows.iloc[0]

    return pd.DataFrame(
        [
            {
                "County": county_name,
                "Candidate": f'Amendment, Constitutional - "{side_label[col]}"',
                "Votes": float(pd.to_numeric(totals[col])),
            }
            for col in value_cols
        ]
    )


def load_ks_referendum_workbook(path: str | Path, county_fips: Mapping[str, str]) -> pd.DataFrame:
    """Load the full Kansas referendum panel from the official workbook.

    Most counties are in the long main sheet; the four largest are split into
    separate WIDE sheets keyed by county name. Both layouts are normalized to
    the long shape and aggregated together — so the panel is complete, not
    the ~52% the main sheet alone yields (the gap the acceptance run caught).
    """
    workbook = pd.read_excel(path, sheet_name=None)
    long_frames = [workbook[_KS_MAIN_SHEET].loc[:, ["County", "Candidate", "Votes"]]]
    for sheet_name, sheet in workbook.items():
        if sheet_name == _KS_MAIN_SHEET:
            continue
        long_frames.append(_wide_county_sheet_to_long(sheet_name, sheet))
    return load_ks_referendum(pd.concat(long_frames, ignore_index=True), county_fips)
