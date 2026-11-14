// The wave player's frame logic: pure functions, loaded by public/waves.html
// as a module and unit-tested in src/waves.test.ts. Each county ships as one
// string, one character per frame (geofluid.map.waves): "0"-"9" = 0-90% of
// the county's own final total so far, "A" = all of it.
export function levelAt(series, frame) {
  return parseInt(series[frame], 16);
}

// Nothing yet -> all of it, one hue, evenly by channel: a county darkens as
// the idea fills it in.
export const EMPTY = "#ece8df";
export const FULL = "#0b5563";
const rgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));

export function levelColor(level) {
  const t = level / 10;
  const [a, b] = [rgb(EMPTY), rgb(FULL)];
  return "#" + a.map((v, i) => Math.round(v + (b[i] - v) * t).toString(16).padStart(2, "0")).join("");
}

// The wave front: the frame a county crosses the topic's mark (the take-off
// rule; mark 5 = 50% of its own final total). Flashed on the page, so the
// moving edge shows. Each topic picks the mark where its story is: a
// candidate's base catches on at 20%; at 50% it lands on debate weeks.
export function isFront(series, frame, mark) {
  const before = frame === 0 ? 0 : levelAt(series, frame - 1);
  return levelAt(series, frame) >= mark && before < mark;
}

// Per frame, the share of counties at or past the mark. A wave draws an
// S-curve over months; a broadcast draws a cliff on one day.
export function markCurve(seriesList, mark) {
  const frames = seriesList.length ? seriesList[0].length : 0;
  return Array.from(
    { length: frames },
    (_, f) => seriesList.filter((s) => levelAt(s, f) >= mark).length / seriesList.length,
  );
}
