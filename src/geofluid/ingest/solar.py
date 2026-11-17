"""Ingest Berkeley Lab's rooftop-solar data file into a canonical install table.

The raw input is Lawrence Berkeley National Laboratory's public data file
(Tracking the Sun / Distributed Solar, 2026 edition): one row per PV system,
with an install date and the host's ZIP code. The output is one row per
install, the input to the adoption panel that the wave and timing models read.

Why this data: solar is an idea known to spread person to person, recorded
install by install. It is the "known wave" the engine is tested on before the
same machinery is pointed back at politics.
"""

import pandas as pd

INSTALL_COLUMNS = ["state", "zip5", "install_date", "residential"]


def _zip5(zip_code: pd.Series) -> pd.Series:
    """Normalise the raw ZIP text to a five-digit ZIP."""
    # About 2.2 million California rows store the ZIP as a float's text
    # ("93004.0"); the ZIP is the integer part.
    # Padding is common (" 61801", "85621       ", a trailing non-breaking
    # space); str.strip() removes Unicode whitespace, \xa0 included.
    z = zip_code.str.strip().str.removesuffix(".0").str.split("-").str[0]
    # New England / New Jersey ZIPs start with 0; ~248,000 rows lost it when
    # the ZIP was once stored as a number ("6033" is Connecticut's 06033).
    z = z.where(z.str.len() != 4, z.str.zfill(5))
    # What is left is a ZIP only if it is five digits, or nine (ZIP+4 run
    # together, "846632587"; the hyphenated form was split off above).
    # Everything else ("-1", "redacted", "Multiple", "0", "301", "852485", a
    # spilled city field) is missing, never a guess.
    usable = z.str.fullmatch(r"\d{5}|\d{9}").fillna(False).astype(bool)
    return z.str[:5].where(usable)


def load_solar_installs(raw: pd.DataFrame) -> pd.DataFrame:
    """Transform raw LBNL rows into the canonical install table."""
    installs = pd.DataFrame(
        {
            "state": raw["state"],
            "zip5": _zip5(raw["zip_code"]),
            # The raw timestamp is a calendar date at midnight
            # ("2015-10-26T00:00:00.000000000"); the first ten characters are
            # the date itself.
            "install_date": pd.to_datetime(raw["installation_date"].str[:10]),
            # A household choosing solar is the idea tracked: RES, RES_SF
            # (single-family), RES_MF (multi-family). Unknown ("-1", blank) is
            # not residential, and the column is a plain True/False with no
            # missing values whatever text type the raw column arrived as.
            "residential": raw["customer_segment"].str.startswith("RES", na=False).astype(bool),
        }
    )
    return installs.loc[:, INSTALL_COLUMNS]


PANEL_COLUMNS = ["fips", "quarter", "new_installs", "cumulative_installs"]

# State FIPS prefix -> postal code: reference data for checking that an
# install's ZIP lands in a county of its own state. 50 states and DC.
_STATE_POSTAL = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT",
    "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL",
    "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD",
    "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE",
    "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
    "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV",
    "55": "WI", "56": "WY",
}  # fmt: skip


def county_adoption_panel(installs: pd.DataFrame, lookup: pd.DataFrame) -> pd.DataFrame:
    """Count household installs per county per quarter, new and cumulative.

    `installs` is `load_solar_installs` output; `lookup` is
    `geofluid.ingest.zcta_county.zip_to_county` output (one county per ZIP).
    A quarter is labelled by its first day.
    """
    # The idea tracked is a household choosing solar; schools, businesses
    # and farms are other decisions.
    df = installs[installs["residential"]].merge(lookup, on="zip5")
    # An install whose ZIP lands in another state's county has two fields
    # that disagree (0.056% of the real file: mostly DC-labelled installs on
    # ZIPs whose land is mainly in Maryland, plus typos). The county is not
    # trusted, so the install is left out.
    df = df[df["fips"].str[:2].map(_STATE_POSTAL) == df["state"]]
    df["quarter"] = df["install_date"].dt.to_period("Q").dt.start_time
    counts = df.groupby(["fips", "quarter"]).size()
    # The timing model reads WHEN a county takes off, so quiet quarters are
    # rows with zero, not gaps: every county gets every quarter of the span.
    span = pd.date_range(df["quarter"].min(), df["quarter"].max(), freq="QS")
    grid = pd.MultiIndex.from_product(
        [sorted(df["fips"].unique()), span], names=["fips", "quarter"]
    )
    panel = counts.reindex(grid, fill_value=0).rename("new_installs").reset_index()
    panel["cumulative_installs"] = panel.groupby("fips")["new_installs"].cumsum()
    return panel.loc[:, PANEL_COLUMNS]
