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
  swing_dem_2p: number | null;
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

// ---------------------------------------------------------------------------
// Metric registry: what the map can color by.
//
// Partisan quantities use the red-blue diverging ramp. Demographics use a
// viridis-style sequential ramp on purpose — coloring income or age in
// red/blue would invite readers to see partisanship where there is none.
// ---------------------------------------------------------------------------
const PARTISAN_RAMP = ["#b2182b", "#ef8a62", "#f7f7f7", "#67a9cf", "#2166ac"];
const SEQUENTIAL_RAMP = ["#440154", "#3b528b", "#21918c", "#5ec962", "#fde725"];

interface MetricDef {
  key: keyof Metrics;
  label: string;
  stops: number[];
  colors: string[];
  legendLeft: string;
  legendRight: string;
}

const METRIC_DEFS: MetricDef[] = [
  {
    key: "dem_share_2p",
    label: "Two-party result",
    stops: [0.2, 0.35, 0.5, 0.65, 0.8],
    colors: PARTISAN_RAMP,
    legendLeft: "More Republican",
    legendRight: "More Democratic",
  },
  {
    key: "swing_dem_2p",
    label: "Swing since last election",
    stops: [-0.15, -0.075, 0, 0.075, 0.15],
    colors: PARTISAN_RAMP,
    legendLeft: "Swung Republican",
    legendRight: "Swung Democratic",
  },
  {
    key: "median_age",
    label: "Median age",
    stops: [30, 37, 44, 51, 58],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "Younger",
    legendRight: "Older",
  },
  {
    key: "pct_65_plus",
    label: "Share 65 and over",
    stops: [0.1, 0.16, 0.22, 0.28, 0.34],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "Fewer seniors",
    legendRight: "More seniors",
  },
  {
    key: "median_hh_income",
    label: "Median household income",
    stops: [40_000, 60_000, 80_000, 100_000, 120_000],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "$40k",
    legendRight: "$120k+",
  },
  {
    key: "median_home_value",
    label: "Median home value",
    stops: [80_000, 190_000, 300_000, 410_000, 520_000],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "$80k",
    legendRight: "$520k+",
  },
  {
    key: "pct_owner_occupied",
    label: "Owner-occupied share",
    stops: [0.5, 0.6, 0.7, 0.8, 0.9],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "More renters",
    legendRight: "More owners",
  },
  {
    key: "pct_bachelors_plus",
    label: "Bachelor's or higher",
    stops: [0.1, 0.2, 0.3, 0.4, 0.5],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "Less college",
    legendRight: "More college",
  },
];

const status = document.getElementById("status")!;
const yearLabel = document.getElementById("year-label")!;
const slider = document.getElementById("year") as HTMLInputElement;
const metricSelect = document.getElementById("metric") as HTMLSelectElement;
const legendLeft = document.getElementById("legend-left")!;
const legendRight = document.getElementById("legend-right")!;
const ramp = document.getElementById("ramp")!;

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

// A county colors only when it has data AND the selected metric is an actual
// number for it — swing is null in 2000 (no previous election in the panel)
// and a few counties carry null ACS medians. Those render neutral gray, the
// same as policy-excluded geographies: gray always means "no value here".
function fillColor(def: MetricDef): mapboxgl.ExpressionSpecification {
  const interpolate: unknown[] = [
    "interpolate",
    ["linear"],
    ["to-number", ["feature-state", def.key]],
  ];
  def.stops.forEach((stop, i) => interpolate.push(stop, def.colors[i]));
  return [
    "case",
    [
      "all",
      ["==", ["feature-state", "has_data"], true],
      ["==", ["typeof", ["feature-state", def.key]], "number"],
    ],
    interpolate,
    "#d4d4d4",
  ] as mapboxgl.ExpressionSpecification;
}

function applyMetric(): void {
  const def = currentMetricDef();
  map.setPaintProperty("county-fills", "fill-color", fillColor(def));
  legendLeft.textContent = def.legendLeft;
  legendRight.textContent = def.legendRight;
  ramp.style.background = `linear-gradient(to right, ${def.colors.join(", ")})`;
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

function popupHtml(name: string, m: Metrics): string {
  return `
    <strong>${name}</strong>
    <table>
      <tr><td>Two-party result</td><td><b>${fmtLean(m.dem_share_2p)}</b></td></tr>
      <tr><td>Swing vs last election</td><td>${fmtSwing(m.swing_dem_2p)}</td></tr>
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
        "fill-color": fillColor(METRIC_DEFS[0]!),
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
