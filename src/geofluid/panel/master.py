"""The master panel: county election returns joined with demographic context.

The ingest panels stay faithful to their sources; every geography
reconciliation between them is decided here, explicitly. The join policy is
specified in tests/unit/test_master_panel.py, one test per decision.
"""

import pandas as pd

# Counties renamed or recoded over the study period. Applied to the returns
# side before joining: the returns file spans 2000-2024 and uses whichever
# code was current when (or, for Shannon/Oglala Lakota, inconsistently even
# within one release); demographics use only the current code.
#   46113 -> 46102: Shannon County SD renamed Oglala Lakota County (2015).
_FIPS_RECODES = {"46113": "46102"}


def build_master_panel(returns: pd.DataFrame, demographics: pd.DataFrame) -> pd.DataFrame:
    """Join the returns panel with the demographics panel on county FIPS.

    The demographics panel's "year" column is renamed "acs_vintage": the
    election year and the survey vintage are different facts (a 2024 election
    viewed through 2023 ACS context) and must never collide in one column.
    """
    ret = returns.assign(fips=returns["fips"].replace(_FIPS_RECODES))

    # Policy exclusions — geographies that can never join, removed silently
    # and deliberately (any OTHER unmatched county is an error, not policy):
    #  - Alaska (02xxx): elections are reported by legislative district,
    #    demographics by borough; no county-level crosswalk exists. Alaska
    #    is analyzed statewide, never at "county" level.
    #  - State buckets (XX000, e.g. New York's 36000 unallocated absentee
    #    votes in 2024): real votes that belong to no county.
    is_alaska = ret["fips"].str.startswith("02")
    is_state_bucket = ret["fips"].str.endswith("000")
    ret = ret[~is_alaska & ~is_state_bucket]

    demo = demographics.rename(columns={"year": "acs_vintage"})
    return ret.merge(demo, on="fips", how="left")
