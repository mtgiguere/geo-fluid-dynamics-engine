"""Moran's I: global spatial autocorrelation of a county-level quantity.

The statistic behind Module 1's founding question. I ranges from roughly +1
(neighbors resemble each other — waves, clusters, fronts) through 0 (spatial
noise; the expectation under no autocorrelation is -1/(n-1), slightly below
zero) to roughly -1 (neighbors oppose each other — a checkerboard).

With row-standardized W the formula reduces to

    I = (n / S0) * (z' W z) / (z' z)        z = values - mean(values)

where S0 is the sum of all weights. In plain language: the average
co-movement between each county and the mean of its neighbors, scaled by the
overall variance. If swing were scattered randomly across the map, I would
sit near zero; political waves show up as strongly positive I.
"""

from collections.abc import Mapping

import pandas as pd

from geofluid.spatial.weights import spatial_weights


def morans_i(values: "pd.Series[float]", adjacency: Mapping[str, frozenset[str]]) -> float:
    """Global Moran's I of a fips-indexed series under queen adjacency.

    Alignment is internal — values are matched to the weights matrix by fips
    index, never by position (TDD_CONTRACT.md Bug #3 lived in exactly that
    positional assumption).
    """
    # Listwise exclusion, in three layers: a county participates only if it
    # has a non-missing value AND at least one neighbor that also does.
    # Islands (no neighbors), NaN counties, counties absent from the values
    # index, and counties orphaned by their neighbors' missingness all drop
    # out — symmetry of adjacency guarantees the kept neighbors of a kept
    # county are themselves kept, so the subset is closed.
    present = values.dropna()
    usable = {fips for fips in adjacency if fips in present.index}
    kept = {fips for fips in usable if adjacency[fips] & usable}
    sub_adjacency = {fips: frozenset(adjacency[fips] & usable) for fips in kept}

    matrix, order = spatial_weights(sub_adjacency)

    z = values.loc[order].to_numpy(dtype=float)
    z = z - z.mean()
    s0 = matrix.sum()
    n = len(order)
    return float((n / s0) * (z @ matrix @ z) / (z @ z))
