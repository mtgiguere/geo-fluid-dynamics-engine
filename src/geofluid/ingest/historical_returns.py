"""Ingest Algara-Sharif county presidential returns (1868-2020).

The raw input is the `pres_elections_release` object from the Algara & Sharif
"Partisanship & Nationalization" dataset (Harvard Dataverse doi:10.7910/DVN/
DGUMFI), read from RData via pyreadr in the export layer. It is already
FIPS-coded with county-lifespan metadata — the authors did the 150-year
boundary harmonization, so this loader is a straight mapping onto the
canonical returns-panel schema (identical to `load_county_returns`), letting
the whole downstream pipeline run over a century and a half unchanged.
"""

import pandas as pd

# Identical to the MIT returns panel so the two sources share one spine.
PANEL_COLUMNS = [
    "fips",
    "year",
    "dem_votes",
    "rep_votes",
    "other_votes",
    "total_votes",
    "dem_share_2p",
]


def load_historical_returns(raw: pd.DataFrame) -> pd.DataFrame:
    """Map Algara-Sharif rows to the canonical county-year returns panel."""
    df = raw.loc[
        :,
        [
            "fips",
            "election_year",
            "democratic_raw_votes",
            "republican_raw_votes",
            "raw_county_vote_totals",
        ],
    ].copy()

    # A county-year without recorded two-party votes (a county that did not
    # yet exist, or no returns) has no two-party share — drop it rather than
    # fabricate a zero.
    df = df.dropna(subset=["democratic_raw_votes", "republican_raw_votes"])
    df = df[(df["democratic_raw_votes"] + df["republican_raw_votes"]) > 0]

    panel = pd.DataFrame(
        {
            "fips": df["fips"].astype(str),
            "year": df["election_year"].astype(int),
            "dem_votes": df["democratic_raw_votes"].astype("int64"),
            "rep_votes": df["republican_raw_votes"].astype("int64"),
        }
    )
    # raw_county_vote_totals counts every candidate; the others bloc is what's
    # left after the two major parties. Where the total is missing, fall back
    # to the two-party sum (no third-party data for that county-year).
    total = df["raw_county_vote_totals"].fillna(
        df["democratic_raw_votes"] + df["republican_raw_votes"]
    )
    panel["total_votes"] = total.astype("int64")
    panel["other_votes"] = panel["total_votes"] - panel["dem_votes"] - panel["rep_votes"]
    panel["dem_share_2p"] = panel["dem_votes"] / (panel["dem_votes"] + panel["rep_votes"])

    return panel.sort_values(["fips", "year"], ignore_index=True).loc[:, PANEL_COLUMNS]
