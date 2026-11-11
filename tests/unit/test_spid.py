"""Tests for the state-policy ingest: 724 laws, each adopted by the states
one at a time, 1691-2017.

Why this is here: solar shows a wave in the last 25 years, but people and
places change, so the roads a wave travels may change too. State policies
are hundreds of separate political waves over the same 50 states across a
century, so we can ask whether the same states keep going first and the same
neighbours keep following, era by era.

The raw input is the State Policy Innovation and Diffusion (SPID) database,
v1.2 (Boehmke, LaCombe and Brockway; Harvard Dataverse doi:10.7910/DVN/CVYSR7,
CC0). Two Stata files: adoptions (`SPID_v1.2.dta`: policy, statenam,
adopt_year; one row per state that adopted, never one for a state that did
not) and policies (`SPID_v1.2_policies.dta`: policy, source, majortopic_str,
and more). The canonical output is one row per adoption, keyed by the state's
two-digit FIPS code so it joins the county data (a county's state is the
first two digits of its fips).
"""

import pandas as pd
import pytest

from geofluid.ingest.spid import load_spid_adoptions

ADOPTION_COLUMNS = ["policy", "state_fips", "adopt_year", "topic", "source"]


def _policies(rows: list[dict[str, object]]) -> pd.DataFrame:
    """A raw policies frame from compact overrides."""
    defaults: dict[str, object] = {
        "policy": "aborparn",
        "first_year": 1981,
        "last_year": 2000,
        "adopt_count": 17,
        "source": "Boehmke-Skinner",
        "description": "Parent Notification For Abortion By A Minor",
        "majortopic": 12,
        "majortopic_str": "Law and Crime",
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def test_an_adoption_gets_its_state_code_and_its_policy_topic() -> None:
    """One adoption in, one row out. Missouri adopting parental notification
    for a minor's abortion in 1985 becomes state_fips "29" (Missouri's FIPS
    code), with the policy's topic ("Law and Crime") and source
    ("Boehmke-Skinner") joined from the policies file."""
    adoptions = pd.DataFrame(
        {"policy": ["aborparn"], "statenam": ["Missouri"], "adopt_year": [1985]}
    )

    out = load_spid_adoptions(adoptions, _policies([{}]))

    assert list(out.columns) == ADOPTION_COLUMNS
    assert out.to_dict("records") == [
        {
            "policy": "aborparn",
            "state_fips": "29",
            "adopt_year": 1985,
            "topic": "Law and Crime",
            "source": "Boehmke-Skinner",
        }
    ]


def test_a_state_name_that_is_not_a_state_stops_the_load() -> None:
    """All 50 names in v1.2 are spelled the standard way, but a future
    version, or a hand edit, could carry "Missisippi" or a territory. A name
    with no FIPS code would become a blank state and drop out of every
    neighbour count without a word. The load stops instead, naming it."""
    adoptions = pd.DataFrame(
        {
            "policy": ["aborparn"] * 2,
            "statenam": ["Missouri", "Missisippi"],
            "adopt_year": [1985] * 2,
        }
    )

    with pytest.raises(ValueError, match="Missisippi"):
        load_spid_adoptions(adoptions, _policies([{}]))


def test_an_adoption_of_a_policy_missing_from_the_policy_list_stops_the_load() -> None:
    """Every policy in the v1.2 adoptions file is in its policy list (724 of
    724). If a later version broke that, a plain join would quietly lose
    every adoption of the orphan policy, a whole wave. The load stops
    instead, naming the policy."""
    adoptions = pd.DataFrame(
        {
            "policy": ["aborparn", "orphanlaw"],
            "statenam": ["Missouri"] * 2,
            "adopt_year": [1985] * 2,
        }
    )

    with pytest.raises(ValueError, match="orphanlaw"):
        load_spid_adoptions(adoptions, _policies([{}]))
