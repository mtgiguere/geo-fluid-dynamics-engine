"""Tests for the referendum ingest — issue votes, the engine's real fuel.

First source: the Kansas SoS official precinct file for the August 2022
constitutional amendment (the abortion referendum). Format: one row per
(County, Precinct, Candidate) where Candidate is the string
'Amendment, Constitutional - "YES"' or '... - "NO"', votes as numbers,
counties by NAME (no FIPS — the name->fips mapping comes from our own
boundary file).

Semantics note, explicit because it inverts intuition: for this measure
"NO" was the vote to PRESERVE abortion rights (the amendment would have
removed them). The panel carries raw yes/no and no_share; downstream
analysis decides which side maps to which politics, per measure.
"""

import pandas as pd
import pytest

from geofluid.ingest.referendum import load_ks_referendum

_NAME_TO_FIPS = {"ALLEN": "20001", "JOHNSON": "20091"}


def _raw(rows: list[dict[str, object]]) -> pd.DataFrame:
    defaults: dict[str, object] = {
        "County": "Allen",
        "Precinct": "Carlyle Township",
        "Race": "Constitutional Amendment",
        "Candidate": 'Amendment, Constitutional - "YES"',
        "Party": float("nan"),
        "Votes": 0.0,
        "VTD": "000010",
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def test_precincts_aggregate_to_county_with_no_share() -> None:
    """The county referendum panel: precinct rows sum per county per side;
    no_share = NO / (YES + NO). Allen: YES 66 + 54 = 120, NO 48 + 22 = 70,
    no_share = 70 / 190 (derived here, before the assertion was written).
    Counties arrive as names and leave as FIPS, sorted."""
    raw = _raw(
        [
            {"Votes": 66.0},
            {"Candidate": 'Amendment, Constitutional - "NO"', "Votes": 48.0},
            {"Precinct": "Cottage Grove", "Votes": 54.0},
            {
                "Precinct": "Cottage Grove",
                "Candidate": 'Amendment, Constitutional - "NO"',
                "Votes": 22.0,
            },
            {"County": "Johnson", "Votes": 100.0},
            {
                "County": "Johnson",
                "Candidate": 'Amendment, Constitutional - "NO"',
                "Votes": 300.0,
            },
        ]
    )

    panel = load_ks_referendum(raw, _NAME_TO_FIPS)

    assert list(panel.columns) == ["fips", "yes_votes", "no_votes", "total_votes", "no_share"]
    assert list(panel["fips"]) == ["20001", "20091"]
    allen = panel.iloc[0]
    assert allen["yes_votes"] == 120
    assert allen["no_votes"] == 70
    assert allen["total_votes"] == 190
    assert abs(allen["no_share"] - 70 / 190) < 1e-12
    assert abs(panel.iloc[1]["no_share"] - 0.75) < 1e-12


def test_unknown_county_name_fails_loudly() -> None:
    """A county name that maps to no FIPS is a join defect (misspelling,
    wrong state, format drift) — silent dropping would shrink the panel
    invisibly. Raise, naming the county."""
    raw = _raw([{"County": "Gotham", "Votes": 5.0}])

    with pytest.raises(ValueError, match="GOTHAM"):
        load_ks_referendum(raw, _NAME_TO_FIPS)


def test_unexpected_candidate_label_fails_loudly() -> None:
    """A referendum has exactly two sides. A third candidate string means
    the format changed (write-ins, a new race mixed in) — never a silent
    'other' bucket."""
    raw = _raw([{"Candidate": "Amendment, Constitutional - ABSTAIN", "Votes": 5.0}])

    with pytest.raises(ValueError, match="ABSTAIN"):
        load_ks_referendum(raw, _NAME_TO_FIPS)
