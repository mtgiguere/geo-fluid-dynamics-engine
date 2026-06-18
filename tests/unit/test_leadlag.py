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


def test_county_with_too_few_paired_elections_is_excluded() -> None:
    """A lagged correlation from two paired points is +/-1 by construction, so a
    county whose own series is too sparse to form one cannot have a meaningful
    score and is dropped — never fabricated.

    A line A - B - C over five elections. A and B are present throughout. C joins
    only in the last two elections (2012, 2016), so after the one-election shift
    its lead pairing has a single non-NaN pair and its lag pairing two — both below
    the minimum of three. C is excluded; A and B remain.

    C's sparseness must not exclude its well-populated neighbour B: B's
    neighbourhood mean draws on A (full), so B's own pairings stay complete. The
    exclusion is about a county's OWN observations, not its neighbours'."""
    panel = _panel(
        {
            "01001": {2000: 0.0, 2004: 0.1, 2008: 0.2, 2012: 0.1, 2016: 0.3},  # A: full
            "01003": {2000: 0.2, 2004: 0.0, 2008: 0.3, 2012: 0.2, 2016: 0.1},  # B: full
            "01005": {2012: 0.5, 2016: 0.4},  # C: only two elections
        }
    )
    adjacency = {
        "01001": frozenset({"01003"}),
        "01003": frozenset({"01001", "01005"}),
        "01005": frozenset({"01003"}),
    }

    s = lead_lag(panel, adjacency, value_column="swing")

    assert list(s.index) == ["01001", "01003"]


def test_island_with_no_neighbours_is_excluded() -> None:
    """An island (empty adjacency, like Hawaii or Nantucket) has no neighbourhood
    series to correlate against, so it cannot have a lead-lag score and is dropped.
    Spatial weights deliberately keep islands in the keys with an all-zero row (so
    the matrix stays aligned); here the consequence is that the island simply has
    no neighbourhood mean, so no pairs survive and it is excluded — not crashed on,
    not scored as zero. A normal adjacent pair is present to show it is the
    islandness, not some global effect, doing the excluding."""
    panel = _panel(
        {
            "01001": {2000: 0.0, 2004: 0.1, 2008: 0.2, 2012: 0.1, 2016: 0.3},  # mainland
            "01003": {2000: 0.2, 2004: 0.0, 2008: 0.3, 2012: 0.2, 2016: 0.1},  # mainland
            "15003": {2000: 0.4, 2004: 0.5, 2008: 0.3, 2012: 0.6, 2016: 0.2},  # island
        }
    )
    adjacency = {
        "01001": frozenset({"01003"}),
        "01003": frozenset({"01001"}),
        "15003": frozenset(),  # island: no neighbours
    }

    s = lead_lag(panel, adjacency, value_column="swing")

    assert "15003" not in s.index
    assert "01001" in s.index


def test_county_with_constant_swing_is_excluded() -> None:
    """Correlation is undefined when a series has no variance — dividing by a zero
    standard deviation. A county whose swing never moves (constant across every
    election) therefore has no lead or lag correlation and is excluded, rather than
    leaking a NaN score into the result.

    A line A - B - K. K's swing is a flat 0.5 throughout. K has enough paired
    elections (it is not sparse), so the only reason to drop it is the zero
    variance — this isolates the constant-series case from the min-paired case. A
    and B vary and remain; K's flatness does not exclude B, whose neighbourhood
    mean still varies through A."""
    panel = _panel(
        {
            "01001": {2000: 0.0, 2004: 0.1, 2008: 0.2, 2012: 0.1, 2016: 0.3},  # A: varies
            "01003": {2000: 0.2, 2004: 0.0, 2008: 0.3, 2012: 0.2, 2016: 0.1},  # B: varies
            "01005": {2000: 0.5, 2004: 0.5, 2008: 0.5, 2012: 0.5, 2016: 0.5},  # K: constant
        }
    )
    adjacency = {
        "01001": frozenset({"01003"}),
        "01003": frozenset({"01001", "01005"}),
        "01005": frozenset({"01003"}),
    }

    s = lead_lag(panel, adjacency, value_column="swing")

    assert "01005" not in s.index
    assert list(s.index) == ["01001", "01003"]
