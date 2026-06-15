"""Realignment detection (spec Module 4, the Chaos Sensor — seed).

A realignment is when the old rules stop predicting: counties land far from
where their own recent trajectory pointed, the misses are spatially coherent
(not noise), and they line up on a new cleavage. This module provides the
core primitive — the per-county trend surprise. Spatial coherence is measured
with `geofluid.spatial.moran.morans_i`; the axis a realignment runs on is read
off in analysis (e.g. correlating the surprise with education or region).

The 1964 (Southern) and 2016 (education) realignments both light up under this
method — see the analysis notebook.
"""

import numpy as np
import pandas as pd


def trend_surprise(
    panel: pd.DataFrame,
    target_year: int,
    value_column: str,
    window: int = 8,
    min_obs: int = 5,
) -> "pd.Series[float]":
    """Per-county residual of the target election from its own trend.

    For each county, fit a linear trend through the `window` elections
    strictly BEFORE `target_year` (presidential cadence, so a span of
    4*window years), extrapolate to the target, and return actual minus
    predicted. Counties with fewer than `min_obs` training points, or no
    value in the target election, are excluded — never fabricated.

    Negative = the county landed more Republican than its trajectory
    predicted; positive = more Democratic.
    """
    wide = panel.pivot_table(index="fips", columns="year", values=value_column)
    years = sorted(int(y) for y in wide.columns)
    if target_year not in years:
        return pd.Series(dtype=float, name="trend_surprise")
    train_years = [y for y in years if target_year - 4 * window <= y < target_year]

    residuals: dict[str, float] = {}
    for fips, row in wide.iterrows():
        actual = row[target_year]
        if pd.isna(actual):
            continue
        observed = [(y, float(row[y])) for y in train_years if pd.notna(row[y])]
        if len(observed) < min_obs:
            continue
        fit_years = np.array([y for y, _ in observed], dtype=float)
        fit_values = np.array([v for _, v in observed])
        slope, intercept = np.polyfit(fit_years, fit_values, 1)
        residuals[str(fips)] = float(actual) - (slope * target_year + intercept)

    return pd.Series(residuals, name="trend_surprise")
