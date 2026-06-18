"""Temporal lead-lag node influence — the Gravity Engine retry (spec Module 2).

The contemporaneous-conformity classifier in `influence.py` was falsified on real
data: presidential swing is so spatially autocorrelated that every county co-moves
with its neighbourhood within an election, so same-election correlation cannot
separate the roles the spec cares about. A Bellwether and a Buffer BOTH co-move —
the difference is timing. The Bellwether's swing *precedes* its region's; the
Buffer's *echoes* it.

`lead_lag` reads that timing off the panel. For a county with own swing series
o(t) and neighbourhood-mean swing series h(t):

    lead = corr(o(t), h(t + 1))   # the county moves first, the region follows -> LEADS
    lag  = corr(o(t), h(t - 1))   # the county echoes what the region already did -> FOLLOWS
    lead_lag = lead - lag          # > 0 Bellwether-like, < 0 Buffer-like

The one-election shift is positional over the sorted election columns (the next
contest, not the next calendar year), so it is unaffected by the irregular spacing
of the pre-2000 historical returns. This needs the time depth the 1868-2024 spine
provides; over seven modern elections alone the lagged correlations were too thin.
"""

from collections.abc import Mapping

import numpy as np
import pandas as pd


def lead_lag(
    panel: pd.DataFrame,
    adjacency: Mapping[str, frozenset[str]],
    value_column: str,
) -> pd.Series:
    """Per-county lead-lag score from a long (fips, year, value) panel.

    Returns a Series indexed by fips: a county's correlation with its
    neighbourhood one election in the future, minus its correlation one election
    in the past. Positive means the county tends to move before its region
    (Bellwether-like); negative means it moves after (Buffer-like).
    """
    wide = panel.pivot_table(index="fips", columns="year", values=value_column)

    scores: dict[str, float] = {}
    for fips in wide.index:
        own = wide.loc[fips].to_numpy()
        neighbours = [n for n in adjacency.get(fips, frozenset()) if n in wide.index]
        hood = wide.loc[neighbours].mean(axis=0).to_numpy()

        # Pair own(t) with the neighbourhood one election later (lead) and one
        # election earlier (lag), positionally over the sorted election columns.
        lead = np.corrcoef(own[:-1], hood[1:])[0, 1]
        lag = np.corrcoef(own[1:], hood[:-1])[0, 1]
        scores[fips] = float(lead - lag)

    return pd.Series(scores, name="lead_lag").sort_index()
