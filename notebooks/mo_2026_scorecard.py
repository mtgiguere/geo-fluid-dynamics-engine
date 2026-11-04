# ---
# jupyter:
#   jupytext:
#     formats: py:percent,ipynb
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Missouri, November 3 2026: the scorecard
#
# *An analysis notebook for the Geo-Fluid Dynamics Engine. TDD-exempt EDA:
# every grade comes from the tested `geofluid.scoring` functions that were
# frozen BEFORE the election; this notebook only feeds them the results and
# prints what they say.*
#
# ## What this notebook is
#
# On 2026-10-14 we froze county-by-county predictions for Missouri's five
# November measures (`data/predictions/*_REGISTERED_2026-10-14.csv`, tag
# `registration-2026-11-03`), then added two dated supplements: a stricter
# statistical test after an outside review (2026-10-15), and a head-to-head
# against On Point Politics' published county forecasts (2026-11-02, the day
# before the vote). This notebook scores every one of those calls exactly as
# written, in the order of `docs/RUNBOOK_2026.md` step 2. Nothing here edits a
# registered file; the freeze guard would fail the test suite if anything did.
#
# **Status is read from the results page itself** (the first printed line):
# "Unofficial Results" on election night makes this a **PROVISIONAL**
# scorecard; once the Board of State Canvassers certifies, re-fetch, re-run,
# and the label flips to **CERTIFIED** on its own. The certified run is the one
# that goes into `docs/FINDINGS.md` and unseals the playbooks (§10).
#
# ---
#
# ### For the field: how to read this notebook
#
# Before the election we wrote down, for every county, what share of voters
# would pick each side, and how we'd be graded. Now the votes are in. This is
# the grading, with nothing changed after the fact. Wins and losses are both
# printed, because a forecaster who only shows wins is selling something.
#
# Four words, in plain English:
#
# * **Level.** The statewide number: "55 out of 100 Missourians vote NO."
#   We gave a range (a *bracket*) for each measure. Inside it = a hit.
# * **Pattern.** Which counties come in above or below the state, and by how
#   much. This is what a campaign actually uses to decide where to go, and it
#   is the main thing we're graded on.
# * **Relevel.** Before grading the pattern, we slide every forecast up or
#   down so its statewide total matches the real one. That way a good or bad
#   statewide guess (or a national wave) can't make the county map look
#   better or worse than it was. Same trick for us, the baseline and On Point.
# * **Baseline.** The "lazy" forecast: assume every county votes exactly its
#   party. If we can't beat that, our extra work wasn't worth anything.

# %%
import re
from math import comb, erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

from geofluid.ingest.county_geometry import county_shapefile_to_geojson
from geofluid.ingest.referendum import parse_mo_canvass, parse_mo_enr_results
from geofluid.scoring import (
    classify_coupling,
    coupling_slope,
    relevel,
    score_counties,
    score_level,
    score_summary,
)
from geofluid.seal import verify_manifest
from geofluid.spatial.moran import morans_i
from geofluid.spatial.weights import county_adjacency

ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "pyproject.toml").exists())
RAW = ROOT / "data/raw"
PRED = ROOT / "data/predictions"
ENR_PREFIX = "enr_mo_20261103"
RNG = np.random.default_rng()  # no seed: report the spread, not a lucky draw
DRAWS = 10_000
pd.set_option("display.width", 200)


def logit(p: "pd.Series[float]") -> "pd.Series[float]":
    return np.log(p / (1 - p))


def inv_logit(z: "pd.Series[float]") -> "pd.Series[float]":
    return 1 / (1 + np.exp(-z))


# %% [markdown]
# ## 1. The results, read from the Secretary of State's portal
#
# Fetched with `scripts/fetch_mo_enr.cjs` (RUNBOOK step 1; the map referendum
# is listed on the portal as **"Proposition A"**). Each page is parsed by
# `parse_mo_enr_results`, which refuses any page whose jurisdictions do not
# sum exactly to its own statewide block. The name-to-FIPS map is the one the
# predictions notebook used, so the joins are identical.

# %%
mit = pd.read_csv(
    RAW / "countypres_2000-2024.csv", dtype={"county_fips": "string"}, low_memory=False
)
mo_rows = mit[mit["state_po"] == "MO"]
names = mo_rows[["county_name", "county_fips"]].drop_duplicates()
fips_map = {
    str(n).title(): str(f).zfill(5)
    for n, f in zip(names["county_name"], names["county_fips"], strict=True)
}
fips_map.update(
    {"Kansas City": "2938000", "McDonald": "29119", "St. Louis": "29189", "De Kalb": "29063"}
)
county_name = {v: k for k, v in fips_map.items()}
county_name["29189"] = "St. Louis County"

# measure_id -> (portal page slug, On Point slug)
PAGES = {
    "mo_20261103_amendment_3": ("constitutional_amendment_no_3", "amendment-3"),
    "mo_20261103_amendment_6": ("constitutional_amendment_no_6", "amendment-6"),
    "mo_20261103_amendment_7": ("constitutional_amendment_no_7", "amendment-7"),
    "mo_20261103_amendment_8": ("constitutional_amendment_no_8", "amendment-8"),
    "mo_20261103_map_referendum": ("proposition_a", "proposition-a"),
}
SHORT = {
    "mo_20261103_amendment_3": "Amdt 3",
    "mo_20261103_amendment_6": "Amdt 6",
    "mo_20261103_amendment_7": "Amdt 7",
    "mo_20261103_amendment_8": "Amdt 8",
    "mo_20261103_map_referendum": "Prop A (map)",
}

reg = pd.read_csv(PRED / "mo_2026-11-03_REGISTERED_2026-10-14.csv", dtype={"fips": str})
side = reg.groupby("measure_id")["progressive_side"].first()

banners, actual, votes, yes_share = set(), {}, {}, {}
for mid, (page, _) in PAGES.items():
    text = (RAW / f"{ENR_PREFIX}_{page}.txt").read_text(encoding="utf-8")
    banner = re.search(r"^(Unofficial Results|Official Results[^\n]*)$", text, flags=re.MULTILINE)
    stamp = re.search(r"^as of [^\n]+$", text, flags=re.MULTILINE)
    banners.add(f"{banner.group(1) if banner else '??'} | {stamp.group(0) if stamp else '??'}")
    panel = parse_mo_enr_results(text, fips_map).set_index("fips")
    actual[mid] = panel["no_share"] if side[mid] == "no" else 1 - panel["no_share"]
    votes[mid] = panel["total_votes"]
    yes_share[mid] = float(panel["yes_votes"].sum() / panel["total_votes"].sum())
actual = pd.DataFrame(actual)
votes = pd.DataFrame(votes)
statewide = (actual * votes).sum() / votes.sum()

STATUS = "CERTIFIED" if all(b.startswith("Official") for b in banners) else "PROVISIONAL"
print(f"STATUS: {STATUS}")
for b in sorted(banners):
    print("  portal:", b)
print(f"{actual.shape[0]} jurisdictions x {actual.shape[1]} measures; registered rows: {len(reg)}")
print(
    pd.DataFrame(
        {
            "progressive_side": side,
            "statewide_progressive": statewide.round(4),
            "statewide_yes": pd.Series(yes_share).round(4),
            "outcome": pd.Series(yes_share).map(lambda y: "PASSED" if y > 0.5 else "FAILED"),
        }
    ).rename(index=SHORT)
)

# %% [markdown]
# **For the field — what you just saw.** The state's own count for each
# measure, checked to the last vote against its statewide total. "Progressive
# side" is just which answer we tracked (NO on four, YES on Amendment 6); it
# is a label for the side the measure's geography puts on the
# Democratic-leaning end, not an endorsement. The STATUS line matters: until
# the state certifies, these are unofficial, and every grade below is
# provisional.

# %% [markdown]
# ## 2. Level: the seven statewide brackets
#
# Five Missouri brackets from the registered file, plus the two statewide-only
# calls (Nevada Question 6, Massachusetts Question 8). Those two have no county
# file; their certified shares are typed in below from each state's election
# office when available (`None` = not yet in).

# %%
OTHER_STATES = {  # measure_id -> certified progressive share (source in the comment)
    "nv_20261103_question_6": None,  # Nevada SoS — pending
    "ma_20261103_question_8": None,  # MA Secretary of the Commonwealth — pending
}
levels = reg.groupby("measure_id")[["level_low", "level_central", "level_high"]].first()
level_rows = []
for mid, row in levels.iterrows():
    g = score_level(
        low=row.level_low, central=row.level_central, high=row.level_high, actual=statewide[mid]
    )
    level_rows.append(
        {
            "measure": SHORT[mid],
            "bracket": f"{row.level_low:.3f} - {row.level_high:.3f}",
            "central": row.level_central,
            "actual": round(statewide[mid], 4),
            "miss_points": round(100 * g.level_error, 1),
            "in_bracket": "HIT" if g.in_bracket else "MISS",
        }
    )
so = pd.read_csv(PRED / "statewide_only_2026-11-03_REGISTERED_2026-10-14.csv").set_index(
    "measure_id"
)
for mid, row in so.iterrows():
    a = OTHER_STATES[mid]
    g = (
        score_level(low=row.level_low, central=row.level_central, high=row.level_high, actual=a)
        if a is not None
        else None
    )
    level_rows.append(
        {
            "measure": mid,
            "bracket": f"{row.level_low:.3f} - {row.level_high:.3f}",
            "central": row.level_central,
            "actual": a,
            "miss_points": None if g is None else round(100 * g.level_error, 1),
            "in_bracket": "pending" if g is None else ("HIT" if g.in_bracket else "MISS"),
        }
    )
level_table = pd.DataFrame(level_rows)
print(level_table.to_string(index=False))
moved_no = {
    SHORT[m]: float(
        round(100 * ((statewide[m] - levels.level_central[m]) * (1 if side[m] == "no" else -1)), 1)
    )
    for m in levels.index
}
print("\nshift toward NO vs our central call (points):", moved_no)

# %% [markdown]
# **For the field — what you just saw.** "Miss" is our middle guess minus the
# real result, in points out of 100 (negative = the side we tracked did better
# than we said). A HIT means the result landed inside the range we published.
#
# The last line is worth a second look: it measures, for each measure, how
# far the real result moved toward NO compared with our middle guess,
# whichever side we tracked. If every number is positive, NO did better than
# we expected everywhere, including Amendment 6, where the side we tracked
# was YES. A purely Democratic wave would have pushed Amendment 6's YES *up*,
# not down. So a general "when in doubt, vote No" lean is a live explanation
# alongside the national mood (roll-off in §9 is one check on it).
#
# *For the decision-maker:* brackets are judgement, not model output, and are
# graded as such. A miss on the level does not touch the county pattern grade
# below; the relevel step separates them on purpose.

# %% [markdown]
# ## 3. Pattern: the registered test (H1) and its supplement
#
# Both the registered prediction and the partisanship-only baseline are
# relevelled to the actual statewide share with `scoring.relevel` (turnout
# weights = each jurisdiction's 2026 votes cast on the measure, **as shares
# summing to 1**: `relevel` finds the logit shift at which the weighted SUM of
# shares equals the target, so raw vote counts would be wrong). Then
# `score_counties` / `score_summary` per measure.

# %%
wshare = votes / votes.sum()
scored, summaries = [], {}
for mid in PAGES:
    g = reg[reg["measure_id"] == mid].set_index("fips")
    rl = g.copy()
    for col in ("pred_progressive_share", "baseline_partisan_only"):
        rl[col] = relevel(g[col], target=statewide[mid], weights=wshare[mid])
    sc = score_counties(rl.reset_index(), actual[mid])
    sc["measure_id"] = mid
    scored.append(sc)
    summaries[SHORT[mid]] = score_summary(sc)
scored = pd.concat(scored, ignore_index=True)
summary = pd.DataFrame(summaries).T
print(summary[["n_counties", "rmse_model", "rmse_baseline", "skill_vs_baseline"]].round(4))
total = score_summary(scored)
print(
    f"\nALL {len(scored)} ROWS: RMSE ours {total.rmse_model:.4f} vs baseline "
    f"{total.rmse_baseline:.4f}; skill {total.skill_vs_baseline:+.3f}"
)


# %% [markdown]
# ### The tests
#
# * **Registered (2026-10-14):** one-sided paired Wilcoxon signed-rank on
#   |error_ours| − |error_baseline| over all 580 rows, alpha 0.05. Labelled
#   *anti-conservative* by the 2026-10-15 supplement: a county's errors are
#   correlated across its five measures, so 580 rows are not 580 independent
#   pieces of evidence.
# * **Preferred (2026-10-15):** county-blocked bootstrap of the skill score —
#   resample the 116 jurisdictions with replacement, all five measures
#   travelling together, 10,000 draws. Call: skill > 0 with the 95% interval
#   excluding 0. Plus per-measure one-sided Wilcoxon tests (116 rows each),
#   Holm-adjusted.
#
# The Wilcoxon here is the normal approximation with tie correction (scipy is
# not a project dependency). That is also what `scipy.stats.wilcoxon` uses at
# these sample sizes (its exact method is only for n ≤ 50 without ties).
# The bootstrap is unseeded on purpose: rerunning moves the third decimal,
# and that wobble is the honest size of the simulation error.


# %%
def wilcoxon_less(d: "pd.Series[float]") -> tuple[float, float]:
    """One-sided signed-rank test that the paired differences d are shifted
    below zero. Zeros dropped (Wilcoxon's convention), average ranks for
    ties, tie-corrected variance, normal approximation. Returns (z, p)."""
    d = d[d != 0]
    n = len(d)
    ranks = d.abs().rank()
    w_plus = float(ranks[d > 0].sum())
    mean = n * (n + 1) / 4
    ties = d.abs().value_counts()
    var = n * (n + 1) * (2 * n + 1) / 24 - float(((ties**3) - ties).sum()) / 48
    z = (w_plus - mean) / sqrt(var)
    return z, 0.5 * (1 + erf(z / sqrt(2)))


def holm(pvalues: "pd.Series[float]") -> "pd.Series[float]":
    """Holm step-down adjusted p-values (monotone, capped at 1)."""
    order = pvalues.sort_values()
    m = len(order)
    adj = np.maximum.accumulate([(m - i) * p for i, p in enumerate(order)])
    return pd.Series(np.minimum(adj, 1.0), index=order.index).reindex(pvalues.index)


def blocked_bootstrap(
    errors: "dict[str, pd.DataFrame]", blocks: "pd.Index", draws: int = DRAWS
) -> np.ndarray:
    """Skill = 1 - sqrt(SSE_model / SSE_reference) over all rows, with whole
    jurisdictions (every measure at once) resampled with replacement. Each
    frame in `errors` is jurisdiction x measure; 'model' and 'reference'."""
    sse_m = (errors["model"] ** 2).sum(axis=1).reindex(blocks).to_numpy()
    sse_r = (errors["reference"] ** 2).sum(axis=1).reindex(blocks).to_numpy()
    counts = RNG.multinomial(len(blocks), np.full(len(blocks), 1 / len(blocks)), size=draws)
    return 1 - np.sqrt((counts @ sse_m) / (counts @ sse_r))


def report_bootstrap(label: str, point: float, boot: np.ndarray) -> None:
    lo, hi = np.percentile(boot, [2.5, 97.5])
    verdict = (
        "MET (interval above 0)"
        if lo > 0
        else ("REVERSED (interval below 0)" if hi < 0 else "NOT MET (interval straddles 0)")
    )
    print(
        f"{label}: skill {point:+.3f}, 95% [{lo:+.3f}, {hi:+.3f}], "
        f"share of draws <= 0: {(boot <= 0).mean():.3f} -> {verdict}"
    )


diff = scored["abs_error"] - scored["baseline_error"].abs()
z, p = wilcoxon_less(diff)
print(
    f"H1, registered 580-row Wilcoxon (anti-conservative): z = {z:.2f}, one-sided p = {p:.2g} "
    f"-> {'MET' if p < 0.05 else 'NOT MET'}; ours closer on {(diff < 0).mean():.0%} of rows"
)

err = scored.pivot(index="fips", columns="measure_id", values="error")
base_err = scored.pivot(index="fips", columns="measure_id", values="baseline_error")
boot = blocked_bootstrap({"model": err, "reference": base_err}, err.index)
report_bootstrap("Supplement, 116-block bootstrap vs baseline", total.skill_vs_baseline, boot)

per = {}
for mid in PAGES:
    s = scored[scored["measure_id"] == mid]
    per[SHORT[mid]] = wilcoxon_less(s["abs_error"] - s["baseline_error"].abs())[1]
per = pd.Series(per)
print(
    pd.DataFrame(
        {
            "skill": summary["skill_vs_baseline"].round(3),
            "p_one_sided": per.map(lambda x: f"{x:.3g}"),
            "p_holm": holm(per).map(lambda x: f"{x:.3g}"),
        }
    )
)

# %% [markdown]
# **For the field — what you just saw.** "Skill" is how much smaller our
# average county miss was than the lazy party-only forecast: +0.05 means our
# misses were about 5% smaller; 0 means no better; negative means worse. The
# bootstrap asks "if we'd had a different but similar set of counties, would
# we still come out ahead?" by re-drawing the counties 10,000 times. If even
# the unlucky draws stay above zero, the edge is real, not a fluke.
#
# The per-measure lines say *where* the edge came from. That is the useful
# part for a campaign: a method that helps on one kind of question and not
# another tells you when to trust it.
#
# *For the decision-maker:* the edge over party is what you'd be paying for.
# Read its size, not only its significance: a small, reliable edge across 116
# places is worth money; a big edge on one measure and none on another means
# "use this where the precedent is strong."

# %% [markdown]
# ## 4. Calibration: did our county ranges hold the truth 90% of the time?
#
# Two numbers. The **registered** one counts rows inside the published
# `[pred_low_90, pred_high_90]`; those ranges carry the statewide bracket, so
# they mostly re-grade the level call. The **supplement's** preferred one
# (2026-10-15) asks only about the pattern: is the actual inside the
# relevelled prediction ± 1.645 × 0.147 on the logit scale? Call: 0.85–0.95.

# %%
raw_cov = {}
for mid in PAGES:
    g = reg[reg["measure_id"] == mid]
    a = g["fips"].map(actual[mid])
    raw_cov[SHORT[mid]] = float(((a >= g["pred_low_90"]) & (a <= g["pred_high_90"])).mean())
half = 1.645 * 0.147
z_pred, z_act = logit(scored["pred_progressive_share"]), logit(scored["actual"])
scored["in_band_relevelled"] = (z_act >= z_pred - half) & (z_act <= z_pred + half)
cal = pd.DataFrame(
    {
        "registered_coverage": pd.Series(raw_cov),
        "relevelled_coverage": scored.groupby("measure_id")["in_band_relevelled"]
        .mean()
        .rename(index=SHORT),
        "level": level_table.set_index("measure")["in_bracket"],
    }
).dropna(subset=["registered_coverage"])
print(cal.round(3))
rel_all = float(scored["in_band_relevelled"].mean())
print(
    f"\nALL ROWS: registered {np.mean(list(raw_cov.values())):.3f}; "
    f"relevelled {rel_all:.3f} -> "
    + ("calibrated" if 0.85 <= rel_all <= 0.95 else ("understated" if rel_all < 0.85 else "padded"))
)

# %% [markdown]
# **For the field — what you just saw.** For each county we published a range
# we expected the result to fall inside nine times out of ten. The first
# column is the honest raw count against those published ranges; where the
# statewide guess missed (the "level" column), whole counties fall outside
# together, which is why those columns drop. The second column fixes the
# statewide total first and asks only "did we have each county's position
# right, give or take our stated error?" Near 0.90 means our stated
# uncertainty was honest; well below means we were overconfident about the
# county map; well above means we padded it.

# %% [markdown]
# ## 5. Module 5 proposition: is Amendment 3 as party-coupled as 2024?
#
# Registered call: HOLD-or-STEEPEN against the 2024 slope 0.7974, tolerance
# 0.05 (OLS slope of logit(NO) on logit(2024 Dem two-party), `coupling_slope`).
# Kansas City is excluded as in the registration (it has no county 2024
# baseline of its own in the slope fit's universe).

# %%
a3 = "mo_20261103_amendment_3"
dem24 = reg[reg["measure_id"] == a3].set_index("fips")["dem_two_party_2024"]
idx = actual.index.drop("2938000")
slope = coupling_slope(actual.loc[idx, a3], dem24.loc[idx])
verdict = classify_coupling(slope, reference=0.7974, tolerance=0.05)
print(
    f"slope 2026 = {slope:.3f} vs 2024 = 0.797 -> {verdict}; "
    f"call HOLD-or-STEEPEN {'MET' if verdict in ('HOLD', 'STEEPEN') else 'NOT MET'}"
)

# %% [markdown]
# **For the field — what you just saw.** This asks whether the abortion vote
# followed party lines as tightly as it did two years ago. HOLD means about
# the same: the issue did not melt into party, and it did not break away
# from it either. That matters for the next section: if the vote had snapped
# back to party (RELAX would be the opposite: looser), the counties that
# crossed party in 2024 would have stopped crossing.

# %% [markdown]
# ## 6. Diagnostic: do our Amendment 3 misses cluster on the map?
#
# Registered: Moran's I of the relevelled Amendment 3 county errors under
# queen adjacency, significant at 0.05 by permutation. Kansas City is folded
# into Jackson County (vote-weighted) because it has no polygon of its own.
# Permutation: shuffle the errors across the same 115 counties 9,999 times.

# %%
geo = county_shapefile_to_geojson(RAW / "cb_2021" / "cb_2021_us_county_500k.shp")
geo["features"] = [f for f in geo["features"] if str(f["id"]).startswith("29")]
adj = county_adjacency(geo)


def fold_kc(s: "pd.Series[float]", w: "pd.Series[float]") -> "pd.Series[float]":
    """Fold Kansas City into Jackson County, weighted by w (2026 votes)."""
    s = s.copy()
    j, k = "29095", "2938000"
    s[j] = (s[j] * w[j] + s[k] * w[k]) / (w[j] + w[k])
    return s.drop(k)


a3_err = fold_kc(err[a3], votes[a3])
i_obs = morans_i(a3_err, adj)
perm = np.array(
    [
        morans_i(pd.Series(RNG.permutation(a3_err.to_numpy()), index=a3_err.index), adj)
        for _ in range(9_999)
    ]
)
p_perm = (1 + (perm >= i_obs).sum()) / (1 + len(perm))
print(
    f"Moran's I of Amendment 3 errors = {i_obs:.3f}, permutation p = {p_perm:.4f} -> "
    + ("MET: errors cluster" if i_obs > 0 and p_perm < 0.05 else "NOT MET: no clustering shown")
)

# %% [markdown]
# **For the field — what you just saw.** If our misses sit in clumps (a run of
# neighbouring counties all a bit too high, say), something local is going on
# that our model doesn't see, and the map itself would have helped: the
# "geo" in geo-fluid. If the misses are scattered like salt, there's no
# shared local factor left over, and the map's job is describing, not
# predicting. Moran's I is near 0 for scattered, positive for clumped.

# %% [markdown]
# ## 7. Diagnostic: did a changed electorate drive the misses?
#
# Registered: Pearson r between the relevelled Amendment 3 error and each
# jurisdiction's turnout ratio (2026 votes cast on Amendment 3 / 2018 votes
# cast on Amendment 1, Clean Missouri — the last midterm statewide measure).
# Call: |r| < 0.3. Positive r = we over-predicted where turnout grew.

# %%
import pdfplumber  # noqa: E402  (only this diagnostic needs the 2018 canvass)

with pdfplumber.open(RAW / "ActualResults-November62018-FINAL.pdf") as pdf:
    pages18 = [page.extract_text() or "" for page in pdf.pages]
cast18 = parse_mo_canvass(pages18, "Amendment 1", fips_map).set_index("fips")["total_votes"]
ratio = (votes[a3] / cast18).dropna()
r = float(np.corrcoef(err[a3].reindex(ratio.index), ratio)[0, 1])
print(
    f"turnout ratio 2026/2018: median {ratio.median():.2f} "
    f"(range {ratio.min():.2f}-{ratio.max():.2f}); r(error, ratio) = {r:+.3f} -> "
    + ("MET: composition not the dominant miss" if abs(r) < 0.3 else "NOT MET: model turnout")
)

# %% [markdown]
# **For the field — what you just saw.** Our forecast assumed the people who
# show up in 2026 look like the people who showed up in the last midterm. The
# ratio is how many voted this time per voter in 2018, county by county. If
# our misses lined up with where turnout jumped or fell (a big r, either
# sign), "who showed up" was the story and we'd need to forecast turnout
# next. A small r means our assumption held well enough.

# %% [markdown]
# ## 8. The external benchmark: On Point Politics (2026-11-02 supplement)
#
# First the evidence: their captured pages, screenshots and extracted county
# table (kept off-repo, third-party content) must hash to what we registered
# the day before the vote.

# %%
CAPTURE = RAW / "onpoint_20261102"
evidence = pd.read_csv(PRED / "onpoint_benchmark_evidence_2026-11-02.csv")
check = verify_manifest(evidence[["file", "sha256"]], root=CAPTURE)
print(f"capture verified: {int(check['ok'].sum())}/{len(check)} files match the registered hashes")
if not check["ok"].all():
    raise RuntimeError(f"On Point capture does not match its registration:\n{check}")

# %% [markdown]
# The comparison, exactly as registered: their county Yes/(Yes+No), flipped to
# No where our side is NO; joined on FIPS; Kansas City folded into Jackson for
# ours and for the result (vote-weighted, 2026 votes); ours, theirs and the
# baseline each relevelled to the actual statewide share over the 115
# jurisdictions.

# %%
op = pd.read_csv(CAPTURE / "onpoint_mo_counties_20261102.csv", dtype={"fips": str})
fold = {"ours": {}, "theirs": {}, "base": {}, "actual": {}}
for mid, (_, slug) in PAGES.items():
    t = op[op["slug"] == slug].set_index("fips")
    their_yes = t["yes"] / (t["yes"] + t["no"])
    w = votes[mid]
    a115 = fold_kc(actual[mid], w)
    w115 = w.drop("2938000")
    w115["29095"] = w["29095"] + w["2938000"]
    w115 = w115 / w115.sum()
    s = scored[scored["measure_id"] == mid].set_index("fips")
    fold["ours"][mid] = fold_kc(s["pred_progressive_share"], w)
    fold["base"][mid] = fold_kc(s["baseline_partisan_only"], w)
    theirs = (1 - their_yes if side[mid] == "no" else their_yes).reindex(a115.index)
    fold["theirs"][mid] = relevel(theirs, target=statewide[mid], weights=w115)
    fold["actual"][mid] = a115
F = {k: pd.DataFrame(v) for k, v in fold.items()}
missing = F["theirs"].isna().sum().sum()
print(f"115 x 5 joined; missing On Point cells: {missing}")

e_ours, e_theirs, e_base = (
    F["ours"] - F["actual"],
    F["theirs"] - F["actual"],
    F["base"] - F["actual"],
)


def rmse(e: "pd.DataFrame | pd.Series") -> float:
    return float(np.sqrt(np.nanmean(np.asarray(e, dtype=float) ** 2)))


bench = pd.DataFrame(
    {
        "rmse_ours": {SHORT[m]: rmse(e_ours[m]) for m in PAGES},
        "rmse_onpoint": {SHORT[m]: rmse(e_theirs[m]) for m in PAGES},
        "rmse_baseline": {SHORT[m]: rmse(e_base[m]) for m in PAGES},
    }
)
bench["skill_ours_vs_onpoint"] = 1 - bench.rmse_ours / bench.rmse_onpoint
bench["skill_onpoint_vs_baseline"] = 1 - bench.rmse_onpoint / bench.rmse_baseline
print(bench.round(4))
point = 1 - rmse(e_ours) / rmse(e_theirs)
boot_op = blocked_bootstrap({"model": e_ours, "reference": e_theirs}, e_ours.index)
report_bootstrap("\nOurs vs On Point, 115-block bootstrap", point, boot_op)
op_skill = 1 - rmse(e_theirs) / rmse(e_base)
print(f"On Point's own skill vs the party-only baseline, all rows: {op_skill:+.3f}")


# %% [markdown]
# ### Where the two models disagreed most
#
# Registered: Amendment 3 jurisdictions where ours and theirs differ by ≥ 5
# points after relevelling; share where the actual is closer to ours; call >
# 0.5; one-sided exact binomial (descriptive only if fewer than 10). All five
# measures pooled as a secondary line.


# %%
def binom_greater(k: int, n: int) -> float:
    """Exact one-sided P(X >= k) for X ~ Binomial(n, 0.5)."""
    return sum(comb(n, i) for i in range(k, n + 1)) / 2**n


def disagreement(mids: "list[str]") -> tuple[int, int, pd.DataFrame]:
    rows = []
    for m in mids:
        gap = (F["ours"][m] - F["theirs"][m]).abs()
        for f in gap[gap >= 0.05].index:
            rows.append(
                {
                    "measure": SHORT[m],
                    "fips": f,
                    "county": county_name.get(f, f),
                    "actual": F["actual"][m][f],
                    "ours": F["ours"][m][f],
                    "onpoint": F["theirs"][m][f],
                    "baseline": F["base"][m][f],
                }
            )
    d = pd.DataFrame(rows)
    d["closer_to_ours"] = (d.ours - d.actual).abs() < (d.onpoint - d.actual).abs()
    return int(d.closer_to_ours.sum()), len(d), d


k, n, dis_a3 = disagreement([a3])
print(
    f"Amendment 3: {n} disagreement jurisdictions, {k} closer to ours ({k / n:.0%}); "
    + (f"exact one-sided p = {binom_greater(k, n):.2g}" if n >= 10 else "descriptive only (n < 10)")
)
k5, n5, dis_all = disagreement(list(PAGES))
print(
    f"All five pooled (secondary): {n5} rows, {k5} closer to ours ({k5 / n5:.0%}); "
    f"exact one-sided p = {binom_greater(k5, n5):.2g}"
)
print(
    dis_all.groupby("measure")["closer_to_ours"]
    .agg(["sum", "count"])
    .rename(columns={"sum": "closer_to_ours", "count": "n"})
)
show = dis_a3.assign(gap=(dis_a3.ours - dis_a3.onpoint).abs()).nlargest(12, "gap")
print((show.set_index("county")[["actual", "ours", "onpoint", "baseline"]] * 100).round(1))

# %% [markdown]
# ### The statewide calls side by side (descriptive)

# %%
HEADLINE_YES = {
    "amendment-3": 48.2,
    "amendment-6": 54.7,
    "amendment-7": 66.6,
    "amendment-8": 75.9,
    "proposition-a": 49.3,
}  # their page headline, 2026-11-02
lv = []
for mid, (_, slug) in PAGES.items():
    t = op[op["slug"] == slug]
    table_yes = 100 * t["yes"].sum() / (t["yes"] + t["no"]).sum()

    def prog(y: float, m: str = mid) -> float:
        return 100 - y if side[m] == "no" else y

    act = 100 * statewide[mid]
    ours_c = 100 * levels.level_central[mid]
    passed = yes_share[mid] > 0.5
    ours_pass = (ours_c < 50) if side[mid] == "no" else (ours_c > 50)
    lv.append(
        {
            "measure": SHORT[mid],
            "actual": round(act, 1),
            "ours": round(ours_c, 1),
            "onpoint_headline": round(prog(HEADLINE_YES[slug]), 1),
            "onpoint_table": round(prog(table_yes), 1),
            "err_ours": round(abs(ours_c - act), 1),
            "err_onpoint_headline": round(abs(prog(HEADLINE_YES[slug]) - act), 1),
            "outcome_ours": "right" if ours_pass == passed else "WRONG",
            "outcome_onpoint": "right" if (HEADLINE_YES[slug] > 50) == passed else "WRONG",
        }
    )
print("(all on the progressive side, points out of 100)")
print(pd.DataFrame(lv).to_string(index=False))

# %% [markdown]
# **For the field — what you just saw.** On Point Politics is a professional
# forecasting site that published county numbers for these same five
# measures. Their county map is built from party, age, education, race and
# density, pulled toward polls. Ours is built from party plus each county's own
# record on past ballot questions. We wrote down how we'd be compared the day
# before the vote, and saved copies of their pages with the Internet Archive
# so nobody can say the comparison was rigged.
#
# Three results, each answering a different question:
#
# * **The whole county map** (skill vs On Point): whose county-by-county
#   picture was closer overall, after both are slid to the real statewide
#   total. If the 95% range straddles zero, neither of us showed a real edge.
# * **The counties where we disagreed** — the ones that decide where a
#   campaign spends its Saturdays. This is the sharpest test of the core
#   idea: does a red county that crossed party on abortion in 2024 do it
#   again (our bet), or fall back to its party label (theirs)?
# * **The statewide calls**, which is what the news reports.
#
# *For the decision-maker:* the disagreement counties are where the two
# forecasts would have sent you to different places. Read that line as
# "when the two forecasts disagree about a county, which one should I
# believe?" and the per-measure breakdown as "for which kinds of question?"

# %% [markdown]
# ## 9. Roll-off: who skipped the measures?
#
# RUNBOOK step 8: votes cast on each measure vs the top of the ticket. In
# 2026 Missouri's top statewide race is **State Auditor**; its county table
# has three candidate columns, parsed ad hoc here and checked against the
# page's own statewide total.

# %%
aud = (RAW / f"{ENR_PREFIX}_state_auditor.txt").read_text(encoding="utf-8")
aud_total = int(re.search(r"Total Votes:\t([\d,]+)", aud).group(1).replace(",", ""))
rows, in_table = {}, False
for line in aud.splitlines():
    if line.startswith("County\t"):
        in_table = True
        continue
    m = (
        re.match(r"^([A-Za-z][A-Za-z .'\-]*?)((?:\t[\d,]+)+)$", line.rstrip("\r"))
        if in_table
        else None
    )
    if m:
        rows[fips_map[m.group(1)]] = sum(
            int(x.replace(",", "")) for x in m.group(2).split("\t")[1:]
        )
aud_cast = pd.Series(rows)
if aud_cast.sum() != aud_total:
    raise ValueError(f"auditor table sums to {aud_cast.sum():,}, page says {aud_total:,}")
print(f"State Auditor: {aud_total:,} votes, {len(aud_cast)} jurisdictions (reconciles)")
rolloff = pd.DataFrame({SHORT[m]: 1 - votes[m] / aud_cast for m in PAGES})
state_rolloff = pd.Series({SHORT[m]: 1 - votes[m].sum() / aud_total for m in PAGES})
print("statewide roll-off (share of auditor voters who skipped the measure):")
print((100 * state_rolloff).round(2).to_string())
# Is skipping related to where NO over-performed us? Pattern error vs roll-off, per measure.
corr = {
    SHORT[m]: float(np.corrcoef(err[m].reindex(aud_cast.index), rolloff[SHORT[m]])[0, 1])
    for m in PAGES
}
print(
    "\nr(our relevelled county error, county roll-off):", {k: round(v, 3) for k, v in corr.items()}
)

# %% [markdown]
# **For the field — what you just saw.** Roll-off is the share of people who
# voted for State Auditor but left a measure blank: a rough gauge of
# confusion or "not my business." A measure with high roll-off is one where
# a lot of voters didn't know what to make of it, and confused voters
# historically lean No. The last line asks whether the counties where we
# missed are the counties where people skipped; a clear relationship would
# point to confusion, not opinion, as the driver of those misses.

# %% [markdown]
# ## 10. The sealed playbooks (certified pass only)
#
# RUNBOOK §4: the ten playbooks sealed on 2026-10-14 are unsealed only after
# certification, verified byte-for-byte against
# `SEALED_MANIFEST_REGISTERED_2026-10-14.csv`, and graded: did the counties
# flagged as persuasion ground with positive headroom over-perform the
# partisanship baseline in the predicted direction? Not run on a provisional
# pass, by design.

# %%
if STATUS == "CERTIFIED":
    print("CERTIFIED: unseal and grade the playbooks per RUNBOOK section 4 before publishing.")
else:
    print("PROVISIONAL: playbook grading waits for certification.")

# %% [markdown]
# ## 11. The scorecard in five sentences (for the field)
#
# Printed from the numbers above so it can never drift from them.

# %%
hits = (level_table["in_bracket"] == "HIT").sum()
graded = level_table["in_bracket"].isin(["HIT", "MISS"]).sum()
lo_b, hi_b = np.percentile(boot, [2.5, 97.5])
lo_o, hi_o = np.percentile(boot_op, [2.5, 97.5])
wins = [r["measure"] for r in lv if r["err_ours"] < r["err_onpoint_headline"]]
print(f"[{STATUS}]")
print(
    f"1. Statewide: {hits} of {graded} graded brackets hit; pass/fail called right on "
    f"{sum(r['outcome_ours'] == 'right' for r in lv)} of 5 Missouri measures "
    f"(On Point: {sum(r['outcome_onpoint'] == 'right' for r in lv)} of 5)."
)
print(
    f"2. County map vs party alone: misses {total.skill_vs_baseline:.0%} smaller "
    f"(95% range {lo_b:+.3f} to {hi_b:+.3f}): " + ("a real edge." if lo_b > 0 else "no edge shown.")
)
print(
    f"3. County map vs On Point: skill {point:+.3f} (95% range {lo_o:+.3f} to {hi_o:+.3f}): "
    + ("ours better." if lo_o > 0 else ("theirs better." if hi_o < 0 else "a draw overall."))
)
print(
    f"4. Where the two disagreed on Amendment 3, the result sided with us in {k} of {n} "
    f"jurisdictions."
)
print(
    f"5. Our statewide number was closer than On Point's on {len(wins)} of 5 measures; "
    f"misses outside our brackets: "
    + (", ".join(level_table.loc[level_table.in_bracket == "MISS", "measure"]) or "none")
    + "."
)
