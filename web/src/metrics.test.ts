// Contract tests for the pure map-styling logic. These exist because the
// frontend crossed the line drawn in TDD_CONTRACT.md ("The Frontend Line"):
// once UI code accumulates real logic — color expression builders, legend
// models, categorical metrics — that logic gets unit tests like any other.
// E2E golden paths verify integration; THESE verify the logic.

import { describe, expect, it } from "vitest";
import { METRIC_DEFS, fillColor, legendModel } from "./metrics";

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

describe("legendModel", () => {
  it("ramp metrics produce end labels and a CSS gradient", () => {
    const legend = legendModel(result);

    expect(legend).toEqual({
      kind: "ramp",
      left: "More Republican",
      right: "More Democratic",
      gradientCss:
        "linear-gradient(to right, #b2182b, #ef8a62, #f7f7f7, #67a9cf, #2166ac)",
    });
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
