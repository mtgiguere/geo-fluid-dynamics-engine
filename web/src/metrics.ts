// The metric registry and the pure styling logic the map is driven by.
// Everything here is contract-tested in metrics.test.ts (the frontend's
// Vitest line, per TDD_CONTRACT.md); main.ts only wires results to Mapbox.

export type Metrics = {
  dem_votes: number;
  rep_votes: number;
  other_votes: number;
  total_votes: number;
  dem_share_2p: number;
  swing_dem_2p: number | null;
  swing_lisa_quadrant: string | null;
  acs_vintage: number;
  total_population: number;
  median_age: number | null;
  pct_65_plus: number | null;
  median_hh_income: number | null;
  median_home_value: number | null;
  pct_owner_occupied: number | null;
  pct_bachelors_plus: number | null;
};

// Partisan quantities use the red-blue diverging ramp. Demographics use a
// viridis-style sequential ramp on purpose — coloring income or age in
// red/blue would invite readers to see partisanship where there is none.
const PARTISAN_RAMP = ["#b2182b", "#ef8a62", "#f7f7f7", "#67a9cf", "#2166ac"];
const SEQUENTIAL_RAMP = ["#440154", "#3b528b", "#21918c", "#5ec962", "#fde725"];

// `key` is the feature-state field the layer colors by. It is a string, not
// `keyof Metrics`, because measure overlays (dissonance) add fields outside
// the per-year Metrics shape; feature-state is dynamic at the Mapbox layer.
interface RampMetric {
  kind: "ramp";
  key: string;
  label: string;
  stops: number[];
  colors: string[];
  legendLeft: string;
  legendRight: string;
  // The explainer line, always shown: what this view answers and what gray
  // means. Required on every view (the "map must explain itself" rule) so a
  // first-time volunteer is never left guessing what a color stands for.
  caption: string;
}

interface CategoricalMetric {
  kind: "categories";
  key: string;
  label: string;
  // Plain-language explanation rendered with the legend. Exists because a
  // real user read wave-anchor red over Chicago as "Chicago votes R" —
  // the layer shows clusters of CHANGE, and intuition will not supply that
  // distinction on its own. The map must explain itself.
  caption: string;
  categories: { value: string; label: string; color: string }[];
}

export type MetricDef = RampMetric | CategoricalMetric;

export const METRIC_DEFS: MetricDef[] = [
  {
    kind: "ramp",
    key: "dem_share_2p",
    label: "Who won",
    stops: [0.2, 0.35, 0.5, 0.65, 0.8],
    colors: PARTISAN_RAMP,
    legendLeft: "More Republican",
    legendRight: "More Democratic",
    caption:
      "Which party won each county's presidential vote. Darker = bigger margin. Gray = no county-level data.",
  },
  {
    kind: "ramp",
    key: "swing_dem_2p",
    label: "Who gained ground",
    stops: [-0.15, -0.075, 0, 0.075, 0.15],
    colors: PARTISAN_RAMP,
    legendLeft: "Swung Republican",
    legendRight: "Swung Democratic",
    caption:
      "Which way each county moved since the last election — not who won. Gray = no comparison yet (first election or no data).",
  },
  {
    // The wave-anchor layer: LISA quadrants of swing. high-high = a county
    // swinging D inside a D-swinging neighborhood (a wave core); low-low =
    // the R mirror; the off-diagonal quadrants are counties defying their
    // region. Computed per election by geofluid.spatial.moran.
    kind: "categories",
    key: "swing_lisa_quadrant",
    label: "The wave — change spreading together",
    caption:
      "Clusters of change vs the previous election — not partisan lean. Gray: no significant cluster.",
    categories: [
      { value: "high-high", label: "Swung D together", color: "#2166ac" },
      { value: "low-low", label: "Swung R together", color: "#b2182b" },
      { value: "high-low", label: "Swung D, neighbors R", color: "#92c5de" },
      { value: "low-high", label: "Swung R, neighbors D", color: "#f4a582" },
    ],
  },
  {
    kind: "ramp",
    key: "median_age",
    label: "Median age",
    stops: [30, 37, 44, 51, 58],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "Younger",
    legendRight: "Older",
    caption: "Median resident age (Census ACS). Gray = no data. Does not change with the year.",
  },
  {
    kind: "ramp",
    key: "pct_65_plus",
    label: "Share 65 and over",
    stops: [0.1, 0.16, 0.22, 0.28, 0.34],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "Fewer seniors",
    legendRight: "More seniors",
    caption: "Share of residents 65 and older (Census ACS). Gray = no data.",
  },
  {
    kind: "ramp",
    key: "median_hh_income",
    label: "Median household income",
    stops: [40_000, 60_000, 80_000, 100_000, 120_000],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "$40k",
    legendRight: "$120k+",
    caption: "Median household income (Census ACS). Gray = no data.",
  },
  {
    kind: "ramp",
    key: "median_home_value",
    label: "Median home value",
    stops: [80_000, 190_000, 300_000, 410_000, 520_000],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "$80k",
    legendRight: "$520k+",
    caption: "Median home value (Census ACS). Gray = no data.",
  },
  {
    kind: "ramp",
    key: "pct_owner_occupied",
    label: "Owner-occupied share",
    stops: [0.5, 0.6, 0.7, 0.8, 0.9],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "More renters",
    legendRight: "More owners",
    caption: "Share of homes lived in by their owner (Census ACS). Gray = no data.",
  },
  {
    kind: "ramp",
    key: "pct_bachelors_plus",
    label: "Bachelor's or higher",
    stops: [0.1, 0.2, 0.3, 0.4, 0.5],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "Less college",
    legendRight: "More college",
    caption: "Share of adults 25+ with a bachelor's degree or higher (Census ACS). Gray = no data.",
  },
];

const NO_VALUE_GRAY = "#d4d4d4";

// A county colors only when it has data AND the selected metric carries an
// actual value for it (swing is null in 2000; quadrants are absent for
// excluded counties; a few ACS medians are null). Gray always means
// "no value here" — same as policy-excluded geographies.
function guarded(key: string, valueType: "number" | "string", painted: unknown): unknown[] {
  return [
    "case",
    [
      "all",
      ["==", ["feature-state", "has_data"], true],
      ["==", ["typeof", ["feature-state", key]], valueType],
    ],
    painted,
    NO_VALUE_GRAY,
  ];
}

export function fillColor(def: MetricDef): unknown[] {
  if (def.kind === "ramp") {
    const interpolate: unknown[] = [
      "interpolate",
      ["linear"],
      ["to-number", ["feature-state", def.key]],
    ];
    def.stops.forEach((stop, i) => interpolate.push(stop, def.colors[i]));
    return guarded(def.key, "number", interpolate);
  }
  const match: unknown[] = ["match", ["feature-state", def.key]];
  for (const category of def.categories) {
    match.push(category.value, category.color);
  }
  match.push(NO_VALUE_GRAY);
  return guarded(def.key, "string", match);
}

// ---------------------------------------------------------------------------
// The storyline: one plain sentence narrating what the screen shows, computed
// live from the loaded data. Our median user is a campaign volunteer — a
// retiree, a student, a barista — not a statistician. The sentence carries
// the entire interpretation so the colors never have to.
// ---------------------------------------------------------------------------
export function storyline(key: string, year: number, data: Record<string, Metrics>): string {
  const counties = Object.values(data);
  if (key === "dem_share_2p") {
    const rep = counties.filter((c) => c.dem_share_2p < 0.5).length;
    const dem = counties.filter((c) => c.dem_share_2p > 0.5).length;
    return `${year}: Republicans got more votes in ${rep.toLocaleString()} counties, Democrats in ${dem.toLocaleString()}. Click any county for details.`;
  }
  if (key === "swing_dem_2p" || key === "swing_lisa_quadrant") {
    const swings = counties.map((c) => c.swing_dem_2p).filter((s): s is number => s != null);
    if (swings.length === 0) {
      return `${year}: the first election in our data — nothing earlier to compare against yet.`;
    }
    if (key === "swing_dem_2p") {
      const towardR = swings.filter((s) => s < 0).length;
      const towardD = swings.filter((s) => s > 0).length;
      return `${year}: since the last election, ${towardR.toLocaleString()} counties moved toward Republicans and ${towardD.toLocaleString()} toward Democrats.`;
    }
    const repCores = counties.filter((c) => c.swing_lisa_quadrant === "low-low").length;
    const demCores = counties.filter((c) => c.swing_lisa_quadrant === "high-high").length;
    return `${year}: the wave — ${repCores.toLocaleString()} counties moved toward Republicans TOGETHER with their neighbors, ${demCores.toLocaleString()} toward Democrats.`;
  }
  const def = METRIC_DEFS.find((d) => d.key === key);
  const vintage = counties[0]?.acs_vintage ?? 2023;
  return `Counties colored by ${def ? def.label.toLowerCase() : String(key)} (Census ACS ${vintage}). This does not change with the election year.`;
}

export type LegendModel =
  | { kind: "ramp"; left: string; right: string; gradientCss: string; caption: string }
  | { kind: "categories"; caption: string; items: { label: string; color: string }[] };

export function legendModel(def: MetricDef): LegendModel {
  if (def.kind === "ramp") {
    return {
      kind: "ramp",
      left: def.legendLeft,
      right: def.legendRight,
      gradientCss: `linear-gradient(to right, ${def.colors.join(", ")})`,
      caption: def.caption,
    };
  }
  return {
    kind: "categories",
    caption: def.caption,
    items: def.categories.map(({ label, color }) => ({ label, color })),
  };
}
