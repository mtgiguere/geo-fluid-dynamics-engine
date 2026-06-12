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
    values: "pd.Series[float]",
    adjacency: Mapping[str, frozenset[str]],
    *,
    permutations: int | None = None,
    rng: np.random.Generator | None = None,
) -> pd.DataFrame:
    """Local Moran's I (LISA): each county's contribution to the global
    pattern, I_i = z_i * (W z)_i / m2 with m2 = z'z / n.

    Returns a DataFrame indexed by the usable fips with column i_local.
    Positive I_i: the county resembles its neighbors (part of a cluster —
    a wave core or a calm basin). Negative: it defies them (an outlier).

    With `permutations`, adds a pseudo p-value per county via conditional
    permutation (Anselin): the county's own value stays fixed while the
    others are shuffled across the remaining locations, asking "how often
    would a neighborhood this coherent arise by chance?" One-sided in the
    direction of the observed statistic; p = (extreme + 1)/(permutations + 1).
    Pass a seeded numpy Generator via `rng` for reproducible published runs.
    """
    sub_adjacency = _usable_subset(values, adjacency)
    matrix, order = spatial_weights(sub_adjacency)
    z = values.loc[order].to_numpy(dtype=float)
    z = z - z.mean()
    m2 = (z @ z) / len(order)
    lag = matrix @ z
    i_local = z * lag / m2
    # The LISA quadrants: own value vs neighborhood average, both relative
    # to the mean. high-high = wave core, low-low = calm basin, high-low =
    # defiant outlier, low-high = a hole inside a wave.
    own = np.where(z >= 0, "high", "low")
    neighborhood = np.where(lag >= 0, "high", "low")
    quadrant = np.char.add(np.char.add(own, "-"), neighborhood)
    frame = pd.DataFrame(
        {"i_local": i_local, "quadrant": quadrant},
        index=pd.Index(order, name="fips"),
    )

    if permutations is not None:
        generator = rng if rng is not None else np.random.default_rng()
        n = len(order)
        max_k = max(len(sub_adjacency[fips]) for fips in order)
        # One shared bank of permutations (PySAL's trick): each row is a
        # random ordering of the n-1 "other" positions; county i reads its
        # first k_i columns as that permutation's neighbor draw.
        draw_bank = np.argsort(generator.random((permutations, n - 1)), axis=1)[:, :max_k]
        p_values = np.empty(n)
        for i, fips in enumerate(order):
            k = len(sub_adjacency[fips])
            others = np.delete(z, i)
            simulated = z[i] * others[draw_bank[:, :k]].mean(axis=1) / m2
            if i_local[i] >= 0:
                extreme = int((simulated >= i_local[i]).sum())
            else:
                extreme = int((simulated <= i_local[i]).sum())
            p_values[i] = (extreme + 1) / (permutations + 1)
        frame["p_value"] = p_values
    return frame


def significant_quadrants(lisa: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """Map honesty: keep a quadrant label only where the clustering beats
    chance at the chosen alpha; everything else becomes None (gray on the
    map via the existing null path). Values and p-values stay untouched —
    the mask hides labels, never evidence."""
    masked = lisa.copy()
    # astype(object) so the masked entries are literal None, not the NaN
    # pandas' string dtype would silently substitute — "no label" is a
    # decision, and None says so unambiguously.
    masked["quadrant"] = masked["quadrant"].astype(object).where(masked["p_value"] <= alpha, None)
    return masked


def local_morans_by_year(
    panel: pd.DataFrame,
    adjacency: Mapping[str, frozenset[str]],
    value_column: str,
) -> pd.DataFrame:
    """One LISA run per election year, returned tidy: fips, year, i_local,
    quadrant. Counties excluded for a year (missing value, island, orphan)
    have no row that year — absence, never a fabricated label."""
    frames = []
    for year in sorted(panel["year"].unique()):
        values = panel[panel["year"] == year].set_index("fips")[value_column]
        local = local_morans_i(values, adjacency).reset_index()
        local.insert(1, "year", year)
        frames.append(local)
    return pd.concat(frames, ignore_index=True)
