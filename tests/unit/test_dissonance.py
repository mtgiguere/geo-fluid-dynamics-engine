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

import pandas as pd

from geofluid.dissonance import compute_dissonance


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
