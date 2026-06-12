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

import numpy as np
import pandas as pd

from geofluid.spatial.weights import spatial_weights


def _usable_subset(
    values: "pd.Series[float]", adjacency: Mapping[str, frozenset[str]]
) -> dict[str, frozenset[str]]:
    """Listwise exclusion, in three layers: a county participates only if it
    has a non-missing value AND at least one neighbor that also does.
    Islands (no neighbors), NaN counties, counties absent from the values
    index, and counties orphaned by their neighbors' missingness all drop
    out — symmetry of adjacency guarantees the kept neighbors of a kept
    county are themselves kept, so the subset is closed."""
    present = values.dropna()
    usable = {fips for fips in adjacency if fips in present.index}
    kept = {fips for fips in usable if adjacency[fips] & usable}
    return {fips: frozenset(adjacency[fips] & usable) for fips in kept}


def morans_i(values: "pd.Series[float]", adjacency: Mapping[str, frozenset[str]]) -> float:
    """Global Moran's I of a fips-indexed series under queen adjacency.

    Alignment is internal — values are matched to the weights matrix by fips
    index, never by position (TDD_CONTRACT.md Bug #3 lived in exactly that
    positional assumption).
    """
    matrix, order = spatial_weights(_usable_subset(values, adjacency))
    n = len(order)
    # Below three usable counties the statistic is meaningless: a single
    # pair yields exactly +/-1 for ANY data — a confident-looking artifact.
    if n < 3:
        raise ValueError(f"Moran's I needs at least 3 usable counties, found {n}")

    z = values.loc[order].to_numpy(dtype=float)
    z = z - z.mean()
    denominator = z @ z
    # Zero variance makes I equal 0/0: undefined, not "no autocorrelation".
    # numpy would silently emit NaN here — that is a fabricated finding.
    if denominator == 0.0:
        raise ValueError("Moran's I is undefined for a constant field (zero variance)")

    s0 = matrix.sum()
    return float((n / s0) * (z @ matrix @ z) / denominator)


def local_morans_i(
    values: "pd.Series[float]", adjacency: Mapping[str, frozenset[str]]
) -> pd.DataFrame:
    """Local Moran's I (LISA): each county's contribution to the global
    pattern, I_i = z_i * (W z)_i / m2 with m2 = z'z / n.

    Returns a DataFrame indexed by the usable fips with column i_local.
    Positive I_i: the county resembles its neighbors (part of a cluster —
    a wave core or a calm basin). Negative: it defies them (an outlier).
    """
    matrix, order = spatial_weights(_usable_subset(values, adjacency))
    z = values.loc[order].to_numpy(dtype=float)
    z = z - z.mean()
    m2 = (z @ z) / len(order)
    lag = matrix @ z
    # The LISA quadrants: own value vs neighborhood average, both relative
    # to the mean. high-high = wave core, low-low = calm basin, high-low =
    # defiant outlier, low-high = a hole inside a wave.
    own = np.where(z >= 0, "high", "low")
    neighborhood = np.where(lag >= 0, "high", "low")
    quadrant = np.char.add(np.char.add(own, "-"), neighborhood)
    return pd.DataFrame(
        {"i_local": z * lag / m2, "quadrant": quadrant},
        index=pd.Index(order, name="fips"),
    )
