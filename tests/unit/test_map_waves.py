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

from geofluid.map.waves import chance_handoffs, handoffs, running_share_levels


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


def test_a_hand_off_is_drawn_from_a_neighbour_that_crossed_in_the_last_few_frames() -> None:
    """The arrows on the map. Three counties in a line, A - B - C, crossing
    the mark (level 5) at frames 1, 2 and 3: "0555", "0055", "0005". With a
    window of 1 frame, B crossed one frame after its neighbour A, and C one
    frame after B: arrows A -> B at frame 2 and B -> C at frame 3. A has no
    neighbour that crossed before it, so no arrow points at A."""
    series = {"A": "0555", "B": "0055", "C": "0005"}
    adjacency = {"A": frozenset({"B"}), "B": frozenset({"A", "C"}), "C": frozenset({"B"})}

    out = handoffs(series, mark=5, adjacency=adjacency, window=1)

    assert out == [("A", "B", 2), ("B", "C", 3)]


def test_no_arrow_from_a_neighbour_that_crossed_long_ago_or_in_the_same_frame() -> None:
    """A neighbour that crossed long before the window is old news; one
    crossing in the same frame could not have been seen yet (the hazard
    model's "strictly earlier"). B crosses at frame 3; A crossed at frame 0
    (3 frames earlier, outside a 2-frame window); C crossed at frame 3 too.
    No arrow points at B (nor at A or C, which had no earlier neighbour)."""
    series = {"A": "5555", "B": "0005", "C": "0005"}
    adjacency = {"A": frozenset({"B"}), "B": frozenset({"A", "C"}), "C": frozenset({"B"})}

    out = handoffs(series, mark=5, adjacency=adjacency, window=2)

    assert out == []


def test_hand_offs_expected_by_chance_shuffle_the_state_s_timings_exactly() -> None:
    """When everyone crosses at once (a broadcast), most counties have a
    neighbour that crossed "recently", so arrows appear anyway. The honest
    yardstick is how many arrows chance alone would draw: keep a county's
    own crossing frame, shuffle the other counties' frames within its state.
    A neighbour then crossed in the window with probability c / (n - 1),
    where c is how many OTHER counties in the state crossed in the window and
    n how many crossed at all. Expected arrows into the county: its in-state
    neighbours x c / (n - 1). Exact; no random draws.

    Line A - B - C (all Missouri, "29"), crossing frames 1, 2, 3, window 1:
      A: nothing in the state crossed in [0, 1) -> 0
      B: 2 neighbours; one other county (A) crossed in [1, 2); n - 1 = 2
         -> 2 x 1 / 2 = 1.0
      C: 1 neighbour; one other (B) crossed in [2, 3) -> 1 x 1 / 2 = 0.5
    Total 1.5 by chance, against the 2 actual hand-offs (A->B, B->C)."""
    series = {"29001": "0555", "29003": "0055", "29005": "0005"}
    adjacency = {
        "29001": frozenset({"29003"}),
        "29003": frozenset({"29001", "29005"}),
        "29005": frozenset({"29003"}),
    }

    out = chance_handoffs(series, mark=5, adjacency=adjacency, window=1)

    assert out == {"29001": 0.0, "29003": 1.0, "29005": 0.5}


def test_a_county_alone_in_its_state_has_no_chance_arrows() -> None:
    """With no other county in its state to shuffle, chance draws nothing:
    0.0, not a division by zero. One Missouri county and one Kansas county,
    neighbours across the state line, both crossing at frame 1."""
    series = {"29001": "05", "20001": "05"}
    adjacency = {"29001": frozenset({"20001"}), "20001": frozenset({"29001"})}

    out = chance_handoffs(series, mark=5, adjacency=adjacency, window=1)

    assert out == {"29001": 0.0, "20001": 0.0}


def test_a_county_that_never_crosses_the_mark_gets_no_arrows_and_no_chance() -> None:
    """A county still below the mark at the last frame ("0124") never crossed:
    it is neither the end of an arrow nor counted by chance. Its neighbour
    crossing at frame 1 has no earlier neighbour either."""
    series = {"29001": "0555", "29003": "0124"}
    adjacency = {"29001": frozenset({"29003"}), "29003": frozenset({"29001"})}

    assert handoffs(series, mark=5, adjacency=adjacency, window=2) == []
    assert chance_handoffs(series, mark=5, adjacency=adjacency, window=2) == {"29001": 0.0}
