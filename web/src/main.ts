import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import "./style.css";
import { METRIC_DEFS, fillColor, legendModel } from "./metrics";
import type { MetricDef, Metrics } from "./metrics";

// Every static fetch is BASE_URL-prefixed. This is the lesson of the prior
// project's Bug #8: an absolute "/data/..." path 404s the moment the app is
// deployed under a sub-path (GitHub Pages), and no unit test can see it.
const BASE = import.meta.env.BASE_URL;

// The seven elections in the master panel. The slider indexes this array.
const YEARS = [2000, 2004, 2008, 2012, 2016, 2020, 2024] as const;

type YearMetrics = Record<string, Metrics>;

const status = document.getElementById("status")!;
const yearLabel = document.getElementById("year-label")!;
const slider = document.getElementById("year") as HTMLInputElement;
const metricSelect = document.getElementById("metric") as HTMLSelectElement;
const legend = document.getElementById("legend")!;

for (const def of METRIC_DEFS) {
  const option = document.createElement("option");
  option.value = def.key;
  option.textContent = def.label;
  metricSelect.appendChild(option);
}

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

function currentMetricDef(): MetricDef {
  return METRIC_DEFS.find((d) => d.key === metricSelect.value) ?? METRIC_DEFS[0]!;
}

function renderLegend(def: MetricDef): void {
  const model = legendModel(def);
  if (model.kind === "ramp") {
    legend.innerHTML = `
      <span id="legend-left">${model.left}</span>
      <div id="ramp" style="background: ${model.gradientCss}"></div>
      <span id="legend-right">${model.right}</span>`;
    return;
  }
  const chips = model.items
    .map(
      (item) =>
        `<span class="chip"><i style="background: ${item.color}"></i>${item.label}</span>`,
    )
    .join("");
  legend.innerHTML = `<div>${chips}<div class="caption">${model.caption}</div></div>`;
}

function applyMetric(): void {
  const def = currentMetricDef();
  map.setPaintProperty(
    "county-fills",
    "fill-color",
    fillColor(def) as mapboxgl.ExpressionSpecification,
  );
  renderLegend(def);
}

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
      m ? { ...m, has_data: true } : { has_data: false },
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
function fmtLean(share: number): string {
  return share >= 0.5
    ? `D +${((share - 0.5) * 200).toFixed(1)}`
    : `R +${((0.5 - share) * 200).toFixed(1)}`;
}
function fmtSwing(swing: number | null): string {
  if (swing == null) return "–";
  return swing >= 0 ? `D +${(swing * 100).toFixed(1)}` : `R +${(-swing * 100).toFixed(1)}`;
}
function fmtQuadrant(quadrant: string | null): string {
  const labels: Record<string, string> = {
    "high-high": "D-swing core",
    "low-low": "R-swing core",
    "high-low": "D outlier",
    "low-high": "R outlier",
  };
  return quadrant == null ? "–" : (labels[quadrant] ?? quadrant);
}

function popupHtml(name: string, m: Metrics): string {
  return `
    <strong>${name}</strong>
    <table>
      <tr><td>Two-party result</td><td><b>${fmtLean(m.dem_share_2p)}</b></td></tr>
      <tr><td>Swing vs last election</td><td>${fmtSwing(m.swing_dem_2p)}</td></tr>
      <tr><td>Wave position</td><td>${fmtQuadrant(m.swing_lisa_quadrant)}</td></tr>
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
        "fill-color": fillColor(METRIC_DEFS[0]!) as mapboxgl.ExpressionSpecification,
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

  applyMetric();
  await loadYear(YEARS[Number(slider.value)]!);

  slider.addEventListener("input", () => {
    void loadYear(YEARS[Number(slider.value)]!);
  });
  metricSelect.addEventListener("change", applyMetric);

  map.on("click", "county-fills", (e) => {
    const feature = e.features?.[0];
    if (!feature) return;
    const fips = (feature.properties as { fips: string }).fips;
    const name = (feature.properties as { NAME: string }).NAME;
    const m = currentMetrics[fips];
    new mapboxgl.Popup({ maxWidth: "320px" })
      .setLngLat(e.lngLat)
      .setHTML(
        m
          ? popupHtml(name, m)
          : `<strong>${name}</strong><br/><small>No county-level data (reported statewide or non-voting territory)</small>`,
      )
      .addTo(map);
  });
  map.on("mouseenter", "county-fills", () => {
    map.getCanvas().style.cursor = "pointer";
  });
  map.on("mouseleave", "county-fills", () => {
    map.getCanvas().style.cursor = "";
  });
});
