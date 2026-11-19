"""The report layer: every number and date a public page publishes.

The page builders in scripts/ (the November receipt, the blueprint, the
demo) are HTML assembly. The decisions behind what a reader sees (which file
is the registered record, when the registration happened, how a chance is
worded, what each measure's call and odds are) live here, under test. A page
can then only drift from the record if this module does, and its tests pin
it to the frozen registration files (TDD_CONTRACT.md, Section 7).
"""

from pathlib import Path


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
