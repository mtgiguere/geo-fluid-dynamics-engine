"""Frames for the wave player: how far along each county is, period by period.

The research log measures waves with a hazard model; the wave player
(`scripts/build_wave_player.py` -> `web/public/waves.html`) shows them. Each
frame colours a county by the share of its OWN final total reached so far,
the yardstick of the take-off rule (`geofluid.spatial.timing`): a big county
and a small one are read by the shape of their arrival, not their size.
"""

from collections.abc import Sequence

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
