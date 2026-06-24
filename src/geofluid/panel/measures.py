"""The cross-measure contest panel — Module 2 path (b)'s fips x measure_id schema.

A single ballot measure is one observation per county (N=1): there is no
structure in it to model influence or resistance against. The issue-resistance
route needs VARIATION — the same or different issues across states and time —
so a county's persuadability can be compared against its partisan identity over
many contests. This module stacks the per-measure referendum panels (each from
a load_*_referendum loader, all sharing the canonical schema) into one tidy
long panel keyed (measure_id, fips).

The one transformation it adds is orientation. Each loader reports raw yes/no
and no_share and stays politics-agnostic (which side is "progressive" is a
per-measure fact). To compare counties ACROSS measures, the progressive vote
must be on a common axis: for an abortion measure a NO vote was the progressive
(rights-preserving) position, while for a cannabis-legalization measure a YES
vote was. progressive_share carries that correction so 0.70 means the same
thing — 70% voted the progressive way — in every measure.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Measure:
    """One ballot measure's canonical panel plus the orientation needed to make
    it comparable across measures.

    progressive_side names which ballot answer ("yes" or "no") was the
    progressive vote for this measure; it is the only per-measure fact the
    combine needs to put every county on a common progressive axis.
    """

    measure_id: str
    progressive_side: str
    panel: pd.DataFrame

    def __post_init__(self) -> None:
        if self.progressive_side not in ("yes", "no"):
            raise ValueError(
                f"progressive_side must be 'yes' or 'no', got {self.progressive_side!r} "
                f"for measure {self.measure_id!r}"
            )


def build_measures_panel(measures: Sequence[Measure]) -> pd.DataFrame:
    """Stack per-measure panels into one tidy (measure_id, fips) panel.

    Adds progressive_share — the progressive side's share of the two-way vote,
    oriented per measure so it is comparable across all of them. The result is
    sorted by (measure_id, fips) so an index built on it aligns regardless of
    the order measures were supplied.
    """
    frames = []
    for measure in measures:
        frame = measure.panel.copy()
        frame.insert(0, "measure_id", measure.measure_id)
        progressive_votes = (
            frame["yes_votes"] if measure.progressive_side == "yes" else frame["no_votes"]
        )
        frame["progressive_share"] = progressive_votes / frame["total_votes"]
        frames.append(frame)

    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(["measure_id", "fips"], ignore_index=True)
        .loc[
            :,
            [
                "measure_id",
                "fips",
                "yes_votes",
                "no_votes",
                "total_votes",
                "no_share",
                "progressive_share",
            ],
        ]
    )
