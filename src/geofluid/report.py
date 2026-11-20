"""The report layer: every number and date a public page publishes.

The page builders in scripts/ (the November receipt, the blueprint, the
demo) are HTML assembly. The decisions behind what a reader sees (which file
is the registered record, when the registration happened, how a chance is
worded, what each measure's call and odds are) live here, under test. A page
can then only drift from the record if this module does, and its tests pin
it to the frozen registration files (TDD_CONTRACT.md, Section 7).
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from geofluid.scoring import bracket_odds


def registration_dates(pred_dir: Path) -> tuple[str, list[str]]:
    """The registration date and any dated supplements, oldest first.

    Every registration writes a `REGISTERED_SHA256_<date>.csv` hash file. The
    FIRST is the registration itself (the tagged, pre-vote record); each
    later one is a supplement that adds files and never edits the earlier
    ones. Dates are ISO, so sorting the names sorts them in time.
    """
    dates = sorted(p.stem.split("_")[-1] for p in pred_dir.glob("REGISTERED_SHA256_*.csv"))
    if not dates:
        raise FileNotFoundError(f"no REGISTERED_SHA256_*.csv in {pred_dir}")
    return dates[0], dates[1:]


def latest_prediction_file(pred_dir: Path, prefix: str) -> tuple[Path, str]:
    """The file a page shows for `prefix`, and its status.

    A REGISTERED file always wins over a draft, however new the draft: only
    the registered numbers are the record that gets graded.
    """
    registered = sorted(pred_dir.glob(f"{prefix}_REGISTERED_*.csv"))
    if registered:
        return registered[-1], "REGISTERED"
    drafts = sorted(pred_dir.glob(f"{prefix}_DRAFT_*.csv"))
    if not drafts:
        raise FileNotFoundError(f"no {prefix}_REGISTERED_* or {prefix}_DRAFT_* file in {pred_dir}")
    return drafts[-1], "DRAFT"


def reader_percent(p: float) -> str:
    """A chance as a reader sees it: whole percentage points, never certain.

    Nothing a forecast says is certain, so a chance that would print as 0% or
    100% reads "under 1%" or "over 99%". The test is made on the ROUNDED
    figure, the one the reader would see: thresholds on the raw chance leave
    a gap at the rounding edge (0.995 printed as "100%").
    """
    shown = f"{p * 100:.0f}"
    if shown == "0":
        return "under 1%"
    if shown == "100":
        return "over 99%"
    return f"{shown}%"


@dataclass(frozen=True)
class MeasureCall:
    """What a receipt card publishes for one measure (shares of the tracked side)."""

    low: float
    central: float
    high: float
    counties_won: int
    n_counties: int
    chance_now: float
    chance_plus_one: float


def measure_call(rows: pd.DataFrame) -> MeasureCall:
    """The published call for one measure, from its registered prediction rows.

    The statewide bracket (`level_low` / `level_central` / `level_high`) is
    repeated on every county row; `counties_won` counts the counties whose
    predicted share for the tracked side is above one half. The two chances
    are the bracket read as odds (`scoring.bracket_odds`): the tracked side
    ahead as things stand, and after one statewide point its way.
    """
    first = rows.iloc[0]
    low, central, high = (float(first[c]) for c in ("level_low", "level_central", "level_high"))
    now, plus_one, _sd = bracket_odds(low=low, central=central, high=high)
    return MeasureCall(
        low=low,
        central=central,
        high=high,
        counties_won=int((rows["pred_progressive_share"] > 0.5).sum()),
        n_counties=len(rows),
        chance_now=now,
        chance_plus_one=plus_one,
    )
