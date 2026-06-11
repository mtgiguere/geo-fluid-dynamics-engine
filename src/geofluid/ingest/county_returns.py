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

# Vote-mode labels that mean "this row is the county's complete count" rather
# than one reporting channel (election day, absentee, early, ...). Both labels
# appear in the raw data: "TOTAL" through 2020, "TOTAL VOTES" in 2024.
_TOTAL_MODES = ["TOTAL", "TOTAL VOTES"]

# The canonical panel schema, in order. dem_share_2p is the TWO-PARTY share —
# Democratic votes over (Democratic + Republican) — the standard quantity for
# tracking partisan movement over time, because it is not distorted by
# year-to-year swings in third-party participation.
PANEL_COLUMNS = ["fips", "year", *_BLOC_COLUMNS, "total_votes", "dem_share_2p"]


def load_county_returns(raw: pd.DataFrame) -> pd.DataFrame:
    """Transform raw MIT-format county returns into the canonical county-year panel."""
    df = raw.loc[:, ["county_fips", "year", "party", "candidatevotes", "mode"]].copy()

    # Rows without a county FIPS are not counties — the raw file uses them for
    # statewide records such as "FEDERAL PRECINCT" overseas-absentee ballots.
    # A county panel cannot represent them, so they are excluded here rather
    # than crashing the cast below or fabricating a join key.
    df = df.dropna(subset=["county_fips"])

    # Rows without a party are bookkeeping, not candidate votes: the 2024 file
    # carries "TOTAL VOTES CAST" pseudo-candidate rows (party=NaN) holding each
    # county's reported turnout. Counting them would double total_votes.
    df = df.dropna(subset=["party"])
    # county_fips arrives as float in the raw file (missing values force float
    # dtype), so the canonical form is reached via float -> int -> zero-padded
    # 5-character string: 1001.0 -> "01001". String inputs like "29189" take the
    # same path unchanged.
    df["fips"] = df["county_fips"].astype(float).astype(int).astype(str).str.zfill(5)

    # Total-mode precedence. Some states report a county's complete count as a
    # TOTAL / TOTAL VOTES row AND the per-channel breakdown alongside it
    # (Texas 2024, Utah 2020). Summing everything would count those ballots
    # twice — when a county-year's total-mode rows carry the votes, they alone
    # are the truth and every sub-mode row is discarded.
    #
    # The precedence is conditional on the total rows actually carrying votes:
    # other states (Arkansas, Louisiana, Oklahoma, Pennsylvania in 2024) ship
    # zero-vote placeholder TOTAL rows with the real count in the sub-mode
    # rows. For those, the sub-mode sum is the county's count.
    #
    # A deliberate consequence: county-years whose rows are ALL zero-vote
    # placeholders (Alaska's DISTRICT 99, defunct Bedford City VA) drop out of
    # the panel entirely — zero ballots is not an observation.
    is_total_mode = df["mode"].isin(_TOTAL_MODES)
    votes_in_total_rows = df["candidatevotes"].where(is_total_mode, 0)
    total_rows_carry_votes = (
        votes_in_total_rows.groupby([df["fips"], df["year"]]).transform("sum") > 0
    )
    df = df[is_total_mode == total_rows_carry_votes]

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
    # Vote counts are integers by definition. The raw candidatevotes column can
    # arrive as float — NaN for unreported minor-candidate values (New Mexico
    # 2024) forces float dtype. The sum already treats unreported as zero;
    # the cast guarantees no NaN leaked through and restores integer votes.
    panel[_BLOC_COLUMNS] = panel[_BLOC_COLUMNS].astype("int64")
    panel["total_votes"] = panel[_BLOC_COLUMNS].sum(axis=1)
    panel["dem_share_2p"] = panel["dem_votes"] / (panel["dem_votes"] + panel["rep_votes"])
    return panel.loc[:, PANEL_COLUMNS]
