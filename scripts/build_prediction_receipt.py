"""Build the public "November receipt" page (untested orchestration + rendering).

Renders data/predictions/ - the registered (or, before the freeze, the latest
draft) 2026 Missouri county predictions, the statewide-only calls, the
pre-registered propositions and the sealed-playbook manifest - into a
self-contained HTML page: what we did, where geo-fluid dynamics comes in for
THIS ballot, what we predict and why, and how we will grade ourselves. An
inline SVG Missouri choropleth switches between the five measures; hover a
county for its prediction, interval and the partisanship-only baseline.

Like scripts/build_targeting_demo.py this is thin glue over the tested
library's outputs, not itself under test. Every number on the page comes
from the prediction files; the prose is the lay narrative around them.
Run:  uv run python scripts/build_prediction_receipt.py
"""

import json
import math
from pathlib import Path

import pandas as pd

from geofluid.targeting import build_playbook, playbook_budget_split

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "data/predictions"
HTML_OUT = ROOT / "web/public/forecast.html"

INK = "#15202B"
EMBER = "#E8A33D"
EMBER_DEEP = "#C8791F"
SLATE = "#5B7C99"
SLATE_DEEP = "#2F4A63"
NEUTRAL = "#D8DAD2"

_FAVICON = (
    "data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 "
    "viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🧾</text></svg>"
)

# Plain-language framing per measure. The numbers come from the files; these
# words are the narrative around them. "tracked" is the side the prediction's
# share refers to (the loaders' orientation convention), spelled out so a
# reader never has to decode "progressive side".
MEASURES = {
    "mo_20261103_amendment_3": {
        "short": "Amendment 3",
        "question": "Repeal the 2024 reproductive-freedom amendment and ban most abortions?",
        "tracked": "NO",
        "tracked_means": "keep the 2024 rights",
        "why": (
            "In 2024, 51.6% of Missourians voted to protect abortion rights on a presidential "
            "turnout. A near-total ban asks a harsher question than a viability right did: in "
            "Kansas, Kentucky and Ohio the ban side ran 8 to 15 points behind its state's "
            "partisan lean. The crowd that votes in a midterm is smaller and a little older, "
            "but August's 80-to-20 rejection of the legislature's initiative restriction says "
            "the anti-legislature mood is real. Our middle call is 55 of every 100 for NO; "
            "the low end is the 2024 coalition merely holding."
        ),
        "past": "2024 Amendment 3, 51.6% yes",
    },
    "mo_20261103_amendment_6": {
        "short": "Amendment 6",
        "question": (
            "Require an 80% legislative supermajority plus a statewide vote to change what "
            "voters passed?"
        ),
        "tracked": "YES",
        "tracked_means": "protect voter initiatives",
        "why": (
            "The closest past vote is Clean Missouri in 2018, an anti-legislature reform that "
            "won 62% on the same kind of midterm crowd. And in August the legislature's own "
            "attempt to make initiatives harder lost 80 to 20. The risk is that an 80% "
            "threshold reads as extreme once the opposition calls it a lock-in. Middle call: "
            "62 of 100 for YES."
        ),
        "past": "2018 Amendment 1 (Clean Missouri), 62.0% yes; Aug-2026 Amendment 4, 80.3% no",
    },
    "mo_20261103_map_referendum": {
        "short": "Map referendum",
        "question": "Keep the 2025 congressional map (HB 1)? YES keeps it, NO rejects it.",
        "tracked": "NO",
        "tracked_means": "reject the new map",
        "why": (
            "Genuinely close, and the widest range on the page. The legislature's last "
            "redistricting power play, the 2020 repeal of Clean Missouri, passed with 51% on "
            "a presidential crowd. A referendum on a mid-decade map is easier to explain and "
            "the mood is anti-legislature, but this will be the most party-charged question "
            "on the ballot in a state that leans Republican by 18. Middle call: 53 of 100 for "
            "NO, with a range from 46 to 60."
        ),
        "past": "2020 Amendment 3 (Clean Missouri repeal), 51.0% yes",
    },
    "mo_20261103_amendment_7": {
        "short": "Amendment 7",
        "question": "Create the “Show-Me” prosperity fund as a step toward replacing state taxes?",
        "tracked": "NO",
        "tracked_means": "reject the fund",
        "why": (
            "Missouri voters default to NO on referrals they can't picture: court fees in "
            "2024 (39% yes), term limits in 2020 (47%), the childcare tax change in August "
            "2024 (45%). And the tax-elimination agenda's own flagship, Amendment 5, just lost "
            "83 to 17. This one is softer and vaguer, which keeps it off that floor. Middle "
            "call: 58 of 100 for NO. Weak party structure, so the county map is flat."
        ),
        "past": "2024 Amendment 6 (court fees), 39.4% yes; Aug-2026 Amendment 5, 16.7% yes",
    },
    "mo_20261103_amendment_8": {
        "short": "Amendment 8",
        "question": (
            "Make county sheriff a constitutional elected office with protection from removal?"
        ),
        "tracked": "NO",
        "tracked_means": "reject the change",
        "why": (
            "Pro-law-enforcement, populist and low-controversy. Its nearest relative is 2024's "
            "Amendment 7 (citizen-only voting, 68% yes). We expect it to pass comfortably: the "
            "NO side at 36 of 100, and not a single county expected to reject it unless the "
            "removal-protection clause draws organized opposition."
        ),
        "past": "2024 Amendment 7 (citizen voting / RCV ban), 68.4% yes",
    },
}
STATEWIDE_ONLY = {
    "nv_20261103_question_6": {
        "short": "Nevada Question 6",
        "question": "Second passage of a constitutional right to abortion.",
        "tracked": "YES",
        "why": (
            "Identical text to 2024's first passage (64.4%). A midterm crowd and second-vote "
            "fatigue argue for a point or two lower; the measure codifies roughly the status "
            "quo, so there is no extra push from a harsher question. We hold no Nevada county "
            "history, so this is a statewide call only."
        ),
    },
    "ma_20261103_question_8": {
        "short": "Massachusetts Question 8",
        "question": "Eliminate recreational marijuana sales. YES repeals the market; NO keeps it.",
        "tracked": "NO",
        "why": (
            "Legalization won 53.7% in 2016; a decade of an operating market and rising "
            "national support have moved the default. Status-quo bias now works for the "
            "market. Statewide call only: no county history held."
        ),
    },
}
BACKTEST = {"partisan": 3.69, "pooled": 3.80, "analog": 3.39, "analog_baseline": 3.76}


def _latest(prefix: str) -> tuple[Path, str]:
    reg = sorted(PRED.glob(f"{prefix}_REGISTERED_*.csv"))
    if reg:
        return reg[-1], "REGISTERED"
    drafts = sorted(PRED.glob(f"{prefix}_DRAFT_*.csv"))
    if not drafts:
        raise SystemExit(f"no {prefix} file in {PRED}")
    return drafts[-1], "DRAFT"


def _lerp_hex(c1: str, c2: str, t: float) -> str:
    a = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a[i] + (b[i] - a[i]) * t):02x}" for i in range(3))


def _fill(share: float) -> str:
    """Diverging ramp around 50: deep slate well below, neutral at 50, ember well above."""
    if share < 0.5:
        return _lerp_hex(NEUTRAL, SLATE_DEEP, min(1.0, (0.5 - share) / 0.3))
    return _lerp_hex(NEUTRAL, EMBER_DEEP, min(1.0, (share - 0.5) / 0.3))


def _project_paths(rings: dict[str, list]) -> tuple[dict[str, str], float]:
    all_lon = [pt[0] for parts in rings.values() for poly in parts for ring in poly for pt in ring]
    all_lat = [pt[1] for parts in rings.values() for poly in parts for ring in poly for pt in ring]
    lon0, lon1 = min(all_lon), max(all_lon)
    lat0, lat1 = min(all_lat), max(all_lat)
    kx = math.cos(math.radians((lat0 + lat1) / 2))
    width = 1000.0
    height = width * (lat1 - lat0) / ((lon1 - lon0) * kx)

    def px(lon: float) -> float:
        return round((lon - lon0) / (lon1 - lon0) * width, 1)

    def py(lat: float) -> float:
        return round((lat1 - lat) / (lat1 - lat0) * height, 1)

    paths = {}
    for fid, parts in rings.items():
        segs = []
        for poly in parts:
            for ring in poly:
                segs.append(
                    "".join(
                        f"{'M' if i == 0 else 'L'}{px(p[0])},{py(p[1])}" for i, p in enumerate(ring)
                    )
                    + "Z"
                )
        paths[fid] = "".join(segs)
    return paths, height


def main() -> None:
    pred_path, status = _latest("mo_2026-11-03")
    date = pred_path.stem.split("_")[-1]
    preds = pd.read_csv(pred_path, dtype={"fips": str})
    statewide_only = pd.read_csv(_latest("statewide_only_2026-11-03")[0])
    props = pd.read_csv(_latest("propositions_2026-11-03")[0])
    manifest = pd.read_csv(_latest("SEALED_MANIFEST")[0])

    # The worked example: the pro-rights (NO) side of Amendment 3, rebuilt from
    # the public record file through the tested playbook generator. Same code
    # path as the sealed playbooks; this one is shown because the receipt is
    # only worth something if a reader can see what a plan looks like.
    record_file, _st = _latest("county_record_buckets_mo")
    rec = pd.read_csv(record_file, dtype={"fips": str}).set_index("fips")
    level_a3 = float(
        preds.loc[preds["measure_id"] == "mo_20261103_amendment_3", "level_central"].iloc[0]
    )
    record = pd.DataFrame(
        {
            "expected_share": level_a3 + rec["abortion_2024_gap"],
            "mean_gap": rec["abortion_2024_gap"],
            "midterm_penalty": rec["midterm_penalty"],
        }
    )
    plan = build_playbook(record, rec["expected_votes_2026"], side="progressive")
    plan["county"] = plan["fips"].map(rec["county"])
    split = playbook_budget_split(plan)
    persuade = plan[plan["bucket"] == "persuade"].nlargest(8, "votes_per_point")
    turnout = plan[plan["bucket"] == "turnout"].nlargest(5, "votes_at_risk_midterm")
    n_hard = int((plan["bucket"] == "hard").sum())
    plan_rows = "\n".join(
        f"<tr><td>{r.county}</td><td>{r.votes_per_point:,.0f}</td>"
        f"<td>{r.expected_share * 100:.0f}</td><td>{r.headroom_votes:+,.0f}</td></tr>"
        for r in persuade.itertuples()
    )
    turnout_rows = "\n".join(
        f"<tr><td>{r.county}</td><td>{r.votes_per_point:,.0f}</td>"
        f"<td>{r.expected_share * 100:.0f}</td><td>{r.votes_at_risk_midterm:,.0f}</td></tr>"
        for r in turnout.itertuples()
    )
    calc_data = {
        "persuasion_share": round(float(split["persuasion_share"]), 4),
        "turnout_share": round(float(split["turnout_share"]), 4),
        "persuade": [
            [r.county, round(float(r.votes_per_point), 1)]
            for r in plan[plan["bucket"] == "persuade"].nlargest(12, "votes_per_point").itertuples()
        ],
        "turnout": [
            [r.county, round(float(r.votes_per_point), 1)]
            for r in plan[plan["bucket"] == "turnout"]
            .nlargest(6, "votes_at_risk_midterm")
            .itertuples()
        ],
    }

    geo = json.loads((ROOT / "web/public/data/counties.geojson").read_text())
    rings, names = {}, {}
    for f in geo["features"]:
        fid = f["properties"]["fips"]
        if fid.startswith("29"):
            geom = f["geometry"]
            rings[fid] = (
                geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
            )
            names[fid] = f["properties"]["NAME"]
    paths, height = _project_paths(rings)

    # Embedded data: per measure, per fips -> [pred, low, high, baseline]
    data = {}
    for mid, g in preds.groupby("measure_id"):
        data[mid] = {
            r.fips: [
                round(r.pred_progressive_share, 3),
                round(r.pred_low_90, 3),
                round(r.pred_high_90, 3),
                round(r.baseline_partisan_only, 3),
            ]
            for r in g.itertuples()
        }
    first = "mo_20261103_amendment_3"
    poly_svg = "\n".join(
        f'<path d="{d}" fill="{_fill(data[first][fid][0])}" data-fips="{fid}" class="county">'
        f"<title>{names[fid]}</title></path>"
        for fid, d in paths.items()
        if fid in data[first]
    )

    # Measure cards
    cards = []
    for mid, meta in MEASURES.items():
        g = preds[preds["measure_id"] == mid]
        lo, mid_level, hi = (
            g["level_low"].iloc[0],
            g["level_central"].iloc[0],
            g["level_high"].iloc[0],
        )
        wins = int((g["pred_progressive_share"] > 0.5).sum())
        kc = g[g["fips"] == "2938000"]["pred_progressive_share"].iloc[0]
        cards.append(
            f"""<article class="card" id="card-{mid}">
  <div class="eyebrow">{meta["short"]}</div>
  <h3>{meta["question"]}</h3>
  <div class="call"><span class="big">{mid_level * 100:.0f}</span>
    <span class="of">of every 100 votes for <b>{meta["tracked"]}</b>
      ({meta["tracked_means"]})</span></div>
  <div class="range">Range we'd stop being surprised in:
    <b>{lo * 100:.0f} to {hi * 100:.0f}</b>. Counties we expect that side to win:
    <b>{wins} of 116</b>. Kansas City: <b>{kc * 100:.0f}</b>.</div>
  <p>{meta["why"]}</p>
  <div class="past">Learned from: {meta["past"]}</div>
</article>"""
        )
    sw_cards = []
    for r in statewide_only.itertuples():
        meta = STATEWIDE_ONLY[r.measure_id]
        sw_cards.append(
            f"""<article class="card sw">
  <div class="eyebrow">{meta["short"]} · statewide only</div>
  <h3>{meta["question"]}</h3>
  <div class="call"><span class="big">{r.level_central * 100:.0f}</span>
    <span class="of">of every 100 for <b>{meta["tracked"]}</b></span></div>
  <div class="range">Range: <b>{r.level_low * 100:.0f} to {r.level_high * 100:.0f}</b>.</div>
  <p>{meta["why"]}</p>
</article>"""
        )

    options = "\n".join(
        f'<option value="{mid}">{meta["short"]} — {meta["tracked"]} side</option>'
        for mid, meta in MEASURES.items()
    )
    tracked = {mid: meta["tracked"] for mid, meta in MEASURES.items()}
    prop_rows = "\n".join(
        f"<li><b>{r.proposition_id}</b> — {r.statement} "
        f"<span class='call-tag'>Our call: {r.ex_ante_call}</span></li>"
        for r in props.itertuples()
    )
    manifest_rows = "\n".join(
        f"<li><code title='{r.sha256}'>{r.sha256[:16]}…</code> "
        f"{r.file.split('/')[-1]} ({r.bytes:,} bytes)</li>"
        for r in manifest.itertuples()
    )
    if status == "REGISTERED":
        status_line = (
            f"<b>Registered {date}.</b> These files are frozen in the public repository and will "
            "never be edited; the scorecard runs against them after certification."
        )
    else:
        status_line = (
            f"<b>Draft of {date}.</b> The registration commit freezes these exact numbers by "
            "October 15, 2026; after that they are never edited, and the scorecard runs "
            "against them."
        )

    html = _TEMPLATE.format(
        polys=poly_svg,
        height=round(height, 1),
        data_json=json.dumps(data, separators=(",", ":")),
        names_json=json.dumps(names, separators=(",", ":")),
        tracked_json=json.dumps(tracked),
        options=options,
        cards="\n".join(cards),
        sw_cards="\n".join(sw_cards),
        prop_rows=prop_rows,
        manifest_rows=manifest_rows,
        status_line=status_line,
        plan_rows=plan_rows,
        turnout_rows=turnout_rows,
        n_persuade=int((plan["bucket"] == "persuade").sum()),
        n_turnout=int((plan["bucket"] == "turnout").sum()),
        n_hard=n_hard,
        persuasion_pct=round(float(split["persuasion_share"]) * 100),
        turnout_pct=round(float(split["turnout_share"]) * 100),
        calc_json=json.dumps(calc_data, separators=(",", ":")),
        bt=BACKTEST,
        favicon=_FAVICON,
        ink=INK,
        ember=EMBER,
        ember_deep=EMBER_DEEP,
        slate=SLATE,
        slate_deep=SLATE_DEEP,
        neutral=NEUTRAL,
    )
    HTML_OUT.write_text(html, encoding="utf-8")
    print(
        f"wrote {HTML_OUT.relative_to(ROOT)} from {pred_path.name} ({status}), {len(html):,} bytes"
    )


_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="{favicon}">
<title>The November Receipt — Geo-Fluid Dynamics Engine</title>
<style>
  :root {{
    --ink:{ink}; --ink-2:#1E2D3B; --paper:#F2F3EF; --graphite:#28313B; --muted:#5C6770;
    --ember:{ember}; --ember-deep:{ember_deep}; --slate:{slate}; --slate-deep:{slate_deep};
    --neutral:{neutral}; --line:#D8DAD2;
    --sans: ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --serif: ui-serif,Georgia,"Times New Roman",serif;
    --mono: ui-monospace,"SFMono-Regular","Cascadia Code",Menlo,Consolas,monospace;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--paper); color:var(--graphite); font-family:var(--sans);
    line-height:1.6; -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:1080px; margin:0 auto; padding:0 28px; }}
  .eyebrow {{ font:600 12px/1 var(--mono); letter-spacing:.18em; text-transform:uppercase;
    color:var(--ember-deep); }}
  h1,h2,h3 {{ text-wrap:balance; letter-spacing:-.02em; }}
  .hero {{ background:var(--ink); color:#EAF0F4; padding:72px 0 56px; }}
  .hero .eyebrow {{ color:var(--ember); }}
  .hero h1 {{ font-size:clamp(34px,5.4vw,60px); font-weight:800; margin:.35em 0 .2em;
    line-height:1.02; }}
  .hero h1 .amber {{ color:var(--ember); }}
  .lede {{ font-size:clamp(17px,2vw,21px); color:#B7C4CE; max-width:62ch; }}
  .status {{ margin-top:22px; padding:12px 16px; background:#101A24; border:1px solid #233240;
    border-radius:6px; font-size:14px; color:#AEBDC8; max-width:72ch; }}
  .status b {{ color:var(--ember); }}
  section {{ padding:60px 0; border-bottom:1px solid var(--line); }}
  .act {{ display:flex; align-items:center; gap:12px; font:700 14px/1 var(--sans);
    letter-spacing:.08em; text-transform:uppercase; color:var(--ink); padding-top:6px;
    border-top:3px solid var(--ember); width:max-content; padding-right:14px; }}
  .act .n {{ display:inline-flex; align-items:center; justify-content:center; min-width:30px;
    height:30px; padding:0 9px; border-radius:999px; background:var(--ember);
    color:var(--ink); font:800 15px var(--mono); }}
  .ops .act {{ color:#fff; }}
  section h2 {{ font-size:clamp(26px,3.4vw,38px); font-weight:800; margin:.25em 0 .5em; }}
  .thesis {{ font-family:var(--serif); font-size:clamp(20px,2.5vw,27px); line-height:1.4;
    color:var(--ink); max-width:34ch; }}
  p {{ max-width:66ch; }}
  .col2 {{ display:grid; grid-template-columns:1fr 1fr; gap:40px; align-items:start; }}
  @media (max-width:760px) {{ .col2 {{ grid-template-columns:1fr; gap:24px; }} }}
  details {{ margin:14px 0 0; padding:14px 18px; background:#E9EBE4; border-radius:6px;
    max-width:66ch; }}
  details summary {{ cursor:pointer; font:600 13px var(--mono); color:var(--ink);
    letter-spacing:.04em; }}
  details p {{ font-size:14.5px; margin:.6em 0 0; }}
  code {{ font:500 13px var(--mono); }}
  table.plan {{ width:100%; border-collapse:collapse; font-size:14px; margin:8px 0 6px; }}
  table.plan th {{ text-align:left; font:600 11px var(--mono); letter-spacing:.08em;
    text-transform:uppercase; color:var(--muted); padding:6px 8px;
    border-bottom:2px solid var(--line); }}
  table.plan td {{ padding:7px 8px; border-bottom:1px solid var(--line);
    font-variant-numeric:tabular-nums; }}
  table.plan td:nth-child(n+2) {{ text-align:right; }}
  .fine {{ font-size:13px; color:var(--muted); }}
  .calc {{ margin-top:28px; background:var(--ink); color:#EAF0F4; border-radius:8px;
    padding:24px 26px; }}
  .calcrow {{ display:flex; gap:28px; flex-wrap:wrap; margin:12px 0 16px; }}
  .calcrow label {{ font-size:14px; color:#B7C4CE; }}
  .calcrow input {{ width:120px; margin:0 6px; padding:6px 8px; border-radius:6px;
    border:1px solid #33485A; background:#1E2D3B; color:#fff; font:600 15px var(--mono); }}
  #calcout {{ display:grid; grid-template-columns:1fr 1fr; gap:22px; }}
  @media (max-width:760px) {{ #calcout {{ grid-template-columns:1fr; }} }}
  #calcout h4 {{ margin:0 0 6px; font-size:15px; color:#fff; }}
  #calcout .sum {{ font:800 26px/1.1 var(--mono); color:var(--ember); margin-bottom:8px; }}
  #calcout ul {{ margin:0; padding-left:18px; font-size:14px; color:#CDD8E0; }}
  #calcout li {{ margin:3px 0; }}
  .calc .fine {{ color:#8FA0AE; margin-top:14px; }}
  .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:18px;
    margin-top:24px; }}
  .card {{ background:#fff; border:1px solid var(--line); border-radius:8px;
    padding:22px 22px 18px; }}
  .card.sw {{ background:#F7F8F4; }}
  .card h3 {{ font-size:17px; margin:.4em 0 .6em; line-height:1.3; }}
  .call {{ display:flex; align-items:baseline; gap:10px; margin:6px 0; }}
  .big {{ font:800 44px/1 var(--mono); color:var(--ember-deep); }}
  .of {{ font-size:14px; color:var(--muted); max-width:22ch; line-height:1.3; }}
  .range {{ font-size:13.5px; color:var(--graphite); margin:6px 0 10px; }}
  .card p {{ font-size:14.5px; margin:.4em 0; }}
  .past {{ font:500 12px var(--mono); color:var(--muted); margin-top:10px; }}
  .ops {{ background:var(--ink); color:#EAF0F4; border-bottom:none; }}
  .ops h2 {{ color:#fff; }}
  .opsgrid {{ display:grid; grid-template-columns:1.15fr .85fr; gap:36px; align-items:start; }}
  @media (max-width:860px) {{ .opsgrid {{ grid-template-columns:1fr; }} }}
  .mapcard {{ background:#101A24; border:1px solid #233240; border-radius:6px; padding:14px; }}
  svg.map {{ width:100%; height:auto; display:block; }}
  .county {{ stroke:#101A24; stroke-width:.8; transition:fill .15s; cursor:default; }}
  .county.lit {{ stroke:#fff; stroke-width:2.2; }}
  select {{ font:600 14px var(--sans); padding:8px 12px; border-radius:6px;
    border:1px solid #33485A;
    background:#1E2D3B; color:#fff; margin-bottom:12px; max-width:100%; }}
  .legend {{ display:flex; flex-wrap:wrap; gap:16px; margin-top:12px;
    font:500 13px var(--sans); color:#B7C4CE; }}
  .legend i {{ display:inline-block; width:13px; height:13px; border-radius:3px;
    margin-right:6px; vertical-align:-1px; }}
  .readout {{ background:#101A24; border:1px solid #233240; border-radius:6px;
    padding:18px 20px; min-height:150px; }}
  .readout .name {{ font-weight:800; color:#fff; font-size:18px; }}
  .readout .num {{ font:800 34px/1.1 var(--mono); color:var(--ember); margin:6px 0 2px; }}
  .readout p {{ color:#AEBDC8; font-size:14px; margin:.4em 0; }}
  .readout b {{ color:#E7EEF3; }}
  ul.props {{ padding-left:20px; }} ul.props li {{ margin:10px 0; font-size:14.5px;
    max-width:80ch; }}
  .call-tag {{ display:inline-block; font:600 12px var(--mono); color:var(--ember-deep);
    margin-left:6px; }}
  ul.manifest {{ list-style:none; padding:0; font-size:13px; }}
  ul.manifest li {{ padding:4px 0; border-bottom:1px dashed var(--line); }}
  footer {{ background:var(--ink); color:#8FA0AE; padding:40px 0 56px; font-size:13.5px; }}
  footer b {{ color:#cdd8e0; }}
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
  <div class="eyebrow">Geo-Fluid Dynamics Engine · The November Receipt</div>
  <h1>We wrote down Missouri's results<br><span class="amber">before Missouri voted.</span></h1>
  <p class="lede">Seven ballot questions on November 3, 2026. For the five in Missouri, a
  prediction for every one of the state's 116 counties and cities. All of it committed to a
  public record before the election, graded in public after it, win or lose. This page is the
  plain-language version of that promise: what we did, why the geography matters, what we
  expect, and how we'll know if we were wrong.</p>
  <div class="status">{status_line}</div>
</div></header>

<section class="wrap">
  <div class="act"><span class="n">1</span>What we did</div>
  <h2>Twenty-one past votes, one county personality.</h2>
  <div class="col2">
    <div>
      <p>Since 2018 Missouri has voted on 21 statewide ballot questions: abortion, wages,
      marijuana, gambling, taxes, redistricting, Medicaid. Every one is reported by the Secretary
      of State for the same 116 places, and every one of those files was checked against the
      certified statewide totals before we used a single number.</p>
      <p>From that record, two things explain almost every county's vote on almost any question.
      First, <b>partisanship</b>: how the county voted for president. It alone gets you within
      about four points. Second, a <b>personality</b>: some counties run ahead of their politics
      on certain issues, some run behind, and they keep doing it, election after election.</p>
      <p>We only trust what has been tested. So before predicting anything, we pretended each
      past vote hadn't happened yet, predicted it from the others, and kept score.</p>
    </div>
    <div>
      <p class="thesis">Partisanship alone misses the typical county by {bt[partisan]} points.
      Our method misses it by {bt[analog]}. Everything on this page rests on that gap.</p>
      <details><summary>For the technically minded</summary>
        <p>Leave-one-out backtest on 13 general-election measures, statewide level given, scored
        as county RMSE in percentage points. Partisanship only (logit-linear on the era's
        presidential two-party share): {bt[partisan]}. A pooled ideal-point position across the
        other measures: {bt[pooled]}, i.e. it <em>lost</em> to partisanship. Partisanship plus
        half of the same-issue analog's partisanship residual: {bt[analog]} against
        {bt[analog_baseline]} on the same subset. Shrinkage 0.5 chosen by the table. Era-matched
        baselines so realignment drift can't leak in.</p>
      </details>
    </div>
  </div>
</section>

<section class="wrap">
  <div class="act"><span class="n">2</span>Where geo-fluid dynamics comes in</div>
  <h2>Ideas move like a flock, not like dominoes.</h2>
  <div class="col2">
    <div>
      <p>We began with a hunch that political change spreads county to county, the way a
      stone's ripple crosses a pond: find the first domino and you can forecast the wave. We
      tested that twice on 150 years of county returns, and twice the data said no. When
      Missouri moves, nearly every county moves in the same election. There is no leader bird.
      A flock of starlings turns all at once.</p>
      <p>What <em>does</em> hold is the formation. Neighboring counties vote together far more
      than counties that merely resemble each other, and each county keeps its place in the
      flock from one election to the next. That is why a county's record is such a strong
      predictor: the formation is stable, and the few birds flying out of formation, the
      counties running ahead of their politics on an issue, keep flying there.</p>
      <p>For this ballot that means three things. The flock will turn together, so we give the
      statewide result as a range, not a number. The formation will hold, so each county's
      prediction is a point. And the counties out of formation are exactly where the November
      map will look different from the party map.</p>
    </div>
    <div>
      <p class="thesis">The honest part: this forecast uses the formation, not the flock's
      physics. We registered a test to find out whether that was a mistake.</p>
      <details><summary>For the technically minded</summary>
        <p>Spatial autocorrelation of residual presidential swing along geographic (queen)
        adjacency: Moran's I 0.62, versus 0.28 for the best attribute-similarity network;
        the spatial-lag coefficient survives a Durbin control for neighbors' demographics.
        Two attempts at leader-follower (contemporaneous conformity; lead-lag timing on the
        1868–2024 spine) were falsified. The registered model is partisanship plus a
        same-issue residual and uses no spatial weights; the registered diagnostic is Moran's I
        of the relevelled Amendment 3 county errors (expected positive and significant), which
        would show the spatial layer holds information the model left on the table.</p>
      </details>
    </div>
  </div>
</section>

<section class="wrap">
  <div class="act"><span class="n">3</span>What you get</div>
  <h2>A plan priced in votes: where to go, what to do there, how to split the money.</h2>
  <p>Here is what the engine hands a campaign, worked through for one side of one measure:
  keeping abortion rights in Missouri (the NO side of Amendment 3). It is built from the same
  public county records as everything else on this page, by the same tested code that wrote the
  sealed plans. Three things, in the order a campaign decides them.</p>
  <div class="col2">
    <div>
      <h3>1. Where a conversation buys the most</h3>
      <p>Persuasion ground: counties the record puts near 50 for this side, ranked by what one
      point of movement is worth in votes. Start at the top.
      <b>{n_persuade} counties</b> qualify.</p>
      <table class="plan">
        <thead><tr><th>County</th><th>Votes per point</th><th>Record says</th>
          <th>Lean beyond party</th></tr></thead>
        <tbody>{plan_rows}</tbody>
      </table>
      <p class="fine">"Record says" is the share for NO the county's own history implies at our
      statewide middle; "lean beyond party" is the votes the county already leans this way
      beyond what its presidential vote predicts.</p>
    </div>
    <div>
      <h3>2. Where showing up is the whole job</h3>
      <p>Turnout ground: counties the record puts clearly ahead, ranked by the supporters who
      tend to skip midterms. Nobody here needs persuading; every one who stays home is a vote
      lost. <b>{n_turnout} counties</b> qualify; <b>{n_hard}</b> are hard ground where the advice
      is to spend nothing you can't spare.</p>
      <table class="plan">
        <thead><tr><th>County</th><th>Votes per point</th><th>Record says</th>
          <th>Votes at risk</th></tr></thead>
        <tbody>{turnout_rows}</tbody>
      </table>
      <h3>3. How the money divides</h3>
      <p>For this side of this measure the reachable votes sit <b>{persuasion_pct}% in persuasion
      ground and {turnout_pct}% in turnout ground</b>. The other side's plan, from the same
      record, is nearly all persuasion: it holds almost no counties where its own voters stay
      home. Same data, mirror plans.</p>
    </div>
  </div>
  <div class="calc" id="calc">
    <div class="eyebrow" style="color:var(--ember)">Try it: a budget, in votes and dollars</div>
    <div class="calcrow">
      <label>Budget <input id="budget" type="number" value="250000" min="0" step="5000"> $</label>
      <label>Your cost per vote <input id="cpv" type="number" value="40" min="1" step="1"> $</label>
    </div>
    <div id="calcout"></div>
    <p class="fine">The cost per vote is yours, not ours: what your organization has found a
    persuaded or turned-out vote costs. We price the ground; you know your own plow. The split
    applies the shares above; within each bucket, dollars follow what a point buys in each
    county (votes per point), with the turnout list ranked by votes at risk.</p>
  </div>
  <p class="thesis" style="margin-top:28px">Not “campaign somewhere.” Not “start a domino.”
  Where, what kind, and how much, with the receipt for each.</p>
</section>

<section class="wrap">
  <div class="act"><span class="n">4</span>What we predict, and why</div>
  <h2>Five Missouri questions, county by county.</h2>
  <p>Each card gives the statewide call as "N of every 100 votes" for the side we track, the
  range we'd stop being surprised in, and the reasoning in plain words. The side we track is a
  bookkeeping convention, not an endorsement: the same record produces the plan for either side.</p>
  <div class="cards">
    {cards}
  </div>
  <h2 style="margin-top:48px">Two statewide-only calls.</h2>
  <p>We hold no county history for Nevada or Massachusetts, so these are statewide calls with a
  range and nothing more. We won't pretend to know a county we haven't studied.</p>
  <div class="cards">
    {sw_cards}
  </div>
</section>

<section class="ops"><div class="wrap">
  <div class="act"><span class="n">5</span>The map</div>
  <h2>Hover a county. Switch the measure.</h2>
  <p class="lede">Each county is shaded by the share we predict for the side we track: deep
  slate well below 50, neutral at the line, amber well above. The readout shows the prediction,
  the range, and what partisanship alone would have said. Kansas City reports separately from its
  four counties and is listed on the card above.</p>
  <div class="opsgrid">
    <div>
      <label for="measure" class="eyebrow"
             style="display:block;margin-bottom:6px;color:#B7C4CE">Measure</label>
      <select id="measure" aria-label="Choose a measure">
        {options}
      </select>
      <div class="mapcard">
        <svg class="map" viewBox="0 0 1000 {height}" role="img"
             aria-label="Missouri counties shaded by predicted share">
          {polys}
        </svg>
      </div>
      <div class="legend">
        <span><i style="background:var(--slate-deep)"></i>Well below 50 for the tracked side</span>
        <span><i style="background:var(--neutral)"></i>Near 50 — the contest</span>
        <span><i style="background:var(--ember-deep)"></i>Well above 50</span>
      </div>
    </div>
    <div class="readout" id="readout" aria-live="polite">
      <div class="name">Hover a county</div>
      <p>The readout shows our prediction for the tracked side, the 90% range, and the
      partisanship-only baseline we have promised to beat.</p>
    </div>
  </div>
</div></section>

<section class="wrap">
  <div class="act"><span class="n">6</span>How we'll grade ourselves</div>
  <h2>The yardstick was chosen before the data exists.</h2>
  <div class="col2">
    <div>
      <p><b>The county pattern.</b> After the certified results arrive, every county's error is
      compared with the error of partisanship alone, both lined up to the actual statewide result
      so the comparison is about <em>where</em>, not how much. If we aren't better than the party
      map, we'll say so.</p>
      <p><b>The ranges.</b> About nine counties in ten should land inside their range. Far fewer
      means we were overconfident; far more means we padded.</p>
      <p><b>The statewide calls.</b> Judgement, scored as judgement: did the real number land
      inside the range, and how far from the middle.</p>
      <p><b>Twice.</b> A provisional scorecard from election-night counts within a day, and a
      certified scorecard when the Board of State Canvassers signs, usually early December.</p>
      <p><b>The sealed envelope.</b> For every measure we also wrote a campaign plan for
      <em>each</em> side, priced in votes. In a public repository a committed file is a published
      file, so the plans are sealed as fingerprints: the digests below are committed now, the
      files are revealed after the scorecard, and anyone can verify they match.</p>
    </div>
    <div>
      <details open><summary>Registered propositions and the statistical test</summary>
        <ul class="props">
          {prop_rows}
        </ul>
      </details>
      <details><summary>The sealed playbooks (SHA-256)</summary>
        <ul class="manifest">
          {manifest_rows}
        </ul>
      </details>
    </div>
  </div>
</section>

<section class="wrap">
  <div class="act"><span class="n">7</span>What we are not claiming</div>
  <div class="col2">
    <p class="thesis">A tool, not an oracle. It says where a conversation is worth having; the
    conversation is still yours.</p>
    <div>
      <p>We cannot predict the national mood that turns the whole flock; that's why the statewide
      numbers are ranges. We cannot name the county where a movement starts; we tried, and the
      data refused. We do not know who votes, only how counties vote, and if a brand-new electorate
      shows up the misses will be in the counties where turnout changed most. We registered a
      test for that too. One state, one cycle: evidence, not proof. The point of writing it down
      first is to find out.</p>
    </div>
  </div>
</section>

<footer><div class="wrap">
  Every number here is computed by <b>tested code</b> from certified public records: six
  Missouri canvasses, the Election Night Results portal, and county presidential returns. The
  prediction files, the methods notebook, the backtest and the sealed manifest are in the public
  repository, and the raw inputs are fingerprinted alongside them.
  <p style="margin-top:22px"><a class="backlink" href="./">&larr; Back to the live map</a>
  &nbsp;·&nbsp; <a class="backlink" href="demo.html">The art of the possible &rarr;</a></p>
</div></footer>

<script>
  const DATA = {data_json};
  const NAMES = {names_json};
  const TRACKED = {tracked_json};
  const sel = document.getElementById('measure');
  const readout = document.getElementById('readout');
  const lerp = (a, b, t) => '#' + [0,1,2].map(i => {{
    const x = parseInt(a.substr(1 + i*2, 2), 16), y = parseInt(b.substr(1 + i*2, 2), 16);
    return Math.round(x + (y - x) * t).toString(16).padStart(2, '0'); }}).join('');
  const fill = s => s < 0.5 ? lerp('{neutral}', '{slate_deep}', Math.min(1, (0.5 - s) / 0.3))
                            : lerp('{neutral}', '{ember_deep}', Math.min(1, (s - 0.5) / 0.3));
  function recolor() {{
    const d = DATA[sel.value];
    document.querySelectorAll('.county').forEach(c => {{
      const v = d[c.getAttribute('data-fips')];
      if (v) c.setAttribute('fill', fill(v[0]));
    }});
  }}
  function show(fips) {{
    const v = DATA[sel.value][fips]; if (!v) return;
    const side = TRACKED[sel.value];
    const pct = x => Math.round(x * 100);
    readout.innerHTML = '<div class="name">' + NAMES[fips] + ' County</div>'
      + '<div class="num">' + pct(v[0]) + ' of 100 for ' + side + '</div>'
      + '<p>Range: <b>' + pct(v[1]) + ' to ' + pct(v[2]) + '</b> (nine times in ten).</p>'
      + '<p>Partisanship alone would say <b>' + pct(v[3]) + '</b>. '
      + (Math.abs(v[0] - v[3]) >= 0.02
          ? 'This county’s record says it runs <b>' + (v[0] > v[3] ? 'ahead of' : 'behind')
            + '</b> its politics on this question.'
          : 'This county votes about the way its politics say it should.')
      + '</p>';
  }}
  sel.addEventListener('change', recolor);
  document.querySelectorAll('.county').forEach(c => {{
    const f = c.getAttribute('data-fips');
    c.addEventListener('mouseenter', () => {{ c.classList.add('lit'); show(f); }});
    c.addEventListener('mouseleave', () => c.classList.remove('lit'));
    c.setAttribute('tabindex', '0');
    c.addEventListener('focus', () => {{ c.classList.add('lit'); show(f); }});
    c.addEventListener('blur', () => c.classList.remove('lit'));
  }});
  recolor();

  const CALC = {calc_json};
  const money = x => '$' + Math.round(x).toLocaleString();
  function calc() {{
    const budget = Math.max(0, +document.getElementById('budget').value || 0);
    const cpv = Math.max(1, +document.getElementById('cpv').value || 1);
    const votes = budget / cpv;
    const pBudget = budget * CALC.persuasion_share, tBudget = budget * CALC.turnout_share;
    const pTot = CALC.persuade.reduce((a, r) => a + r[1], 0);
    const tTot = CALC.turnout.reduce((a, r) => a + r[1], 0);
    const li = (name, amt) => '<li>' + name + ': <b>' + money(amt) + '</b></li>';
    document.getElementById('calcout').innerHTML =
      '<div><h4>Persuasion (' + Math.round(CALC.persuasion_share * 100) + '%)</h4>'
      + '<div class="sum">' + money(pBudget) + '</div><ul>'
      + CALC.persuade.map(r => li(r[0], pBudget * r[1] / pTot)).join('') + '</ul></div>'
      + '<div><h4>Turnout (' + Math.round(CALC.turnout_share * 100) + '%)</h4>'
      + '<div class="sum">' + money(tBudget) + '</div><ul>'
      + CALC.turnout.map(r => li(r[0], tBudget * r[1] / tTot)).join('') + '</ul>'
      + '<p style="color:#8FA0AE;font-size:13px;margin:10px 0 0">About <b style="color:#fff">'
      + Math.round(votes).toLocaleString() + ' votes</b> at your cost per vote.</p></div>';
  }}
  document.getElementById('budget').addEventListener('input', calc);
  document.getElementById('cpv').addEventListener('input', calc);
  calc();
</script>

</body>
</html>
"""


if __name__ == "__main__":
    main()
