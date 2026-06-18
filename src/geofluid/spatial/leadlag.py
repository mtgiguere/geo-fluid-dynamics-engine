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
import numpy.typing as npt
import pandas as pd

# Minimum non-missing paired observations for a lagged correlation to mean
# anything. Two paired points are always +/-1 by construction; require more.
_MIN_PAIRED = 3


def _lagged_corr(
    own: npt.NDArray[np.float64],
    hood: npt.NDArray[np.float64],
    min_paired: int,
) -> float | None:
    """Pearson correlation of own(t) against hood(t) over the elections where both
    are present. Returns None when fewer than `min_paired` pairs survive, so the
    caller can exclude the county rather than fabricate a score from too little.

    `own` and `hood` are passed already shifted by one election relative to each
    other (own[:-1] with hood[1:] for the lead, own[1:] with hood[:-1] for the lag)."""
    mask = ~(np.isnan(own) | np.isnan(hood))
    if int(mask.sum()) < min_paired:
        return None
    return float(np.corrcoef(own[mask], hood[mask])[0, 1])


def lead_lag(
    panel: pd.DataFrame,
    adjacency: Mapping[str, frozenset[str]],
    value_column: str,
    min_paired: int = _MIN_PAIRED,
) -> pd.Series:
    """Per-county lead-lag score from a long (fips, year, value) panel.

    Returns a Series indexed by fips: a county's correlation with its
    neighbourhood one election in the future, minus its correlation one election
    in the past. Positive means the county tends to move before its region
    (Bellwether-like); negative means it moves after (Buffer-like).

    A county is excluded (absent from the Series) when either its lead or its lag
    correlation has fewer than `min_paired` paired elections — a score from too
    little overlap is meaningless, so it is never fabricated.
    """
    wide = panel.pivot_table(index="fips", columns="year", values=value_column)

    scores: dict[str, float] = {}
    for fips in wide.index:
        own = wide.loc[fips].to_numpy()
        neighbours = [n for n in adjacency.get(fips, frozenset()) if n in wide.index]
        hood = wide.loc[neighbours].mean(axis=0).to_numpy()

        # Pair own(t) with the neighbourhood one election later (lead) and one
        # election earlier (lag), positionally over the sorted election columns.
        lead = _lagged_corr(own[:-1], hood[1:], min_paired)
        lag = _lagged_corr(own[1:], hood[:-1], min_paired)
        if lead is None or lag is None:
            continue
        scores[fips] = lead - lag

    return pd.Series(scores, name="lead_lag", dtype=float).sort_index()
