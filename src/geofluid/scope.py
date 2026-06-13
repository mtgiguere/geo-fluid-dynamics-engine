"""Geographic scope — restrict the map to the area an organization works.

A scope is a set of county FIPS. The national map is too much for the real
user, who works a state, a metro, or a district. State scopes are a FIPS
prefix; metro/region scopes are a seed of core counties expanded outward
through the queen-adjacency graph, which crosses state lines by construction
(St. Louis reaches its Illinois neighbors across the river).

Scopes are a DISPLAY lens: the spatial statistics are always computed
nationally so border counties keep their out-of-state neighbors. A scope
chooses what to show and where to point the camera, never what to recompute.
"""

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

# State/territory FIPS prefix -> name. Reference data, not logic: the lookup
# that turns a 2-digit prefix into a dropdown label. Covers the 50 states, DC,
# and the territories present in the Census boundary file.
_STATE_NAMES = {
    "01": "Alabama",
    "02": "Alaska",
    "04": "Arizona",
    "05": "Arkansas",
    "06": "California",
    "08": "Colorado",
    "09": "Connecticut",
    "10": "Delaware",
    "11": "District of Columbia",
    "12": "Florida",
    "13": "Georgia",
    "15": "Hawaii",
    "16": "Idaho",
    "17": "Illinois",
    "18": "Indiana",
    "19": "Iowa",
    "20": "Kansas",
    "21": "Kentucky",
    "22": "Louisiana",
    "23": "Maine",
    "24": "Maryland",
    "25": "Massachusetts",
    "26": "Michigan",
    "27": "Minnesota",
    "28": "Mississippi",
    "29": "Missouri",
    "30": "Montana",
    "31": "Nebraska",
    "32": "Nevada",
    "33": "New Hampshire",
    "34": "New Jersey",
    "35": "New Mexico",
    "36": "New York",
    "37": "North Carolina",
    "38": "North Dakota",
    "39": "Ohio",
    "40": "Oklahoma",
    "41": "Oregon",
    "42": "Pennsylvania",
    "44": "Rhode Island",
    "45": "South Carolina",
    "46": "South Dakota",
    "47": "Tennessee",
    "48": "Texas",
    "49": "Utah",
    "50": "Vermont",
    "51": "Virginia",
    "53": "Washington",
    "54": "West Virginia",
    "55": "Wisconsin",
    "56": "Wyoming",
    "60": "American Samoa",
    "66": "Guam",
    "69": "Northern Mariana Islands",
    "72": "Puerto Rico",
    "78": "U.S. Virgin Islands",
}


def neighborhood(
    adjacency: Mapping[str, frozenset[str]],
    seed: Iterable[str],
    hops: int,
) -> frozenset[str]:
    """The seed counties plus everything within `hops` adjacency steps.

    Expansion follows the same graph the spatial models use, so a metro seed
    reaches across state lines automatically. Seed counties are always
    included, even if absent from the graph (they simply add no neighbors).
    """
    frontier = set(seed)
    visited = set(frontier)
    for _ in range(hops):
        nxt: set[str] = set()
        for fips in frontier:
            nxt |= adjacency.get(fips, frozenset()) - visited
        if not nxt:
            break
        visited |= nxt
        frontier = nxt
    return frozenset(visited)


def build_scope_catalog(
    fips_universe: Iterable[str],
    adjacency: Mapping[str, frozenset[str]],
    metros: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Assemble the shippable scope list: nation, one scope per state present
    (FIPS prefix, named), and each metro preset expanded through the graph.

    Order is deterministic for a stable dropdown: nation, then states
    alphabetical by name, then metros in input order. Each metro spec is
    {id, label, seed, hops}.
    """
    universe = sorted(fips_universe)
    catalog: list[dict[str, Any]] = [
        {"id": "us", "label": "United States", "kind": "nation", "fips": universe}
    ]

    states: dict[str, list[str]] = {}
    for fips in universe:
        states.setdefault(fips[:2], []).append(fips)
    for prefix in sorted(states, key=lambda p: _STATE_NAMES.get(p, p)):
        catalog.append(
            {
                "id": prefix,
                "label": _STATE_NAMES.get(prefix, prefix),
                "kind": "state",
                "fips": sorted(states[prefix]),
            }
        )

    for metro in metros:
        catalog.append(
            {
                "id": metro["id"],
                "label": metro["label"],
                "kind": "metro",
                "fips": sorted(neighborhood(adjacency, metro["seed"], metro["hops"])),
            }
        )
    return catalog
