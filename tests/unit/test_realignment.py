"""Tests for trend_surprise — the realignment-detection primitive (Module 4 seed).

A realignment shows up as counties landing far from where their own recent
trajectory pointed. trend_surprise fits each county's linear trend through a
trailing window of elections, extrapolates one election ahead, and returns
the residual (actual minus predicted). A large, spatially-coherent field of
residuals is the signature of a realignment — see the analysis notebook.

This is the tested backend the notebook leans on; the notebook itself is
exploratory narrative.
"""

import pandas as pd

from geofluid.realignment import trend_surprise


def _panel(series: dict[str, dict[int, float]]) -> pd.DataFrame:
    rows = [
        {"fips": fips, "year": year, "dem_share_2p": value}
        for fips, values in series.items()
        for year, value in values.items()
    ]
    return pd.DataFrame(rows)


def test_residual_is_actual_minus_trend_extrapolation() -> None:
    """County A rises 0.30 -> 0.60 on a perfect line (1/10 per election); the
    fit predicts 0.70 for the next election. If A actually lands 0.70 its
    surprise is 0; county B, same trend but landing 0.50, surprises -0.20
    (0.20 more Republican than its trajectory predicted)."""
    line = {2000: 0.30, 2004: 0.40, 2008: 0.50, 2012: 0.60}
    panel = _panel(
        {
            "01001": {**line, 2016: 0.70},  # A: on trend
            "01003": {**line, 2016: 0.50},  # B: broke down 0.20
        }
    )

    s = trend_surprise(panel, target_year=2016, value_column="dem_share_2p", min_obs=3)

    assert abs(s["01001"]) < 1e-9
    assert abs(s["01003"] - (-0.20)) < 1e-9


def test_counties_below_min_obs_or_missing_target_are_excluded() -> None:
    """A trend from too few points is meaningless, and a county with no value
    in the target election cannot have a residual — both are excluded, never
    fabricated."""
    panel = _panel(
        {
            "01001": {2000: 0.3, 2004: 0.4, 2008: 0.5, 2012: 0.6, 2016: 0.7},  # ok
            "01003": {2008: 0.4, 2012: 0.5, 2016: 0.6},  # only 2 training pts (<3)
            "01005": {2000: 0.3, 2004: 0.4, 2008: 0.5, 2012: 0.6},  # no 2016 value
        }
    )

    s = trend_surprise(panel, target_year=2016, value_column="dem_share_2p", min_obs=3)

    assert list(s.index) == ["01001"]


def test_only_pre_target_elections_train_the_trend() -> None:
    """The trend is fit on elections strictly before the target — a future
    value cannot leak into its own prediction. Here A is on a clean line
    through 2012 and lands exactly on it in 2016 -> surprise 0, regardless of
    any later (2020) value present in the panel."""
    panel = _panel(
        {
            "01001": {2000: 0.30, 2004: 0.40, 2008: 0.50, 2012: 0.60, 2016: 0.70, 2020: 0.10},
        }
    )

    s = trend_surprise(panel, target_year=2016, value_column="dem_share_2p", min_obs=3)

    assert abs(s["01001"]) < 1e-9  # 2020's 0.10 must not pull the 2016 prediction
