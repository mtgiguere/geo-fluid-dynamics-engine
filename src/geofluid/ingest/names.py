"""Ingest the Social Security Administration's baby names by state.

Every name given to 5 or more babies of one sex in one state in one year,
1910-2025 (namesbystate.zip, public domain). Each new name is a wave that
millions of parents carry from state to state, a mass behaviour beside the
state laws (`geofluid.ingest.spid`) that a few hundred legislators carry.
The output keys the state by its two-digit FIPS code so it joins the county
and state data.
"""

import pandas as pd

from geofluid.ingest.solar import _STATE_POSTAL

# The state files have no header; these are the fields of each line.
RAW_NAME_COLUMNS = ["state", "sex", "year", "name", "births"]
NAME_COLUMNS = ["name", "sex", "state_fips", "year", "births"]

# Postal code -> FIPS, the inverse of the solar ingest's table (reference
# data kept in one place, not copied).
_POSTAL_FIPS = {postal: fips for fips, postal in _STATE_POSTAL.items()}


def load_state_names(raw: pd.DataFrame) -> pd.DataFrame:
    """Transform the raw state-file lines into canonical name counts."""
    out = raw.assign(state_fips=raw["state"].map(_POSTAL_FIPS))
    # A code with no FIPS (a territory, a typo) would become a blank state
    # and silently drop out of every neighbour count.
    unknown = sorted(set(out.loc[out["state_fips"].isna(), "state"]))
    if unknown:
        raise ValueError(f"SSA state codes with no FIPS code: {unknown}")
    return out.loc[:, NAME_COLUMNS]
