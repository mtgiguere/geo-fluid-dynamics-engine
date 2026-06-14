// Contract tests for the pure map-styling logic. These exist because the
// frontend crossed the line drawn in TDD_CONTRACT.md ("The Frontend Line"):
// once UI code accumulates real logic — color expression builders, legend
// models, categorical metrics — that logic gets unit tests like any other.
// E2E golden paths verify integration; THESE verify the logic.

import { describe, expect, it } from "vitest";
import { METRIC_DEFS, fillColor, legendModel, storyline } from "./metrics";
import type { Metrics } from "./metrics";

const result = METRIC_DEFS.find((d) => d.key === "dem_share_2p")!;
const anchors = METRIC_DEFS.find((d) => d.key === "swing_lisa_quadrant")!;

describe("fillColor for ramp metrics", () => {
  it("guards on has_data and numeric value, then interpolates stops to colors", () => {
    const expr = fillColor(result) as unknown[];

    expect(expr[0]).toBe("case");
    expect(expr[1]).toEqual([
      "all",
      ["==", ["feature-state", "has_data"], true],
      ["==", ["typeof", ["feature-state", "dem_share_2p"]], "number"],
    ]);
    const interpolate = expr[2] as unknown[];
    expect(interpolate.slice(0, 2)).toEqual(["interpolate", ["linear"]]);
    // stops and colors interleave pairwise after the input expression
    expect(interpolate.slice(3)).toEqual([
      0.2, "#b2182b", 0.35, "#ef8a62", 0.5, "#f7f7f7", 0.65, "#67a9cf", 0.8, "#2166ac",
    ]);
    expect(expr[3]).toBe("#d4d4d4"); // everything else: neutral gray
  });
});

describe("fillColor for categorical metrics (wave anchors)", () => {
  it("matches each quadrant to its color with gray fallback", () => {
    const expr = fillColor(anchors) as unknown[];

    expect(expr[0]).toBe("case");
    expect(expr[1]).toEqual([
      "all",
      ["==", ["feature-state", "has_data"], true],
      ["==", ["typeof", ["feature-state", "swing_lisa_quadrant"]], "string"],
    ]);
    const match = expr[2] as unknown[];
    expect(match[0]).toBe("match");
    expect(match[1]).toEqual(["feature-state", "swing_lisa_quadrant"]);
    // category/color pairs, then the in-match fallback
    expect(match.slice(2)).toEqual([
      "high-high", "#2166ac",
      "low-low", "#b2182b",
      "high-low", "#92c5de",
      "low-high", "#f4a582",
      "#d4d4d4",
    ]);
    expect(expr[3]).toBe("#d4d4d4");
  });
});

// A tiny county dataset for storyline tests: values chosen by hand so every
// count below is checkable on fingers.
function county(over: Partial<Metrics>): Metrics {
  return {
    dem_votes: 0,
    rep_votes: 0,
    other_votes: 0,
    total_votes: 0,
    dem_share_2p: 0.5,
    swing_dem_2p: null,
    swing_lisa_quadrant: null,
    acs_vintage: 2023,
    total_population: 0,
    median_age: null,
    pct_65_plus: null,
    median_hh_income: null,
    median_home_value: null,
    pct_owner_occupied: null,
    pct_bachelors_plus: null,
    ...over,
  };
}

describe("storyline — the plain-language sentence for campaign volunteers", () => {
  const data = {
    a: county({ dem_share_2p: 0.7, swing_dem_2p: -0.03, swing_lisa_quadrant: "low-low" }),
    b: county({ dem_share_2p: 0.4, swing_dem_2p: -0.01, swing_lisa_quadrant: "low-low" }),
    c: county({ dem_share_2p: 0.45, swing_dem_2p: 0.02, swing_lisa_quadrant: "high-high" }),
    d: county({ dem_share_2p: 0.55, swing_dem_2p: null, swing_lisa_quadrant: null }),
  };

  it("result view counts who won where", () => {
    expect(storyline("dem_share_2p", 2024, data)).toBe(
      "2024: Republicans got more votes in 2 counties, Democrats in 2. Click any county for details.",
    );
  });

  it("swing view counts movement vs the previous election", () => {
    expect(storyline("swing_dem_2p", 2024, data)).toBe(
      "2024: since the last election, 2 counties moved toward Republicans and 1 toward Democrats.",
    );
  });

  it("wave view counts counties moving together", () => {
    expect(storyline("swing_lisa_quadrant", 2024, data)).toBe(
      "2024: the wave — 2 counties moved toward Republicans TOGETHER with their neighbors, 1 toward Democrats.",
    );
  });

  it("the first election in the data explains why change cannot show yet", () => {
    const none = { a: county({}), b: county({}) };
    expect(storyline("swing_dem_2p", 2000, none)).toBe(
      "2000: the first election in our data — nothing earlier to compare against yet.",
    );
  });

  it("demographic views state what is colored and its vintage", () => {
    expect(storyline("median_age", 2024, data)).toBe(
      "Counties colored by median age (Census ACS 2023). This does not change with the election year.",
    );
  });
});

describe("legendModel", () => {
  it("ramp metrics produce end labels, a gradient, and a plain-language caption", () => {
    const legend = legendModel(result);

    expect(legend).toEqual({
      kind: "ramp",
      left: "More Republican",
      right: "More Democratic",
      gradientCss:
        "linear-gradient(to right, #b2182b, #ef8a62, #f7f7f7, #67a9cf, #2166ac)",
      caption:
        "Which party won each county's presidential vote. Darker = bigger margin. Gray = no county-level data.",
    });
  });

  it("every view carries a non-empty caption — the explainer key", () => {
    // The "before any outside user" rule: no view may ship without a
    // plain-language line saying what it shows and what gray means. A ramp
    // metric with only color labels (the pre-explainer state) would fail here.
    for (const def of METRIC_DEFS) {
      expect(legendModel(def).caption.length).toBeGreaterThan(10);
    }
  });

  it("categorical metrics produce labeled chips and a plain-language caption", () => {
    // The caption exists because a real user (the project owner) read the
    // wave-anchors red over Chicago as "Chicago is Republican". The layer
    // shows clusters of CHANGE, not lean — and the map must say so itself.
    const legend = legendModel(anchors);

    expect(legend).toEqual({
      kind: "categories",
      caption:
        "Clusters of change vs the previous election — not partisan lean. Gray: no significant cluster.",
      items: [
        { label: "Swung D together", color: "#2166ac" },
        { label: "Swung R together", color: "#b2182b" },
        { label: "Swung D, neighbors R", color: "#92c5de" },
        { label: "Swung R, neighbors D", color: "#f4a582" },
      ],
    });
  });
});
