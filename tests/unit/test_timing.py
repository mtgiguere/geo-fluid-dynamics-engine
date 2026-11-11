"""Tests for the timing model: does an idea reach a county after it reaches the
county's neighbours? (Module 1, the survival/hazard half of the Wave Predictor.)

Our election snapshots say a whole state moves at once. The timing model asks
the question a snapshot cannot: WHEN did each county adopt an idea, and was the
idea already next door when it did? It is built and proved first on rooftop
solar, an idea known to spread from neighbour to neighbour and recorded install
by install, before it is pointed back at politics.

Three steps, each tested here:
  1. take-off: the quarter each county's adoption "takes off";
  2. the at-risk table: one row per county per quarter until it takes off,
     with the share of its neighbours that had already taken off;
  3. the hazard fit: how much a neighbour having taken off raises a county's
     chance of taking off this quarter, after the nationwide clock (the same
     quarter for everyone) is accounted for.
"""

import pandas as pd
import pytest

from geofluid.spatial.timing import (
    at_risk_table,
    fit_hazard,
    fit_neighbour_hazard,
    takeoff_quarters,
)

TAKEOFF_COLUMNS = ["fips", "takeoff"]
AT_RISK_COLUMNS = ["fips", "period", "event", "neighbour_share"]

_QUARTERS = [pd.Timestamp(q) for q in ["2015-01-01", "2015-04-01", "2015-07-01", "2015-10-01"]]


def _panel(cumulative: dict[str, list[int]]) -> pd.DataFrame:
    """A county-quarter adoption panel (geofluid.ingest.solar output) from each
    county's cumulative installs over the four quarters of 2015."""
    rows = [
        {"fips": fips, "quarter": q, "cumulative_installs": c}
        for fips, series in cumulative.items()
        for q, c in zip(_QUARTERS, series, strict=True)
    ]
    return pd.DataFrame(rows)


def test_takeoff_is_the_first_quarter_a_county_reaches_its_share_of_its_final_count() -> None:
    """A county "takes off" in the first quarter its running total reaches a
    set share of the total it ends with. Measured against the county's OWN
    final count, so a state whose ZIP codes are only partly reported (Texas,
    Maryland, about a quarter) is not mistaken for a late adopter.

    County 06073 ends 2015 with 10 installs: running total 0, 1, 5, 10. At a
    share of 0.5 the bar is 5, first reached in Q3 (2015-07-01)."""
    panel = _panel({"06073": [0, 1, 5, 10]})

    takeoffs = takeoff_quarters(panel, share=0.5, min_installs=1)

    assert list(takeoffs.columns) == TAKEOFF_COLUMNS
    assert takeoffs.to_dict("records") == [{"fips": "06073", "takeoff": pd.Timestamp("2015-07-01")}]


def test_a_county_with_too_few_installs_has_no_takeoff() -> None:
    """With two installs, "half its final count" is simply its first install:
    one household's decision, not a county taking off. A county is timed only
    if it ends with at least `min_installs`. A county with none at all would
    otherwise "reach" a bar of zero in the very first quarter.

    At min_installs 5: 06073 (ends at 10) is timed, Q3 as before; 29510 (ends
    at 2) and 29189 (ends at 0) are left out."""
    panel = _panel({"06073": [0, 1, 5, 10], "29510": [0, 0, 1, 2], "29189": [0, 0, 0, 0]})

    takeoffs = takeoff_quarters(panel, share=0.5, min_installs=5)

    assert takeoffs.to_dict("records") == [{"fips": "06073", "takeoff": pd.Timestamp("2015-07-01")}]


def _takeoffs(quarters: dict[str, str]) -> pd.DataFrame:
    """A take-off table (takeoff_quarters output) from fips -> quarter start."""
    return pd.DataFrame(
        {"fips": list(quarters), "takeoff": [pd.Timestamp(q) for q in quarters.values()]}
    )


def test_at_risk_table_has_a_row_per_county_quarter_until_takeoff() -> None:
    """The survival layout: a county is "at risk" of taking off every quarter
    until it does, so it has one row per quarter from the first take-off
    anywhere up to and including its own. `event` is 1 in its take-off
    quarter and 0 before. `neighbour_share` is the share of its neighbours
    that took off in an EARLIER quarter (strictly before: a neighbour taking
    off the same quarter cannot yet have been seen).

    Three counties in a line, A - B - C. A takes off Q1 2015, B Q2, C Q4.
      A: Q1 event 1, neighbour B not yet            -> share 0
      B: Q1 event 0, neither A nor C yet            -> 0
         Q2 event 1, A (Q1) yes, C no               -> 1/2
      C: Q1 event 0, B not yet                      -> 0
         Q2 event 0, B is taking off THIS quarter   -> 0
         Q3 event 0, B (Q2) yes                     -> 1
         Q4 event 1                                 -> 1
    Seven rows, sorted by county, then quarter."""
    takeoffs = _takeoffs({"A": "2015-01-01", "B": "2015-04-01", "C": "2015-10-01"})
    adjacency = {"A": frozenset({"B"}), "B": frozenset({"A", "C"}), "C": frozenset({"B"})}

    table = at_risk_table(takeoffs, adjacency)

    assert list(table.columns) == AT_RISK_COLUMNS
    assert table["fips"].tolist() == ["A", "B", "B", "C", "C", "C", "C"]
    assert table["period"].tolist() == [_QUARTERS[0], _QUARTERS[0], _QUARTERS[1], *_QUARTERS]
    assert table["event"].tolist() == [1, 0, 1, 0, 0, 0, 1]
    assert table["neighbour_share"].tolist() == [0.0, 0.0, 0.5, 0.0, 0.0, 1.0, 1.0]


def test_an_untimed_neighbour_counts_neither_way() -> None:
    """A neighbour with no take-off (too few installs, or outside the source
    file, like every Missouri county across the line from Illinois) is
    unknown, not "not yet". It is left out of the share entirely.

    B borders A (takes off Q1) and D (untimed). B takes off Q2. At Q2 its
    known neighbours are just A, which took off earlier: share 1, not 1/2."""
    takeoffs = _takeoffs({"A": "2015-01-01", "B": "2015-04-01"})
    adjacency = {"A": frozenset({"B"}), "B": frozenset({"A", "D"})}

    table = at_risk_table(takeoffs, adjacency)

    assert table[table["fips"] == "B"]["neighbour_share"].tolist() == [0.0, 1.0]


def test_a_county_with_no_timed_neighbour_is_left_out() -> None:
    """A county none of whose neighbours is timed has no share to measure
    (0 of 0), and a county missing from the adjacency map (no county shape
    to border anything) is the same case. Both are left out of the table
    rather than given a made-up share.

    A and B border each other. C's only neighbour, D, is untimed; E is not
    in the adjacency map at all. Only A and B have rows."""
    takeoffs = _takeoffs(
        {"A": "2015-01-01", "B": "2015-04-01", "C": "2015-04-01", "E": "2015-04-01"}
    )
    adjacency = {"A": frozenset({"B"}), "B": frozenset({"A"}), "C": frozenset({"D"})}

    table = at_risk_table(takeoffs, adjacency)

    assert sorted(set(table["fips"])) == ["A", "B"]


def _cells(cells: list[tuple[int, float, int, int]], state: str = "06") -> pd.DataFrame:
    """An at-risk table from (quarter index, neighbour_share, rows, events)
    cells: `rows` county-quarters with that share, `events` of them taking
    off. Every county is in `state` (its fips starts with the state code)."""
    rows = [
        {
            "fips": f"{state}{q}{x}{i}",
            "period": _QUARTERS[q],
            "event": int(i < events),
            "neighbour_share": x,
        }
        for q, x, n, events in cells
        for i in range(n)
    ]
    return pd.DataFrame(rows, columns=AT_RISK_COLUMNS)


def test_hazard_fit_recovers_the_neighbour_odds_ratio_exactly() -> None:
    """The hazard model is a logistic regression on the at-risk table: each
    county-quarter's chance of taking off, with one baseline per quarter
    (the nationwide clock: incentives, prices, the same for everyone) and
    one coefficient on neighbour_share (the wave). The answer is reported
    as an odds ratio: how many times the odds of taking off this quarter
    are multiplied for a county whose neighbours have ALL taken off,
    against one whose neighbours have none.

    A noise-free world built to have odds ratio exactly 4:
      Q1, share 0: 5 rows, 1 takes off  -> p 1/5, odds 1/4
      Q1, share 1: 2 rows, 1 takes off  -> p 1/2, odds 1     (x4)
      Q2, share 0: 2 rows, 1 takes off  -> p 1/2, odds 1
      Q2, share 1: 5 rows, 4 take off   -> p 4/5, odds 4     (x4)
    The two quarters have different baselines (odds 1/4 vs 1 with no
    neighbour), but the same multiplier, so the model fits every cell
    exactly and the maximum-likelihood odds ratio is 4."""
    table = _cells([(0, 0.0, 5, 1), (0, 1.0, 2, 1), (1, 0.0, 2, 1), (1, 1.0, 5, 4)])

    odds_ratio = fit_neighbour_hazard(table, clock="national")

    assert odds_ratio == pytest.approx(4.0, rel=1e-9)


def test_a_quarter_where_nobody_or_everybody_takes_off_does_not_move_the_answer() -> None:
    """The real table has many quarters in which no county takes off (the
    early years) and ends on a quarter in which the last county still at
    risk does. Such a quarter says nothing about neighbours: with no events
    its baseline is pushed toward odds 0, with all events toward infinity,
    and neither limit exists. The fit sets those quarters aside.

    The odds-ratio-4 world from above, plus Q3 (three rows at share 1/2,
    none taking off) and Q4 (two rows at share 0 and 1, both taking off):
    the answer is still exactly 4."""
    table = _cells(
        [
            (0, 0.0, 5, 1),
            (0, 1.0, 2, 1),
            (1, 0.0, 2, 1),
            (1, 1.0, 5, 4),
            (2, 0.5, 3, 0),
            (3, 0.0, 1, 1),
            (3, 1.0, 1, 1),
        ]
    )

    odds_ratio = fit_neighbour_hazard(table, clock="national")

    assert odds_ratio == pytest.approx(4.0, rel=1e-9)


def test_a_nationwide_clock_alone_is_not_read_as_a_wave() -> None:
    """The trap the quarter baselines exist to close. Late quarters have
    both more take-offs (a tax credit, cheaper panels) and more neighbours
    already taken off, simply because time has passed. Pooled, that looks
    like neighbours mattering. Within each quarter here they do not:
      Q1, share 0: 8 rows, 2 take off -> p 1/4
      Q1, share 1: 4 rows, 1 takes off -> p 1/4   (same)
      Q2, share 0: 2 rows, 1 takes off -> p 1/2
      Q2, share 1: 8 rows, 4 take off -> p 1/2   (same)
    Pooled, share 0 is 3 of 10 and share 1 is 5 of 12, a false odds ratio of
    about 1.67. With one baseline per quarter the answer is exactly 1: no
    wave, only a clock."""
    table = _cells([(0, 0.0, 8, 2), (0, 1.0, 4, 1), (1, 0.0, 2, 1), (1, 1.0, 8, 4)])

    odds_ratio = fit_neighbour_hazard(table, clock="national")

    assert odds_ratio == pytest.approx(1.0, rel=1e-9)


def test_a_state_clock_alone_is_not_read_as_a_wave() -> None:
    """The same trap one level down. A state programme (Illinois's 2019
    incentive, Maryland's 2021 surge) lifts every county in that state in
    the same quarters, and most of a county's neighbours are in its own
    state. A nationwide clock cannot see that, so a state moving all at once
    looks like a wave. With clock="state" each state gets its own baseline
    per quarter, and only what spreads beyond the state's own clock counts.

    One quarter, two states, and within each state neighbours do not matter:
      California (06), share 0: 2 rows, 1 takes off -> p 1/2
      California (06), share 1: 8 rows, 4 take off  -> p 1/2   (same)
      Illinois   (17), share 0: 8 rows, 2 take off  -> p 1/4
      Illinois   (17), share 1: 4 rows, 1 takes off -> p 1/4   (same)
    With one national baseline the quarter pools to share 0: 3 of 10,
    share 1: 5 of 12; a single binary predictor fits those two rates
    exactly, so the odds ratio is (5/7) / (3/7) = 5/3: a false wave. With
    one baseline per state it is exactly 1."""
    table = pd.concat(
        [
            _cells([(0, 0.0, 2, 1), (0, 1.0, 8, 4)], state="06"),
            _cells([(0, 0.0, 8, 2), (0, 1.0, 4, 1)], state="17"),
        ]
    )

    assert fit_neighbour_hazard(table, clock="national") == pytest.approx(5 / 3, rel=1e-9)
    assert fit_neighbour_hazard(table, clock="state") == pytest.approx(1.0, rel=1e-9)


def test_at_risk_table_can_step_by_year() -> None:
    """Laws are dated by year, not quarter. With freq="YS" (year start) the
    table steps one year at a time. A adopts in 2001, B in 2003; they border.
      A: 2001 event 1, B not yet           -> share 0
      B: 2001 event 0, A not yet earlier   -> 0
         2002 event 0, A (2001) yes        -> 1
         2003 event 1                      -> 1"""
    takeoffs = _takeoffs({"A": "2001-01-01", "B": "2003-01-01"})
    adjacency = {"A": frozenset({"B"}), "B": frozenset({"A"})}

    table = at_risk_table(takeoffs, adjacency, freq="YS")

    assert table["period"].dt.year.tolist() == [2001, 2001, 2002, 2003]
    assert table["event"].tolist() == [1, 0, 0, 1]
    assert table["neighbour_share"].tolist() == [0.0, 0.0, 1.0, 1.0]


def test_a_unit_that_never_takes_off_stays_at_risk_to_the_end_and_counts_as_not_yet() -> None:
    """Solar timed only counties that took off. A law is different: a state
    that has not adopted by the data's last year (2017 in SPID) is not
    unknown, it is "not yet". It stays at risk every period to `end` with no
    event (right-censored, in survival terms), and as a neighbour it counts
    in the share's denominator, as not yet adopted.

    A line A - B - C, observed to 2003. A adopts 2001, C 2002, B never.
      A: 2001 event 1, B not yet                  -> share 0
      B: 2001 event 0, neither A nor C yet         -> 0
         2002 event 0, A (2001) yes, C no          -> 1/2
         2003 event 0, A and C both earlier        -> 1
      C: 2001 event 0, B not yet                   -> 0
         2002 event 1, B not yet                   -> 0
    Six rows, sorted by unit, then period."""
    takeoffs = _takeoffs({"A": "2001-01-01", "C": "2002-01-01"})
    adjacency = {"A": frozenset({"B"}), "B": frozenset({"A", "C"}), "C": frozenset({"B"})}

    table = at_risk_table(
        takeoffs, adjacency, freq="YS", never=["B"], end=pd.Timestamp("2003-01-01")
    )

    assert table["fips"].tolist() == ["A", "B", "B", "B", "C", "C"]
    assert table["period"].dt.year.tolist() == [2001, 2001, 2002, 2003, 2001, 2002]
    assert table["event"].tolist() == [1, 0, 0, 0, 0, 1]
    assert table["neighbour_share"].tolist() == [0.0, 0.0, 0.5, 1.0, 0.0, 0.0]


def test_each_wave_in_a_pooled_table_keeps_its_own_clock() -> None:
    """Pooling 724 laws into one table: each law has its own clock (a
    Supreme Court ruling or a federal grant pushes one law, not the others).
    A table that pools waves carries a `wave` column, and the baselines are
    per wave per period, so one law's busy year is not credited to
    neighbours adopting a different law.

    One year, one state, two laws, and within each law neighbours do not
    matter:
      law p1, share 0: 2 rows, 1 adopts -> p 1/2
      law p1, share 1: 8 rows, 4 adopt  -> p 1/2
      law p2, share 0: 8 rows, 2 adopt  -> p 1/4
      law p2, share 1: 4 rows, 1 adopts -> p 1/4
    Without the wave column the year pools to 3 of 10 vs 5 of 12: odds ratio
    (5/7) / (3/7) = 5/3, a false wave. With it, exactly 1."""
    pooled = pd.concat(
        [
            _cells([(0, 0.0, 2, 1), (0, 1.0, 8, 4)]).assign(wave="p1"),
            _cells([(0, 0.0, 8, 2), (0, 1.0, 4, 1)]).assign(wave="p2"),
        ],
        ignore_index=True,
    )

    assert fit_neighbour_hazard(pooled, clock="national") == pytest.approx(1.0, rel=1e-9)
    unlabelled = pooled.drop(columns="wave")
    assert fit_neighbour_hazard(unlabelled, clock="national") == pytest.approx(5 / 3, rel=1e-9)


def test_hazard_fit_recovers_two_odds_ratios_at_once() -> None:
    """The placebo needs two shares in ONE model. A state adopts once, so a
    neighbour adopting in the next few years is by construction one that
    has not adopted yet: fitted alone, the future share is dragged below 1
    by the past share it is tangled with. Fitted together, each is read
    holding the other fixed: past share = learning from a neighbour who went
    first; future share = neighbours being alike (they cannot be learned from).

    A noise-free world with odds ratio 4 on the past share and 2 on the
    future share, one quarter (baseline odds 1/4):
      past 0, future 0: 5 rows, 1 takes off -> odds 1/4
      past 1, future 0: 2 rows, 1 takes off -> odds 1     (x4)
      past 0, future 1: 3 rows, 1 takes off -> odds 1/2   (x2)
      past 1, future 1: 3 rows, 2 take off  -> odds 2     (x4 x2)
    Every cell fits the additive model exactly, so the maximum-likelihood
    odds ratios are 4 and 2."""
    cells = [(0.0, 0.0, 5, 1), (1.0, 0.0, 2, 1), (0.0, 1.0, 3, 1), (1.0, 1.0, 3, 2)]
    table = pd.DataFrame(
        [
            {
                "fips": f"06{past:.0f}{future:.0f}{i}",
                "period": _QUARTERS[0],
                "event": int(i < events),
                "past_share": past,
                "future_share": future,
            }
            for past, future, n, events in cells
            for i in range(n)
        ]
    )

    odds_ratios = fit_hazard(table, ["past_share", "future_share"], clock="national")

    assert odds_ratios == pytest.approx({"past_share": 4.0, "future_share": 2.0}, rel=1e-9)
