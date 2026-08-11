"""The ballot-measure metadata table (docs/MEASUREMENT_DESIGN.md step 2).

`data/catalog/ballot_measures.csv` is statewide measure METADATA —
identity, date, topic, orientation (`progressive_side`), certified yes
share, outcome, severity note, and same-ballot structure — assembled by
`scripts/assemble_measure_catalog.py` from the researched corpora. This
loader hands analysis code a validated, typed table. It is metadata,
not an ingest: county-level results still arrive measure-by-measure
through `geofluid.ingest.referendum` with certified-total acceptance.
"""

from pathlib import Path

import pandas as pd


def load_measure_catalog(path: str | Path) -> pd.DataFrame:
    """Load the measure catalog CSV as a validated DataFrame."""
    panel = pd.read_csv(path, dtype={"yes_pct": float})
    panel["election_date"] = pd.to_datetime(panel["election_date"])

    duplicated = panel["measure_id"][panel["measure_id"].duplicated()]
    if len(duplicated) > 0:
        raise ValueError(f"duplicate measure_id(s) in catalog: {sorted(set(duplicated))}")

    # progressive_side signs every dissonance computation (NO was the
    # progressive vote in KS/KY, YES in OH — the orientation lesson);
    # outcome partitions analyses. Unknown values in either would corrupt
    # results silently, so both are closed vocabularies.
    for column, allowed in (
        ("progressive_side", {"yes", "no"}),
        ("outcome", {"pass", "fail"}),
    ):
        bad = panel.loc[~panel[column].isin(sorted(allowed)), "measure_id"]
        if len(bad) > 0:
            raise ValueError(f"invalid {column} value(s) for measure_id(s): {sorted(bad)}")

    return panel
