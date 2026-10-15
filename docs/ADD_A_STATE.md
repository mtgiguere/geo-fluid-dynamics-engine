# Add a State (the programmer's companion to Bring Your Own State)

`docs/BRING_YOUR_OWN_STATE.md` tells a lay reader what it takes: five
ingredients, one of which needs a programmer. This is that one ingredient,
written for the programmer, with the Missouri loader as the worked example.
Budget a day for a clean state format, two for a messy one. The lie
detector at the end is not optional.

## 0. What you are producing

One function per state format that turns the state's certified results
file into the **canonical referendum panel**: one row per county,

| column | meaning |
|---|---|
| `fips` | five-character county FIPS as a string (state + county), or a documented pseudo-code for a jurisdiction that is not a county |
| `yes_votes` | int |
| `no_votes` | int |
| `total_votes` | `yes_votes + no_votes` |
| `no_share` | `no_votes / total_votes` |

Sorted by `fips`. Nothing about which answer is "progressive" lives in the
loader; that is a per-measure fact recorded in the catalog and applied by
`geofluid.panel.measures.Measure(progressive_side=...)` downstream. Every
existing loader funnels through `_assemble_referendum_panel` in
`src/geofluid/ingest/referendum.py`, which builds those columns from a long
`(fips, side, votes)` frame. Yours should too.

## 1. Get the file and read it by eye first

Download the state's official county-level results for the measure (see
`docs/DATA_SOURCES.md` for how each existing state publishes). Open it. Find:

- how counties are named (and which rows are not counties: statewide totals,
  cities that report separately, placeholder rows);
- where YES and NO live (columns, label rows, repeated per-page headers);
- the statewide total the publisher prints. Write that number down. It is
  your acceptance target.

Kansas was a workbook with a long main sheet and wide per-county sheets.
Kentucky a text export. Ohio a workbook with the header on the third row.
Missouri a PDF whose text repeats `"<contest> YES NO Total"` on every page
of a contest's section and ends with a `Total` row. Expect yours to be
different again.

## 2. Write the failing test first

Loaders are tested on **small synthetic fixtures that specify the
contract**, never on the real file (which is git-ignored). Add a section to
`tests/unit/test_referendum.py`. The Missouri tests are the template:

```python
_MO_NAME_TO_FIPS = {"Adair": "29001", "Andrew": "29003", "St. Louis City": "29510"}


def test_mo_parses_county_rows_into_canonical_panel() -> None:
    """Two counties under an 'Amendment 3 YES NO Total' header become the
    canonical panel. Derivation: Adair 4677 yes / 5509 no -> total 10186,
    no_share 5509/10186; the page's own Total row (sum of both counties)
    is consumed as an integrity check, not emitted as data."""
    page = _mo_page(
        "Amendment 3", ["Adair 4677 5509 10186", "Andrew 4104 5693 9797", "Total 8781 11202 19983"]
    )
    panel = parse_mo_canvass([page], "Amendment 3", _MO_NAME_TO_FIPS)
    assert list(panel["fips"]) == ["29001", "29003"]
    assert list(panel["yes_votes"]) == [4677, 4104]
    assert abs(panel["no_share"].iloc[0] - 5509 / 10186) < 1e-12
```

Write the derivation into the docstring before the assertion. Run the test.
Confirm it fails because the function does not exist. Only then write the
function. Then, one at a time, the tests the contract requires of every
loader:

- **Unknown jurisdiction fails loudly.** A county name missing from the
  name-to-FIPS map raises naming it. Kansas City is why: silently dropping
  it would vanish a hundred thousand of the most progressive votes in
  Missouri.
- **Integrity check against the file's own total.** If the publisher prints
  a statewide total, parsed counties must reproduce it exactly or the loader
  raises. If the file has no such row, say so in the docstring and lean
  harder on step 4.
- **Thousands separators, multi-page sections, missing sides**: whatever
  your format does, one test each.
- **Absent contest fails loudly** rather than returning an empty panel.

Split the function in two if the input is a file: a pure parser that takes
text or a frame (fully testable on fixtures), and a thin `load_*` shell that
opens the file (`pdfplumber`, `openpyxl`, plain `open`). The shell is the
only untested line, and it should be one line.

## 3. Name-to-FIPS is the caller's policy

Build the map from the MIT county returns (`county_name` → `county_fips` for
the state), then add aliases explicitly in code with a comment on each:

```python
fips_map.update(
    {
        "Kansas City": "2938000",  # reports separately; MIT place-code convention
        "McDonald": "29119",  # str.title() yields "Mcdonald"
        "St. Louis": "29189",  # the canvass drops the "County" suffix
        "De Kalb": "29063",  # the results portal spells it with a space
    }
)
```

A pseudo-jurisdiction needs a presidential baseline too, or it cannot be
compared to its partisanship. If the state's presidential file does not
report it separately, say so in the catalog note and exclude it from
partisanship-based analyses rather than inventing one.

## 4. The lie detector: certified-total acceptance

Run the loader on the real file and compare the statewide share to the
number the state certified. To the decimal. For every contest you intend to
use. Paste the output into the PR. The Missouri acceptance looked like:

```
Amendment 3 2024: parsed 51.60% yes (certified 51.60) — 116 jurisdictions
Proposition A 2024: parsed 57.57% yes (certified 57.57) — 116 jurisdictions
...
```

If one contest is off by a county, the loader is wrong, not the state. Do
not ship. This step is what lets a non-programmer trust the map: they can
check one number themselves.

## 5. Record the measure in the catalog

Add a row to `data/catalog/ballot_measures.csv` (or the upcoming-measures
JSON for a future vote): state, date, election type, topic, the ballot
text's meaning, certified `yes_pct`, and **`progressive_side`**: which
answer was the progressive vote. This is the one human judgement in the
pipeline and the easiest place to be silently, perfectly backwards. Read the
ballot language, not the campaign's name for it. In Kansas 2022 a NO vote
protected abortion rights; in Ohio 2023 a YES did; in Missouri's 2026
referendum a YES keeps the legislature's map.

## 6. Plug it in

- **Map overlay:** add an entry to `MEASURES` in `scripts/export_web_data.py`
  (id, loader, path, baseline year, `progressive_side`); rerun the export;
  the measure appears in the app's measure picker with its caption.
- **Contest panel:** wrap the panel in
  `Measure(measure_id, progressive_side, panel)` and stack with
  `build_measures_panel` to compare it against other measures.
- **Analysis:** a jupytext notebook under `notebooks/` that calls the
  tested library (`dissonance.issue_resistance`, `targeting.history_buckets`,
  `targeting.build_playbook`). Notebooks are exempt from TDD; the library
  is not.
- **A prediction:** follow `docs/MEASUREMENT_DESIGN.md` §7 and
  `data/predictions/README.md`. Register before the vote; score after.

## 7. Before you open the PR

```
uv run ruff check . && uv run ruff format . && uv run mypy && uv run pytest
```

The pre-commit hook runs the same gates. Add the new raw file to
`docs/DATA_SOURCES.md` with its source and quirks, and a line to
`CLAUDE.md`'s layout if you added a module. If the state's canvass is
published late but a results portal carries certified numbers earlier (as
Missouri's does), consider a fetch script like `scripts/fetch_mo_enr.cjs`
and a text parser with the same integrity check.

## The ESRI question

Everything above is free and documented. Doing it well for a state you do
not know, on a deadline, with a certified-total check and a prediction
registered in time, is the service. Both paths lead to the same map; the
documentation exists so that choosing the service is a decision, not a leap.
