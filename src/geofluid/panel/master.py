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
#   51515 -> 51019: Bedford City VA, an independent city through 2013, merged
#                   into Bedford County; its 2000-2012 votes aggregate into
#                   the county's rows (current-geography harmonization).
_FIPS_RECODES = {"46113": "46102", "51515": "51019"}

_VOTE_COLUMNS = ["dem_votes", "rep_votes", "other_votes", "total_votes"]


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

    # Recodes can merge two jurisdictions into one (Bedford City's votes join
    # Bedford County's for 2000-2012). Aggregate to one row per (fips, year),
    # recomputing the two-party share from the summed votes — an identity for
    # every county that was not part of a merge.
    ret = ret.groupby(["fips", "year"], as_index=False)[_VOTE_COLUMNS].sum()
    ret["dem_share_2p"] = ret["dem_votes"] / (ret["dem_votes"] + ret["rep_votes"])

    demo = demographics.rename(columns={"year": "acs_vintage"})
    panel = ret.merge(demo, on="fips", how="left")

    # Outside the policy exclusions, a county without demographics is a data
    # defect. A silent left-join NaN would propagate through every downstream
    # mean and model fit — fail here, naming the counties, so the defect is
    # diagnosable from the message alone.
    unmatched = sorted(panel.loc[panel["acs_vintage"].isna(), "fips"].unique())
    if unmatched:
        raise ValueError(f"Counties missing demographics: {unmatched}")
    # Recoding changes sort positions (46113 -> 46102 moves the county
    # earlier); re-sort so serialization and diffs stay deterministic.
    return panel.sort_values(["fips", "year"], ignore_index=True)
