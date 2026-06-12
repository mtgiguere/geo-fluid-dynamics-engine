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

import pandas as pd

from geofluid.ingest.county_demographics import acs5_county_url, load_county_demographics
from geofluid.ingest.county_geometry import county_shapefile_to_geojson
from geofluid.ingest.county_returns import load_county_returns
from geofluid.map.layers import export_year_metrics
from geofluid.panel.master import build_master_panel
from geofluid.spatial.moran import local_morans_by_year
from geofluid.spatial.weights import county_adjacency

OUT = Path("web/public/data")


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
    lisa = local_morans_by_year(panel, adjacency, value_column="swing_dem_2p")
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


if __name__ == "__main__":
    main()
