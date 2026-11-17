"""Build the wave player: `web/public/waves.html` + `web/public/data/waves.json`.

Show, don't tell. Pick an idea, press play, and watch each county fill in as
the idea arrives (colour = share of the county's OWN final total so far,
`geofluid.map.waves`); the counties crossing halfway each frame flash, so the
moving edge of the wave shows. Each topic sets its mark where its story is
(see `mark` below). Some ideas roll across the map (rooftop
solar, a new candidate's donor base); some land everywhere at once (a famous
candidate's launch, giving after Dobbs). The numbers behind each are in
docs/RESEARCH_LOG.md (fourth to ninth looks).

Needs the gitignored raw data under data/raw/ (see docs/DATA_SOURCES.md):
the LBNL county-quarter solar panel, the 2019 ActBlue extracts, the 2022
ActBlue newcomer extract, and the Census ZCTA-county file.

    uv run python scripts/build_wave_player.py
"""

import json
from pathlib import Path

import pandas as pd

from geofluid.ingest.zcta_county import zip_to_county
from geofluid.map.svg import project_rings
from geofluid.map.waves import chance_handoffs, handoffs, running_share_levels
from geofluid.scope import _STATE_NAMES
from geofluid.spatial.weights import county_adjacency

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
DATA_OUT = ROOT / "web/public/data/waves.json"
# Alaska, Hawaii, Puerto Rico and the Pacific and Caribbean territories are
# left off: on one projection they would shrink the lower 48 to a speck.
OFF_MAP = ("02", "15", "60", "66", "69", "72", "78")

CANDIDATES = {
    "buttigieg": ("Pete Buttigieg's donors, 2019", "1.64 [1.13, 2.26]: a wave"),
    "sanders": ("Bernie Sanders' donors, 2019", "1.42 [1.09, 1.88]: a wave"),
    "warren": ("Elizabeth Warren's donors, 2019", "1.45 [0.95, 2.13]: probably a wave"),
    "yang": ("Andrew Yang's donors, 2019", "1.06 [0.64, 1.82]: no county wave"),
    "biden": ("Joe Biden's donors, 2019", "1.09 [0.79, 1.47]: a broadcast"),
}
# The state where each idea is easiest to SEE, from a scratch scan
# (2026-11-14) of hand-offs against chance (`chance_handoffs`) at every mark
# and window. Only solar beats chance clearly enough to feature: New York,
# 80 hand-offs against 49 by chance. Candidates' best states (1.3-1.6x on
# 20-40 arrows) are what picking the best of 50 states finds by luck, so none
# is featured; their learning ratio is real but too small to see by eye.
# Biden's Iowa is featured as the contrast: everything at once.
FEATURED = {
    "Rooftop solar, 2000-2025": (
        "36",
        "80 hand-offs against 49 by chance, the clearest wave on the map",
    ),
    "Joe Biden's donors, 2019": (
        "19",
        "the contrast: nearly every county in two weeks, hand-offs no more than chance",
    ),
}
# Arrows reach back this many frames: about the hazard model's windows.
WINDOW = {"quarter": 4, "week": 4, "day": 3}


def _zip_county() -> pd.DataFrame:
    path = RAW / "us_census_zcta_county2020_20261110/tab20_zcta520_county20_natl.txt"
    return zip_to_county(pd.read_csv(path, sep="|", dtype=str))


def _solar() -> dict:
    panel = pd.read_csv(
        RAW / "us_lbnl_dss2026_20261109/county_quarter_panel.csv.gz",
        dtype={"fips": str},
        parse_dates=["quarter"],
    )
    counts = panel.rename(columns={"quarter": "period", "new_installs": "count"})
    periods = [p for p in sorted(counts["period"].unique()) if p >= pd.Timestamp("2000-01-01")]
    # Installs before 2000 are the head start, not part of the show: they are
    # folded into the first frame so a county's running total is still right.
    counts.loc[counts["period"] < periods[0], "period"] = periods[0]
    return {
        "title": "Rooftop solar, 2000-2025",
        "step": "quarter",
        "labels": [f"{p.year} Q{(p.month - 1) // 3 + 1}" for p in pd.to_datetime(periods)],
        "series": running_share_levels(counts, periods, min_total=25),
        "mark": 5,
        "verdict": "Learning ratio 2.4-3: a wave. Neighbours about 9 months apart.",
    }


def _candidates(look: pd.DataFrame) -> list[dict]:
    # One row per candidate, ZIP and day: how many donors gave to that
    # candidate for the first time (counts only; built from the streamed
    # filings, docs/DATA_SOURCES.md).
    donors = pd.read_csv(
        RAW / "us_fec_actblue_raw_2019_20261111/actblue_2019_new_donors_by_zip_day.csv.gz",
        dtype={"zip5": str},
        keep_default_na=False,
        parse_dates=["date"],
    )
    donors = donors.merge(look, on="zip5")
    donors["period"] = donors["date"] - pd.to_timedelta(donors["date"].dt.weekday, unit="D")
    periods = list(pd.date_range("2018-12-31", "2020-01-27", freq="W-MON"))
    topics = []
    for cand, (title, ratio) in CANDIDATES.items():
        counts = donors[donors["cand"] == cand].groupby(["fips", "period"])["new_donors"].sum()
        counts = counts.rename("count").reset_index()
        topics.append(
            {
                "title": title,
                "step": "week",
                "labels": [f"week of {p:%b %d, %Y}" for p in periods],
                "series": running_share_levels(counts, periods, min_total=20),
                # 20%: the weeks a county's base catches on. At 50% every
                # candidate's mark lands on the summer debates and the June 30
                # deadline, a broadcast that hides the difference.
                "mark": 2,
                "verdict": f"Learning ratio {ratio}.",
            }
        )
    return topics


def _dobbs(look: pd.DataFrame) -> dict:
    gifts = pd.read_csv(
        RAW / "us_fec_actblue_raw_20261111/actblue_zip_day_newcomers_2022.csv.gz",
        dtype={"zip5": str},
        keep_default_na=False,
        parse_dates=["date"],
    )
    # Around the ruling (June 24). From mid-April, most counties pass any
    # mark before the ruling, through steady giving and the leak, and the
    # day-one jump is hidden.
    periods = list(pd.date_range("2022-06-10", "2022-07-31", freq="D"))
    gifts = gifts[gifts["date"].between(periods[0], periods[-1])].merge(look, on="zip5")
    counts = gifts.groupby(["fips", "date"])["newcomers"].sum().rename("count").reset_index()
    counts = counts.rename(columns={"date": "period"})
    return {
        "title": "New donors around the Dobbs ruling, June-July 2022",
        "step": "day",
        "labels": [f"{p:%a %b %d, %Y}" for p in periods],
        "series": running_share_levels(counts, periods, min_total=20),
        "mark": 3,
        "verdict": "A broadcast: on June 24, 735 of 797 surging counties jumped the same day.",
    }


def _map() -> tuple[dict[str, str], float]:
    geo = json.loads((ROOT / "web/public/data/counties.geojson").read_text())
    rings = {}
    for f in geo["features"]:
        if f["id"][:2] in OFF_MAP:
            continue
        geom = f["geometry"]
        coords = geom["coordinates"]
        rings[f["id"]] = coords if geom["type"] == "MultiPolygon" else [coords]
    paths, _, height = project_rings(rings)
    return paths, height


def main() -> None:
    look = _zip_county()
    paths, height = _map()
    geo = json.loads((ROOT / "web/public/data/counties.geojson").read_text())
    adjacency = county_adjacency(geo)
    topics = [_solar(), *_candidates(look), _dobbs(look)]
    for t in topics:
        t["series"] = {k: v for k, v in t["series"].items() if k in paths}
        t["window"] = WINDOW[t["step"]]
        t["handoffs"] = handoffs(t["series"], t["mark"], adjacency, t["window"])
        chance = chance_handoffs(t["series"], t["mark"], adjacency, t["window"])
        t["chance"] = {k: round(v, 3) for k, v in chance.items() if v}
        if t["title"] in FEATURED:
            state, why = FEATURED[t["title"]]
            t["featured"] = {"state": state, "why": why}
        print(
            f"{t['title']}: {len(t['series'])} counties x {len(t['labels'])} frames, "
            f"{len(t['handoffs'])} hand-offs"
        )
    states = {f: _STATE_NAMES[f] for f in sorted({k[:2] for k in paths}) if f in _STATE_NAMES}
    DATA_OUT.write_text(
        json.dumps(
            {"height": height, "paths": paths, "states": states, "topics": topics},
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    print(f"wrote {DATA_OUT.relative_to(ROOT)} ({DATA_OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
