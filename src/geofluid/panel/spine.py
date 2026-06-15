"""The returns spine: one 1868-2024 county panel from two sources.

The Algara-Sharif historical loader and the MIT modern loader emit the same
canonical schema. The spine joins them at a cutover year: the modern source
(validated, demographic-bearing) is authoritative from `cutover_year` on, and
the historical source supplies only the years before it — so the overlap is
resolved in the modern source's favour and never double-counted.
"""

import pandas as pd


def build_returns_spine(
    historical: pd.DataFrame,
    modern: pd.DataFrame,
    cutover_year: int = 2000,
) -> pd.DataFrame:
    """Stitch historical (pre-cutover) and modern (cutover onward) returns
    into one (fips, year) panel, modern winning the overlap."""
    before = historical[historical["year"] < cutover_year]
    on_and_after = modern[modern["year"] >= cutover_year]
    return (
        pd.concat([before, on_and_after], ignore_index=True)
        .sort_values(["fips", "year"], ignore_index=True)
        .loc[:, list(modern.columns)]
    )
