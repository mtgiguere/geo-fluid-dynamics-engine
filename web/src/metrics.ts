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

interface RampMetric {
  kind: "ramp";
  key: keyof Metrics;
  label: string;
  stops: number[];
  colors: string[];
  legendLeft: string;
  legendRight: string;
}

interface CategoricalMetric {
  kind: "categories";
  key: keyof Metrics;
  label: string;
  categories: { value: string; label: string; color: string }[];
}

export type MetricDef = RampMetric | CategoricalMetric;

export const METRIC_DEFS: MetricDef[] = [
  {
    kind: "ramp",
    key: "dem_share_2p",
    label: "Two-party result",
    stops: [0.2, 0.35, 0.5, 0.65, 0.8],
    colors: PARTISAN_RAMP,
    legendLeft: "More Republican",
    legendRight: "More Democratic",
  },
  {
    kind: "ramp",
    key: "swing_dem_2p",
    label: "Swing since last election",
    stops: [-0.15, -0.075, 0, 0.075, 0.15],
    colors: PARTISAN_RAMP,
    legendLeft: "Swung Republican",
    legendRight: "Swung Democratic",
  },
  {
    // The wave-anchor layer: LISA quadrants of swing. high-high = a county
    // swinging D inside a D-swinging neighborhood (a wave core); low-low =
    // the R mirror; the off-diagonal quadrants are counties defying their
    // region. Computed per election by geofluid.spatial.moran.
    kind: "categories",
    key: "swing_lisa_quadrant",
    label: "Wave anchors (swing clusters)",
    categories: [
      { value: "high-high", label: "D-swing core", color: "#2166ac" },
      { value: "low-low", label: "R-swing core", color: "#b2182b" },
      { value: "high-low", label: "D outlier", color: "#92c5de" },
      { value: "low-high", label: "R outlier", color: "#f4a582" },
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
  },
  {
    kind: "ramp",
    key: "pct_65_plus",
    label: "Share 65 and over",
    stops: [0.1, 0.16, 0.22, 0.28, 0.34],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "Fewer seniors",
    legendRight: "More seniors",
  },
  {
    kind: "ramp",
    key: "median_hh_income",
    label: "Median household income",
    stops: [40_000, 60_000, 80_000, 100_000, 120_000],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "$40k",
    legendRight: "$120k+",
  },
  {
    kind: "ramp",
    key: "median_home_value",
    label: "Median home value",
    stops: [80_000, 190_000, 300_000, 410_000, 520_000],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "$80k",
    legendRight: "$520k+",
  },
  {
    kind: "ramp",
    key: "pct_owner_occupied",
    label: "Owner-occupied share",
    stops: [0.5, 0.6, 0.7, 0.8, 0.9],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "More renters",
    legendRight: "More owners",
  },
  {
    kind: "ramp",
    key: "pct_bachelors_plus",
    label: "Bachelor's or higher",
    stops: [0.1, 0.2, 0.3, 0.4, 0.5],
    colors: SEQUENTIAL_RAMP,
    legendLeft: "Less college",
    legendRight: "More college",
  },
];

const NO_VALUE_GRAY = "#d4d4d4";

// A county colors only when it has data AND the selected metric carries an
// actual value for it (swing is null in 2000; quadrants are absent for
// excluded counties; a few ACS medians are null). Gray always means
// "no value here" — same as policy-excluded geographies.
function guarded(key: keyof Metrics, valueType: "number" | "string", painted: unknown): unknown[] {
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

export type LegendModel =
  | { kind: "ramp"; left: string; right: string; gradientCss: string }
  | { kind: "categories"; items: { label: string; color: string }[] };

export function legendModel(def: MetricDef): LegendModel {
  if (def.kind === "ramp") {
    return {
      kind: "ramp",
      left: def.legendLeft,
      right: def.legendRight,
      gradientCss: `linear-gradient(to right, ${def.colors.join(", ")})`,
    };
  }
  return {
    kind: "categories",
    items: def.categories.map(({ label, color }) => ({ label, color })),
  };
}
