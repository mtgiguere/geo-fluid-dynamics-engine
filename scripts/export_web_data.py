"""Export the frontend's static data products.

Thin orchestration only — every transform it calls is contract-tested.
Writes to web/public/data/:
  counties.geojson      county geometry (cb_2021 5m scale), fetched once
  metrics_<year>.json   per-election metrics, joined client-side by fips

Requires CENSUS_API_KEY in the environment and the MIT returns CSV plus the
cb_2021 5m boundary shapefile under data/raw/ (see README in repo root).
"""

import json
import os
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from geofluid.dissonance import build_measure_overlay
from geofluid.ingest.county_demographics import acs5_county_url, load_county_demographics
from geofluid.ingest.county_geometry import county_shapefile_to_geojson
from geofluid.ingest.county_returns import load_county_returns
from geofluid.ingest.referendum import load_ks_referendum_workbook
from geofluid.map.layers import export_year_metrics
from geofluid.panel.master import build_master_panel
from geofluid.scope import build_scope_catalog
from geofluid.spatial.moran import local_morans_by_year, significant_quadrants
from geofluid.spatial.weights import county_adjacency

OUT = Path("web/public/data")

# Ballot measures — the modular "issue overlay" catalog. Each measure compares
# a county's issue vote against its presidential lean (dissonance) and ships
# its own data file. One entry today; append to add more states/measures.
MEASURES = [
    {
        "id": "ks_abortion_2022",
        "label": "Kansas: Abortion rights (Aug 2022)",
        "scope": "20",
        "baseline_year": 2020,
        "issue_label": "Voted NO — to keep abortion rights",
        "workbook": "data/raw/ks_amendment_2022_precinct.xlsx",
    },
]

# Metro presets — cross-border by design (seeds expand through the adjacency
# graph, so these span state lines). Seeds are core counties; hops=1 pulls in
# the surrounding metro including the other side of the river / state line.
METROS = [
    # St. Louis City + County -> reaches Madison/St. Clair/Monroe IL.
    {"id": "stl", "label": "St. Louis (MO-IL)", "seed": ["29510", "29189"], "hops": 1},
    # Jackson MO (Kansas City) + Wyandotte KS -> spans the state line.
    {"id": "kc", "label": "Kansas City (MO-KS)", "seed": ["29095", "20209"], "hops": 1},
]


def fetch_acs(year: int, api_key: str) -> pd.DataFrame:
    with urllib.request.urlopen(acs5_county_url(year, api_key=api_key)) as resp:  # noqa: S310
        return load_county_demographics(json.load(resp), year=year)


def main() -> None:
    key = os.environ["CENSUS_API_KEY"]
    OUT.mkdir(parents=True, exist_ok=True)

    geojson = county_shapefile_to_geojson("data/raw/cb_2021_5m/cb_2021_us_county_5m.shp")
    (OUT / "counties.geojson").write_text(json.dumps(geojson, allow_nan=False))
    print(f"counties.geojson: {len(geojson['features'])} features")

    # Connecticut's demographic context comes from ACS 2021, the last vintage
    # on the old-county geography the returns use (see TDD_CONTRACT.md and
    # the master panel tests for the full CT story).
    acs23 = fetch_acs(2023, key)
    ct21 = fetch_acs(2021, key).pipe(lambda d: d[d["fips"].str.startswith("09")])
    demographics = pd.concat([acs23, ct21], ignore_index=True)

    returns = load_county_returns(pd.read_csv("data/raw/countypres_2000-2024.csv"))
    panel = build_master_panel(returns, demographics)

    # Wave anchors: LISA quadrants of swing per year, computed on the
    # analysis-grade 500k boundaries (NOT the 5m display file — generalized
    # geometry is for eyes, adjacency is for math).
    adjacency = county_adjacency(
        county_shapefile_to_geojson("data/raw/cb_2021/cb_2021_us_county_500k.shp")
    )
    # 999 conditional permutations per county-year; quadrant labels survive
    # only below alpha = 0.05 (standard LISA practice — the map paints no
    # cluster that chance could explain). The generator is SEEDED so the
    # published map is exactly reproducible — a documented reproducibility
    # decision, distinct from the seed-specific test assertions the contract
    # bans (TDD_CONTRACT.md RED FLAG 3).
    lisa = local_morans_by_year(
        panel,
        adjacency,
        value_column="swing_dem_2p",
        permutations=999,
        rng=np.random.default_rng(20260612),
    )
    lisa = significant_quadrants(lisa.set_index("fips"), alpha=0.05).reset_index()
    panel = panel.merge(
        lisa.rename(columns={"quadrant": "swing_lisa_quadrant"})[
            ["fips", "year", "swing_lisa_quadrant"]
        ],
        on=["fips", "year"],
        how="left",
    )

    for year in sorted(panel["year"].unique()):
        metrics = export_year_metrics(panel, year=int(year))
        path = OUT / f"metrics_{year}.json"
        path.write_text(json.dumps(metrics, allow_nan=False))
        print(f"{path.name}: {len(metrics)} counties")

    # Scope catalog: nation + every state + the cross-border metro presets,
    # built on the analysis-grade adjacency (so metros span state lines).
    fips_universe = [f["id"] for f in geojson["features"]]
    catalog = build_scope_catalog(fips_universe, adjacency, METROS)
    (OUT / "scopes.json").write_text(json.dumps(catalog, allow_nan=False))
    print(f"scopes.json: {len(catalog)} scopes")

    # Ballot-measure overlays: dissonance = issue vote vs presidential lean.
    # The source workbooks are gitignored (like the MIT returns CSV), so skip
    # any measure whose file is absent rather than failing the whole export.
    county_name_to_fips = {
        f["properties"]["NAME"].upper() + "|" + f["id"][:2]: f["id"] for f in geojson["features"]
    }
    published = []
    for measure in MEASURES:
        if not Path(measure["workbook"]).exists():
            print(f"  skip {measure['id']}: {measure['workbook']} not present")
            continue
        state = measure["scope"]
        name_to_fips = {
            name.split("|")[0]: fips
            for name, fips in county_name_to_fips.items()
            if name.endswith("|" + state)
        }
        referendum = load_ks_referendum_workbook(measure["workbook"], name_to_fips)
        baseline = returns[
            (returns["year"] == measure["baseline_year"]) & (returns["fips"].str.startswith(state))
        ].set_index("fips")["dem_share_2p"]
        overlay = build_measure_overlay(referendum, baseline)
        (OUT / f"measure_{measure['id']}.json").write_text(json.dumps(overlay, allow_nan=False))
        published.append(
            {k: measure[k] for k in ("id", "label", "scope", "baseline_year", "issue_label")}
        )
        print(f"measure_{measure['id']}.json: {len(overlay)} counties")
    (OUT / "measures.json").write_text(json.dumps(published, allow_nan=False))
    print(f"measures.json: {len(published)} measures")


if __name__ == "__main__":
    main()
