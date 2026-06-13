// Ballot-measure overlays: dissonance between a county's issue vote and its
// partisan identity. A separate data family from the per-year metrics (a
// measure is a single point in time), so it gets its own module. The pure
// helpers here are Vitest-tested; main.ts wires them to Mapbox.

import type { MetricDef } from "./metrics";

export interface Measure {
  id: string;
  label: string;
  scope: string; // the state FIPS prefix this measure covers
  baseline_year: number; // the presidential election dissonance compares against
  issue_label: string; // the issue side, as a comparative noun ("pro-choice")
}

// The map colors a measure by dissonance on the partisan diverging ramp,
// centered at 0: negative (issue trailed the party) toward red, positive
// (ran ahead — a False Bastion) toward blue. Reuses the metrics ramp
// machinery (fillColor / legendModel) via the shared MetricDef shape.
export const DISSONANCE_DEF: MetricDef = {
  kind: "ramp",
  key: "dissonance",
  label: "Dissonance (issue vs party)",
  stops: [-0.3, -0.15, 0, 0.15, 0.3],
  colors: ["#b2182b", "#ef8a62", "#f7f7f7", "#67a9cf", "#2166ac"],
  legendLeft: "Trailed its party",
  legendRight: "Ran ahead (False Bastion)",
};

export interface MeasureCounty {
  no_share: number;
  partisan_share: number | null;
  dissonance: number | null;
}

export type MeasureOverlay = Record<string, MeasureCounty>;

// The plain-language sentence. Phrasing is COMPARATIVE on purpose: dissonance
// > 0 means a county leaned more toward the issue than it voted Democratic —
// NOT that it voted majority that way (a county can lean more pro-choice than
// its party while still voting majority-no). Conflating the two is exactly
// the Chicago misreading the contract warns about.
export function measureStoryline(measure: Measure, overlay: MeasureOverlay): string {
  const withBaseline = Object.values(overlay).filter((c) => c.dissonance != null);
  const ahead = withBaseline.filter((c) => (c.dissonance as number) > 0).length;
  return (
    `${measure.label} — ${ahead} of ${withBaseline.length} counties leaned more ` +
    `${measure.issue_label} than they voted Democratic in ${measure.baseline_year}.`
  );
}

export function measureCaption(measure: Measure): string {
  return (
    `Blue = leaned more ${measure.issue_label} than its ${measure.baseline_year} ` +
    `Democratic vote (a "False Bastion"). Single measure — the year slider does not apply.`
  );
}
