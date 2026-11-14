"""Tests for the wave player's frames: how far along each county is, period by
period, in adopting an idea.

Why this is here: the research log measures waves (rooftop solar, a
candidate's donor base, giving after Dobbs) with a hazard model. The public
wave player SHOWS them instead: press play and watch each county fill in as
the idea arrives. Each frame colours a county by the share of its own final
total it has reached so far, the same yardstick the take-off rule uses
(`geofluid.spatial.timing.takeoff_quarters`). Against its own total, a big
county and a small one are read the same way: by the shape of their arrival.

The page gets one short string per county, one character per frame: "0" to
"9" for 0-90% (rounded down to the 10% step), "A" for all of it. Compact
enough to ship thousands of counties times hundreds of frames to a browser.
"""

import pandas as pd

from geofluid.map.waves import running_share_levels


def test_each_frame_is_the_share_of_the_countys_own_final_total_so_far() -> None:
    """One county, four periods, new adoptions 1, 0, 3, 6 (final total 10).
    Running total 1, 1, 4, 10 -> share 10%, 10%, 40%, 100% -> levels
    "1", "1", "4", "A". The period with no row (the 0) is a period with no
    new adoptions, not a gap: the running total carries over."""
    periods = list(pd.date_range("2019-01-07", periods=4, freq="W-MON"))
    counts = pd.DataFrame(
        {
            "fips": ["29510", "29510", "29510"],
            "period": [periods[0], periods[2], periods[3]],
            "count": [1, 3, 6],
        }
    )

    out = running_share_levels(counts, periods, min_total=1)

    assert out == {"29510": "114A"}


def test_a_county_with_too_few_adoptions_to_have_a_shape_is_left_out() -> None:
    """With two donors, "half its final count" is one person's decision. Like
    the take-off rule, a county ending below `min_total` is left out (drawn
    as no data), not drawn as an early or late adopter. County A ends with
    20 (kept), county B with 19 (dropped) at min_total 20."""
    periods = [pd.Timestamp("2019-01-07")]
    counts = pd.DataFrame({"fips": ["A", "B"], "period": periods * 2, "count": [20, 19]})

    out = running_share_levels(counts, periods, min_total=20)

    assert list(out) == ["A"]
