"""Tests for the dissonance metric — Module 3's first measurement.

Dissonance is the signed gap between a county's ISSUE position and its
PARTISAN identity: issue_share - partisan_share, both fips-indexed and both
oriented so higher = the same political direction. For Kansas Aug 2022 the
caller passes the referendum NO share (pro-choice) as issue_share and the
presidential Democratic two-party share as partisan_share, so:

  positive dissonance = MORE progressive on the issue than partisan lean
  predicts -- a "False Bastion": a county that looks red but is persuadable
  on this specific question (the Kansas story).

The function stays agnostic about which side is "progressive"; orienting the
two shares the same direction is the caller's job, exactly as the referendum
loader leaves the politics to the analysis layer.
"""

import json

import numpy as np
import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

from geofluid.dissonance import build_measure_overlay, compute_dissonance, issue_resistance


def test_dissonance_is_issue_share_minus_partisan_share() -> None:
    """County 20001 votes 40% Democratic for president but 55% pro-choice on
    the measure -> dissonance +0.15 (a False Bastion). County 20091 is 62%
    Democratic and 65% pro-choice -> +0.03 (consistent). Derived here before
    the assertion."""
    issue = pd.Series({"20001": 0.55, "20091": 0.65})
    partisan = pd.Series({"20001": 0.40, "20091": 0.62})

    result = compute_dissonance(issue, partisan)

    assert list(result.columns) == ["fips", "issue_share", "partisan_share", "dissonance"]
    assert list(result["fips"]) == ["20001", "20091"]
    assert abs(result.iloc[0]["dissonance"] - 0.15) < 1e-12
    assert abs(result.iloc[1]["dissonance"] - 0.03) < 1e-12


def test_county_missing_partisan_share_gets_nan_not_dropped() -> None:
    """A county present in the issue universe but absent from the partisan
    series has no defined dissonance. It stays in the frame with NaN (the
    codebase's absence-not-fabrication idiom, as with swing and LISA) rather
    than being silently dropped, which would shrink the map invisibly."""
    issue = pd.Series({"20001": 0.55, "20201": 0.48})
    partisan = pd.Series({"20001": 0.40})  # 20201 missing

    result = compute_dissonance(issue, partisan)

    assert list(result["fips"]) == ["20001", "20201"]
    assert abs(result.iloc[0]["dissonance"] - 0.15) < 1e-12
    assert pd.isna(result.iloc[1]["dissonance"])
    assert pd.isna(result.iloc[1]["partisan_share"])
    assert result.iloc[1]["issue_share"] == 0.48  # the issue side is intact


def test_measure_overlay_is_browser_ready_keyed_by_fips() -> None:
    """The map overlay data product: {fips: {no_share, partisan_share,
    dissonance}}. NaN (a county lacking a partisan baseline) becomes None so
    the file survives browser JSON.parse — the lesson the metrics export
    already learned. issue_share is surfaced as no_share for the popup."""
    referendum = pd.DataFrame(
        {
            "fips": ["20001", "20201"],
            "no_share": [0.55, 0.48],
        }
    )
    partisan = pd.Series({"20001": 0.40})  # 20201 has no baseline

    overlay = build_measure_overlay(referendum, partisan)

    assert set(overlay) == {"20001", "20201"}
    assert abs(overlay["20001"]["dissonance"] - 0.15) < 1e-12
    assert abs(overlay["20001"]["no_share"] - 0.55) < 1e-12
    assert abs(overlay["20001"]["partisan_share"] - 0.40) < 1e-12
    # The county with no baseline: dissonance and partisan null, issue intact.
    assert overlay["20201"]["dissonance"] is None
    assert overlay["20201"]["partisan_share"] is None
    assert abs(overlay["20201"]["no_share"] - 0.48) < 1e-12
    # Proves it round-trips through strict JSON (no literal NaN).
    json.dumps(overlay, allow_nan=False)


def test_overlay_orients_issue_share_by_progressive_side() -> None:
    """For a measure where YES is the progressive vote (Ohio Issue 1, which
    ESTABLISHED abortion rights and passed), the county's pro-choice position is
    its YES share, not NO. build_measure_overlay(..., progressive_side="yes")
    must compute dissonance against yes/total: county 39001 votes 60 yes / 40 no
    (yes-share 0.60) and was 45% Democratic in the baseline, so dissonance =
    0.60 - 0.45 = +0.15 (derived before the assertion) — the False-Bastion
    signal oriented correctly, the opposite of the Kansas/Kentucky default. The
    reported no_share stays the literal NO share: the field is politics-agnostic
    and the orientation lives only in the dissonance the map actually colours."""
    referendum = pd.DataFrame(
        {
            "fips": ["39001"],
            "yes_votes": [60],
            "no_votes": [40],
            "total_votes": [100],
            "no_share": [0.40],
        }
    )
    partisan = pd.Series({"39001": 0.45})

    overlay = build_measure_overlay(referendum, partisan, progressive_side="yes")

    assert abs(overlay["39001"]["dissonance"] - 0.15) < 1e-12
    assert abs(overlay["39001"]["no_share"] - 0.40) < 1e-12


def test_overlay_progressive_side_must_be_yes_or_no() -> None:
    """progressive_side decides which ballot answer is the progressive vote and
    so the SIGN of every county's dissonance. A typo must raise, naming the bad
    value, never silently fall to one orientation and invert the whole map."""
    referendum = pd.DataFrame(
        {
            "fips": ["39001"],
            "yes_votes": [60],
            "no_votes": [40],
            "total_votes": [100],
            "no_share": [0.40],
        }
    )

    with pytest.raises(ValueError, match="maybe"):
        build_measure_overlay(referendum, pd.Series({"39001": 0.45}), progressive_side="maybe")


# --- Issue resistance: dissonance done right (partisanship controlled) --------
#
# Raw dissonance (issue_share - partisan_share) assumes a county "should" vote
# progressive exactly as much as it votes Democratic -- a 1:1 line. Empirically
# the line is flatter (Ohio: slope ~0.9), so the raw gap is a biased estimate of
# "votes more progressively than its partisanship predicts." issue_resistance is
# the rigorous version: the residual of progressive_share regressed (OLS) on
# partisan_share across the measure's counties -- how much a county over- or
# under-performs the partisan expectation set by its PEERS, not by an assumed
# 1:1. Promoted from the Ohio generality notebook's hand-rolled residual into
# tested library code (the next generality test reuses it).


def test_issue_resistance_is_the_residual_from_the_fitted_partisan_line() -> None:
    """Resistance is measured against the OLS line progressive ~ partisan, not a
    1:1 assumption. Construct a fixture whose fitted line is exactly
    progressive = partisan: two anchors on that line (0.2->0.2, 0.8->0.8) and two
    counties at the SAME partisanship 0.5 deviating symmetrically (0.7 and 0.3).
    Means are both 0.5; cov/var = 0.18/0.18 = 1, intercept 0 -> line is
    progressive = partisan. So residuals are progressive - partisan exactly:
    anchors 0, the 0.7 county +0.2, the 0.3 county -0.2. (Hand-derived before the
    assertion.)"""
    progressive = pd.Series({"anchor_lo": 0.2, "anchor_hi": 0.8, "above": 0.7, "below": 0.3})
    partisan = pd.Series({"anchor_lo": 0.2, "anchor_hi": 0.8, "above": 0.5, "below": 0.5})

    resistance = issue_resistance(progressive, partisan)

    assert abs(resistance["anchor_lo"]) < 1e-9
    assert abs(resistance["anchor_hi"]) < 1e-9
    assert abs(resistance["above"] - 0.2) < 1e-9
    assert abs(resistance["below"] - (-0.2)) < 1e-9


def test_issue_resistance_is_zero_when_every_county_is_on_the_line() -> None:
    """If the issue vote is a perfect linear function of partisanship
    (progressive = 0.3 + 0.5 * partisan for everyone), no county defies its
    partisan expectation -- every resistance is zero. The slope and intercept are
    arbitrary on purpose: resistance is relative to whatever line the data set,
    not to a fixed baseline."""
    partisan = pd.Series({"a": 0.1, "b": 0.4, "c": 0.6, "d": 0.9})
    progressive = 0.3 + 0.5 * partisan

    resistance = issue_resistance(progressive, partisan)

    assert (resistance.abs() < 1e-9).all()


@given(
    rows=st.lists(
        st.tuples(st.floats(0.01, 0.99), st.floats(0.01, 0.99)),
        min_size=3,
        max_size=40,
        unique_by=lambda t: t[0],  # distinct partisanship so the OLS fit is defined
    )
)
def test_issue_resistance_is_orthogonal_to_partisanship(rows: list[tuple[float, float]]) -> None:
    """The defining property -- what "controlling for partisanship" MEANS: the
    residuals sum to ~0 and are ~uncorrelated with partisanship, for ANY input.
    That is the OLS guarantee, and it is exactly why resistance is the part of
    the issue vote that partisanship cannot explain -- the signal, with party
    projected out."""
    partisan = pd.Series([p for p, _ in rows], index=[str(i) for i in range(len(rows))])
    progressive = pd.Series([q for _, q in rows], index=partisan.index)

    resistance = issue_resistance(progressive, partisan)

    assert abs(resistance.sum()) < 1e-6
    if partisan.std() > 0 and resistance.std() > 1e-9:
        assert abs(np.corrcoef(partisan, resistance)[0, 1]) < 1e-6


def test_issue_resistance_county_with_no_partisan_baseline_is_nan_not_dropped() -> None:
    """A county lacking a partisan baseline cannot be placed against the line, so
    it gets NaN resistance and stays in the frame -- absence is explicit, the
    codebase's idiom (and it must not enter the fit). The other counties' fit is
    computed on the complete cases only."""
    progressive = pd.Series({"a": 0.2, "b": 0.8, "c": 0.5})
    partisan = pd.Series({"a": 0.2, "b": 0.8})  # c has no baseline

    resistance = issue_resistance(progressive, partisan)

    assert set(resistance.index) == {"a", "b", "c"}
    assert pd.isna(resistance["c"])
    assert abs(resistance["a"]) < 1e-9  # a, b lie on their own fitted line
    assert abs(resistance["b"]) < 1e-9
