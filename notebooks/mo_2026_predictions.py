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
# # Missouri, November 3 2026: the pre-registration draft
#
# *An analysis notebook for the Geo-Fluid Dynamics Engine. Exploratory
# narrative — the tested library (`geofluid`) does the ingest; the model here
# is deliberately simple enough to be audited line by line.*
#
# ## What this notebook is
#
# The protocol in `docs/MEASUREMENT_DESIGN.md` §7 commits us to predicting
# every statewide measure on Missouri's November 2026 ballot **county by
# county, before the election**, freezing the file in git by 2026-10-15, and
# scoring it in public afterwards. This notebook is the DRAFT of that file: it
# assembles every Missouri statewide measure we can certify (21 contests,
# 2018–2026, three electorate types), picks the prediction model by backtest,
# states each measure's statewide "level" as an explicit ex-ante bracket, and
# writes `data/predictions/mo_2026-11-03_DRAFT_<date>.csv`. Nothing here is
# registered yet; the registration commit will rename the file and stop
# editing it.
#
# ## The five measures (the slate widened on 2026-09-03)
#
# * **Amendment 3** — YES repeals the 2024 reproductive-freedom amendment
#   (near-total ban). Progressive side: NO. Closest past vote: 2024 Amdt 3
#   (51.6% yes).
# * **Amendment 6** — YES requires an 80% legislative supermajority plus a
#   statewide vote to alter voter-passed initiatives. Progressive side: YES.
#   Closest: 2018 Amdt 1 Clean Missouri (62.0%), Aug-2026 Amdt 4 (80.3% NO).
# * **Congressional map referendum** — YES upholds HB 1, the 2025 7–1 map.
#   Progressive side: NO. Closest: 2020 Amdt 3 Clean Missouri repeal (51.0%).
# * **Amendment 7** — YES creates the "Show-Me" prosperity fund toward
#   replacing taxes. Progressive side: NO. Closest: 2024 Amdt 6 court fees
#   (39.4%), Aug-2026 Amdt 5 income-tax phaseout (16.7%).
# * **Amendment 8** — YES makes county sheriff a constitutional elected office
#   with removal protection. Progressive side: NO. Closest: 2024 Amdt 7
#   citizen-only / RCV ban (68.4%), Aug-2024 Amdt 4 KC police (51.1%).
#
# "Progressive side" is the orientation convention shared with the loaders
# and the catalog — a label for which answer the measure's own coalition
# geography puts on the Democratic-leaning end, not an endorsement.

# %%
import re
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pdfplumber

from geofluid.ingest.referendum import parse_mo_canvass, parse_mo_enr_results

ROOT = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "pyproject.toml").exists())
RAW = ROOT / "data/raw"
TODAY = date.today().isoformat()


def logit(p: "pd.Series[float]") -> "pd.Series[float]":
    return np.log(p / (1 - p))


def inv_logit(z: "pd.Series[float]") -> "pd.Series[float]":
    return 1 / (1 + np.exp(-z))


# %% [markdown]
# ## 1. Data: 116 jurisdictions, 21 measures, three electorates
#
# Missouri reports 114 counties + St. Louis City + **Kansas City** (which
# spans four counties and carries MIT's place-code `2938000`, so it has a
# real presidential baseline). Every measure below passed the loader's
# built-in integrity check (parsed jurisdictions reproduce the certified
# statewide total exactly). The Aug-2026 primary comes from the SoS's
# Election Night Results portal — certified by the Board of State Canvassers
# on 2026-08-25, served as a race page because the canvass PDF was still
# unposted on 2026-09-14 — through `parse_mo_enr_results`.

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
    {
        "Kansas City": "2938000",  # MIT place-code convention (spans 4 counties)
        "McDonald": "29119",  # str.title() yields "Mcdonald"
        "St. Louis": "29189",  # the canvass drops the "County" suffix
        "De Kalb": "29063",  # the ENR portal spells DeKalb with a space
    }
)
county_name = {v: k for k, v in fips_map.items()}
county_name["29189"] = "St. Louis County"


def dem_two_party(year: int) -> "pd.Series[float]":
    y = mo_rows[mo_rows["year"] == year].copy()
    y["fips"] = y["county_name"].str.title().map(fips_map)
    two = y[y["party"].isin(["DEMOCRAT", "REPUBLICAN"])]
    pv = two.pivot_table(index="fips", columns="party", values="candidatevotes", aggfunc="sum")
    return pv["DEMOCRAT"] / (pv["DEMOCRAT"] + pv["REPUBLICAN"])


dem = {year: dem_two_party(year) for year in (2016, 2020, 2024)}

CANVASSES = [
    "ActualResults-November62018-FINAL.pdf",
    "ActualResults-August72018.pdf",
    "ActualResults-August42020.pdf",
    "ActualResults-November32020.pdf",
    "ActualResults-August62024.pdf",
    "ActualResults-November52024.pdf",
]
pages = {}
for canvass in CANVASSES:
    with pdfplumber.open(RAW / canvass) as pdf:
        pages[canvass] = [page.extract_text() or "" for page in pdf.pages]

NOV18 = "ActualResults-November62018-FINAL.pdf"
NOV20 = "ActualResults-November32020.pdf"
NOV24 = "ActualResults-November52024.pdf"
# (label, canvass, contest, progressive side, electorate type)
MEASURES = [
    ("cleanmo_2018", NOV18, "Amendment 1", "yes", "midterm"),
    ("cannabis_med_2018", NOV18, "Amendment 2", "yes", "midterm"),
    ("bingo_2018", NOV18, "Amendment 4", "yes", "midterm"),
    ("minwage_2018", NOV18, "Proposition B", "yes", "midterm"),
    ("gastax_2018", NOV18, "Proposition D", "yes", "midterm"),
    ("termlimits_2020", NOV20, "Amendment 1", "yes", "presidential"),
    ("cleanmo_repeal_2020", NOV20, "Amendment 3", "no", "presidential"),
    ("sportsbet_2024", NOV24, "Amendment 2", "yes", "presidential"),
    ("abortion_2024", NOV24, "Amendment 3", "yes", "presidential"),
    ("casino_2024", NOV24, "Amendment 5", "yes", "presidential"),
    ("courtfees_2024", NOV24, "Amendment 6", "no", "presidential"),
    ("rcvban_2024", NOV24, "Amendment 7", "no", "presidential"),
    ("minwage_2024", NOV24, "Proposition A", "yes", "presidential"),
    ("rtw_2018p", "ActualResults-August72018.pdf", "Proposition A", "no", "primary"),
    ("medicaid_2020p", "ActualResults-August42020.pdf", "Amendment 2", "yes", "primary"),
    ("childcare_tax_2024p", "ActualResults-August62024.pdf", "Amendment 1", "yes", "primary"),
    ("kcpolice_2024p", "ActualResults-August62024.pdf", "Amendment 4", "no", "primary"),
]
ENR_2026 = [  # (label, amendment number, progressive side)
    ("parks_tax_2026p", 1, "yes"),
    ("jackson_assessor_2026p", 2, "no"),
    ("init_restrict_2026p", 4, "no"),
    ("income_tax_phaseout_2026p", 5, "no"),
]

shares, totals, electorate = {}, {}, {}
for label, canvass, contest, side, etype in MEASURES:
    panel = parse_mo_canvass(pages[canvass], contest, fips_map).set_index("fips")
    shares[label] = 1 - panel["no_share"] if side == "yes" else panel["no_share"]
    totals[label] = panel["total_votes"]
    electorate[label] = etype
for label, number, side in ENR_2026:
    text = (RAW / f"enr_mo_20260804_amendment_{number}.txt").read_text(encoding="utf-8")
    panel = parse_mo_enr_results(text, fips_map).set_index("fips")
    shares[label] = 1 - panel["no_share"] if side == "yes" else panel["no_share"]
    totals[label] = panel["total_votes"]
    electorate[label] = "primary"
share = pd.DataFrame(shares)
total = pd.DataFrame(totals)
statewide = (share * total).sum() / total.sum()
print(f"{share.shape[0]} jurisdictions x {share.shape[1]} measures")
print(
    pd.DataFrame(
        {"progressive_share_statewide": statewide.round(4), "electorate": pd.Series(electorate)}
    ).to_string()
)

# %% [markdown]
# ### A midterm partisan baseline: the 2018 U.S. Senate race
#
# MIT's file is presidential only. Missouri's 2018 canvass gives us the last
# midterm electorate's partisan vote directly (Hawley–McCaskill). This is an
# ad hoc, notebook-grade parse of a candidate race — so it is validated the
# only way that counts, against the certified statewide totals.

# %%
senate_rows = []
row_re = re.compile(r"^([A-Za-z][A-Za-z .'\-]*?)((?:\s+[\d,]+){6})$")
for page in pages[NOV18]:
    if "United States Senator" not in page:
        continue
    for line in page.splitlines():
        m = row_re.match(line.strip())
        if m and m.group(1) != "Total":
            nums = [int(x.replace(",", "")) for x in m.group(2).split()]
            senate_rows.append((fips_map[m.group(1)], nums[0], nums[1]))
senate18 = pd.DataFrame(senate_rows, columns=["fips", "hawley", "mccaskill"]).set_index("fips")
certified_2018 = (1254927, 1112935)
parsed_2018 = (int(senate18["hawley"].sum()), int(senate18["mccaskill"].sum()))
if parsed_2018 != certified_2018:
    raise ValueError(f"2018 Senate parse {parsed_2018} != certified {certified_2018}")
dem18_senate = senate18["mccaskill"] / (senate18["hawley"] + senate18["mccaskill"])
pres_1620 = ((dem[2016] + dem[2020]) / 2).reindex(dem18_senate.index)
print(f"2018 Senate: {len(senate18)} jurisdictions; certified statewide totals reproduced exactly")
r_senate = np.corrcoef(dem18_senate, pres_1620)[0, 1]
print(f"corr(dem 2018 Senate, dem pres 2016/2020 avg) = {r_senate:.3f}")

# %% [markdown]
# ## 2. Choosing the model by backtest
#
# Three candidate models for a county's share on a *new* measure, all on the
# logit scale and all with the statewide level treated as given (the level
# is a separate, explicitly-bracketed judgement — see §4 — so the backtest
# isolates the *county pattern* skill):
#
# 1. **Partisanship only** — `logit(share) = a + b·logit(dem two-party)` of
#    the measure's own era. The baseline we claim to beat.
# 2. **Pooled position** — the mean standardized logit share across all
#    *other* general-election measures (the design doc's ideal point, built
#    the simple way).
# 3. **Partisanship + analog residual** — model 1 plus `k` times the
#    partisanship residual of the closest past measure (the tested
#    `issue_resistance` idea: a county that defied its partisan peers on the
#    analog is expected to defy them again).
#
# Every fit is leave-one-out on the measure being predicted; the analog's
# residual is computed from the analog's own era baseline.

# %%
L = logit(share.clip(0.01, 0.99))
general = [m[0] for m in MEASURES if m[4] != "primary"]
ERA_BASELINE = {
    "2018": (dem[2016] + dem[2020]) / 2,
    "2020": dem[2020],
    "2024": dem[2024],
    "2026": dem[2024],
}


def era_of(label: str) -> str:
    match = re.search(r"(20\d\d)", label)
    if match is None:
        raise ValueError(label)
    return match.group(1)


def partisan_fit(label: str) -> tuple[float, float, "pd.Series[float]"]:
    """OLS of a measure's logit share on its era's logit partisanship; returns
    intercept, slope, residual (fips-indexed)."""
    y = L[label]
    x = logit(ERA_BASELINE[era_of(label)].reindex(y.index))
    slope, intercept = np.polyfit(x, y, 1)
    return float(intercept), float(slope), y - (intercept + slope * x)


def rmse_pp(pred_logit: "pd.Series[float]", label: str) -> float:
    return float(np.sqrt(((inv_logit(pred_logit) - share[label]) ** 2).mean()) * 100)


weights = total["abortion_2024"] / total["abortion_2024"].sum()


def standardized(label: str) -> "pd.Series[float]":
    mean = (L[label] * weights).sum()
    sd = np.sqrt((((L[label] - mean) ** 2) * weights).sum())
    return (L[label] - mean) / sd


Z = pd.DataFrame({m: standardized(m) for m in general})

# Analog pairs for model 3: the closest earlier measure by content
# (same issue where one exists; nearest governance/tax sibling otherwise).
ANALOG_BACKTEST = {
    "minwage_2024": "minwage_2018",
    "cleanmo_repeal_2020": "cleanmo_2018",
    "abortion_2024": "minwage_2024",  # cross-issue: the Ohio-style trait test
    "casino_2024": "sportsbet_2024",
    "courtfees_2024": "termlimits_2020",
    "rcvban_2024": "cleanmo_repeal_2020",
    "sportsbet_2024": "bingo_2018",
    "gastax_2018": "bingo_2018",
}
K_GRID = (0.5, 0.75, 1.0)

rows = []
for label in general:
    intercept, slope, _resid = partisan_fit(label)
    x = logit(ERA_BASELINE[era_of(label)].reindex(L.index))
    pred1 = intercept + slope * x
    pos = Z[[m for m in general if m != label]].mean(axis=1)
    s2, i2 = np.polyfit(pos, L[label], 1)
    pred2 = i2 + s2 * pos
    row: dict[str, object] = {
        "measure": label,
        "partisan_only": rmse_pp(pred1, label),
        "pooled_position": rmse_pp(pred2, label),
    }
    if label in ANALOG_BACKTEST:
        _, _, analog_resid = partisan_fit(ANALOG_BACKTEST[label])
        for k in K_GRID:
            pred3 = pred1 + k * analog_resid.reindex(L.index)
            row[f"partisan+analog k={k}"] = rmse_pp(pred3, label)
        row["analog"] = ANALOG_BACKTEST[label]
    rows.append(row)
backtest = pd.DataFrame(rows).set_index("measure")
print("county RMSE in percentage points (statewide level given):")
print(backtest.round(2).to_string())
print("\nmeans:")
print(backtest.drop(columns="analog").mean().round(2).to_string())

# %% [markdown]
# **Reading the backtest.** Partisanship alone is a strong baseline — the
# pooled position does *not* beat it on average (it helps on low-salience
# gambling/tax measures where partisanship is loose, and hurts on the
# hot-button ones where partisanship already explains 90%+ of the
# variance). The analog residual is where the skill is — but only when the
# analog is a true sibling: minimum wage 2018 → 2024, sports betting →
# casino, and minimum wage → abortion (the cross-issue trait) all cut county
# error by a quarter to a half, while flavor-guess analogs (term limits →
# court fees, Clean Missouri repeal → RCV ban) make it worse. Shrinking the
# residual by half is the compromise that wins on average, so we register
# **model 3 with k = 0.5** and keep same-issue analogs where they exist.

# %%
k_cols = [c for c in backtest.columns if c.startswith("partisan+analog")]
k_table = backtest[["partisan_only", *k_cols]].dropna()
print(k_table.round(2).to_string())
print("\nmean over measures with an analog:")
print(k_table.mean().round(2).to_string())
K = 0.5  # registered shrinkage — best mean in the table; revisit ONLY before registration

# %% [markdown]
# ## 3. The electorate question
#
# Two things could break a midterm prediction built on presidential
# baselines: the *level* (who turns out) and the *pattern* (whether counties
# keep their relative order). The level is handled by the bracket in §4. For
# the pattern, three checks:

# %%
midterm = [m[0] for m in MEASURES if m[4] == "midterm"]
presidential = [m[0] for m in MEASURES if m[4] == "presidential"]
pos_mid = Z[midterm].mean(axis=1)
pos_pres = Z[presidential].mean(axis=1)
r_a = np.corrcoef(pos_mid, pos_pres)[0, 1]
r_b = np.corrcoef(dem18_senate, dem[2024].reindex(dem18_senate.index))[0, 1]
print(f"(a) county position from 2018 midterm vs presidential-year measures: r = {r_a:.3f}")
print(f"(b) 2018 Senate two-party Dem share vs 2024 presidential: r = {r_b:.3f}")
print("(c) the Aug-2026 primary (a real 2026 electorate) against the 2024 presidential baseline:")
x24 = logit(dem[2024].reindex(L.index))
for label, _n, _s in ENR_2026:
    r_c = np.corrcoef(x24, L[label])[0, 1]
    print(f"    {label:28s} r = {r_c:+.3f}   statewide progressive share {statewide[label]:.3f}")

# %% [markdown]
# The county *pattern* is stable across electorate types for measures with
# partisan structure (the direct-democracy measure Amendment 4 in Aug 2026
# still ordered counties by partisanship even in a landslide); the
# low-salience referrals (Jackson County assessor, income-tax phaseout) have
# almost no partisan structure at all — which is exactly why their 2026
# siblings (Amendments 7 and 8) get the humblest intervals below.
#
# **Turnout weights.** For the statewide aggregation of county predictions
# we assume each jurisdiction's share of the 2026 vote equals its share of
# the 2018 midterm vote (Clean Missouri's total votes). This is an explicit
# assumption; the file also carries the 2024-presidential-weighted variant.

# %%
turnout_2018 = total["cleanmo_2018"] / total["cleanmo_2018"].sum()
turnout_2024 = total["abortion_2024"] / total["abortion_2024"].sum()

# %% [markdown]
# ## 4. The five measures: analogs and ex-ante level brackets
#
# The **level** is the statewide progressive share we expect. It is a
# judgement, stated before the fact, with the reasoning written down so it
# can be scored as a judgement. The county pattern then comes from the
# registered model (slope from the analog's era fit, analog residual shrunk
# by `K`), shifted so the turnout-weighted statewide share equals the level.
#
# * **Amdt 3 (abortion repeal; progressive = NO): 51.5 / 55.0 / 59.0.**
#   The 2024 rights side won 51.6% on a presidential electorate. A near-total
#   ban is a harsher cutpoint than a viability right — in KS-2022, KY-2022
#   and OH-2023 the ban side under-performed the state's partisan lean by
#   8–15 points. Midterm 2022 electorates favored the rights side, and
#   Aug-2026's 80–20 rejection of Amendment 4 shows an anti-legislature mood.
#   Low end: the 2024 coalition merely holds.
# * **Amdt 6 (initiative protection; progressive = YES): 55 / 62 / 70.**
#   Clean Missouri 2018 (anti-legislature reform) got 62.0% on a midterm —
#   the same electorate type; Aug-2026 Amendment 4 (the legislature's
#   initiative restriction) lost 80–20. Risk: the 80% threshold reads as
#   extreme and the opposition will call it a lock-in.
# * **Map referendum (progressive = NO = reject HB 1): 46 / 53 / 60.** The
#   2020 Clean Missouri repeal — the legislature's last redistricting power
#   play — passed 51.0% on a presidential electorate. A referendum on a
#   mid-decade gerrymander is more legible and the 2026 mood is
#   anti-legislature, but partisan salience will be maximal and Missouri
#   leans R+18. Genuinely close; widest bracket.
# * **Amdt 7 (prosperity fund; progressive = NO): 50 / 58 / 68.** Missouri
#   voters default NO on referrals they don't understand (2024 court fees 39%
#   yes, 2020 term limits 47%, Aug-2024 childcare 45%), and the
#   tax-elimination agenda's own Amendment 5 just lost 83–17. Softer, vaguer
#   text than Amdt 5 keeps it off the landslide floor.
# * **Amdt 8 (sheriffs; progressive = NO): 28 / 36 / 45.** Pro-law-enforcement,
#   populist, low-controversy: closest to 2024 Amendment 7 (68.4% yes) in
#   flavor; passes comfortably unless the removal-protection clause draws
#   organized opposition.

# %%
SLATE = [
    # (measure_id, ballot label, progressive side, analogs, (low, central, high) level)
    (
        "mo_20261103_amendment_3",
        "Amendment 3 — repeal 2024 reproductive-freedom amendment",
        "no",
        ["abortion_2024"],
        (0.515, 0.550, 0.590),
    ),
    (
        "mo_20261103_amendment_6",
        "Amendment 6 — Respect Missouri Voters (initiative protection)",
        "yes",
        ["cleanmo_2018", "init_restrict_2026p"],
        (0.55, 0.62, 0.70),
    ),
    (
        "mo_20261103_map_referendum",
        "Congressional map referendum on HB 1",
        "no",
        ["cleanmo_repeal_2020"],
        (0.46, 0.53, 0.60),
    ),
    (
        "mo_20261103_amendment_7",
        "Amendment 7 — Show-Me prosperity fund",
        "no",
        ["courtfees_2024", "income_tax_phaseout_2026p"],
        (0.50, 0.58, 0.68),
    ),
    (
        "mo_20261103_amendment_8",
        "Amendment 8 — constitutional elected sheriffs",
        "no",
        ["rcvban_2024", "kcpolice_2024p"],
        (0.28, 0.36, 0.45),
    ),
]


def county_pattern(analogs: list[str]) -> "pd.Series[float]":
    """The registered model's county pattern for a new measure: the mean of
    the analogs' partisan slopes applied to 2024 partisanship, plus K times
    the mean analog residual. Un-levelled (the level shift is applied next)."""
    slopes, resids = [], []
    for analog in analogs:
        _i, slope, resid = partisan_fit(analog)
        slopes.append(slope)
        resids.append(resid.reindex(L.index))
    return float(np.mean(slopes)) * x24 + K * pd.concat(resids, axis=1).mean(axis=1)


def level_shift(
    pattern: "pd.Series[float]", level: float, w: "pd.Series[float]"
) -> "pd.Series[float]":
    """Find the additive logit shift that makes the turnout-weighted statewide
    progressive share equal the stated level (bisection; monotone)."""
    lo, hi = -10.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if float((inv_logit(pattern + mid) * w).sum()) < level:
            lo = mid
        else:
            hi = mid
    return inv_logit(pattern + (lo + hi) / 2)


# County-level uncertainty from the backtest: the analog model's RMSE in
# logit units, averaged over the measures where an analog existed. The 90%
# interval is honest about pattern error ON TOP of the level bracket.
analog_errors = []
for lbl, analog in ANALOG_BACKTEST.items():
    intercept, slope, _r = partisan_fit(lbl)
    pred = (
        intercept
        + slope * logit(ERA_BASELINE[era_of(lbl)].reindex(L.index))
        + K * partisan_fit(analog)[2].reindex(L.index)
    )
    analog_errors.append(float(np.sqrt(((pred - L[lbl]) ** 2).mean())))
pattern_rmse_logit = float(np.mean(analog_errors))
print(f"pattern RMSE (logit units) from the analog-model backtest: {pattern_rmse_logit:.3f}")

# %%
z90 = 1.645 * pattern_rmse_logit
records = []
for measure_id, ballot, side, analogs, (low, central, high) in SLATE:
    pattern = county_pattern(analogs)
    pred_low = level_shift(pattern, low, turnout_2018)
    pred_mid = level_shift(pattern, central, turnout_2018)
    pred_high = level_shift(pattern, high, turnout_2018)
    pred_mid_24w = level_shift(pattern, central, turnout_2024)
    mid_logit = logit(pred_mid)
    band_lo = inv_logit(mid_logit - z90)
    band_hi = inv_logit(mid_logit + z90)
    for fips in L.index:
        records.append(
            {
                "measure_id": measure_id,
                "ballot": ballot,
                "progressive_side": side,
                "fips": fips,
                "county": county_name.get(fips, fips),
                "dem_two_party_2024": round(float(dem[2024].get(fips, np.nan)), 4),
                "pred_progressive_share": round(float(pred_mid[fips]), 4),
                "pred_low_90": round(float(min(pred_low[fips], band_lo[fips])), 4),
                "pred_high_90": round(float(max(pred_high[fips], band_hi[fips])), 4),
                "level_low": low,
                "level_central": central,
                "level_high": high,
                "analogs": "+".join(analogs),
                "turnout_weights": "2018 midterm",
                "pred_central_2024_turnout_weights": round(float(pred_mid_24w[fips]), 4),
            }
        )
predictions = pd.DataFrame(records)

summary_rows = []
for measure_id, *_rest in SLATE:
    g = predictions[predictions["measure_id"] == measure_id].set_index("fips")
    summary_rows.append(
        {
            "measure_id": measure_id,
            "statewide_progressive_central": float(
                (g["pred_progressive_share"] * turnout_2018).sum()
            ),
            # the SAME county predictions aggregated with 2024's county turnout
            # shares: how much the turnout-composition assumption moves the state
            "statewide_if_2024_turnout_pattern": float(
                (g["pred_progressive_share"] * turnout_2024).sum()
            ),
            "counties_progressive_majority": int((g["pred_progressive_share"] > 0.5).sum()),
            "min_county": float(g["pred_progressive_share"].min()),
            "max_county": float(g["pred_progressive_share"].max()),
        }
    )
print(pd.DataFrame(summary_rows).set_index("measure_id").round(3).to_string())

# %% [markdown]
# ## 5. What the map would look like — and the partisanship-only baseline we claim to beat
#
# The registered scorecard compares our county predictions with a
# partisanship-only prediction at the SAME level (so the comparison is about
# pattern skill, not about who guessed the statewide number). Both are
# written to the file.

# %%
baseline_records = []
for measure_id, _b, _s, analogs, (_lo, central, _hi) in SLATE:
    slope = float(np.mean([partisan_fit(a)[1] for a in analogs]))
    base = level_shift(slope * x24, central, turnout_2018)
    baseline_records.extend(
        {"measure_id": measure_id, "fips": f, "baseline_partisan_only": round(float(base[f]), 4)}
        for f in L.index
    )
predictions = predictions.merge(pd.DataFrame(baseline_records), on=["measure_id", "fips"])

fig, axes = plt.subplots(1, len(SLATE), figsize=(4 * len(SLATE), 4), sharey=True)
for ax, (measure_id, ballot, *_rest) in zip(axes, SLATE, strict=True):
    g = predictions[predictions["measure_id"] == measure_id]
    ax.scatter(g["dem_two_party_2024"], g["pred_progressive_share"], s=8, label="registered model")
    ax.scatter(
        g["dem_two_party_2024"],
        g["baseline_partisan_only"],
        s=8,
        alpha=0.4,
        label="partisanship only",
    )
    ax.axhline(0.5, color="grey", lw=0.5)
    ax.set_title(ballot.split(" — ")[0][:34], fontsize=9)
    ax.set_xlabel("Dem two-party 2024")
axes[0].set_ylabel("predicted progressive share")
axes[0].legend(fontsize=7)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 6. Write the DRAFT file
#
# Not registered. The registration commit (by 2026-10-15) will copy this to
# a file without `DRAFT` in the name and never edit it again; a later
# revision, if any, is a NEW dated file and this one still gets scored.

# %%
out_dir = ROOT / "data/predictions"
out_dir.mkdir(exist_ok=True)
out = out_dir / f"mo_2026-11-03_DRAFT_{TODAY}.csv"
predictions.to_csv(out, index=False)
n_measures = predictions["measure_id"].nunique()
n_fips = predictions["fips"].nunique()
print(f"wrote {out.relative_to(ROOT)}: {len(predictions)} rows ({n_measures} x {n_fips})")
show_cols = [
    "county",
    "dem_two_party_2024",
    "pred_progressive_share",
    "pred_low_90",
    "pred_high_90",
    "baseline_partisan_only",
]
amdt3 = predictions[predictions["measure_id"] == "mo_20261103_amendment_3"]
print("\nAmendment 3 - most pro-rights predicted:")
print(amdt3.nlargest(5, "pred_progressive_share")[show_cols].to_string(index=False))
print("\nAmendment 3 - least:")
print(amdt3.nsmallest(5, "pred_progressive_share")[show_cols].to_string(index=False))
print("\nAmendment 3 - where the model departs most from partisanship alone:")
amdt3 = amdt3.assign(departure=amdt3["pred_progressive_share"] - amdt3["baseline_partisan_only"])
departures = amdt3.reindex(amdt3["departure"].abs().sort_values(ascending=False).index)
print(departures.head(8)[[*show_cols, "departure"]].to_string(index=False))

# %% [markdown]
# ## 6b. Statewide-only calls: Nevada Question 6 and Massachusetts Question 8
#
# We hold no county files for Nevada or Massachusetts, so these two get
# **statewide-only** rows in a separate file (decided 2026-09-15). They are
# still receipts — a level call with a bracket, scored the same way as the
# Missouri levels — just without the county pattern.
#
# * **NV Question 6 (progressive = YES): 58 / 63 / 68.** Identical text to
#   2024's first passage (64.4% on a presidential electorate); a midterm
#   electorate and second-vote fatigue argue for a point or two lower, and
#   the measure codifies roughly the status quo, so it has no headroom from
#   a harsher cutpoint. The fixed-cutpoint control of the experiment.
# * **MA Question 8 (progressive = NO = keep the market): 58 / 65 / 72.**
#   2016 Question 4 legalized at 53.7%; a decade of an operating market,
#   national support for legal cannabis up since, and a repeal that would
#   close licensed businesses — status-quo bias now works FOR the market.
#   Risk to the high end: the "limited possession stays legal" framing lets
#   ambivalent voters say yes to repeal without feeling prohibitionist.

# %%
STATEWIDE_ONLY = [
    (
        "nv_20261103_question_6",
        "NV Question 6 — right to abortion (second passage)",
        "yes",
        (0.58, 0.63, 0.68),
        "2024 NV Q6 first passage 64.4%",
    ),
    (
        "ma_20261103_question_8",
        "MA Question 8 — eliminate recreational marijuana sales",
        "no",
        (0.58, 0.65, 0.72),
        "2016 MA Q4 legalization 53.7%",
    ),
]
statewide_only = pd.DataFrame(
    [
        {
            "measure_id": mid_,
            "ballot": ballot,
            "progressive_side": side,
            "level_low": lo,
            "level_central": mid,
            "level_high": hi,
            "basis": basis,
            "granularity": "statewide only (no county file held)",
        }
        for mid_, ballot, side, (lo, mid, hi), basis in STATEWIDE_ONLY
    ]
)
out_sw = out_dir / f"statewide_only_2026-11-03_DRAFT_{TODAY}.csv"
statewide_only.to_csv(out_sw, index=False)
print(f"wrote {out_sw.relative_to(ROOT)}")
print(statewide_only.drop(columns="ballot").to_string(index=False))

# %% [markdown]
# ## 7. Known weaknesses, stated now
#
# * **The level is a judgement.** Everything county-level is conditional on
#   the bracket; a statewide miss outside the bracket is scored as a level
#   miss, separately from pattern skill.
# * **Two of the five measures have no true same-issue predecessor** (the map
#   referendum and Amendment 8); their analogs are flavor matches and their
#   intervals are correspondingly wide.
# * **Turnout composition is assumed, not modelled** — 2018's county shares
#   stand in for 2026's; the file carries the 2024-weighted alternative.
# * **Kansas City is a pseudo-jurisdiction**; its 2024 partisan baseline comes
#   from MIT's separate KC reporting.
# * **One state, one cycle.** This is evidence, not proof — the point of
#   registering it is to find out.
