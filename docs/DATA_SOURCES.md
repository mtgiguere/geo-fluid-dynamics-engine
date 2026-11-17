# Data Sources — every raw file, where it comes from, and what consumes it

Everything under `data/raw/` is git-ignored (large, and some of it is
licensed for redistribution only by its publisher). This document is the
map back to the source so anyone can rebuild the inputs from scratch. Each
entry says what the file is, where to get it, any quirk the loader handles,
and which code reads it. Certified-total acceptance (the project's
"lie detector" for loaders) is noted where it applies.

Verified digests of the files used for the 2026 registration are in
`data/predictions/inputs_manifest_REGISTERED_2026-10-14.csv`.

## The spine: county presidential returns

| File | `data/raw/countypres_2000-2024.csv` |
|---|---|
| Source | MIT Election Data and Science Lab, *County Presidential Election Returns 2000–2024*, Harvard Dataverse, doi:10.7910/DVN/VOQCHQ. Release used: 20260225. |
| How to get it | Browser download only: the Dataverse API is blocked by a mandatory guestbook. Accept the terms, download the CSV, place it at the path above. |
| Consumed by | `geofluid.ingest.county_returns.load_county_returns` (the loader handles statewide rows with no FIPS, float FIPS, 2024 pseudo-candidate rows, TOTAL-mode rows, placeholder entities, unreported minor-candidate values; each quirk has a test). The notebooks read it directly for the Missouri partisan baseline. |
| Acceptance | National two-party totals match certified results for all seven elections (2024: 75,012,514 D / 77,302,467 R). |
| Known issue | The raw `totalvotes` column is unreliable in 2024 (Philadelphia counted twice, Harris County TX 3.5×). Never use it as ground truth; sum candidate votes instead. |

| File | `data/raw/_hist_pres_1868_2020.tab` (and `.tsv`, `.RData` copies) |
|---|---|
| Source | Algara, Carlos; Sharif Amlani, *Replication Data for: Partisanship & Nationalization in American Elections*, Harvard Dataverse (county presidential returns 1868–2020). |
| Consumed by | `geofluid.ingest.historical_returns` → `geofluid.panel.spine` (joined to MIT; the modern source wins the 2000–2020 overlap). |
| Acceptance | Cross-validates against MIT at correlation 0.9999 in 2020; 40-election panel, ~117k county-years. |

## Demographics

| Source | U.S. Census Bureau, American Community Survey 5-year estimates (B-tables), via the Census API. |
|---|---|
| How to get it | Set `CENSUS_API_KEY` in the environment (free key from api.census.gov). `scripts/export_web_data.py` fetches on demand; nothing is stored under `data/raw/`. |
| Consumed by | `geofluid.ingest.county_demographics` → `geofluid.panel.master`. |
| Quirks | Census sentinel values for suppressed cells are handled by the loader (tested). |

## Geometry

| Files | `data/raw/cb_2021_5m/` (shapefile, 1:5m) and `data/raw/cb_2021/` (1:500k) |
|---|---|
| Source | U.S. Census Bureau cartographic boundary files, county, vintage 2021 (`cb_2021_us_county_5m.zip`, `cb_2021_us_county_500k.zip`). |
| Why 2021 | Predates Connecticut's 2022 switch to planning regions, so it matches the FIPS universe of the returns; see `geofluid.ingest.county_geometry`. |
| Consumed by | `geofluid.ingest.county_geometry` → `web/public/data/counties.geojson` (committed, 3,234 features with `fips` and `NAME`). The page builders read the committed GeoJSON, not the shapefile. |

## Ballot measures (one certified file per state format)

The canonical output of every loader is the same panel: one row per
county, `fips`, `yes_votes`, `no_votes`, `total_votes`, `no_share`. Which
answer is the progressive one is decided downstream by the catalog's
`progressive_side`, never inside the loader.

| State · measure | File | Source and format | Loader | Acceptance |
|---|---|---|---|---|
| Kansas, Aug 2022 "Value Them Both" amendment | `data/raw/ks_amendment_2022_precinct.xlsx` | Kansas Secretary of State official results workbook: a long main sheet plus wide per-county sheets with COUNTY-TOTALS rows | `load_ks_referendum_workbook` | certified statewide totals |
| Kentucky, Nov 2022 Amendment 2 | `data/raw/2022 Kentucky Amendment 2 - No Right To Abortion Election Results.txt` | Kentucky State Board of Elections text export | `load_ky_referendum` | certified statewide totals |
| Ohio, Nov 2023 Issues 1 and 2 | `data/raw/precinct-summary.xlsx` | Ohio Secretary of State county workbook (header on the third row; Issue 1 and Issue 2 as two YES/NO pairs) | `load_oh_referendum(..., issue=1 or 2)` | certified statewide totals |
| Missouri, 2018–2024 (eight general and primary canvasses) | `data/raw/ActualResults-<Month><D><YYYY>.pdf` from `sos.mo.gov/CMSImages/ElectionResultsStatistics/` (plain `curl` gets 403; a browser User-Agent gets 200) | SoS official canvass PDF; one "<contest> YES NO Total" section per measure, 116 jurisdictions (114 counties + St. Louis City + Kansas City) | `load_mo_referendum` / `parse_mo_canvass` (pdfplumber text pages; the canvass Total row is the integrity check) | every contest reproduces the certified statewide share to the decimal |
| Missouri, Aug 2026 primary (Amendments 1, 2, 4, 5) | `data/raw/enr_mo_20260804_amendment_<n>.txt` | SoS Election Night Results portal (`enr.sos.mo.gov`, "Pick a Race"), page text saved by `scripts/fetch_mo_enr.cjs`; certified by the Board of State Canvassers 2026-08-25, served before the canvass PDF existed | `parse_mo_enr_results` (the statewide YES/NO block is the integrity check) | all four reproduce the portal's certified statewide shares |

Jurisdiction naming decisions that a new reader needs to know:

- **Kansas City, Missouri** reports as its own jurisdiction spanning four
  counties. It carries MIT's place-code convention `2938000` so it has a
  presidential baseline. It has no polygon on the map.
- **St. Louis City** is `29510`; the canvass's "St. Louis" (county) is
  `29189`; "McDonald" and "De Kalb" need explicit aliases (title-casing
  and the portal's spelling).
- An unmapped jurisdiction name makes every Missouri loader raise. Silent
  drops are forbidden by design.

## The known wave: rooftop solar (and the ZIP-to-county bridge)

Solar is the engine's test bed for a wave: an idea known to spread person to
person, recorded install by install with a date and a ZIP code.

| File | `data/raw/us_lbnl_dss2026_20261109/LBNL_distributed_solar_dataset_public.zip` (→ `TTS_LBNL_public_file_28-Jul-2026_all.csv`, 2.4 GB) plus the user guide (8.07.26) |
|---|---|
| Source | Lawrence Berkeley National Laboratory, *Tracking the Sun* / Distributed Solar public data file, 2026 edition (installs through year-end 2025). Free. The 2025 edition is kept beside it in `us_lbnl_tts2025_20261109/`. |
| How to get it | Browser download only (emp.lbl.gov blocks scripts). The zip uses **Deflate64**, which Python's `zipfile` and Windows `tar` cannot read; stream it with `unzip -p` (Git for Windows and Linux both ship it). Read the CSV with `dtype=str, encoding="latin-1"`. |
| Consumed by | `geofluid.ingest.solar.load_solar_installs` (ZIP quirks, each with a test: float text `93004.0` in ~2.2M California rows, ZIP+4 hyphenated or run together, lost leading zeros `6033`, padding and non-breaking spaces, junk `-1`/`redacted`/`Multiple` → missing) and `county_adoption_panel` (household installs per county per quarter, quiet quarters zero-filled). |
| Acceptance | 3,995,665 rows (the guide: "about 4.0 million PV systems installed through year-end 2025"); residential 3,872,115 = RES + RES_SF + RES_MF exactly; panel total 3,643,662 equals an independent count of household installs matched to a same-state county; 1,119 counties × 112 quarters (1998–2025). |
| Known gaps | Missouri is not in the file (27 states + DC). Texas and Maryland have ZIPs on only ~25% of rows, Rhode Island none. 0.056% of matched installs (mostly DC-labelled installs on Maryland-majority ZIPs) land in another state's county and are dropped. |

| File | `data/raw/us_census_zcta_county2020_20261110/tab20_zcta520_county20_natl.txt` |
|---|---|
| Source | US Census Bureau, 2020 ZCTA-to-county relationship file (www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/). Pipe-delimited, UTF-8 with a byte-order mark (`encoding="utf-8-sig"`). |
| Consumed by | `geofluid.ingest.zcta_county.zip_to_county`: one county per ZIP, the county holding most of the ZIP's land (about 10,000 ZIPs cross a county line); blank-ZCTA rows (county land in no ZIP) dropped. |
| Acceptance | 33,791 ZIPs, the 2020 Census count; 99.81% of solar installs with a ZIP find a county. |

## The roads: commuting and migration between counties

| File | `data/raw/us_census_commuting2020_20261110/table1.xlsx` |
|---|---|
| Source | US Census Bureau, ACS 2016–2020 county-to-county commuting flows (www2.census.gov/programs-surveys/demo/tables/metro-micro/2020/commuting-flows-2020/). |
| Consumed by | Not yet: the "which road does the wave travel" comparison. |

| File | `data/raw/us_irs_migration2223_20261110/countyinflow2223.csv`, `countyoutflow2223.csv` |
|---|---|
| Source | IRS Statistics of Income, county-to-county migration, tax years 2022–2023 (www.irs.gov/pub/irs-soi/). Earlier years follow the same naming. |
| Consumed by | Not yet: the "which road" comparison. |

## Waves over time: state policy adoptions (SPID)

| File | `data/raw/us_spid_v12_20261111/SPID_v1.2.dta`, `SPID_v1.2_policies.dta` (in `dataverse_files.zip`, with the codebook and the v1.2 changes list) |
|---|---|
| Source | State Policy Innovation and Diffusion database v1.2 (Boehmke, LaCombe, Brockway; Harvard Dataverse doi:10.7910/DVN/CVYSR7). CC0. The year each state first adopted each of 724 policies, 1691–2017. |
| Consumed by | `geofluid.ingest.spid.load_spid_adoptions`. The "do the roads a wave travels change over time?" question. |
| Acceptance | 17,823 adoptions, 724 policies, 50 states, mean 24.6 states per policy, 1691–2017, no blanks: equal to the codebook. |
| Quirks | Dataverse's "Download ZIP" serves its re-exported `.dta`, not the original upload. The files are about 3x the listed size, and the adoptions file has only `policy`, `statenam`, `adopt_year`; the codebook's other state identifiers are absent. The state name is enough: the loader maps it to FIPS and stops on any name it cannot map. A state that never adopted a policy has no row; it is "not yet" through 2017, not missing. 194 policies come from the Uniform Law Commission, a model-law shop: a natural "pushed" group to set against the rest. |

Related, not yet downloaded: the researchers' own estimated state-to-state diffusion ties for each year 1960–2017 (doi:10.7910/DVN/1QJCDJ, CC0), an answer key for the era-by-era comparison. Also the replication data for "From Borders to Networks: The Changing Channels of Education Policy Diffusion" (doi:10.7910/DVN/VHAH07, 2026). Its description reports the main channel shifting from bordering states to policy networks.

## Waves over time, a mass behaviour: baby names by state (SSA)

| File | `data/raw/us_ssa_namesbystate_20261111/namesbystate.zip` (51 `XX.TXT` files + `StateReadMe.pdf`; extracted alongside, `SHA256SUMS` covers all) |
|---|---|
| Source | Social Security Administration, "Popular baby names by state" (ssa.gov/oact/babynames/limits.html), tabulated from SSN records as of 2026-03-01. Public domain. |
| Consumed by | `geofluid.ingest.names.load_state_names`. Each new name is a wave across 50 states + DC, 1910-2025. |
| Acceptance | 6,696,687 rows, 51 states, 1910-2025, no duplicates, minimum count 5, names 2-15 characters. Summed state counts give SSA's published national #1s: Mary/John 1910, Linda/James 1950, Emily/Jacob 2000, Olivia/Liam 2024. |
| Quirks | Headerless lines `state,sex,year,name,count`. Names under 5 in a state-year are suppressed, so state sums fall short of the national file, most in small states. **Read with `keep_default_na=False`:** pandas would otherwise turn the names "Nan" and "Na" into missing values. |

## Political giving: FEC individual contributions (2021-22 cycle)

| File | `data/raw/us_fec_2022_20261111/indiv22.zip` (plus `cm22.zip`, the committee master, and FEC's header files; `SHA256SUMS`). Extracts written beside it: `gifts_zip_week_group_2022.csv.gz` (gifts and dollars per ZIP per week for ActBlue, WinRed and other) and `abortion_gifts_2022.csv.gz`. |
|---|---|
| Source | Federal Election Commission bulk data (fec.gov/data/browse-data/?tab=bulk-data), downloaded 2026-11-11. Public. |
| Consumed by | `geofluid.ingest.fec.load_contributions`: individuals only, 5-digit ZIP, date, amount; undated rows dropped. Committee selection: `data/catalog/fec_abortion_committees_2022.csv`. |
| Acceptance | 63,885,802 rows in `by_date/`; 63,850,655 individual and dated. ActBlue's and WinRed's own rows sum to $1.14B and $0.87B, against FEC's published 2022 totals of $2.19B and $1.10B (`/committee/{id}/totals`). The gap is the documented $200 inclusion rule, not lost data. No month is missing. |
| Quirks | **`itcont.txt` in the zip is truncated** (4.5 GB, ends mid-row, missing most of 2022). Read the `by_date/` files instead (12 GB, complete). **Small, one-off donors are left out:** since 2015 a gift is included only once the donor's total to that committee passes $200 (cycle-to-date for candidates, year-to-date for PACs and parties). The bulk file is committed donors; every gift of any size is only in the raw electronic filings (ActBlue and WinRed itemize everything). ActBlue's own rows are one per gift: `24T` (passed on, earmarked) or `15` (a tip to ActBlue). The receiving committee reports the same gift again as `15E` with OTHER_ID = ActBlue, so count one side, not both. WinRed also files refunds as `22Y`. Headerless and pipe-delimited; read as latin-1 with quoting off. |

### Every gift, any size: ActBlue's raw electronic filings

| File | `data/raw/us_fec_actblue_raw_20261111/*.fec`: ActBlue's Form 3X monthly reports M2-M9 2022 (file numbers 1571224, 1575938, 1589733, 1597432, 1604622, 1618546, 1626598, 1631900), 12 GB, `SHA256SUMS`. Extracts: `actblue_zip_week_newcomers_2022.csv.gz`, `actblue_zip_day_newcomers_2022.csv.gz` (counts only; no names written). |
|---|---|
| Source | `https://docquery.fec.gov/dcdev/posted/{file_number}.fec`. Report list from the FEC API (`/v1/filings/?committee_id=C00401224`). Public. |
| Acceptance | 28,791,997 individual gifts with valid dates and 2,943,318 distinct name + ZIP donors, Jan-Aug 2022. A dollar check against each report's own summary line (F3XN) is still to do. |
| Quirks | FEC electronic format v8.4: fields separated by the ASCII file separator (0x1C), one record type per line (`HDR`, `F3XN`, `SA11AI` for individual receipts, `TEXT`, ...). In `SA11AI`, zero-based fields: 7 last name, 8 first name, 16 ZIP, 19 date (YYYYMMDD), 20 amount. ActBlue leaves the aggregate (field 21) at 0.00, so "first gift ever" cannot be read from the file; a newcomer is defined from the data itself. Contains personal names and addresses (public record): extracts keep counts only. |

### 2019 primary: ActBlue's raw filings, streamed

| File | `data/raw/us_fec_actblue_raw_2019_20261111/`: per-filing extracts `1780795.pkl` (2019 midyear, amended, Jan-Jun), `1378435.pkl` (2019 year-end, Jul-Dec), `1385527.pkl` (Jan 2020), with logs and `SHA256SUMS` of the raw files. The raw `.fec` files (5.8, 10.5 and 2.3 GB) were streamed through the extractor and not kept; re-download to reproduce. |
|---|---|
| Source | `https://docquery.fec.gov/dcdev/posted/{file_number}.fec`. In 2019 ActBlue filed semiannually (MY, YE), then monthly from 2020. Use the amended MY (1780795), not the original (1344765). |
| Acceptance | 18,133,520 earmarked individual gifts to 15 Democratic presidential committees (Jan 2019 to Jan 2020). A dollar check against each committee's published totals is still to do. |
| Quirks | Same v8.3/8.4 layout as the 2022 files. The recipient is in the memo text, field 43: `Earmarked for <NAME> (<committee id>)`; field 22 says `Earmark` or `Contribution to Act Blue`. The extracts hold counts per candidate, ZIP and day plus each donor's first-gift date keyed by a hash of name + ZIP + candidate (`PYTHONHASHSEED=0`, so hashes match across filings). That hash is a pseudonymous key: keep these files out of git like the raw filings. `actblue_2019_new_donors_by_zip_day.csv.gz` (5.3M rows, 8.26M donors) is the keyless summary built from them: new donors per candidate, ZIP and first-gift day. The wave player reads it; it holds counts only. |

### Metro areas (a free stand-in for TV markets)

| File | `data/raw/us_nber_cbsa_fips_20261112/cbsa2fipsxw.csv`: NBER's county to CBSA / CSA crosswalk, 2023 delineation (OMB). |
|---|---|
| Source | `https://data.nber.org/cbsa-csa-fips-county-crosswalk/2023/cbsa2fipsxw_2023.csv`. Public domain (federal delineation). |
| Quirks | All 3,222 rows are counties **in** a CBSA; counties in no metro or micro area are simply absent. Read with `dtype=str` and treat a missing code as "no market"; two missing codes are not the same market. Connecticut uses the 2022 planning regions, not the old counties in `cb_2021`, so CT pairs drop out. Nielsen's DMAs (the real TV markets) are licensed and are not used. |

### National TV attention (GDELT TV API)

| File | `data/raw/us_gdelt_tv_2019_20261112/tv_<candidate>.csv`: 15-second clips per day per national network mentioning each 2019 Democratic candidate (full name in quotes), Jan 2019 to Jan 2020; `SHA256SUMS`. |
|---|---|
| Source | `https://api.gdeltproject.org/api/v2/tv/tv?query="<name>" market:"National"&mode=timelinevol&datanorm=raw&timelinesmooth=0&format=csv`. Free; the API asks for at most one request every 5 seconds. Underlying captions: Internet Archive TV News Archive. |
| Quirks | Nine national networks (CNN, MSNBC, Fox News, Bloomberg, CNBC, Fox Business, C-SPAN 1-3). Local stations in 2019 cover only San Francisco and DC. Surnames alone are ambiguous (Sarah Sanders, Fidel Castro, Harris County), so query full names. Podcasts are not covered. |

## Catalogs (committed, not raw)

- `data/catalog/ballot_measures.csv` — 271 statewide measures, 1996–2025,
  five topic corpora, with `progressive_side`, certified `yes_pct`, and
  same-ballot structure; compiled from Ballotpedia and NCSL with per-measure
  source URLs. See `data/catalog/README.md`.
- `data/catalog/upcoming_2026.json` — the researched November 2026
  landscape, including litigation history and orientation notes.

## Where to look when something is missing

Missouri's canvass PDF for a given election appears weeks after the Board
of State Canvassers certifies (17 to 30 days in 2020–2024; the Aug 2026
primary's was still absent six weeks out). The results portal carries the
same certified county numbers the day certification is announced; use the
fetch script. Other states' election offices vary; Ballotpedia's measure
page usually links the official results.
