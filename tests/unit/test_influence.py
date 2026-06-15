"""Tests for county influence metrics — Module 2's Gravity Engine.

The spec's node types are about influence DYNAMICS: the Buffer Zone is
"highly permeable, takes cues from its neighbours"; the Ideological Bastion
"resists outside ideas" while anchoring its region. Both are measurable from
how a county's swing co-moves with its neighbourhood over the elections we
have:

  - conformity = correlation between a county's own swing series and its
    neighbourhood's mean swing series. High = moves WITH the region (Buffer);
    low/negative = moves independently of it (Bastion-like).
  - volatility = the spread of a county's own swing. Low = holds a steady
    line (anchored); high = moves around.

With seven presidential elections this is descriptive, not inferential — the
classification cycle validates it against known geography, and true temporal
leadership (the Bellwether) needs a lead-lag refinement noted for later.
"""

import pandas as pd

from geofluid.spatial.influence import classify_nodes, county_influence

# A line graph A — B — C (B in the middle), three elections.
_ADJ = {
    "01001": frozenset({"01003"}),  # A, neighbour B
    "01003": frozenset({"01001", "01005"}),  # B, neighbours A and C
    "01005": frozenset({"01003"}),  # C, neighbour B
}


def _panel(series: dict[str, list[float]]) -> pd.DataFrame:
    years = [2016, 2020, 2024]
    rows = [
        {"fips": fips, "year": year, "swing_dem_2p": value}
        for fips, values in series.items()
        for year, value in zip(years, values, strict=True)
    ]
    return pd.DataFrame(rows)


def test_conformity_is_comovement_with_the_neighbourhood() -> None:
    """A's swing equals its only neighbour B's exactly -> conformity +1.
    C's swing is the exact opposite of B's -> conformity -1. B's
    neighbourhood mean is (A + C)/2 = flat (they cancel), so B's conformity
    is undefined (NaN) — correlation against a zero-variance series is not a
    number, and we report that honestly rather than fabricate a value."""
    panel = _panel(
        {
            "01001": [0.1, -0.2, 0.3],  # A
            "01003": [0.1, -0.2, 0.3],  # B (== A)
            "01005": [-0.1, 0.2, -0.3],  # C (== -B)
        }
    )

    influence = county_influence(panel, _ADJ, value_column="swing_dem_2p").set_index("fips")
    conformity = influence["conformity"]

    assert abs(conformity["01001"] - 1.0) < 1e-9
    assert abs(conformity["01005"] - (-1.0)) < 1e-9
    assert pd.isna(conformity["01003"])


def test_volatility_is_the_sample_std_of_own_swing() -> None:
    """volatility = sample std (ddof=1) of a county's own swing. For
    [0.1, -0.2, 0.3]: mean 0.06667, sum of squared deviations 0.126667,
    /(n-1=2) = 0.063333, sqrt = 0.251661."""
    panel = _panel({"01001": [0.1, -0.2, 0.3], "01003": [0.0, 0.0, 0.0]})
    adjacency = {"01001": frozenset({"01003"}), "01003": frozenset({"01001"})}

    volatility = county_influence(panel, adjacency, value_column="swing_dem_2p").set_index("fips")[
        "volatility"
    ]

    assert abs(volatility["01001"] - 0.251661) < 1e-5
    assert volatility["01003"] == 0.0  # never moved


def test_too_few_elections_yields_nan_conformity_not_a_lie() -> None:
    """Conformity needs enough paired observations to mean anything. With
    only two non-missing elections (below the min), it is NaN — a correlation
    from two points is always +/-1 by construction, a fabricated certainty."""
    panel = pd.DataFrame(
        [
            {"fips": "01001", "year": 2020, "swing_dem_2p": 0.1},
            {"fips": "01001", "year": 2024, "swing_dem_2p": 0.2},
            {"fips": "01003", "year": 2020, "swing_dem_2p": 0.3},
            {"fips": "01003", "year": 2024, "swing_dem_2p": -0.1},
        ]
    )
    adjacency = {"01001": frozenset({"01003"}), "01003": frozenset({"01001"})}

    influence = county_influence(panel, adjacency, value_column="swing_dem_2p").set_index("fips")

    assert pd.isna(influence["conformity"]["01001"])


def test_classify_nodes_maps_metrics_to_buffer_bastion_ordinary() -> None:
    """The spec's Margin Play pair, from (conformity, volatility):
      - Buffer: conformity >= buffer_min -> moves with its region (permeable).
      - Bastion: conformity <= bastion_max AND steady (volatility at or below
        the median) -> holds an independent line, an anchor.
      - ordinary: everything in between.
      - unknown: conformity could not be computed (too little data) — never
        silently bucketed as ordinary.
    Volatilities [0.2, 0.1, 0.4, 0.2, 0.3] have median 0.2, so 'steady' is
    volatility <= 0.2."""
    influence = pd.DataFrame(
        {
            "fips": ["01001", "01003", "01005", "01007", "01009"],
            "conformity": [0.8, -0.3, -0.3, 0.1, float("nan")],
            "volatility": [0.2, 0.1, 0.4, 0.2, 0.3],
        }
    )

    classified = classify_nodes(influence, buffer_min=0.5, bastion_max=0.0).set_index("fips")
    node = classified["node_type"]

    assert node["01001"] == "buffer"  # high conformity
    assert node["01003"] == "bastion"  # independent AND steady (vol 0.1 <= 0.2)
    assert node["01005"] == "ordinary"  # independent but volatile (vol 0.4 > 0.2)
    assert node["01007"] == "ordinary"  # mid conformity
    assert node["01009"] == "unknown"  # conformity NaN — not silently ordinary
