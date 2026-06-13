import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import "./style.css";
import { METRIC_DEFS, fillColor, legendModel, storyline } from "./metrics";
import type { MetricDef, Metrics } from "./metrics";
import { boundsForScope } from "./scope";
import type { CountyFeature, Scope } from "./scope";
import { DISSONANCE_DEF, measureCaption, measureStoryline } from "./measure";
import type { Measure, MeasureOverlay } from "./measure";

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
const scopeSelect = document.getElementById("scope") as HTMLSelectElement;
const legend = document.getElementById("legend")!;
const storyEl = document.getElementById("storyline")!;
const playButton = document.getElementById("play") as HTMLButtonElement;

// Continental-US bounds, the camera target for the nation scope.
const US_BOUNDS: [[number, number], [number, number]] = [
  [-125, 24],
  [-66.5, 49.5],
];

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
let features: CountyFeature[] = [];
let scopes: Scope[] = [];

// Ballot-measure overlays. A measure is selected via a "measure:<id>" option
// in the metric dropdown; while one is active the map colors by dissonance
// (a single fixed measure), so the year controls are disabled.
const MEASURE_PREFIX = "measure:";
let measures: Measure[] = [];
const measureCache = new Map<string, MeasureOverlay>();
let activeMeasure: Measure | null = null;
let activeOverlay: MeasureOverlay | null = null;

function currentMetricDef(): MetricDef {
  return METRIC_DEFS.find((d) => d.key === metricSelect.value) ?? METRIC_DEFS[0]!;
}

function currentScope(): Scope | undefined {
  return scopes.find((s) => s.id === scopeSelect.value);
}

// The metrics restricted to the active scope — what the storyline counts over,
// so "12 counties moved toward..." means 12 in THIS area, not nationwide.
function scopedMetrics(): YearMetrics {
  const scope = currentScope();
  if (!scope || scope.kind === "nation") return currentMetrics;
  const inScope = new Set(scope.fips);
  return Object.fromEntries(
    Object.entries(currentMetrics).filter(([fips]) => inScope.has(fips)),
  );
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

// The legend for an active ballot measure: the dissonance ramp plus the
// plain-language caption explaining the comparison (and that the year slider
// does not apply).
function renderMeasureLegend(measure: Measure): void {
  const model = legendModel(DISSONANCE_DEF);
  const ramp =
    model.kind === "ramp"
      ? `<span id="legend-left">${model.left}</span>
         <div id="ramp" style="background: ${model.gradientCss}"></div>
         <span id="legend-right">${model.right}</span>`
      : "";
  legend.innerHTML = `<div>${ramp}<div class="caption">${measureCaption(measure)}</div></div>`;
}

function setYearControlsEnabled(enabled: boolean): void {
  slider.disabled = !enabled;
  playButton.disabled = !enabled;
  if (!enabled) stopPlaying();
}

async function loadMeasureOverlay(id: string): Promise<MeasureOverlay> {
  if (!measureCache.has(id)) {
    measureCache.set(id, await fetchJson<MeasureOverlay>(`data/measure_${id}.json`));
  }
  return measureCache.get(id)!;
}

// Apply the selected view — a per-year metric or a ballot measure. Measures
// color by dissonance, push their data into feature-state, auto-focus the
// measure's state, and disable the (irrelevant) year controls.
async function applyView(): Promise<void> {
  const value = metricSelect.value;
  if (value.startsWith(MEASURE_PREFIX)) {
    const id = value.slice(MEASURE_PREFIX.length);
    const measure = measures.find((m) => m.id === id);
    if (!measure) return;
    activeMeasure = measure;
    activeOverlay = await loadMeasureOverlay(id);
    for (const fips of allFips) {
      const county = activeOverlay[fips];
      map.setFeatureState(
        { source: "counties", id: fips },
        county && county.dissonance != null
          ? { has_data: true, dissonance: county.dissonance }
          : { has_data: false },
      );
    }
    map.setPaintProperty(
      "county-fills",
      "fill-color",
      fillColor(DISSONANCE_DEF) as mapboxgl.ExpressionSpecification,
    );
    renderMeasureLegend(measure);
    setYearControlsEnabled(false);
    scopeSelect.value = measure.scope;
    applyScope(); // filter + camera + status + (measure-aware) storyline
    return;
  }

  activeMeasure = null;
  activeOverlay = null;
  setYearControlsEnabled(true);
  const def = currentMetricDef();
  map.setPaintProperty(
    "county-fills",
    "fill-color",
    fillColor(def) as mapboxgl.ExpressionSpecification,
  );
  renderLegend(def);
  // Restore the year's metrics into feature-state (a measure overwrote it).
  await loadYear(YEARS[Number(slider.value)]!);
}

function renderStoryline(): void {
  if (activeMeasure && activeOverlay) {
    storyEl.textContent = measureStoryline(activeMeasure, activeOverlay);
    return;
  }
  const year = YEARS[Number(slider.value)]!;
  storyEl.textContent = storyline(currentMetricDef().key, year, scopedMetrics());
}

// Apply the active scope: show only its counties (Mapbox layer filter), point
// the camera at them, and recount the storyline. A scope is a DISPLAY lens —
// it filters and zooms, never recomputes the statistics (border counties keep
// their cross-state neighbors in the national math).
function applyScope(): void {
  const scope = currentScope();
  if (!scope || scope.kind === "nation") {
    map.setFilter("county-fills", null);
    map.setFilter("county-lines", null);
    map.fitBounds(US_BOUNDS, { padding: 20, duration: 700 });
  } else {
    const filter = ["in", ["get", "fips"], ["literal", scope.fips]] as never;
    map.setFilter("county-fills", filter);
    map.setFilter("county-lines", filter);
    map.fitBounds(boundsForScope(features, new Set(scope.fips)), {
      padding: 40,
      duration: 700,
    });
  }
  renderStatus();
  renderStoryline();
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
  renderStatus();
  renderStoryline();
}

// The status counts counties IN THE ACTIVE SCOPE, so it agrees with the map
// and the storyline (Kansas reads "105 counties", not the national 3,112).
function renderStatus(): void {
  const year = YEARS[Number(slider.value)]!;
  const counted = Object.keys(scopedMetrics()).length;
  status.textContent = `${counted.toLocaleString()} counties · ${year}`;
}

// The time-lapse: the spec's founding pitch is "current tools take a
// photograph; this engine shoots the video". The play button IS that video —
// for a campaign volunteer it replaces every statistic on this screen.
let playTimer: number | null = null;

function stopPlaying(): void {
  if (playTimer !== null) {
    window.clearInterval(playTimer);
    playTimer = null;
  }
  playButton.textContent = "▶ Play";
}

function startPlaying(): void {
  if (Number(slider.value) >= YEARS.length - 1) slider.value = "0";
  void loadYear(YEARS[Number(slider.value)]!);
  playButton.textContent = "⏸ Pause";
  playTimer = window.setInterval(() => {
    const next = Number(slider.value) + 1;
    if (next >= YEARS.length) {
      stopPlaying();
      return;
    }
    slider.value = String(next);
    void loadYear(YEARS[next]!);
  }, 1600);
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
  type FC = { features: CountyFeature[] };
  const [geojson, scopeCatalog, measureCatalog] = await Promise.all([
    fetchJson<FC>("data/counties.geojson"),
    fetchJson<Scope[]>("data/scopes.json"),
    fetchJson<Measure[]>("data/measures.json"),
  ]);
  features = geojson.features;
  allFips = features.map((f) => f.properties.fips);

  scopes = scopeCatalog;
  for (const scope of scopes) {
    const option = document.createElement("option");
    option.value = scope.id;
    option.textContent = scope.label;
    scopeSelect.appendChild(option);
  }

  // Ballot measures join the metric dropdown under their own group, valued
  // "measure:<id>" so the change handler can tell them from per-year metrics.
  measures = measureCatalog;
  if (measures.length > 0) {
    const group = document.createElement("optgroup");
    group.label = "Ballot measures";
    for (const measure of measures) {
      const option = document.createElement("option");
      option.value = `${MEASURE_PREFIX}${measure.id}`;
      option.textContent = measure.label;
      group.appendChild(option);
    }
    metricSelect.appendChild(group);
  }

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

  await applyView(); // initial view is the default metric (loads the year too)

  slider.addEventListener("input", () => {
    stopPlaying();
    void loadYear(YEARS[Number(slider.value)]!);
  });
  metricSelect.addEventListener("change", () => {
    void applyView();
  });
  scopeSelect.addEventListener("change", () => {
    stopPlaying();
    applyScope();
  });
  playButton.addEventListener("click", () => {
    if (playTimer !== null) {
      stopPlaying();
    } else {
      startPlaying();
    }
  });

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
