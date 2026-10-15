"""Tests for the scorecard - grading the 2026 registration against certified results.

The protocol (MEASUREMENT_DESIGN.md s7) grades three things: per-county
error against the partisanship-only baseline at the SAME statewide level
(pattern skill), whether the certified statewide share fell inside the
registered bracket (level), and interval calibration (did ~90% of counties
land inside their 90% interval). This module is written BEFORE any result
exists, so that in December the grading is a button press and nobody can
say the yardstick was chosen after seeing the answer.
"""

import numpy as np
import pandas as pd

from geofluid.scoring import (
    bracket_odds,
    classify_coupling,
    coupling_slope,
    relevel,
    score_counties,
    score_level,
    score_summary,
)


def _predictions() -> pd.DataFrame:
    """Two counties as the registered file describes them: central
    prediction, 90% interval, and the partisanship-only baseline."""
    return pd.DataFrame(
        {
            "fips": ["A", "B"],
            "pred_progressive_share": [0.60, 0.40],
            "pred_low_90": [0.55, 0.35],
            "pred_high_90": [0.65, 0.45],
            "baseline_partisan_only": [0.58, 0.45],
        }
    )


def test_score_counties_errors_and_interval_hits() -> None:
    """Certified: A 0.62, B 0.30. Errors are prediction minus actual:
    A 0.60 - 0.62 = -0.02 (abs 0.02), baseline 0.58 - 0.62 = -0.04, and
    0.62 sits inside [0.55, 0.65] -> in_interval True. B 0.40 - 0.30 =
    +0.10, baseline 0.45 - 0.30 = +0.15, and 0.30 is below 0.35 ->
    in_interval False. Derived before the assertion."""
    actual = pd.Series({"A": 0.62, "B": 0.30})

    scored = score_counties(_predictions(), actual).set_index("fips")

    assert abs(float(scored["error"].loc["A"]) - (-0.02)) < 1e-12
    assert abs(float(scored["abs_error"].loc["A"]) - 0.02) < 1e-12
    assert abs(float(scored["baseline_error"].loc["A"]) - (-0.04)) < 1e-12
    assert abs(float(scored["error"].loc["B"]) - 0.10) < 1e-12
    assert abs(float(scored["baseline_error"].loc["B"]) - 0.15) < 1e-12
    assert list(scored["in_interval_90"]) == [True, False]


def test_score_summary_rmse_skill_and_coverage() -> None:
    """From the two scored counties (errors -0.02 and +0.10; baseline errors
    -0.04 and +0.15; one interval hit of two):
    RMSE model    = sqrt((0.0004 + 0.0100) / 2) = sqrt(0.0052)  = 0.0721110
    RMSE baseline = sqrt((0.0016 + 0.0225) / 2) = sqrt(0.01205) = 0.1097725
    MAE model = (0.02 + 0.10) / 2 = 0.06
    skill = 1 - 0.0721110 / 0.1097725 = 0.343087 (positive = we beat the
    partisanship-only baseline; 0 = no better; negative = worse)
    coverage_90 = 1 / 2 = 0.5. Derived before the assertion."""
    actual = pd.Series({"A": 0.62, "B": 0.30})
    scored = score_counties(_predictions(), actual)

    summary = score_summary(scored)

    assert abs(float(summary["rmse_model"]) - 0.0721110) < 1e-6
    assert abs(float(summary["rmse_baseline"]) - 0.1097725) < 1e-6
    assert abs(float(summary["mae_model"]) - 0.06) < 1e-12
    assert abs(float(summary["skill_vs_baseline"]) - 0.343087) < 1e-5
    assert abs(float(summary["coverage_90"]) - 0.5) < 1e-12
    assert int(summary["n_counties"]) == 2


def test_relevel_hits_the_target_statewide_share_and_keeps_county_order() -> None:
    """Pattern skill must be judged at the CERTIFIED statewide share, so the
    registered county pattern is shifted on the logit scale until its
    turnout-weighted mean equals that share. Two counties at 0.40 and 0.60
    with equal weights average 0.50; relevelled to 0.55 the weighted mean
    must be 0.55 (to 1e-9), the county order must be preserved (a uniform
    logit shift is monotone), and both must have moved UP. Relevelling to
    the current mean (0.50) is the identity."""
    shares = pd.Series({"A": 0.40, "B": 0.60})
    weights = pd.Series({"A": 0.5, "B": 0.5})

    up = relevel(shares, target=0.55, weights=weights)
    same = relevel(shares, target=0.50, weights=weights)

    assert abs(float((up * weights).sum()) - 0.55) < 1e-9
    assert float(up["A"]) < float(up["B"])
    assert float(up["A"]) > 0.40
    assert float(up["B"]) > 0.60
    assert abs(float(same["A"]) - 0.40) < 1e-9
    assert abs(float(same["B"]) - 0.60) < 1e-9


def test_score_level_error_and_bracket_hit() -> None:
    """Bracket 0.515 / 0.55 / 0.59. Certified 0.53: level error = central -
    actual = +0.02, inside the bracket. Certified 0.60: error -0.05, outside
    (above the high end). Certified exactly on an edge counts as inside."""
    inside = score_level(low=0.515, central=0.55, high=0.59, actual=0.53)
    outside = score_level(low=0.515, central=0.55, high=0.59, actual=0.60)
    edge = score_level(low=0.515, central=0.55, high=0.59, actual=0.59)

    assert abs(float(inside["level_error"]) - 0.02) < 1e-12
    assert bool(inside["in_bracket"])
    assert abs(float(outside["level_error"]) - (-0.05)) < 1e-12
    assert not bool(outside["in_bracket"])
    assert bool(edge["in_bracket"])


def test_coupling_slope_recovers_a_constructed_slope_exactly() -> None:
    """Noise-free recovery world (no seeds): build county shares from
    partisanship by the exact rule logit(share) = 0.3 + 0.8 * logit(p) for
    p in {0.2, 0.35, 0.5, 0.7}. The OLS slope of logit(share) on logit(p)
    must recover 0.8 to 1e-9 - the same quantity the registered coupling
    proposition is scored on."""
    p = pd.Series({"A": 0.2, "B": 0.35, "C": 0.5, "D": 0.7})
    z = np.log(p / (1 - p))
    shares = pd.Series(1 / (1 + np.exp(-(0.3 + 0.8 * z))), index=p.index)

    assert abs(coupling_slope(shares, p) - 0.8) < 1e-9


def test_classify_coupling_against_a_reference_with_tolerance() -> None:
    """Reference slope 0.797, tolerance 0.05: 0.90 -> STEEPEN, 0.80 -> HOLD,
    0.70 -> RELAX. Exactly at reference + tolerance (0.847) is still HOLD:
    the bands are closed, the verdicts are open."""
    assert classify_coupling(0.90, reference=0.797, tolerance=0.05) == "STEEPEN"
    assert classify_coupling(0.80, reference=0.797, tolerance=0.05) == "HOLD"
    assert classify_coupling(0.70, reference=0.797, tolerance=0.05) == "RELAX"
    assert classify_coupling(0.847, reference=0.797, tolerance=0.05) == "HOLD"


def test_bracket_odds_reads_the_bracket_as_a_90_percent_interval() -> None:
    """The receipt page's "chance the tracked side is ahead". The bracket is
    read as a 90% interval around the central call: sd = (high - low) /
    (2 * 1.645). Construct it backwards from sd = 0.05 and central 0.55:
    low = 0.55 - 1.645 * 0.05 = 0.46775, high = 0.63225. Then
    z = (0.55 - 0.50) / 0.05 = 1 -> Phi(1) = 0.841344746; one point the
    tracked side's way makes z = 1.2 -> Phi(1.2) = 0.884930330."""
    now, plus_one, sd = bracket_odds(low=0.46775, central=0.55, high=0.63225)

    assert abs(sd - 0.05) < 1e-12
    assert abs(now - 0.841344746) < 1e-8
    assert abs(plus_one - 0.884930330) < 1e-8


def test_bracket_odds_is_exactly_even_at_fifty() -> None:
    """A central call of exactly 0.50 is a coin flip whatever the width:
    Phi(0) = 0.5 exactly. Invariance, not a tolerance."""
    now, _plus_one, _sd = bracket_odds(low=0.40, central=0.50, high=0.60)

    assert now == 0.5
