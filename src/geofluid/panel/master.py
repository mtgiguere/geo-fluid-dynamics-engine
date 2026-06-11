"""The master panel: county election returns joined with demographic context.

The ingest panels stay faithful to their sources; every geography
reconciliation between them is decided here, explicitly. The join policy is
specified in tests/unit/test_master_panel.py, one test per decision.
"""

import pandas as pd


def build_master_panel(returns: pd.DataFrame, demographics: pd.DataFrame) -> pd.DataFrame:
    """Join the returns panel with the demographics panel on county FIPS.

    The demographics panel's "year" column is renamed "acs_vintage": the
    election year and the survey vintage are different facts (a 2024 election
    viewed through 2023 ACS context) and must never collide in one column.
    """
    demo = demographics.rename(columns={"year": "acs_vintage"})
    return returns.merge(demo, on="fips", how="left")
