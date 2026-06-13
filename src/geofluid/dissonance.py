"""Module 3 — Friction & Dissonance Mapper, first measurement.

Dissonance is the signed gap between how a county votes on an ISSUE and how
it votes for a PARTY: issue_share - partisan_share. When both shares are
oriented the same political direction, a positive gap is a county whose issue
position runs ahead of its partisan identity -- the spec's "False Bastion",
a place that looks safe for one side but is persuadable on a specific
question (Kansas Aug 2022: deeply Republican counties that voted to preserve
abortion rights).

This module stays agnostic about which side is "progressive": orienting the
two input shares the same direction is the caller's responsibility, exactly
as the referendum loader leaves politics to the analysis layer.
"""

from typing import Any

import pandas as pd


def compute_dissonance(
    issue_share: "pd.Series[float]",
    partisan_share: "pd.Series[float]",
) -> pd.DataFrame:
    """Signed gap between a county's issue vote and its partisan vote.

    Both inputs are fips-indexed shares, oriented the same political
    direction. The issue series defines the universe (e.g. the 105 counties
    that voted on a state measure); the partisan share is looked up for each.
    A county with no partisan share gets NaN dissonance and stays in the
    frame -- absence is explicit, never a silent drop.
    """
    issue = issue_share.rename("issue_share")
    partisan = partisan_share.reindex(issue.index).rename("partisan_share")
    frame = pd.concat([issue, partisan], axis=1)
    frame["dissonance"] = frame["issue_share"] - frame["partisan_share"]
    return (
        frame.rename_axis("fips")
        .reset_index()
        .sort_values("fips", ignore_index=True)
        .loc[:, ["fips", "issue_share", "partisan_share", "dissonance"]]
    )


def build_measure_overlay(
    referendum: pd.DataFrame,
    partisan_share: "pd.Series[float]",
) -> dict[str, dict[str, Any]]:
    """The map overlay for a ballot measure: {fips: {no_share, partisan_share,
    dissonance}}, browser-ready.

    The referendum panel supplies each county's no_share (the issue position);
    partisan_share is the chosen presidential baseline. NaN becomes None so the
    file survives browser JSON.parse, exactly as the per-year metrics export
    does. issue_share is surfaced as no_share for the county popup.
    """
    diss = compute_dissonance(referendum.set_index("fips")["no_share"], partisan_share)
    overlay: dict[str, dict[str, Any]] = {}
    for row in diss.to_dict("records"):
        overlay[str(row["fips"])] = {
            "no_share": row["issue_share"],
            "partisan_share": None if pd.isna(row["partisan_share"]) else row["partisan_share"],
            "dissonance": None if pd.isna(row["dissonance"]) else row["dissonance"],
        }
    return overlay
