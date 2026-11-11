"""Ingest the State Policy Innovation and Diffusion (SPID) database.

SPID v1.2 (Boehmke, LaCombe and Brockway; Harvard Dataverse
doi:10.7910/DVN/CVYSR7, CC0) records the year each state first adopted each
of 724 policies, 1691-2017. Each policy is a separate political wave over
the same 50 states, which is what the question "do the roads a wave travels
change over time?" needs. The output is one row per adoption, keyed by the
state's two-digit FIPS code so it joins the county data.
"""

import pandas as pd

from geofluid.scope import _STATE_NAMES

ADOPTION_COLUMNS = ["policy", "state_fips", "adopt_year", "topic", "source"]

# State name -> FIPS, the inverse of the scope catalog's FIPS -> name table
# (reference data kept in one place, not copied).
_STATE_FIPS = {name: fips for fips, name in _STATE_NAMES.items()}


def load_spid_adoptions(adoptions: pd.DataFrame, policies: pd.DataFrame) -> pd.DataFrame:
    """Transform the raw SPID adoption and policy files into canonical adoptions."""
    # An adoption whose policy is not in the policy list would vanish in the
    # join below, and with it a piece of a wave.
    orphans = sorted(set(adoptions["policy"]) - set(policies["policy"]))
    if orphans:
        raise ValueError(f"SPID adoptions of policies not in the policy list: {orphans}")
    out = adoptions.merge(
        policies.loc[:, ["policy", "majortopic_str", "source"]], on="policy"
    ).rename(columns={"majortopic_str": "topic"})
    out["state_fips"] = out["statenam"].map(_STATE_FIPS)
    # A name with no FIPS code (a misspelling, a territory) would become a
    # blank state and silently drop out of every neighbour count.
    unknown = sorted(set(out.loc[out["state_fips"].isna(), "statenam"]))
    if unknown:
        raise ValueError(f"SPID state names with no FIPS code: {unknown}")
    return out.loc[:, ADOPTION_COLUMNS]
