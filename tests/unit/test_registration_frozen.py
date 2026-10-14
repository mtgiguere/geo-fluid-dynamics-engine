"""The freeze guard: registered prediction files can never change.

The 2026 protocol (MEASUREMENT_DESIGN.md s7) says a REGISTERED file is never
edited after the registration commit. A rule nobody enforces is decoration,
so this test enforces it on every pytest run - the pre-commit hook and CI
both refuse any commit, on any branch, that alters a byte of a registered
file. The registration script writes REGISTERED_SHA256_<date>.csv alongside
the files; this test re-hashes every file it names.
"""

from pathlib import Path

import pandas as pd

from geofluid.seal import verify_manifest

PRED = Path(__file__).resolve().parents[2] / "data" / "predictions"


def test_every_registered_file_matches_its_committed_digest() -> None:
    """At least one registration manifest exists (the 2026 freeze), and
    every file it names re-hashes to the digest committed at registration."""
    manifests = sorted(PRED.glob("REGISTERED_SHA256_*.csv"))
    assert manifests, "no REGISTERED_SHA256_<date>.csv: the registration has not been committed"
    for manifest in manifests:
        checked = verify_manifest(pd.read_csv(manifest), root=PRED)
        drifted = list(checked.loc[~checked["ok"], "file"])
        assert not drifted, f"registered files changed since {manifest.name}: {drifted}"
