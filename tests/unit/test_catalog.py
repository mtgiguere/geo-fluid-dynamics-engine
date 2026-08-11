"""Tests for geofluid.catalog — the ballot-measure metadata table.

The catalog (data/catalog/ballot_measures.csv, assembled per
docs/MEASUREMENT_DESIGN.md step 2) is statewide measure METADATA:
identity, date, topic, orientation, result, severity note, and
same-ballot structure. The loader's job is to hand analysis code a
validated, typed table — and to fail loudly on the corruption classes
that silently poison downstream joins (duplicate measure ids, unknown
orientation/outcome values).
"""

from pathlib import Path

import pandas as pd
import pytest

from geofluid.catalog import load_measure_catalog

CANONICAL_COLUMNS = [
    "measure_id",
    "ballot_id",
    "state",
    "election_date",
    "election_type",
    "topic",
    "measure_name",
    "description_short",
    "progressive_side",
    "yes_pct",
    "outcome",
    "severity_note",
    "same_ballot_catalog_ids",
    "same_ballot_companions",
    "source_url",
]

HEADER = ",".join(CANONICAL_COLUMNS)


def _row(
    measure_id: str = "ks_20220802_value_them_both",
    state: str = "KS",
    date: str = "2022-08-02",
    side: str = "no",
    yes_pct: str = "41.0",
    outcome: str = "fail",
) -> str:
    return (
        f"{measure_id},KS_{date},{state},{date},primary,abortion,"
        f"Value Them Both,desc,{side},{yes_pct},{outcome},no-right amendment,,,"
        "https://example.org"
    )


def write_catalog(path: Path, rows: list[str]) -> None:
    path.write_text(HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8")


def test_returns_canonical_columns(tmp_path: Path) -> None:
    """The loader returns exactly the canonical catalog schema, in order.

    Consumers join on measure_id and group by topic/date; a renamed or
    reordered column should fail here, not in their code.
    """
    csv = tmp_path / "catalog.csv"
    write_catalog(csv, [_row()])

    panel = load_measure_catalog(csv)

    assert list(panel.columns) == CANONICAL_COLUMNS
    assert len(panel) == 1


def test_dates_are_datetimes_and_yes_pct_is_float_with_missing_as_nan(tmp_path: Path) -> None:
    """election_date parses to a real datetime; yes_pct is float, and a
    measure with no countable result (AR 2024 Issue 3: votes never
    certified by court order) loads as NaN rather than crashing or
    becoming the string "".

    Derivation: row 1 has yes_pct "41.0" -> 41.0 exactly (no float
    surprise: 41.0 is representable); row 2 has an empty yes_pct field.
    """
    csv = tmp_path / "catalog.csv"
    write_catalog(
        csv,
        [
            _row(),
            _row(measure_id="ar_20241105_issue_3", date="2024-11-05", yes_pct=""),
        ],
    )

    panel = load_measure_catalog(csv)

    assert pd.api.types.is_datetime64_any_dtype(panel["election_date"])
    assert panel["election_date"].iloc[0] == pd.Timestamp("2022-08-02")
    assert pd.api.types.is_float_dtype(panel["yes_pct"])
    assert panel["yes_pct"].iloc[0] == 41.0
    assert pd.isna(panel["yes_pct"].iloc[1])


def test_duplicate_measure_id_fails_loudly_naming_the_id(tmp_path: Path) -> None:
    """measure_id is the join key to county referendum panels; a silent
    duplicate would double rows in every downstream merge. The loader
    refuses, naming the offender so the fix is findable.
    """
    csv = tmp_path / "catalog.csv"
    write_catalog(csv, [_row(), _row()])

    with pytest.raises(ValueError, match="ks_20220802_value_them_both"):
        load_measure_catalog(csv)


def test_unknown_progressive_side_fails_loudly(tmp_path: Path) -> None:
    """progressive_side is the orientation bit that signs every dissonance
    computation (the KS/KY "no" vs OH "yes" lesson) — any value outside
    {yes, no} means the sign of downstream results is undefined.
    """
    csv = tmp_path / "catalog.csv"
    write_catalog(csv, [_row(side="progressive")])

    with pytest.raises(ValueError, match="progressive_side"):
        load_measure_catalog(csv)


def test_unknown_outcome_fails_loudly(tmp_path: Path) -> None:
    """outcome must be pass or fail; anything else (e.g. "passed",
    "struck down") would silently vanish from outcome-filtered analysis.
    """
    csv = tmp_path / "catalog.csv"
    write_catalog(csv, [_row(outcome="struck down")])

    with pytest.raises(ValueError, match="outcome"):
        load_measure_catalog(csv)


def test_real_catalog_loads_and_matches_certified_landmarks() -> None:
    """Real-data acceptance on the committed catalog (immediately GREEN —
    regression guard, the Bugs #10-12 pattern applied to metadata).

    Externally certified landmarks:
    - KS Aug-2022 "Value Them Both": certified YES 41.03% -> 41.0.
    - OH Nov-2023 Issue 1: certified YES 56.78% -> 56.8, and its
      progressive side is YES (the orientation flip that motivated
      progressive_side in the first place).
    The committed catalog also loads under every validation gate above
    (unique ids, closed vocabularies), which is itself the acceptance
    claim: the research output satisfies the loader's contract.
    """
    panel = load_measure_catalog(
        Path(__file__).parents[2] / "data" / "catalog" / "ballot_measures.csv"
    )

    assert len(panel) >= 271
    ks = panel[panel["ballot_id"] == "KS_2022-08-02"].iloc[0]
    assert ks["yes_pct"] == 41.0
    assert ks["progressive_side"] == "no"
    oh = panel[(panel["ballot_id"] == "OH_2023-11-07") & (panel["topic"] == "abortion")].iloc[0]
    assert oh["yes_pct"] == 56.8
    assert oh["progressive_side"] == "yes"
