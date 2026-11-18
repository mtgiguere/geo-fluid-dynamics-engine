"""Assign each ZIP code to one county, from the Census ZCTA-county relationship file.

Data located by ZIP (solar installs, and much other non-election data) has to
reach the engine's county map, adjacency and "roads" (commuting, migration).
The Census 2020 relationship file (`tab20_zcta520_county20_natl.txt`) lists
every piece of a ZIP Code Tabulation Area that falls inside a county, with the
piece's land area. The output is one row per ZIP: the county it belongs to.
"""

import pandas as pd

LOOKUP_COLUMNS = ["zip5", "fips"]


def zip_to_county(rel: pd.DataFrame) -> pd.DataFrame:
    """Reduce the relationship file to one county per ZIP."""
    lookup = rel.rename(columns={"GEOID_ZCTA5_20": "zip5", "GEOID_COUNTY_20": "fips"})
    # Rows with a blank ZCTA are county land that lies in no ZIP area (the
    # file opens with them); they say nothing about any ZIP.
    lookup = lookup.dropna(subset=["zip5"])
    # About 10,000 of the 33,791 ZIP areas cross a county line. Each goes
    # whole to the county holding the most of its land. The file is read as
    # text, and as text "900" sorts above "7000", so the area is compared as
    # a number.
    lookup["land"] = pd.to_numeric(lookup["AREALAND_PART"])
    lookup = lookup.sort_values("land", ascending=False).drop_duplicates("zip5")
    return lookup.loc[:, LOOKUP_COLUMNS].reset_index(drop=True)
