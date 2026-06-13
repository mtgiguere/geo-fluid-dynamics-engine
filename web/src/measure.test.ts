import { describe, expect, it } from "vitest";
import { fillColor } from "./metrics";
import { DISSONANCE_DEF, measureCaption, measureStoryline } from "./measure";
import type { Measure, MeasureOverlay } from "./measure";

const KS: Measure = {
  id: "ks_abortion_2022",
  label: "Kansas: Abortion rights (Aug 2022)",
  scope: "20",
  baseline_year: 2020,
  issue_label: "pro-choice",
};

// Three counties: two leaned more pro-choice than their Democratic vote
// (dissonance > 0), one did not; one county has no baseline (null).
const OVERLAY: MeasureOverlay = {
  "20073": { no_share: 0.5, partisan_share: 0.19, dissonance: 0.31 },
  "20091": { no_share: 0.65, partisan_share: 0.62, dissonance: 0.03 },
  "20109": { no_share: 0.21, partisan_share: 0.25, dissonance: -0.04 },
  "20999": { no_share: 0.4, partisan_share: null, dissonance: null },
};

describe("measureStoryline", () => {
  it("counts counties that leaned more toward the issue than their party — a comparison, not a majority", () => {
    // 2 of the 3 counties with a baseline have dissonance > 0; the null one
    // is excluded from the denominator. The phrasing is comparative ("more
    // ... than they voted Democratic"), never "voted pro-choice" — a county
    // can lean more pro-choice than its party while still voting majority-no.
    expect(measureStoryline(KS, OVERLAY)).toBe(
      "Kansas: Abortion rights (Aug 2022) — 2 of 3 counties leaned more pro-choice than they voted Democratic in 2020.",
    );
  });
});

describe("measureCaption", () => {
  it("explains the comparison and that the year slider does not apply", () => {
    expect(measureCaption(KS)).toBe(
      'Blue = leaned more pro-choice than its 2020 Democratic vote (a "False Bastion"). Single measure — the year slider does not apply.',
    );
  });
});

describe("dissonance coloring", () => {
  it("colors only counties with a numeric dissonance; the rest stay gray", () => {
    // Counties outside the measure's state have no dissonance in feature-state
    // and must render the neutral gray, never a misleading ramp color.
    const expr = fillColor(DISSONANCE_DEF) as unknown[];
    expect(expr[0]).toBe("case");
    expect(expr[1]).toEqual([
      "all",
      ["==", ["feature-state", "has_data"], true],
      ["==", ["typeof", ["feature-state", "dissonance"]], "number"],
    ]);
    expect(expr[3]).toBe("#d4d4d4");
  });
});
