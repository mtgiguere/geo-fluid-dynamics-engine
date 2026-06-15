"""County influence metrics — the Gravity Engine (spec Module 2).

The spec classifies counties by their role in how ideas spread: the Buffer
Zone is permeable and takes cues from its neighbours; the Ideological Bastion
resists outside ideas while anchoring the region around it. Both are read
from how a county's swing co-moves with its neighbourhood across elections.

This module computes the per-county primitives; `classify_nodes` turns them
into roles. With only seven presidential elections the metrics are
descriptive, not inferential — see the module tests and the acceptance run.

ACCEPTANCE FINDING (2026-06-15) — the contemporaneous-conformity classifier
is NOT deployed, because the real-data acceptance run falsified it:
  - 96% of counties classified as "buffer"; the spec's own Bastion example
    (Pulaski County / Ft. Leonard Wood) came out "buffer" (conformity 0.93);
    the 14 "bastions" found were tiny, noisy low-population counties.
  - Root cause: swing is so spatially autocorrelated (rho ~ 0.86, Moran's I
    ~ 0.6) that co-movement with neighbours is near-universal — everyone is
    in the wave. Contemporaneous conformity cannot separate the roles:
    Bellwether and Buffer BOTH co-move (distinguishing them needs temporal
    LEAD-LAG, too thin over 7 elections), and an "ideological bastion" is
    about issue-resistance to messaging — closer to the dissonance signal
    than to presidential swing.
  - Path forward (BACKLOG): a lead-lag method once the historical returns
    extension gives the time depth, and/or defining the Bastion via the
    dissonance metric rather than swing co-movement. The primitives below
    stay as tested building blocks; the classifier is kept for the record
    but is not wired into the export/map.
"""

from collections.abc import Mapping

import numpy as np
import pandas as pd

# Minimum non-missing elections for a conformity correlation to mean anything.
# A correlation from two points is always +/-1 by construction; require more.
_MIN_ELECTIONS = 3


def county_influence(
    panel: pd.DataFrame,
    adjacency: Mapping[str, frozenset[str]],
    value_column: str,
    min_elections: int = _MIN_ELECTIONS,
) -> pd.DataFrame:
    """Per-county influence primitives from a long (fips, year, value) panel.

    Returns fips, conformity, volatility:
      - conformity: Pearson correlation between a county's own swing series
        and its neighbourhood's mean swing series, over elections where both
        are present. NaN when fewer than `min_elections` paired observations
        exist, or when either series has no variance (correlation undefined).
      - volatility: sample std (ddof=1) of the county's own swing.
    """
    wide = panel.pivot_table(index="fips", columns="year", values=value_column)

    records = []
    for fips in wide.index:
        own = wide.loc[fips]
        neighbours = [n for n in adjacency.get(fips, frozenset()) if n in wide.index]
        neighbourhood = wide.loc[neighbours].mean(axis=0) if neighbours else None

        conformity = float("nan")
        if neighbourhood is not None:
            paired = pd.concat([own, neighbourhood], axis=1).dropna()
            own_paired, hood_paired = paired.iloc[:, 0], paired.iloc[:, 1]
            # Correlation is undefined when either series is constant; leave
            # conformity NaN rather than divide by a zero standard deviation.
            if len(paired) >= min_elections and own_paired.std() > 0 and hood_paired.std() > 0:
                conformity = own_paired.corr(hood_paired)

        records.append(
            {
                "fips": fips,
                "conformity": conformity,
                "volatility": float(own.std()),
            }
        )
    return pd.DataFrame(records).sort_values("fips", ignore_index=True)


def classify_nodes(
    influence: pd.DataFrame,
    buffer_min: float = 0.5,
    bastion_max: float = 0.0,
) -> pd.DataFrame:
    """Label each county Buffer / Bastion / ordinary / unknown from its
    influence metrics — the spec's Margin Play pair.

    A county is a Buffer when it co-moves strongly with its region
    (conformity >= buffer_min): permeable, takes its cues from neighbours.
    It is a Bastion when it moves independently (conformity <= bastion_max)
    AND holds steady (volatility at or below the panel median): the resistant
    anchor whose grip on its Buffer zones is the thing to weaken. Counties
    without a computable conformity are 'unknown', never silently 'ordinary'.

    'Steady' is defined relative to the panel (below the median volatility),
    because swing volatility has no natural absolute scale — resistance is a
    comparison to peers, exactly as the spec frames it. (Bellwether — temporal
    leadership — needs a lead-lag refinement and is not classified here.)
    """
    result = influence.copy()
    conformity = result["conformity"]
    steady = result["volatility"] <= result["volatility"].median()
    result["node_type"] = np.where(
        conformity.isna(),
        "unknown",
        np.where(
            conformity >= buffer_min,
            "buffer",
            np.where((conformity <= bastion_max) & steady, "bastion", "ordinary"),
        ),
    )
    return result
