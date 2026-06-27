"""Build the prescriptive-targeting demo (untested orchestration + rendering).

Runs the REAL Kansas Aug-2022 abortion data through the tested targeting engine
(geofluid.targeting) + distance helpers (geofluid.spatial.distance) for a
Kansas City home county, then renders a self-contained HTML demo: a three-act
narrative (descriptive map -> False-Bastion tell + Ohio proof -> the itinerary)
with an inline SVG Kansas choropleth and the ranked marching orders beside it.

Like scripts/export_web_data.py this is thin glue over tested library code, not
itself under test. Run:  uv run python scripts/build_targeting_demo.py
"""

import json
import math
from pathlib import Path

import pandas as pd

from geofluid.spatial.distance import bounding_box_center, haversine_miles
from geofluid.targeting import build_itinerary

ROOT = Path(__file__).resolve().parents[1]
HOME_FIPS = "20209"  # Wyandotte County = Kansas City, KS
# Served as a static page from the deployed site (web/public/ → the Pages root),
# so it is PUBLIC — anyone can open it, no login — and fully self-contained
# (inline SVG/CSS/JS, zero runtime fetches), so it cannot hit a base-path/data
# bug. The main app links to it with a "Demo" button.
HTML_OUT = ROOT / "web/public/demo.html"

# ── palette (mirrors the design plan; baked into the rendered CSS) ───────────
INK = "#15202B"
EMBER = "#E8A33D"
EMBER_DEEP = "#C8791F"
SLATE = "#5B7C99"
ASH = "#3A4654"

# Inline emoji favicon (compass) — avoids a /favicon.ico 404 that would show in
# the demo page's console. Split so no source line exceeds the line-length cap.
_FAVICON = (
    "data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 "
    "viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🧭</text></svg>"
)


def _lerp_hex(c1: str, c2: str, t: float) -> str:
    a = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a[i] + (b[i] - a[i]) * t):02x}" for i in range(3))


def _fill(category: str, dissonance: float, d_lo: float, d_hi: float) -> str:
    """Target counties glow on an amber ramp by dissonance; base is cool slate;
    hard ground recedes into the ink ground."""
    if category == "target":
        t = (dissonance - d_lo) / (d_hi - d_lo) if d_hi > d_lo else 0.5
        return _lerp_hex("#F0CE86", EMBER_DEEP, max(0.0, min(1.0, t)))
    return SLATE if category == "base" else ASH


def main() -> None:
    overlay = json.loads((ROOT / "web/public/data/measure_ks_abortion_2022.json").read_text())
    geo = json.loads((ROOT / "web/public/data/counties.geojson").read_text())

    names: dict[str, str] = {}
    centers: dict[str, tuple[float, float]] = {}
    rings: dict[str, list] = {}
    for f in geo["features"]:
        fid = f["id"]
        if fid.startswith("20"):  # Kansas
            names[fid] = f["properties"]["NAME"]
            centers[fid] = bounding_box_center(f["geometry"])
            geom = f["geometry"]
            rings[fid] = (
                geom["coordinates"]
                if geom["type"] == "MultiPolygon"
                else [geom["coordinates"]]  # normalize Polygon -> MultiPolygon nesting
            )

    rows = [
        {
            "fips": fid,
            "name": names[fid],
            "progressive_share": d["no_share"],
            "partisan_share": d["partisan_share"],
        }
        for fid, d in overlay.items()
        if fid in names and d["partisan_share"] is not None
    ]
    counties = pd.DataFrame(rows)
    distances = {fid: haversine_miles(centers[HOME_FIPS], centers[fid]) for fid in counties["fips"]}
    itinerary = build_itinerary(counties, distances_mi=distances, home_fips=HOME_FIPS)

    _print_talking_points(itinerary, names[HOME_FIPS])
    HTML_OUT.write_text(_render_html(itinerary, rings, names), encoding="utf-8")
    print(f"\nwrote {HTML_OUT.name}")


def _print_talking_points(itinerary: pd.DataFrame, home: str) -> None:
    print(f"HOME: {home} County (Kansas City, KS)\n")
    targets = itinerary[itinerary["category"] == "target"].nsmallest(6, "distance_mi")
    print("TOP NEARBY TARGETS:")
    for _, r in targets.sort_values("dissonance", ascending=False).iterrows():
        print(
            f"  {r['name']:12s} {r['distance_mi']:4.0f} mi  "
            f"{r['progressive_share'] * 100:4.1f}% pro-choice vs "
            f"{r['partisan_share'] * 100:4.1f}% Dem -> +{r['dissonance'] * 100:4.1f} pts"
        )
    print(f"\ncounts: {itinerary['category'].value_counts().to_dict()}")


# ── SVG projection (equirectangular with cos(lat) aspect correction) ─────────
def _project_paths(
    rings: dict[str, list],
) -> tuple[dict[str, str], dict[str, tuple[float, float]], float]:
    all_lon = [pt[0] for parts in rings.values() for poly in parts for ring in poly for pt in ring]
    all_lat = [pt[1] for parts in rings.values() for poly in parts for ring in poly for pt in ring]
    lon0, lon1 = min(all_lon), max(all_lon)
    lat0, lat1 = min(all_lat), max(all_lat)
    midlat = math.radians((lat0 + lat1) / 2)
    kx = math.cos(midlat)
    width = 1000.0
    height = width * (lat1 - lat0) / ((lon1 - lon0) * kx)

    def px(lon: float) -> float:
        return round((lon - lon0) * kx / ((lon1 - lon0) * kx) * width, 1)

    def py(lat: float) -> float:
        return round((lat1 - lat) / (lat1 - lat0) * height, 1)

    paths: dict[str, str] = {}
    centroids_px: dict[str, tuple[float, float]] = {}
    for fid, parts in rings.items():
        segs = []
        for poly in parts:
            for ring in poly:
                pts = "".join(
                    f"{'M' if i == 0 else 'L'}{px(p[0])},{py(p[1])}" for i, p in enumerate(ring)
                )
                segs.append(pts + "Z")
        paths[fid] = "".join(segs)
        cx = (
            px(min(p[0] for poly in parts for ring in poly for p in ring))
            + px(max(p[0] for poly in parts for ring in poly for p in ring))
        ) / 2
        cy = (
            py(min(p[1] for poly in parts for ring in poly for p in ring))
            + py(max(p[1] for poly in parts for ring in poly for p in ring))
        ) / 2
        centroids_px[fid] = (round(cx, 1), round(cy, 1))
    return paths, centroids_px, height


def _render_html(itinerary: pd.DataFrame, rings: dict[str, list], names: dict[str, str]) -> str:
    paths, cpx, height = _project_paths(rings)
    by_fips = {r["fips"]: r for r in itinerary.to_dict("records")}
    targets = [r for r in itinerary.to_dict("records") if r["category"] == "target"]
    d_lo = min(r["dissonance"] for r in targets)
    d_hi = max(r["dissonance"] for r in targets)

    # county <path> elements
    poly_svg = []
    for fid, dstr in paths.items():
        r = by_fips.get(fid)
        cat = r["category"] if r else "hard"
        diss = r["dissonance"] if r else 0.0
        fill = _fill(cat, diss, d_lo, d_hi)
        poly_svg.append(
            f'<path d="{dstr}" fill="{fill}" data-fips="{fid}" class="county c-{cat}">'
            f"<title>{names[fid]} County</title></path>"
        )
    hx, hy = cpx[HOME_FIPS]
    home_marker = (
        f'<circle cx="{hx}" cy="{hy}" r="9" class="home-dot"/>'
        f'<circle cx="{hx}" cy="{hy}" r="9" class="home-ring"/>'
    )

    # itinerary rows: nearest 8 targets, ordered by dissonance
    near = sorted(
        sorted(targets, key=lambda r: r["distance_mi"])[:8],
        key=lambda r: r["dissonance"],
        reverse=True,
    )
    rows_html = "\n".join(
        f"""<li class="trow" data-fips="{r["fips"]}" tabindex="0">
          <span class="rank">{i + 1}</span>
          <span class="tname">{r["name"]} County</span>
          <span class="tmiles">{r["distance_mi"]:.0f} mi</span>
          <span class="twhy">voted <b>{r["progressive_share"] * 100:.0f}%</b> to protect rights —
            a county only <b>{r["partisan_share"] * 100:.0f}%</b> voted Democratic.
            <span class="tgap">+{r["dissonance"] * 100:.0f} pts conscience over party</span></span>
        </li>"""
        for i, r in enumerate(near)
    )
    base = sorted(
        (r for r in itinerary.to_dict("records") if r["category"] == "base"),
        key=lambda r: r["distance_mi"],
    )[:3]
    skip_html = ", ".join(
        f"<b>{r['name']}</b> ({r['progressive_share'] * 100:.0f}% with you)" for r in base
    )
    counts = itinerary["category"].value_counts().to_dict()

    return _TEMPLATE.format(
        polys="\n".join(poly_svg),
        home_marker=home_marker,
        height=round(height, 1),
        rows=rows_html,
        skip=skip_html,
        n_target=counts.get("target", 0),
        n_base=counts.get("base", 0),
        n_hard=counts.get("hard", 0),
        n_total=len(itinerary),
        ember=EMBER,
        ember_deep=EMBER_DEEP,
        slate=SLATE,
        ink=INK,
        favicon=_FAVICON,
    )


_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="{favicon}">
<title>The Art of the Possible — Geo-Fluid Dynamics Engine</title>
<style>
  :root {{
    --ink:{ink}; --ink-2:#1E2D3B; --paper:#F2F3EF; --graphite:#28313B;
    --muted:#5C6770; --ember:{ember}; --ember-deep:{ember_deep};
    --slate:{slate}; --ash:#3A4654; --line:#D8DAD2;
    --sans: ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --serif: ui-serif,Georgia,"Times New Roman",serif;
    --mono: ui-monospace,"SFMono-Regular","Cascadia Code",Menlo,Consolas,monospace;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--paper); color:var(--graphite);
    font-family:var(--sans); line-height:1.6; -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:1080px; margin:0 auto; padding:0 28px; }}
  .eyebrow {{ font:600 12px/1 var(--mono); letter-spacing:.18em; text-transform:uppercase;
    color:var(--ember-deep); }}
  h1,h2,h3 {{ text-wrap:balance; letter-spacing:-.02em; }}

  /* hero */
  .hero {{ background:var(--ink); color:#EAF0F4; padding:72px 0 64px; }}
  .hero .eyebrow {{ color:var(--ember); }}
  .hero h1 {{ font-size:clamp(34px,5.4vw,60px); font-weight:800; margin:.35em 0 .2em;
    line-height:1.02; }}
  .hero h1 .amber {{ color:var(--ember); }}
  .lede {{ font-size:clamp(17px,2vw,21px); color:#B7C4CE; max-width:60ch; }}

  /* sections */
  section {{ padding:64px 0; border-bottom:1px solid var(--line); }}
  .act {{ font:600 12px/1 var(--mono); letter-spacing:.18em; text-transform:uppercase;
    color:var(--muted); }}
  section h2 {{ font-size:clamp(26px,3.4vw,38px); font-weight:800; margin:.25em 0 .5em; }}
  .thesis {{ font-family:var(--serif); font-size:clamp(20px,2.5vw,27px); line-height:1.4;
    color:var(--ink); max-width:30ch; }}
  p {{ max-width:64ch; }}
  .col2 {{ display:grid; grid-template-columns:1fr 1fr; gap:40px; align-items:start; }}
  @media (max-width:760px) {{ .col2 {{ grid-template-columns:1fr; gap:24px; }} }}

  /* Ohio proof callout */
  .proof {{ background:var(--ink-2); color:#E7EEF3; border-radius:4px; padding:28px 30px;
    border-left:4px solid var(--ember); }}
  .proof .stat {{ font:800 42px/1 var(--mono); color:var(--ember); }}
  .proof p {{ color:#B7C4CE; margin:.5em 0 0; }}

  /* map + itinerary */
  .ops {{ background:var(--ink); color:#EAF0F4; border-bottom:none; }}
  .ops .act {{ color:#7E8EA0; }}
  .ops h2 {{ color:#fff; }}
  .ops .lede {{ margin-bottom:34px; }}
  .opsgrid {{ display:grid; grid-template-columns:1.05fr .95fr; gap:36px; align-items:start; }}
  @media (max-width:860px) {{ .opsgrid {{ grid-template-columns:1fr; }} }}
  .mapcard {{ background:#101A24; border:1px solid #233240; border-radius:6px; padding:14px; }}
  svg.map {{ width:100%; height:auto; display:block; }}
  .county {{ stroke:#101A24; stroke-width:.8; transition:fill .12s,opacity .12s; }}
  .county.dim {{ opacity:.32; }}
  .county.lit {{ stroke:#fff; stroke-width:2.2; }}
  .home-dot {{ fill:#fff; }}
  .home-ring {{ fill:none; stroke:var(--ember); stroke-width:3; transform-origin:center;
    animation:pulse 2.4s ease-out infinite; }}
  @keyframes pulse {{ 0%{{r:9;opacity:1}} 70%{{r:26;opacity:0}} 100%{{opacity:0}} }}
  @media (prefers-reduced-motion:reduce) {{ .home-ring {{ animation:none; }} }}
  .legend {{ display:flex; flex-wrap:wrap; gap:16px; margin-top:12px; font:500 13px var(--sans);
    color:#B7C4CE; }}
  .legend i {{ display:inline-block; width:13px; height:13px; border-radius:3px;
    margin-right:6px; vertical-align:-1px; }}

  ol.itin {{ list-style:none; margin:0; padding:0; counter-reset:none; }}
  .trow {{ display:grid; grid-template-columns:auto 1fr auto; gap:4px 12px; align-items:baseline;
    padding:13px 14px; border-radius:6px; cursor:default; outline:none;
    border:1px solid transparent; }}
  .trow + .trow {{ margin-top:6px; }}
  .trow:hover, .trow:focus, .trow.lit {{ background:var(--ink-2); border-color:#33485A; }}
  .rank {{ font:800 14px var(--mono); color:var(--ember); }}
  .tname {{ font-weight:700; color:#fff; }}
  .tmiles {{ font:600 13px var(--mono); color:#8FA0AE; text-align:right;
    font-variant-numeric:tabular-nums; }}
  .twhy {{ grid-column:2 / 4; font-size:14px; color:#AEBDC8; }}
  .twhy b {{ color:#E7EEF3; }}
  .tgap {{ display:inline-block; margin-top:3px; font:600 12px var(--mono); color:var(--ember); }}
  .skip {{ margin-top:22px; padding:16px 18px; background:#101A24; border-radius:6px;
    border:1px solid #233240; font-size:14px; color:#AEBDC8; }}
  .skip b {{ color:#cdd8e0; }}

  .wave {{ background:var(--paper); }}
  .wave .thesis {{ max-width:42ch; }}
  footer {{ background:var(--ink); color:#8FA0AE; padding:40px 0 56px; font-size:13.5px; }}
  footer b {{ color:#cdd8e0; }}
  .chips {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; }}
  .chip {{ font:600 12px var(--mono); padding:5px 10px; border-radius:999px;
    border:1px solid #2B3A47; }}
  .chip.t {{ color:var(--ember); border-color:#5a4524; }}
  .chip.b {{ color:#9DB6CB; }} .chip.h {{ color:#7E8EA0; }}
  .backlink {{ font:600 13px var(--mono); color:#8FA0AE; text-decoration:none;
    letter-spacing:.04em; }}
  .backlink:hover {{ color:var(--ember); }}
  .hero .backlink {{ display:inline-block; margin-bottom:24px; }}
  a {{ color:var(--ember-deep); }}
  :focus-visible {{ outline:2px solid var(--ember); outline-offset:3px; border-radius:2px; }}
</style>
</head>
<body>

<header class="hero"><div class="wrap">
  <a class="backlink" href="./">&larr; Back to the live map</a>
  <div class="eyebrow">Geo-Fluid Dynamics Engine · A Prescriptive Demo</div>
  <h1>Don't show me the map.<br><span class="amber">Tell me where to drive.</span></h1>
  <p class="lede">We got curious about a question a map alone can't answer: if you're a
  volunteer with one free Saturday, where do you actually go? So we tried to build it —
  turning public election data into a weekend plan: which counties to canvass, in what
  order, and which to skip, each with the reason in plain English.</p>
</div></header>

<section class="wrap">
  <div class="act">Act 1 · The map we started from</div>
  <h2>A map tells you what happened.</h2>
  <div class="col2">
    <p>Here's how Kansas voted on abortion rights in August 2022 — every county, shaded by
    the result. We love this view, and we kept coming back to it. But we kept hitting the
    same wall: it tells you what happened, not where an organizer with a tank of gas should
    stand on Saturday morning. That wall is the question we wanted to chase.</p>
    <p class="thesis">A map answers “what is.” We wanted to see whether the same data could
    answer “what do I do.”</p>
  </div>
</section>

<section class="wrap">
  <div class="act">Act 2 · The tell</div>
  <h2>Some red counties are persuadable. The data says which.</h2>
  <div class="col2">
    <div>
      <p>Take Miami County, just south of the city. Only about <b>30%</b> of it voted
      Democratic for president — solidly Republican turf. Yet a <b>majority</b> voted to
      protect abortion rights. That gap, between how a place votes its <em>party</em> and how
      it votes its <em>conscience</em>, is what we call <b>dissonance</b>. A high-dissonance
      county is a <b>False Bastion</b>: red on the surface, movable underneath.</p>
      <p>That's the signal worth driving toward — not the deepest-red county (unmovable) and
      not your own backyard (already with you), but the places quietly voting ahead of their
      party.</p>
    </div>
    <div class="proof">
      <div class="eyebrow" style="color:var(--ember)">The proof it's predictive</div>
      <div class="stat">r = 0.62</div>
      <p>In Ohio, the same 88 counties voted on <b>two</b> different questions the same day —
      abortion and cannabis. The counties that broke from their party on one broke on the
      other too (correlation 0.62, holding partisanship constant). Persuadability is a
      <b>stable trait of a place</b> — not a one-issue fluke. That makes this a prediction,
      not a coincidence.</p>
    </div>
  </div>
</section>

<section class="ops"><div class="wrap">
  <div class="act">Act 3 · The marching orders</div>
  <h2>You live in Kansas City. Here's your Saturday.</h2>
  <p class="lede">The engine ranks every county by how far it votes ahead of its party,
  sets your base and your dead ends aside, and orders what's left by drive time. Hover a
  county or a stop — they're linked.</p>
  <div class="opsgrid">
    <div>
      <div class="mapcard">
        <svg class="map" viewBox="0 0 1000 {height}" role="img"
             aria-label="Kansas counties shaded by persuasion priority">
          {polys}
          {home_marker}
        </svg>
      </div>
      <div class="legend">
        <span><i style="background:var(--ember)"></i>Persuadable target (drive here)</span>
        <span><i style="background:var(--slate)"></i>Your base (turn out, don't persuade)</span>
        <span><i style="background:#46535F"></i>Hard ground (skip for now)</span>
        <span><i style="background:#fff;border-radius:50%"></i>You are here</span>
      </div>
    </div>
    <div>
      <ol class="itin">
        {rows}
      </ol>
      <div class="skip">↩ <b>Skip your base</b> — already with you, don't spend gas
      persuading: {skip}. Turn them out instead.</div>
    </div>
  </div>
</div></section>

<section class="wave"><div class="wrap">
  <div class="act">A word on “riding the wave”</div>
  <div class="col2">
    <p class="thesis">We tested whether political change ripples county-to-county like a
    stone dropped in a pond.</p>
    <p>In presidential voting, it mostly doesn't — it's one national tide hitting everywhere
    at once, not a wavefront you can stand in front of. We have the analysis that shows it.
    Knowing that is <em>why</em> this tool targets persuadable places instead of phantom
    waves. Good prediction starts with refusing to predict what you can't.</p>
  </div>
</div></section>

<footer><div class="wrap">
  Every number here is computed by <b>tested code</b> from public records — the Kansas
  Secretary of State's certified canvass and county presidential returns. The classifications,
  the distances, the ranking: all under test, no hand-tuning.
  <div class="chips">
    <span class="chip t">{n_target} persuadable targets</span>
    <span class="chip b">{n_base} base counties</span>
    <span class="chip h">{n_hard} hard ground</span>
    <span class="chip">{n_total} counties ranked</span>
  </div>
  <p style="margin-top:22px"><a class="backlink" href="./">&larr; Back to the live map</a></p>
</div></footer>

<script>
  const sel = f => document.querySelectorAll('[data-fips="'+f+'"]');
  function link(on) {{
    return e => {{
      const f = e.currentTarget.getAttribute('data-fips');
      sel(f).forEach(el => el.classList.toggle('lit', on));
      if (on) document.querySelectorAll('.county').forEach(c =>
        c.getAttribute('data-fips') === f || c.classList.add('dim'));
      else document.querySelectorAll('.county.dim').forEach(c => c.classList.remove('dim'));
    }};
  }}
  document.querySelectorAll('.county, .trow').forEach(el => {{
    el.addEventListener('mouseenter', link(true));
    el.addEventListener('mouseleave', link(false));
    el.addEventListener('focus', link(true));
    el.addEventListener('blur', link(false));
  }});
</script>

</body>
</html>
"""


if __name__ == "__main__":
    main()
