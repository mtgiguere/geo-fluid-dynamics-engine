"""Tests for lead_lag — the temporal node-influence primitive (Module 2 retry).

The contemporaneous-conformity classifier was falsified (see influence.py): swing
is so spatially autocorrelated that every county co-moves with its neighbourhood,
so same-election correlation cannot tell a Bellwether (which LEADS its region) from
a Buffer (which FOLLOWS it). Telling them apart needs the time axis — now that the
1868-2024 spine gives 40 elections of depth.

lead_lag scores each county by whether its swing precedes or echoes its
neighbourhood's mean swing:

    lead = corr(own(t), neighbourhood(t + 1))   # own moves first  -> LEADS
    lag  = corr(own(t), neighbourhood(t - 1))   # own moves after  -> FOLLOWS
    lead_lag = lead - lag                         # > 0 leads, < 0 follows

"shift by one election" is positional over the sorted election columns (the next
contest, not the next calendar year), so it survives the irregular pre-2000 spacing.
"""

import pandas as pd

from geofluid.spatial.leadlag import lead_lag


def _panel(series: dict[str, dict[int, float]]) -> pd.DataFrame:
    rows = [
        {"fips": fips, "year": year, "swing": value}
        for fips, values in series.items()
        for year, value in values.items()
    ]
    return pd.DataFrame(rows)


def test_leader_scores_positive_follower_scores_negative() -> None:
    """Two mutually-adjacent counties over five elections. B's swing is A's swing
    delayed by exactly one election (B copies what A did last contest), so A LEADS
    and B FOLLOWS purely by construction.

        year:  2000  2004  2008  2012  2016
        A:        0     1     0     0    -1
        B:        0     0     1     0     0     (B(t) = A(t-1); B(2000)=0, pre-A)

    A's neighbourhood mean is B's series; B's is A's (single mutual neighbour).
    Derive A's score (own = A, hood = B), pairing positionally over sorted years:

        lead = corr(A[2000..2012], B[2004..2016])
             = corr([0, 1, 0, 0], [0, 1, 0, 0]) = 1.0     # A at t == B at t+1: perfect lead
        lag  = corr(A[2004..2016], B[2000..2012])
             = corr([1, 0, 0, -1], [0, 0, 1, 0])
               u-mean = 0, v-mean = 0.25
               cov ~ 1*(0-.25) + 0 + 0 + (-1)*(0-.25) = 0  -> corr = 0
        lead_lag(A) = 1.0 - 0.0 = +1.0

    By the mirror symmetry of the construction, B's lead = 0 and B's lag = 1.0, so
    lead_lag(B) = 0.0 - 1.0 = -1.0. The leader scores +1; the follower it leads -1."""
    panel = _panel(
        {
            "01001": {2000: 0.0, 2004: 1.0, 2008: 0.0, 2012: 0.0, 2016: -1.0},  # A: leads
            "01003": {2000: 0.0, 2004: 0.0, 2008: 1.0, 2012: 0.0, 2016: 0.0},  # B: follows
        }
    )
    adjacency = {"01001": frozenset({"01003"}), "01003": frozenset({"01001"})}

    s = lead_lag(panel, adjacency, value_column="swing")

    assert abs(s["01001"] - 1.0) < 1e-9
    assert abs(s["01003"] - (-1.0)) < 1e-9
