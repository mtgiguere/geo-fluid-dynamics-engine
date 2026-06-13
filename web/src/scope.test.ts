import { describe, expect, it } from "vitest";
import { boundsForScope } from "./scope";
import type { CountyFeature } from "./scope";

// Two St. Louis-area counties plus a far-away Los Angeles county. A scope of
// the two STL counties must produce a bbox over only them — the LA county is
// ignored, the way a scoped view ignores everything outside the area.
const FEATURES: CountyFeature[] = [
  {
    properties: { fips: "29510" },
    geometry: {
      type: "Polygon",
      coordinates: [[[-90.3, 38.5], [-90.1, 38.7], [-90.2, 38.6], [-90.3, 38.5]]],
    },
  },
  {
    properties: { fips: "17119" }, // Madison IL, across the river
    geometry: {
      type: "MultiPolygon",
      coordinates: [[[[-90.0, 38.8], [-89.8, 39.0], [-90.0, 38.8]]]],
    },
  },
  {
    properties: { fips: "06037" }, // Los Angeles — out of scope
    geometry: {
      type: "Polygon",
      coordinates: [[[-118.0, 34.0], [-117.0, 35.0], [-118.0, 34.0]]],
    },
  },
];

describe("boundsForScope", () => {
  it("bounds the scoped counties only, across Polygon and MultiPolygon", () => {
    const bounds = boundsForScope(FEATURES, new Set(["29510", "17119"]));

    // west/south = mins, east/north = maxes over the two STL features only.
    expect(bounds).toEqual([
      [-90.3, 38.5],
      [-89.8, 39.0],
    ]);
  });

  it("throws when no feature is in scope, rather than returning an empty box", () => {
    // A silent empty/invalid box would point the camera at the ocean; fail loud.
    expect(() => boundsForScope(FEATURES, new Set(["99999"]))).toThrow(/no counties/i);
  });
});
