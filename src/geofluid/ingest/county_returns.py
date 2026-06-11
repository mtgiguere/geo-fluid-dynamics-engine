"""Ingest county-level presidential returns into the canonical county-year panel.

The raw input is the MIT Election Data + Science Lab county presidential returns
format: one row per (year, county, candidate, vote mode). The output is one row
per (county, year) — the panel that the descriptive map, the historical wave
replay, and every predictive module consume.

Design note: this module exposes a single public function rather than separate
parse/filter/pivot/validate steps. The consumer cannot call pipeline steps in the
wrong order or forget a validation step, because there are no steps to misuse —
`load_county_returns` guarantees its output satisfies the panel contract
specified in tests/unit/test_county_returns.py.
"""

import pandas as pd

# Parties are collapsed into three blocs. County-level presidential politics in
# the United States is overwhelmingly two-party; minor parties are aggregated as
# "other" so the panel schema stays stable regardless of which parties happened
# to file in a given year.
_PARTY_BLOC = {"DEMOCRAT": "dem_votes", "REPUBLICAN": "rep_votes"}
_BLOC_COLUMNS = ["dem_votes", "rep_votes", "other_votes"]

# The canonical panel schema, in order. dem_share_2p is the TWO-PARTY share —
# Democratic votes over (Democratic + Republican) — the standard quantity for
# tracking partisan movement over time, because it is not distorted by
# year-to-year swings in third-party participation.
PANEL_COLUMNS = ["fips", "year", *_BLOC_COLUMNS, "total_votes", "dem_share_2p"]


def load_county_returns(raw: pd.DataFrame) -> pd.DataFrame:
    """Transform raw MIT-format county returns into the canonical county-year panel."""
    df = raw.loc[:, ["county_fips", "year", "party", "candidatevotes"]].copy()
    # county_fips arrives as float in the raw file (missing values force float
    # dtype), so the canonical form is reached via float -> int -> zero-padded
    # 5-character string: 1001.0 -> "01001". String inputs like "29189" take the
    # same path unchanged.
    df["fips"] = df["county_fips"].astype(float).astype(int).astype(str).str.zfill(5)
    df["bloc"] = df["party"].map(_PARTY_BLOC).fillna("other_votes")

    panel = (
        df.pivot_table(
            index=["fips", "year"],
            columns="bloc",
            values="candidatevotes",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(columns=_BLOC_COLUMNS, fill_value=0)
        .reset_index()
    )
    panel["total_votes"] = panel[_BLOC_COLUMNS].sum(axis=1)
    panel["dem_share_2p"] = panel["dem_votes"] / (panel["dem_votes"] + panel["rep_votes"])
    return panel.loc[:, PANEL_COLUMNS]
