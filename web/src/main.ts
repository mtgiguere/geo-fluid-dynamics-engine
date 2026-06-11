import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import "./style.css";

// Every static fetch is BASE_URL-prefixed. This is the lesson of the prior
// project's Bug #8: an absolute "/data/..." path 404s the moment the app is
// deployed under a sub-path (GitHub Pages), and no unit test can see it.
const BASE = import.meta.env.BASE_URL;

// The seven elections in the master panel. The slider indexes this array.
const YEARS = [2000, 2004, 2008, 2012, 2016, 2020, 2024] as const;

type Metrics = {
  dem_votes: number;
  rep_votes: number;
  other_votes: number;
  total_votes: number;
  dem_share_2p: number;
  acs_vintage: number;
  total_population: number;
  median_age: number | null;
  pct_65_plus: number | null;
  median_hh_income: number | null;
  median_home_value: number | null;
  pct_owner_occupied: number | null;
  pct_bachelors_plus: number | null;
};
type YearMetrics = Record<string, Metrics>;

const status = document.getElementById("status")!;
const yearLabel = document.getElementById("year-label")!;
const slider = document.getElementById("year") as HTMLInputElement;

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

const map = new mapboxgl.Map({
  container: "map",
  style: "mapbox://styles/mapbox/light-v11",
  center: [-96.5, 38.5],
  zoom: 3.6,
  minZoom: 3,
});

const metricsCache = new Map<number, YearMetrics>();
let allFips: string[] = [];
let currentMetrics: YearMetrics = {};

async function fetchJson<T>(path: string): Promise<T> {
  const resp = await fetch(`${BASE}${path}`);
  if (!resp.ok) throw new Error(`${path}: HTTP ${resp.status}`);
  return resp.json() as Promise<T>;
}

async function loadYear(year: number): Promise<void> {
  if (!metricsCache.has(year)) {
    metricsCache.set(year, await fetchJson<YearMetrics>(`data/metrics_${year}.json`));
  }
  currentMetrics = metricsCache.get(year)!;
  for (const fips of allFips) {
    const m = currentMetrics[fips];
    map.setFeatureState(
      { source: "counties", id: fips },
      m ? { ...m, has_data: true } : { has_data: false, dem_share_2p: null },
    );
  }
  yearLabel.textContent = String(year);
  const counted = Object.keys(currentMetrics).length;
  status.textContent = `${counted.toLocaleString()} counties · ${year}`;
}

function fmtPct(v: number | null): string {
  return v == null ? "–" : `${(v * 100).toFixed(1)}%`;
}
function fmtNum(v: number | null): string {
  return v == null ? "–" : v.toLocaleString();
}
function fmtUsd(v: number | null): string {
  return v == null ? "–" : `$${v.toLocaleString()}`;
}

function popupHtml(name: string, m: Metrics): string {
  const share = m.dem_share_2p;
  const lean =
    share >= 0.5
      ? `D +${((share - 0.5) * 200).toFixed(1)}`
      : `R +${((0.5 - share) * 200).toFixed(1)}`;
  return `
    <strong>${name}</strong>
    <table>
      <tr><td>Two-party result</td><td><b>${lean}</b></td></tr>
      <tr><td>Total votes</td><td>${fmtNum(m.total_votes)}</td></tr>
      <tr><td>Population</td><td>${fmtNum(m.total_population)}</td></tr>
      <tr><td>Median age</td><td>${fmtNum(m.median_age)}</td></tr>
      <tr><td>65 and over</td><td>${fmtPct(m.pct_65_plus)}</td></tr>
      <tr><td>Median income</td><td>${fmtUsd(m.median_hh_income)}</td></tr>
      <tr><td>Median home value</td><td>${fmtUsd(m.median_home_value)}</td></tr>
      <tr><td>Owner-occupied</td><td>${fmtPct(m.pct_owner_occupied)}</td></tr>
      <tr><td>Bachelor's or higher</td><td>${fmtPct(m.pct_bachelors_plus)}</td></tr>
    </table>
    <small>Demographics: ACS 5-year ${m.acs_vintage}</small>`;
}

map.on("load", async () => {
  type FC = { features: { properties: { fips: string } }[] };
  const geojson = await fetchJson<FC>("data/counties.geojson");
  allFips = geojson.features.map((f) => f.properties.fips);

  map.addSource("counties", {
    type: "geojson",
    data: geojson as unknown as GeoJSON.FeatureCollection,
    promoteId: "fips",
  });

  map.addLayer(
    {
      id: "county-fills",
      type: "fill",
      source: "counties",
      paint: {
        // Diverging two-party scale; policy-excluded geographies (Alaska,
        // territories) carry has_data=false and render neutral gray.
        "fill-color": [
          "case",
          ["==", ["feature-state", "has_data"], true],
          [
            "interpolate",
            ["linear"],
            ["to-number", ["feature-state", "dem_share_2p"]],
            0.2,
            "#b2182b",
            0.35,
            "#ef8a62",
            0.5,
            "#f7f7f7",
            0.65,
            "#67a9cf",
            0.8,
            "#2166ac",
          ],
          "#d4d4d4",
        ],
        "fill-opacity": 0.85,
      },
    },
    "waterway-label",
  );
  map.addLayer(
    {
      id: "county-lines",
      type: "line",
      source: "counties",
      paint: { "line-color": "#ffffff", "line-width": 0.4 },
    },
    "waterway-label",
  );

  await loadYear(YEARS[Number(slider.value)]!);

  slider.addEventListener("input", () => {
    void loadYear(YEARS[Number(slider.value)]!);
  });

  map.on("click", "county-fills", (e) => {
    const feature = e.features?.[0];
    if (!feature) return;
    const fips = (feature.properties as { fips: string }).fips;
    const name = (feature.properties as { NAME: string }).NAME;
    const m = currentMetrics[fips];
    new mapboxgl.Popup({ maxWidth: "320px" })
      .setLngLat(e.lngLat)
      .setHTML(m ? popupHtml(name, m) : `<strong>${name}</strong><br/><small>No county-level data (reported statewide or non-voting territory)</small>`)
      .addTo(map);
  });
  map.on("mouseenter", "county-fills", () => {
    map.getCanvas().style.cursor = "pointer";
  });
  map.on("mouseleave", "county-fills", () => {
    map.getCanvas().style.cursor = "";
  });
});
