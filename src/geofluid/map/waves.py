"""Frames for the wave player: how far along each county is, period by period.

The research log measures waves with a hazard model; the wave player
(`scripts/build_wave_player.py` -> `web/public/waves.html`) shows them. Each
frame colours a county by the share of its OWN final total reached so far,
the yardstick of the take-off rule (`geofluid.spatial.timing`): a big county
and a small one are read by the shape of their arrival, not their size.
"""

from collections.abc import Mapping, Sequence

import pandas as pd

# One character per frame: "0"-"9" for 0-90% (rounded down to the 10% step),
# "A" for all of it.
_LEVELS = "0123456789A"


def running_share_levels(
    counts: pd.DataFrame, periods: Sequence[pd.Timestamp], min_total: int
) -> dict[str, str]:
    """Per county, one level character per period in `periods`.

    `counts` has one row per county and period with new adoptions (`fips`,
    `period`, `count`); a period with no row had none.
    """
    wide = counts.pivot_table(index="fips", columns="period", values="count", aggfunc="sum")
    running = wide.reindex(columns=list(periods), fill_value=0).fillna(0).cumsum(axis=1)
    # A county ending with a handful has no shape to read (with two, "half
    # its final count" is one person's decision): left out, drawn as no data.
    running = running[running.iloc[:, -1] >= min_total]
    share = running.div(running.iloc[:, -1], axis=0)
    level = (share * 10).astype(int)
    return {str(fips): "".join(_LEVELS[v] for v in row) for fips, row in level.iterrows()}


def _crossing_frames(series: Mapping[str, str], mark: int) -> dict[str, int]:
    """The first frame each county is at or past `mark`; never-crossers left out."""
    crossed = {}
    for fips, s in series.items():
        frame = next((i for i, c in enumerate(s) if _LEVELS.index(c) >= mark), None)
        if frame is not None:
            crossed[fips] = frame
    return crossed


def handoffs(
    series: Mapping[str, str],
    mark: int,
    adjacency: Mapping[str, frozenset[str]],
    window: int,
) -> list[tuple[str, str, int]]:
    """The arrows: (from, to, frame) for each county crossing `mark` at
    `frame` after a neighbour crossed in the `window` frames before it.

    An arrow says "this neighbour had it first, recently", the hazard
    model's "past neighbour" share drawn on the map. It is not proof that
    the idea passed along that border; the research log's learning ratio is
    the test of that.
    """
    crossed = _crossing_frames(series, mark)
    out = []
    for fips, frame in crossed.items():
        for n in sorted(adjacency.get(fips, frozenset())):
            if n in crossed and frame - window <= crossed[n] < frame:
                out.append((n, fips, frame))
    return sorted(out, key=lambda h: (h[2], h[1], h[0]))


def chance_handoffs(
    series: Mapping[str, str],
    mark: int,
    adjacency: Mapping[str, frozenset[str]],
    window: int,
) -> dict[str, float]:
    """Arrows chance alone would draw into each crossing county.

    In a broadcast, everyone crosses at once, so most counties have a
    neighbour that crossed "recently" and arrows appear anyway. This is the
    yardstick: keep the county's own crossing frame and shuffle the OTHER
    counties' frames within its state (the first two FIPS digits). A given
    neighbour then crossed in the window with probability c / (n - 1): c
    other counties in the state crossed in the window, n crossed at all.
    Expected arrows = in-state neighbours that crossed x c / (n - 1); exact,
    no random draws. More real arrows than this is a wave; about the same is
    a broadcast.
    """
    crossed = _crossing_frames(series, mark)
    by_state: dict[str, list[int]] = {}
    for fips, frame in crossed.items():
        by_state.setdefault(fips[:2], []).append(frame)
    out = {}
    for fips, frame in crossed.items():
        frames = by_state[fips[:2]]
        others = len(frames) - 1
        in_window = sum(frame - window <= f < frame for f in frames)
        neighbours = adjacency.get(fips, frozenset())
        degree = sum(1 for n in neighbours if n[:2] == fips[:2] and n in crossed)
        out[fips] = degree * in_window / others if others else 0.0
    return out
