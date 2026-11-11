"""The timing model: does an idea reach a county after it reaches the county's
neighbours? (Module 1, the survival/hazard half of the Wave Predictor.)

Election snapshots, years apart, say a whole state moves at once: a wave
photographed every four years looks like everyone moving together. The timing
model works from DATED adoptions instead. It finds the quarter each county
"takes off", then asks whether counties take off sooner once a neighbour has,
after the nationwide clock is taken out. It is proved first on rooftop solar
(`geofluid.ingest.solar`), an idea known to spread from neighbour to neighbour,
before it is pointed back at politics.
"""

from collections.abc import Mapping
from typing import Literal

import numpy as np
import pandas as pd

TAKEOFF_COLUMNS = ["fips", "takeoff"]


def takeoff_quarters(panel: pd.DataFrame, share: float, min_installs: int) -> pd.DataFrame:
    """The quarter each county takes off: the first quarter its running total
    reaches `share` of the total it ends the panel with.

    `panel` is `geofluid.ingest.solar.county_adoption_panel` output.
    """
    # The bar is set against the county's OWN final count, not its number of
    # households. Coverage of the source file is uneven (about a quarter of
    # Texas and Maryland installs carry a usable ZIP), so a per-household bar
    # would make a thinly reported county look late. Against its own total, a
    # county's timing is read from its own shape, whatever its coverage.
    final = panel.groupby("fips")["cumulative_installs"].transform("max")
    # A county that ends with a handful of installs has no shape to read: with
    # two, "half its final count" is one household's decision. With none, a
    # bar of zero would be "reached" in the first quarter. Such counties are
    # left untimed.
    timed = final >= min_installs
    reached = panel[timed & (panel["cumulative_installs"] >= share * final)]
    takeoffs = reached.groupby("fips")["quarter"].min().rename("takeoff").reset_index()
    return takeoffs.loc[:, TAKEOFF_COLUMNS]


AT_RISK_COLUMNS = ["fips", "quarter", "event", "neighbour_share"]


def at_risk_table(takeoffs: pd.DataFrame, adjacency: Mapping[str, frozenset[str]]) -> pd.DataFrame:
    """One row per county per quarter while it waits to take off.

    `takeoffs` is `takeoff_quarters` output; `adjacency` maps each fips to the
    fips it borders (`geofluid.spatial.weights.county_adjacency`).
    """
    when = dict(zip(takeoffs["fips"], takeoffs["takeoff"], strict=True))
    span = pd.date_range(takeoffs["takeoff"].min(), takeoffs["takeoff"].max(), freq="QS")
    rows = []
    for fips in sorted(when):
        # A neighbour with no take-off (too few installs, or outside the
        # source file) is unknown, not "not yet": it is left out of the share.
        neighbours = [when[n] for n in adjacency.get(fips, frozenset()) if n in when]
        # No timed neighbour (or no county shape to border anything): there
        # is no share to measure, and none is made up.
        if not neighbours:
            continue
        # The survival layout: a county is at risk every quarter up to and
        # including the one it takes off in, and leaves the table after.
        for quarter in span[span <= when[fips]]:
            rows.append(
                {
                    "fips": fips,
                    "quarter": quarter,
                    "event": int(quarter == when[fips]),
                    # Strictly earlier: a neighbour taking off this same
                    # quarter cannot yet have been seen next door.
                    "neighbour_share": sum(t < quarter for t in neighbours) / len(neighbours),
                }
            )
    return pd.DataFrame(rows, columns=AT_RISK_COLUMNS)


# Newton's method for the hazard fit: a logistic likelihood is concave, so
# from zero it converges in a handful of steps; the cap is a backstop.
_MAX_NEWTON_STEPS = 100
_NEWTON_TOLERANCE = 1e-12


def fit_neighbour_hazard(table: pd.DataFrame, clock: Literal["national", "state"]) -> float:
    """The wave, as one number: the odds ratio on `neighbour_share` in a
    discrete-time hazard model with one baseline per quarter (clock
    "national") or per state per quarter (clock "state").

    `table` is `at_risk_table` output. The model is a logistic regression of
    `event` on a dummy per baseline plus `neighbour_share`, fitted by maximum
    likelihood (Newton's method). The returned odds ratio is how many times
    the odds of taking off this quarter are multiplied for a county whose
    neighbours have ALL taken off, against one whose neighbours have none.
    """
    # The quarter dummies are the nationwide clock: a tax credit, a price
    # drop, a statewide policy, anything that lifts every county in the same
    # quarter. Only what is left after the clock is credited to neighbours,
    # so "everyone moves at once" cannot masquerade as a wave.
    # A state clock goes one level down: a state programme (Illinois 2019,
    # Maryland 2021) lifts all its counties at once, and most neighbours share
    # a state, so only what spreads beyond the state's own clock is a wave.
    # The state is the first two digits of the county fips.
    baseline = table["quarter"].astype(str)
    if clock == "state":
        baseline = table["fips"].str[:2] + " " + baseline
    # A quarter (or state-quarter) in which nobody takes off (the early
    # years), or everybody still at risk does (the last one), says nothing
    # about neighbours: its baseline would run off toward odds 0 or
    # infinity. It is set aside.
    events_in_baseline = table.groupby(baseline)["event"].transform("mean")
    informative = (events_in_baseline > 0) & (events_in_baseline < 1)
    table, baseline = table[informative], baseline[informative]
    dummies = pd.get_dummies(baseline).to_numpy(dtype=float)
    design = np.column_stack([dummies, table["neighbour_share"].to_numpy(dtype=float)])
    event = table["event"].to_numpy(dtype=float)
    coef = np.zeros(design.shape[1])
    for _ in range(_MAX_NEWTON_STEPS):
        p = 1.0 / (1.0 + np.exp(-design @ coef))
        gradient = design.T @ (event - p)
        hessian = design.T @ (design * (p * (1.0 - p))[:, None])
        step = np.linalg.solve(hessian, gradient)
        coef += step
        if np.max(np.abs(step)) < _NEWTON_TOLERANCE:
            break
    return float(np.exp(coef[-1]))
