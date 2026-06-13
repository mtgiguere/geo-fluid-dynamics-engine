// Geographic scope on the frontend: filtering the national map to "my area".
// A scope is a set of county FIPS (loaded from scopes.json). The pure helpers
// here — used by main.ts to filter, fit the camera, and recount the storyline
// — are unit-tested; the Mapbox wiring itself is covered by the E2E suite.

export interface Scope {
  id: string;
  label: string;
  kind: "nation" | "state" | "metro";
  fips: string[];
}

export interface CountyFeature {
  properties: { fips: string };
  geometry: { type: "Polygon" | "MultiPolygon"; coordinates: unknown };
}

type Bounds = [[number, number], [number, number]];

// Recursively collect [lng, lat] pairs from nested GeoJSON coordinate arrays,
// so the same walk handles Polygon (rings) and MultiPolygon (arrays of rings).
function eachPoint(coords: unknown, fn: (lng: number, lat: number) => void): void {
  if (
    Array.isArray(coords) &&
    coords.length >= 2 &&
    typeof coords[0] === "number" &&
    typeof coords[1] === "number"
  ) {
    fn(coords[0], coords[1]);
    return;
  }
  if (Array.isArray(coords)) {
    for (const part of coords) eachPoint(part, fn);
  }
}

// The bounding box of the counties in scope, [[west, south], [east, north]].
// Out-of-scope features are ignored; an empty scope throws rather than
// returning a degenerate box that would aim the camera at nothing.
export function boundsForScope(features: CountyFeature[], fips: Set<string>): Bounds {
  let west = Infinity;
  let south = Infinity;
  let east = -Infinity;
  let north = -Infinity;
  for (const feature of features) {
    if (!fips.has(feature.properties.fips)) continue;
    eachPoint(feature.geometry.coordinates, (lng, lat) => {
      west = Math.min(west, lng);
      south = Math.min(south, lat);
      east = Math.max(east, lng);
      north = Math.max(north, lat);
    });
  }
  if (west === Infinity) {
    throw new Error("boundsForScope: no counties in scope");
  }
  return [
    [west, south],
    [east, north],
  ];
}
