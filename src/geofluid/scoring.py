"""The scorecard: grading the 2026 registration against certified results.

Written before any result exists (see MEASUREMENT_DESIGN.md s7) so that the
yardstick is fixed in advance. Three gradings:

  * pattern  - per-county error of the registered prediction vs the
               partisanship-only baseline, both compared at the same
               statewide level so the comparison is about WHERE, not how much
  * level    - did the certified statewide share land inside the bracket
  * calibration - did roughly 90% of counties land inside their 90% interval

Politics-agnostic like everything upstream: shares are "progressive side"
by the loaders' orientation convention; the grade does not care which side
that is.
"""

import math

import numpy as np
import pandas as pd


def score_counties(predictions: pd.DataFrame, actual: "pd.Series[float]") -> pd.DataFrame:
    """Per-county grade. `predictions` is the registered file (fips,
    pred_progressive_share, pred_low_90, pred_high_90, baseline_partisan_only);
    `actual` is fips -> certified progressive share. Errors are prediction
    minus actual, so a positive error means we were too optimistic for the
    tracked side; in_interval_90 is the calibration hit."""
    out = predictions.copy()
    out["actual"] = out["fips"].map(actual)
    out["error"] = out["pred_progressive_share"] - out["actual"]
    out["abs_error"] = out["error"].abs()
    out["baseline_error"] = out["baseline_partisan_only"] - out["actual"]
    out["in_interval_90"] = (out["actual"] >= out["pred_low_90"]) & (
        out["actual"] <= out["pred_high_90"]
    )
    return out


def score_summary(scored: pd.DataFrame) -> "pd.Series[float]":
    """The headline numbers from score_counties' output: root-mean-square and
    mean-absolute county error for the model, the baseline's RMSE, the skill
    (1 - RMSE_model / RMSE_baseline: positive means we beat partisanship
    alone), and 90% interval coverage (target about 0.9)."""
    rmse_model = float((scored["error"] ** 2).mean() ** 0.5)
    rmse_baseline = float((scored["baseline_error"] ** 2).mean() ** 0.5)
    return pd.Series(
        {
            "n_counties": float(len(scored)),
            "rmse_model": rmse_model,
            "rmse_baseline": rmse_baseline,
            "mae_model": float(scored["abs_error"].mean()),
            "skill_vs_baseline": 1 - rmse_model / rmse_baseline,
            "coverage_90": float(scored["in_interval_90"].mean()),
        }
    )


def relevel(
    shares: "pd.Series[float]", *, target: float, weights: "pd.Series[float]"
) -> "pd.Series[float]":
    """Shift a county pattern on the logit scale until its weighted mean
    equals `target` (bisection on the shift; the map is monotone so the
    county ORDER is untouched). This is how pattern skill is isolated from
    the level call: both the registered prediction and the baseline are
    relevelled to the certified statewide share before their county errors
    are compared."""
    w = weights.reindex(shares.index)
    z = np.log(shares / (1 - shares))
    lo, hi = -10.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if float(((1 / (1 + np.exp(-(z + mid)))) * w).sum()) < target:
            lo = mid
        else:
            hi = mid
    shift = (lo + hi) / 2
    return pd.Series(1 / (1 + np.exp(-(z + shift))), index=shares.index)


def score_level(*, low: float, central: float, high: float, actual: float) -> "pd.Series[float]":
    """The level grade: how far the central call was from the certified
    statewide share (central minus actual) and whether the certified share
    fell inside the registered bracket (edges inclusive)."""
    return pd.Series(
        {
            "level_error": central - actual,
            "in_bracket": float(low <= actual <= high),
        }
    )


def coupling_slope(shares: "pd.Series[float]", partisan: "pd.Series[float]") -> float:
    """The issue-party coupling: OLS slope of logit(share) on logit(partisan
    share) across counties. The Module 5 order parameter the registered
    proposition is scored on - steeper means the measure votes more like a
    party-line contest."""
    y = np.log(shares / (1 - shares))
    x = np.log(partisan.reindex(shares.index) / (1 - partisan.reindex(shares.index)))
    slope, _intercept = np.polyfit(x, y, 1)
    return float(slope)


def classify_coupling(slope: float, *, reference: float, tolerance: float) -> str:
    """STEEPEN / HOLD / RELAX against a reference slope, with a tolerance
    band inside which the verdict is HOLD (band edges inclusive)."""
    if slope > reference + tolerance:
        return "STEEPEN"
    if slope < reference - tolerance:
        return "RELAX"
    return "HOLD"


def bracket_odds(
    *, low: float, central: float, high: float, shift: float = 0.01
) -> tuple[float, float, float]:
    """The chance the tracked side is above 50, read off a registered bracket.

    The bracket is treated as a 90% interval around the central call with
    roughly normal error: sd = (high - low) / (2 * 1.645). Returns the chance
    as things stand, the chance if the state moves `shift` the tracked side's
    way (one point by default - the "does my money change the odds?" lever),
    and the sd. A derived reading of the frozen numbers, not a new prediction.
    """
    sd = (high - low) / (2 * 1.645)

    def phi(z: float) -> float:
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))

    return phi((central - 0.5) / sd), phi((central + shift - 0.5) / sd), sd
