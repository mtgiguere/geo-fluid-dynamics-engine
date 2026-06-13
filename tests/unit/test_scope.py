"""Tests for geographic scope — "my area," cross-border by construction.

Most organizations work a state, a metro, or a district, not the whole
country. A scope is a set of FIPS. A METRO scope must not clip to a state
line: St. Louis influences and is influenced by the Illinois counties across
the river, so "St. Louis and its surroundings" is a seed of core counties
expanded outward through the SAME queen-adjacency graph the spatial models
use — which crosses the river automatically.
"""

from geofluid.scope import build_scope_catalog, neighborhood

# A miniature bi-state St. Louis metro, real FIPS:
#   29510 St. Louis City, 29189 St. Louis County, 29183 St. Charles (MO)
#   17119 Madison, 17163 St. Clair (IL, across the Mississippi)
_STL = {
    "29510": frozenset({"29189"}),
    "29189": frozenset({"29510", "29183", "17119"}),
    "29183": frozenset({"29189"}),
    "17119": frozenset({"29189", "17163"}),
    "17163": frozenset({"17119"}),
}


def test_zero_hops_is_just_the_seed() -> None:
    """hops=0 means exactly the counties you named — no expansion."""
    assert neighborhood(_STL, {"29510"}, hops=0) == frozenset({"29510"})


def test_one_hop_adds_direct_neighbors() -> None:
    """From St. Louis City, one hop reaches St. Louis County (its only
    neighbor here)."""
    assert neighborhood(_STL, {"29510"}, hops=1) == frozenset({"29510", "29189"})


def test_two_hops_cross_the_state_line_into_illinois() -> None:
    """Two hops from St. Louis City reach across the river into Madison
    County, Illinois (and St. Charles MO) — the cross-border influence a
    state-clipped filter would wrongly hide. This is the whole point."""
    assert neighborhood(_STL, {"29510"}, hops=2) == frozenset({"29510", "29189", "29183", "17119"})


def test_seed_county_absent_from_graph_is_still_included() -> None:
    """A seed county with no adjacency entry (an island, or a FIPS not in the
    graph) is still part of the scope — you asked for it. It simply
    contributes no neighbors."""
    assert neighborhood(_STL, {"15003"}, hops=2) == frozenset({"15003"})


def test_catalog_has_nation_every_state_and_cross_border_metros() -> None:
    """The shippable scope list: one nation scope (everything), one scope per
    state present (FIPS prefix, human-named), and each metro preset expanded
    through the graph. Built once in Python because metros need adjacency and
    states need the name map; the frontend just loads it."""
    universe = ["29510", "29189", "29183", "17119", "17163", "20091", "20173"]
    metros = [{"id": "stl", "label": "St. Louis, MO-IL", "seed": ["29510", "29189"], "hops": 1}]

    catalog = build_scope_catalog(universe, _STL, metros)
    by_id = {s["id"]: s for s in catalog}

    # Nation: everything, kind tagged.
    assert by_id["us"]["kind"] == "nation"
    assert sorted(by_id["us"]["fips"]) == sorted(universe)

    # One scope per state prefix, human-named, fips sorted within.
    assert by_id["29"]["kind"] == "state"
    assert by_id["29"]["label"] == "Missouri"
    assert by_id["29"]["fips"] == ["29183", "29189", "29510"]
    assert by_id["17"]["label"] == "Illinois"
    assert by_id["20"]["label"] == "Kansas"

    # Metro: seed expanded one hop, crossing into Illinois (17119).
    assert by_id["stl"]["kind"] == "metro"
    assert by_id["stl"]["label"] == "St. Louis, MO-IL"
    assert set(by_id["stl"]["fips"]) == {"29510", "29189", "29183", "17119"}


def test_catalog_order_is_nation_then_states_by_name_then_metros() -> None:
    """Deterministic ordering for a stable dropdown: nation first, states
    alphabetical by name, metros last in input order."""
    universe = ["29510", "17119", "20091"]
    metros = [{"id": "stl", "label": "St. Louis, MO-IL", "seed": ["29510"], "hops": 0}]

    catalog = build_scope_catalog(universe, _STL, metros)

    assert [s["id"] for s in catalog] == ["us", "17", "20", "29", "stl"]
