"""Build the public "blueprint" page (untested orchestration + rendering).

The deep dive, in the order the work happened: the brainstorm (do ideas
travel across the ground like forests?), the five modules imagined, the data
gathered and the machinery built, the hypotheses tested and what the data
said (figures pulled straight from the executed research notebooks), the
November plan, and the lock-in. It is the companion to forecast.html: the
receipt says what we predict; the blueprint says how we got there.

Like scripts/build_targeting_demo.py this is thin glue, not under test. The
figures are the notebooks' own rendered outputs (matplotlib PNGs embedded as
data URIs) so the page cannot show a chart the research didn't produce.
Run:  uv run python scripts/build_blueprint.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks"
HTML_OUT = ROOT / "web/public/blueprint.html"

INK = "#15202B"
EMBER = "#E8A33D"
EMBER_DEEP = "#C8791F"
SLATE = "#5B7C99"

_FAVICON = (
    "data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 "
    "viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🧭</text></svg>"
)


def _figure(notebook: str, nth: int = 0) -> str:
    """The nth image/png output of an executed notebook, as a data URI."""
    cells = json.loads((NB / f"{notebook}.ipynb").read_text(encoding="utf-8"))["cells"]
    images = [
        o["data"]["image/png"]
        for c in cells
        for o in c.get("outputs", [])
        if "image/png" in o.get("data", {})
    ]
    return "data:image/png;base64," + images[nth].replace("\n", "")


def main() -> None:
    figs = {
        "leadlag": _figure("leadlag_node_roles"),
        "ohio": _figure("issue_generality_ohio"),
        "minwage": _figure("minimum_wage_economic_bastions"),
        "horserace": _figure("diffusion_network_horse_race"),
        "flicker": _figure("education_channel_over_time"),
        "grid": _figure("mo_issue_space"),
        "panels": _figure("mo_2026_predictions"),
        "populist": _figure("gilded_age_rhyme"),
    }
    registered = sorted((ROOT / "data/predictions").glob("REGISTERED_SHA256_*.csv"))
    reg_date = registered[-1].stem.split("_")[-1] if registered else "pending"
    html = _TEMPLATE.format(
        favicon=_FAVICON,
        ink=INK,
        ember=EMBER,
        ember_deep=EMBER_DEEP,
        slate=SLATE,
        reg_date=reg_date,
        **figs,
    )
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"wrote {HTML_OUT.relative_to(ROOT)} ({len(html):,} bytes, {len(figs)} figures)")


_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="{favicon}">
<title>The Blueprint — Geo-Fluid Dynamics Engine</title>
<style>
  :root {{
    --ink:{ink}; --ink-2:#1E2D3B; --paper:#F2F3EF; --graphite:#28313B; --muted:#5C6770;
    --ember:{ember}; --ember-deep:{ember_deep}; --slate:{slate}; --line:#D8DAD2;
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
  section {{ padding:60px 0; border-bottom:1px solid var(--line); }}
  .act {{ display:flex; align-items:center; gap:12px; font:700 14px/1 var(--sans);
    letter-spacing:.08em; text-transform:uppercase; color:var(--ink); padding-top:6px;
    border-top:3px solid var(--ember); width:max-content; padding-right:14px; }}
  .act .n {{ display:inline-flex; align-items:center; justify-content:center; min-width:30px;
    height:30px; padding:0 9px; border-radius:999px; background:var(--ember);
    color:var(--ink); font:800 15px var(--mono); }}
  section h2 {{ font-size:clamp(26px,3.4vw,38px); font-weight:800; margin:.25em 0 .5em; }}
  section h3 {{ font-size:18px; margin:1.4em 0 .4em; }}
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
  figure {{ margin:18px 0; background:#fff; border:1px solid var(--line); border-radius:8px;
    padding:12px; }}
  figure img {{ width:100%; height:auto; display:block; }}
  figcaption {{ font-size:13.5px; color:var(--muted); margin-top:8px; line-height:1.45; }}
  figcaption b {{ color:var(--graphite); }}
  .modules {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:16px;
    margin-top:22px; }}
  .mod {{ background:#fff; border:1px solid var(--line); border-radius:8px; padding:18px 20px; }}
  .mod h3 {{ margin:.2em 0 .4em; font-size:16px; }}
  .mod p {{ font-size:14px; margin:.3em 0; }}
  .badge {{ display:inline-block; font:700 11px var(--mono); letter-spacing:.08em;
    text-transform:uppercase; padding:3px 9px; border-radius:999px; margin-top:8px; }}
  .b-built {{ background:#DDE9E1; color:#1E5A3A; }}
  .b-falsified {{ background:#F3DDD3; color:#7A2E1A; }}
  .b-seed {{ background:#F6E7C8; color:#6B4A0E; }}
  .b-not {{ background:#E4E6E1; color:#5C6770; }}
  .findings {{ counter-reset:f; }}
  .finding {{ display:grid; grid-template-columns:1fr 1fr; gap:34px; align-items:start;
    padding:30px 0; border-top:1px dashed var(--line); }}
  @media (max-width:860px) {{ .finding {{ grid-template-columns:1fr; }} }}
  .finding h3 {{ margin:0 0 .4em; font-size:20px; }}
  .finding .num {{ font:800 13px var(--mono); color:var(--ember-deep); letter-spacing:.1em; }}
  .finding p {{ font-size:15px; }}
  .stat {{ font:800 34px/1 var(--mono); color:var(--ember-deep); margin:4px 0 6px; }}
  .locked {{ background:var(--ink); color:#EAF0F4; }}
  .locked h2 {{ color:#fff; }} .locked .act {{ color:#fff; }}
  .locked p {{ color:#B7C4CE; }}
  .locked .slot {{ margin-top:26px; padding:26px 28px; border:2px dashed #46535F; border-radius:8px;
    color:#8FA0AE; font-family:var(--serif); font-size:20px; max-width:60ch; }}
  .locked code {{ color:var(--ember); font:600 13px var(--mono); }}
  .cta {{ display:inline-block; margin-top:16px; padding:10px 16px; background:var(--ember);
    color:var(--ink); font:700 14px var(--sans); border-radius:6px; text-decoration:none; }}
  .cta:hover {{ background:var(--ember-deep); }}
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
  <div class="eyebrow">Geo-Fluid Dynamics Engine · The Blueprint</div>
  <h1>Do ideas travel across the ground<br><span class="amber">the way forests do?</span></h1>
  <p class="lede">One person, spare evenings, a few months, and a question that wouldn't go
  away. This is the whole arc: the brainstorm, the modules we imagined, the data we gathered
  and the machinery we built, what the data actually said when we tested our ideas against it,
  the plan we made for November 3, 2026, and the moment we locked it in. Written for a curious
  reader; the technical detail folds open where it matters.</p>
</div></header>

<section class="wrap">
  <div class="act"><span class="n">1</span>The brainstorm</div>
  <h2>Ideas are shared with the people we actually talk to.</h2>
  <div class="col2">
    <div>
      <p>At church, at school pickup, at little league, on the porch. If that's how ideas move,
      then they should move across a map the way a forest spreads: from where they are to where
      they aren't, neighbor to neighbor, over years. A documentary about far-right support in
      Europe made the question concrete. The German districts voting for the far right today are,
      to a striking degree, the districts that voted for the Nazi party in the 1930s. Dormant for
      three generations, then reactivated. Grandparents' ideas, still etched into the ground.</p>
      <p>Politics turned out to be the perfect laboratory for the question, not because politics
      is the point, but because it is the only human idea with free, certified, county-by-county
      measurements, repeated every two years for a hundred and fifty years. If ideas travel
      across the ground, votes are where the footprints would show.</p>
      <p>Two worries from the start, both honest: people move, and people have the internet.
      Both got answered by the data later. Hold them.</p>
    </div>
    <div>
      <p class="thesis">A geographer named Torsten Hägerstrand asked the same question in 1952
      about farm innovations in Sweden. We are asking it about ideas, with better data and worse
      odds.</p>
      <details><summary>For the technically minded</summary>
        <p>Hägerstrand's spatial diffusion model (hearth, contagious expansion, hierarchical
        leapfrogging) is the classic frame. The persistence literature is the second anchor:
        Cantoni, Hagemeister and Westcott (2019) on Nazi-era vote share predicting AfD support by
        municipality, with activation by a later shock, and Voigtländer and Voth (2012) on
        medieval pogroms predicting 1920s antisemitism. The engine's data spine: county
        presidential returns 1868–2024 (Algara–Sharif joined to MIT), ACS demographics, Census
        county geometry, and certified state ballot-measure canvasses.</p>
      </details>
    </div>
  </div>
</section>

<section class="wrap">
  <div class="act"><span class="n">2</span>The modules we imagined</div>
  <h2>Five instruments for one question.</h2>
  <p>The original plan broke the question into five pieces, from "where is an idea going" to
  "when do the rules of the game break." Each got a status badge from the data, not from us.</p>
  <div class="modules">
    <div class="mod"><h3>1 · Wave Predictor</h3>
      <p>Where change starts and where it spreads next: neighbor-to-neighbor diffusion.</p>
      <p>Built the measuring tools (neighbor weights, clustering tests, a spatial regression).
      The "wave" itself turned out to be a flock turning together, not a front moving.</p>
      <span class="badge b-built">core built · wave reframed</span></div>
    <div class="mod"><h3>2 · Gravity Engine</h3>
      <p>Which places lead and which follow: the influence hubs.</p>
      <p>Two serious attempts to find leaders and followers were falsified on real data. The
      replacement, issue resistance as a stable county trait, is the engine's best finding.</p>
      <span class="badge b-falsified">hubs falsified · trait found</span></div>
    <div class="mod"><h3>3 · Friction &amp; Dissonance</h3>
      <p>Where a place's vote on an issue diverges from its party label.</p>
      <p>Live on the map for Kansas, Kentucky and Ohio abortion measures and Missouri's whole
      record. The False Bastions.</p>
      <span class="badge b-built">live</span></div>
    <div class="mod"><h3>4 · Chaos &amp; Anomaly Sensor</h3>
      <p>When a variable that used to be noise becomes the signal, like education in 2016.</p>
      <p>The seed exists: each county's surprise against its own trend. The live monitor is not
      built.</p>
      <span class="badge b-seed">seed</span></div>
    <div class="mod"><h3>5 · Phase Transition</h3>
      <p>When a losing side stops accepting the result: structural early warning.</p>
      <p>Not built. One order parameter is registered for November: whether ballot measures
      are becoming party-line votes.</p>
      <span class="badge b-not">not started · one gauge registered</span></div>
  </div>
</section>

<section class="wrap">
  <div class="act"><span class="n">3</span>Gathering, building, testing</div>
  <h2>Free data, tested code, and a rule: no claim without a failing test first.</h2>
  <div class="col2">
    <div>
      <h3>The data</h3>
      <p>County presidential returns for every election since 1868, joined across two sources
      and cross-checked where they overlap. Demographics for every county from the Census.
      County shapes. And the expensive part: certified ballot-measure results, county by county,
      from each state's election office, each in its own format. Missouri's came as PDF
      canvasses and turned out to be the cleanest data any state gave us: 21 statewide measures
      since 2018 on the same 116 jurisdictions.</p>
      <h3>The machinery</h3>
      <p>Which counties touch which. A test for whether a pattern on the map is clustered or
      random. A regression that lets neighbors influence each other, with an honesty check that
      the influence isn't just neighbors looking alike. A way to measure how far a county's
      issue vote runs ahead of its party. A county's record read as turnout ground, persuasion
      ground, or hard ground. A plan generator that prices a county in votes.</p>
    </div>
    <div>
      <h3>The discipline</h3>
      <p>Every piece of machinery was written test-first: a failing test, then the smallest code
      that passes it. Every loader of real data had to reproduce its state's certified totals to
      the vote before anything downstream could use it. Numerical code is verified without
      random seeds, on constructions where the right answer is known exactly. And every
      hypothesis was set up to be falsified: we decided in advance what result would mean we
      were wrong.</p>
      <details><summary>For the technically minded</summary>
        <p>Queen adjacency with row-standardised weights; global and local Moran's I with
        permutation significance; a maximum-likelihood spatial-lag model with a Durbin control;
        an attribute-similarity k-nearest-neighbour network as the rival to geography;
        partisanship-controlled issue residuals (OLS); record-based buckets with consistency and
        a midterm penalty; a side-agnostic playbook generator; a scorer with relevelling. 103
        tests, 98% branch coverage, mutation testing as the watchdog for hollow tests. One
        state's loader is days of work; the certified-total check is its lie detector.</p>
      </details>
    </div>
  </div>
</section>

<section class="wrap">
  <div class="act"><span class="n">4</span>What the data said</div>
  <h2>Eight results, including the two that said no.</h2>
  <p>In the order the argument built. Every chart is the research notebook's own output; the
  page cannot show a figure the analysis didn't produce.</p>
  <div class="findings">

    <div class="finding">
      <div>
        <div class="num">FINDING 1</div>
        <h3>We could not find the first domino. Twice.</h3>
        <p>The founding hope was a wave predictor: find where change starts, forecast where it
        spreads. The first attempt looked for counties that moved before their neighbors. Every
        county moves at once: swing is so clustered that leaders can't be told from followers.
        The second attempt, on 150 years of returns, looked for timing. The signal exists but is
        weak, spatially incoherent, and its extremes are tiny idiosyncratic counties, not hubs.</p>
        <p><b>So the flock turns together.</b> This is a result, not a failure, and it decided
        everything after it: the formation is what's predictable; the gust that turns it is
        not.</p>
      </div>
      <figure><img src="{leadlag}" alt="Lead-lag timing field across counties, weak and incoherent">
        <figcaption><b>The lead-lag test.</b> Own swing versus the neighbourhood one election
        ahead minus one behind, on the 1868–2024 spine. The field exists but is spatially
        incoherent, and its extremes are small counties, not influence hubs.</figcaption></figure>
    </div>

    <div class="finding">
      <div>
        <div class="num">FINDING 2</div>
        <h3>Party is a label. Disposition is the signal.</h3>
        <p>Over the long span the South and the Northeast swapped party labels while their
        underlying dispositions barely moved. So the thing to track is not the party vote but
        the disposition, and the cleanest place to see disposition stripped of party and
        personality is a direct vote on an issue: a ballot measure.</p>
      </div>
      <div>
        <div class="num">FINDING 3</div>
        <h3>False Bastions, on both axes.</h3>
        <p>Places whose issue vote runs ahead of their partisan lean: red on the surface,
        movable underneath. In Ohio, where the same 88 counties voted on abortion and cannabis
        the same day, a county that broke from its party on one broke on the other.</p>
        <div class="stat">r = 0.62</div>
        <p>The trait is a property of the place, not of one issue. And on the economic axis
        the pattern inverts the "What's the matter with Kansas" story: across ten minimum-wage
        measures, the gap between the issue vote and the party vote is largest where the state
        is reddest.</p>
      </div>
    </div>

    <div class="finding">
      <figure><img src="{ohio}" alt="Ohio counties: abortion resistance versus cannabis resistance">
        <figcaption><b>Ohio, November 2023.</b> Each dot is a county; the axes are how far it
        ran ahead of its partisanship on abortion and on cannabis. The cloud leans: persuadable
        on one, persuadable on the other.</figcaption></figure>
      <figure><img src="{minwage}"
        alt="Ten minimum-wage measures: economic dissonance against state partisan lean">
        <figcaption><b>Ten minimum-wage measures, 2006–2020.</b> Every one passed above its
        state's Democratic share, and the gap grows as the state gets redder (correlation
        −0.82). Self-interest crossing party, the opposite direction from abortion.
        </figcaption></figure>
    </div>

    <div class="finding">
      <div>
        <div class="num">FINDING 4</div>
        <h3>Geography beats similarity. Education is the runner-up.</h3>
        <p>The first worry from the brainstorm, the internet. Does change travel across borders
        or between places that resemble each other, college town to college town? We built a
        network of look-alike counties and raced it against plain adjacency.</p>
        <div class="stat">0.62 vs 0.28</div>
        <p>Geography wins decisively. "Ideas hop metro to metro" is not the story. Among the
        ways counties can resemble each other, education matters most and survives the
        controls. The second worry, that people move, turns out to reinforce the pattern:
        movers sort themselves toward places like the ones they left.</p>
      </div>
      <figure><img src="{horserace}"
        alt="Moran's I of residual swing under geographic versus similarity networks">
        <figcaption><b>The horse race.</b> Clustering of residual swing, 2004–2024, under
        geographic adjacency versus the best attribute-similarity network.</figcaption></figure>
    </div>

    <div class="finding">
      <div>
        <div class="num">FINDING 5</div>
        <h3>Realignments flicker. They don't ratchet.</h3>
        <p>Measured election by election, the education cleavage was invisible through 2012,
        lit up in 2016 and 2020, and vanished in 2024, while geography stayed the dominant
        organizer throughout. The "diploma divide" defined two elections' swings, not a new
        permanent map. Anyone who called it permanent in 2020 was wrong by 2024.</p>
      </div>
      <figure><img src="{flicker}" alt="Each network's organizing power, election by election">
        <figcaption><b>The flicker.</b> How strongly residual swing organizes along each
        network, per election. Education spikes in 2016 and 2020 and collapses in 2024.
        </figcaption></figure>
    </div>

    <div class="finding">
      <div>
        <div class="num">FINDING 6</div>
        <h3>A county has a personality, and it repeats.</h3>
        <p>Missouri's 21 certified measures on the same 116 jurisdictions let us ask whether
        the Ohio result was a fluke. Abortion resistance and minimum-wage resistance on the
        same 2024 ballot correlate at 0.52, a social measure and an economic one. Minimum wage
        2018 predicts minimum wage 2024 across six years. And a sharp caveat appeared: the
        trait coheres within an electorate type and barely across them. Who shows up is part of
        what a place is.</p>
      </div>
      <figure><img src="{grid}" alt="Issue-resistance correlation grid across Missouri measures">
        <figcaption><b>The resistance grid.</b> Correlations of partisanship-controlled
        residuals across Missouri measures. General-election measures cohere with each other;
        August primaries cohere with each other; the two blocks barely touch.</figcaption></figure>
    </div>

    <div class="finding">
      <div>
        <div class="num">FINDING 7</div>
        <h3>Partisanship is the bar. The same-issue residual clears it.</h3>
        <p>Before predicting anything we pretended each past measure hadn't happened and
        predicted it from the others. Partisanship alone misses the typical county by 3.69
        points. The fancier pooled "ideal point" we had designed scored 3.80 and lost.
        Partisanship plus half of a true sibling measure's residual scored 3.39. The method
        only helps when the history genuinely rhymes, so that's the only place we use it.</p>
      </div>
      <figure><img src="{panels}"
        alt="Five Missouri measures: predicted share against partisanship, model versus baseline">
        <figcaption><b>The five November measures.</b> Each dot a county: partisanship across,
        predicted share up. Solid dots are the registered model, faint dots partisanship alone.
        Where a solid dot sits above its twin, the record says the county runs ahead of its
        politics.</figcaption></figure>
    </div>

    <div class="finding">
      <div>
        <div class="num">FINDING 8</div>
        <h3>Deep time: the Populist reservoir discharged into the New Deal.</h3>
        <p>The brainstorm's hunch, tested on our own ground. The 1892 Populist vote did not
        become 1912 Progressivism; the places that carried the idea sat out a generation. But it
        did predict which counties broke from their forty-year trend in 1932, when the
        Depression and a willing party arrived. Structure waited forty years for a catalyst.
        The German persistence story, in Kansas and Nebraska.</p>
        <div class="stat">r = +0.38</div>
      </div>
      <figure><img src="{populist}"
        alt="1892 Populist share against the 1932 trend break, by county">
        <figcaption><b>The reservoir.</b> 1892 People's Party share against each county's 1932
        surprise from its own trend, outside the South.</figcaption></figure>
    </div>
  </div>
</section>

<section class="wrap">
  <div class="act"><span class="n">5</span>The plan for November</div>
  <h2>If the method is real, it should work on a vote that hasn't happened.</h2>
  <div class="col2">
    <div>
      <p>So we chose the hardest honest test available: Missouri's November 3, 2026 ballot.
      Five statewide measures, including the repeal of the 2024 abortion amendment and a
      referendum on the legislature's new congressional map, predicted for every one of the
      116 jurisdictions, plus statewide calls for Nevada and Massachusetts. Each statewide
      number is a range, because the national mood is the one thing the data says we cannot
      predict; each county is a point, because the formation holds.</p>
      <p>The plan also contains the prescriptive half: for each measure and for each side, a
      campaign plan priced in votes, sealed as fingerprints and revealed after the scorecard,
      so nobody can say the advice was written after the fact.</p>
      <a class="cta" href="forecast.html">Read the November receipt &rarr;</a>
    </div>
    <div>
      <p class="thesis">The yardstick was chosen before the data exists: our county errors
      against partisanship alone, a calibration band, and the statewide calls graded as the
      judgement they are.</p>
      <details><summary>For the technically minded</summary>
        <p>Model: logit-linear on 2024 two-party presidential share plus 0.5 × the same-issue
        analog's partisanship residual, levelled to a stated statewide bracket with 2018-midterm
        turnout weights. Pre-registered test: one-sided paired Wilcoxon on absolute county
        errors over 580 rows, both model and baseline relevelled to the certified statewide
        share. Diagnostics registered on the engine itself: Moran's I of the Amendment 3 errors
        (does the spatial layer hold information the model left out?) and the correlation of
        errors with the 2026/2018 turnout ratio (did composition drive the misses?). One
        Module 5 gauge: whether the 2026 partisan slope is at least as steep as 2024's.</p>
      </details>
    </div>
  </div>
</section>

<section class="locked"><div class="wrap">
  <div class="act"><span class="n">6</span>Locking it in</div>
  <h2>Registered {reg_date}. Never edited again.</h2>
  <div class="col2">
    <div>
      <p>On {reg_date}, every prediction file was copied to a registered name and committed to
      the public repository under the tag <code>registration-2026-11-03</code>. A test now
      re-hashes every registered file on every run of the test suite; any commit, on any
      branch, that changes a byte of them fails. The raw inputs are fingerprinted alongside, so
      anyone can confirm in December that the predictions came from exactly these certified
      files. The ten sealed playbooks exist only as digests until the scorecard is public.</p>
      <p>A later revision, if any, is a new dated file. The original still gets scored.</p>
    </div>
    <div>
      <p>Then the honest part of the method, the part the data taught us: wait. The flock
      turns on November 3. A provisional scorecard follows within a day from the election-night
      counts; the certified one when the Board of State Canvassers signs, usually early
      December. Win or lose, both go here.</p>
      <div class="slot">December 2026: the scorecard goes here.</div>
    </div>
  </div>
</div></section>

<section class="wrap">
  <div class="act"><span class="n">7</span>So what</div>
  <h2>Why an organization would buy this, and what it gets.</h2>
  <div class="col2">
    <div>
      <h3>The problem it solves</h3>
      <p>Campaigns for ballot measures spend money by county and by media market, but the
      tools they buy score individuals by party. On a ballot question the whole contest is the
      voters who split from their party, and a partisan score cannot see them by construction.
      So the budget gets split by instinct, the volunteers go where it's comfortable, and nobody
      is ever told afterward whether the map was right.</p>
      <h3>What you get</h3>
      <p><b>A county receipt</b> for every jurisdiction: its full record on every certified
      measure, next to the state's, checkable line by line. <b>A plan priced in votes</b>:
      where a point of persuasion buys the most, where showing up is the whole job, where to
      spend nothing, and how the money divides, with your own cost per vote plugged in.
      <b>The other side's best plan</b> from the same record, so you know where to expect them.
      <b>A statewide call with a range</b> and a straight answer to whether your money changes
      the odds or only the margin. And <b>a grade</b>: predictions written down before the vote
      and scored after it, against the obvious alternative.</p>
      <h3>What it costs you</h3>
      <p>Your state's certified county results file, which your election office already
      publishes, and one careful human decision about which side of the measure is which. The
      loader for a new state is days of work with a built-in lie detector: it must reproduce the
      state's certified totals before anything is built on it. No voter file, no polling, no
      license to a data broker.</p>
    </div>
    <div>
      <h3>What it is not</h3>
      <p>Not a replacement for your voter file; that still tells the canvasser who to knock.
      Not a promise of a lift. Nobody has yet followed one of these plans in a campaign, so
      nobody, including us, knows how many points doing so produces. In December we can say
      whether we could see the ground. We cannot say whether acting on it moves votes until
      someone acts on it.</p>
      <h3>Which is the offer</h3>
      <p>The first organization to run the plan becomes the measurement: the plan in half of
      a matched set of counties, nothing different in the other half, the effort logged by
      county, and the difference read in the certified results. That campaign learns what its
      effort bought, in votes, by county, for the first time. Every campaign after it gets that
      number with a receipt. We price the ground; the first client tells us all what the plow
      is worth.</p>
      <p class="thesis" style="margin-top:22px">Every consultant has a map. This one is priced
      in votes, shows you the other side's map too, and has been graded in public.</p>
      <p>To see the idea at the smallest scale, one volunteer with one free Saturday and a tank
      of gas, the Kansas example is the place to start.</p>
      <a class="cta" href="demo.html">The art of the possible &rarr;</a>
    </div>
  </div>
</section>

<footer><div class="wrap">
  Every figure on this page is a research notebook's own rendered output, computed by
  <b>tested code</b> from certified public records. The notebooks, the findings document, the
  prediction files and the registration tag are in the public repository.
  <p style="margin-top:22px"><a class="backlink" href="./">&larr; Back to the live map</a>
  &nbsp;·&nbsp; <a class="backlink" href="forecast.html">The November receipt &rarr;</a>
  &nbsp;·&nbsp; <a class="backlink" href="demo.html">The art of the possible &rarr;</a></p>
</div></footer>

</body>
</html>
"""


if __name__ == "__main__":
    main()
