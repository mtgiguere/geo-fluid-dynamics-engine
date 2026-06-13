"""Ingest official referendum results into a county panel.

Referendums are the engine's purest fuel: actual county-level votes on
TOPICS (abortion, marijuana, wages) rather than parties — the data Module 3
needs to measure the gap between a county's partisan identity and its issue
behavior. First source: the Kansas SoS precinct file for the August 2022
constitutional amendment.

Semantics: the panel carries raw yes/no plus no_share and stays agnostic
about politics. For Kansas 2022 specifically, "NO" preserved abortion
rights — which side is "liberal" is a per-measure fact that belongs to the
analysis layer, never hardcoded here.
"""

from collections.abc import Mapping

import pandas as pd

_SIDE_BY_CANDIDATE_SUFFIX = {'"YES"': "yes_votes", '"NO"': "no_votes"}


def _side(candidate: str) -> str:
    """Map the official candidate string to a referendum side, loudly."""
    for suffix, side in _SIDE_BY_CANDIDATE_SUFFIX.items():
        if candidate.strip().endswith(suffix):
            return side
    raise ValueError(f"Unexpected referendum candidate label: {candidate!r}")


def load_ks_referendum(raw: pd.DataFrame, county_fips: Mapping[str, str]) -> pd.DataFrame:
    """Aggregate the Kansas precinct file to the county referendum panel.

    Counties arrive as names; the caller supplies the name->FIPS mapping
    (built from the project boundary file). Unknown names and unexpected
    candidate labels raise — silent dropping would shrink the panel
    invisibly, and a referendum has exactly two sides.
    """
    df = raw.loc[:, ["County", "Candidate", "Votes"]].copy()
    df["side"] = df["Candidate"].map(_side)

    names = df["County"].str.upper()
    unknown = sorted(set(names) - set(county_fips))
    if unknown:
        raise ValueError(f"County names with no FIPS mapping: {unknown}")
    df["fips"] = names.map(dict(county_fips))

    panel = (
        df.pivot_table(index="fips", columns="side", values="Votes", aggfunc="sum", fill_value=0)
        .reindex(columns=["yes_votes", "no_votes"], fill_value=0)
        .reset_index()
    )
    panel[["yes_votes", "no_votes"]] = panel[["yes_votes", "no_votes"]].astype("int64")
    panel["total_votes"] = panel["yes_votes"] + panel["no_votes"]
    panel["no_share"] = panel["no_votes"] / panel["total_votes"]
    return panel.sort_values("fips", ignore_index=True).loc[
        :, ["fips", "yes_votes", "no_votes", "total_votes", "no_share"]
    ]
