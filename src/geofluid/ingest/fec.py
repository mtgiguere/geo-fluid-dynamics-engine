"""Ingest FEC individual contributions: political giving, dated to the day and
placed by ZIP code.

A donation is a political act with a date and a place, the first political
"adoption" the timing model (`geofluid.spatial.timing`) can follow from
neighbour to neighbour. Source: the FEC bulk file of individual
contributions for a two-year cycle (`indiv22.zip`), public.
"""

import pandas as pd

# The bulk file has no header; these are its fields, from FEC's
# indiv_header_file.csv.
RAW_INDIV_COLUMNS = [
    "CMTE_ID", "AMNDT_IND", "RPT_TP", "TRANSACTION_PGI", "IMAGE_NUM", "TRANSACTION_TP",
    "ENTITY_TP", "NAME", "CITY", "STATE", "ZIP_CODE", "EMPLOYER", "OCCUPATION",
    "TRANSACTION_DT", "TRANSACTION_AMT", "OTHER_ID", "TRAN_ID", "FILE_NUM", "MEMO_CD",
    "MEMO_TEXT", "SUB_ID",
]  # fmt: skip
CONTRIBUTION_COLUMNS = ["cmte_id", "other_id", "zip5", "state", "date", "amount", "memo_cd"]


def load_contributions(raw: pd.DataFrame) -> pd.DataFrame:
    """Transform raw FEC lines (all fields text) into canonical contributions."""
    # Money from organisations, PACs and party committees is a transfer, not
    # a person in a ZIP code deciding to give.
    raw = raw[raw["ENTITY_TP"] == "IND"]
    out = pd.DataFrame(
        {
            "cmte_id": raw["CMTE_ID"],
            "other_id": raw["OTHER_ID"],
            # The first five digits place a gift in a ZIP, and through it a county.
            "zip5": raw["ZIP_CODE"].str[:5],
            "state": raw["STATE"],
            "date": pd.to_datetime(raw["TRANSACTION_DT"], format="%m%d%Y", errors="coerce"),
            "amount": raw["TRANSACTION_AMT"].astype(float),
            "memo_cd": raw["MEMO_CD"],
        }
    )
    # A gift with a blank or impossible date cannot be placed in time; FEC
    # itself sets such rows aside. It is left out, not guessed.
    out = out[out["date"].notna()]
    return out.loc[:, CONTRIBUTION_COLUMNS]
