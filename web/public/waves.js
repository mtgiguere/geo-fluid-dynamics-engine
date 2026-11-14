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

const lerp = (from, to, t) => {
  const [a, b] = [rgb(from), rgb(to)];
  return "#" + a.map((v, i) => Math.round(v + (b[i] - v) * t).toString(16).padStart(2, "0")).join("");
};

export function levelColor(level) {
  return lerp(EMPTY, FULL, level / 10);
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

// Zoom to a state: the box around its counties' boxes, padded by `pad` of
// its width and height on each side (becomes the map's viewBox).
export function zoomBox(boxes, pad) {
  const x0 = Math.min(...boxes.map((b) => b.x)), y0 = Math.min(...boxes.map((b) => b.y));
  const x1 = Math.max(...boxes.map((b) => b.x + b.width)), y1 = Math.max(...boxes.map((b) => b.y + b.height));
  const w = x1 - x0, h = y1 - y0;
  return { x: x0 - pad * w, y: y0 - pad * h, width: w * (1 + 2 * pad), height: h * (1 + 2 * pad) };
}

// The honest yardstick for the arrows (geofluid.map.waves.chance_handoffs):
// by `frame`, how many in-state hand-offs were drawn into counties in view,
// against how many chance alone would draw (the state's timings shuffled).
// A cross-border arrow is drawn but not counted: chance shuffles within a state.
export function tally(topic, frame, inView) {
  let real = 0, chance = 0;
  for (const [a, b, f] of topic.handoffs) {
    if (f <= frame && a.slice(0, 2) === b.slice(0, 2) && inView(b)) real++;
  }
  for (const [fips, v] of Object.entries(topic.chance)) {
    const s = topic.series[fips];
    if (s && inView(fips) && levelAt(s, frame) >= topic.mark) chance += v;
  }
  return { real, chance };
}

// Milliseconds per frame. At 1x a whole run takes about 9 s (16 s zoomed in to
// a state, where there is more to follow), kept within 60-250 ms a frame (450
// zoomed); `speed` then scales it: 0.5 = half speed, twice as long a frame.
export function frameDelay(frames, zoomed, speed) {
  const ms = Math.max(60, Math.min(zoomed ? 450 : 250, (zoomed ? 16000 : 9000) / frames));
  return ms / speed;
}

// The arrival map's input: the frame a county first reaches the mark, or
// null if it never does.
export function crossFrame(series, mark) {
  for (let f = 0; f < series.length; f++) if (levelAt(series, f) >= mark) return f;
  return null;
}

// The arrival map: one still picture, each county coloured by WHEN it reached
// the mark, from the earliest arrival in view (dark) to the latest (pale).
// Order is easier to read in a still map than in an animation of flashes.
export const EARLY = "#24135f";
export const MID = "#c4407a";
export const LATE = "#f6e3a1";

export function arrivalColor(frame, lo, hi) {
  const t = hi > lo ? (frame - lo) / (hi - lo) : 0;
  return t <= 0.5 ? lerp(EARLY, MID, t * 2) : lerp(MID, LATE, (t - 0.5) * 2);
}
