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
