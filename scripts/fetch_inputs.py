"""Fetch the raw inputs behind the 2026 registration and verify them (thin orchestration).

"Anyone can verify in December" needs the inputs, and data/raw/ is
git-ignored. This script downloads what can be downloaded unattended (the
six Missouri Secretary of State canvass PDFs), tells you exactly how to get
the two that cannot (the MIT county returns file, behind a Dataverse
guestbook; the Aug-2026 portal texts, via scripts/fetch_mo_enr.cjs), and
then checks every file against the digests frozen in the registered inputs
manifest. The hashing is geofluid.seal (tested); this is glue.

Run:  uv run python scripts/fetch_inputs.py [--manifest <path>] [--no-download]
"""

import argparse
import urllib.request
from pathlib import Path

import pandas as pd

from geofluid.seal import verify_manifest

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SOS = "https://www.sos.mo.gov/CMSImages/ElectionResultsStatistics/"
# The SoS site returns 403 to a bare client and 200 to a browser User-Agent.
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)
CANVASSES = [
    "ActualResults-November62018-FINAL.pdf",
    "ActualResults-August72018.pdf",
    "ActualResults-August42020.pdf",
    "ActualResults-November32020.pdf",
    "ActualResults-August62024.pdf",
    "ActualResults-November52024.pdf",
]
MANUAL = {
    "countypres_2000-2024.csv": (
        "MIT Election Lab, County Presidential Election Returns 2000-2024, Harvard Dataverse "
        "doi:10.7910/DVN/VOQCHQ (release 20260225). Browser download only (guestbook); "
        "save as data/raw/countypres_2000-2024.csv."
    ),
    "enr_mo_20260804_amendment_": (
        "Aug-2026 primary county tables from enr.sos.mo.gov: "
        "NODE_PATH=web/node_modules node scripts/fetch_mo_enr.cjs --out data/raw "
        "--prefix enr_mo_20260804 --match amendment   (then rename to "
        "enr_mo_20260804_amendment_<n>.txt as listed in the manifest)."
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    default = sorted(ROOT.glob("data/predictions/inputs_manifest_REGISTERED_*.csv"))
    parser.add_argument("--manifest", default=str(default[-1]) if default else None)
    parser.add_argument("--no-download", action="store_true", help="verify only")
    args = parser.parse_args()
    if not args.manifest:
        raise SystemExit("no registered inputs manifest found")
    RAW.mkdir(parents=True, exist_ok=True)

    if not args.no_download:
        for name in CANVASSES:
            dest = RAW / name
            if dest.exists():
                print(f"have     {name}")
                continue
            # S310: the host is the fixed https SoS URL above, never user input.
            req = urllib.request.Request(SOS + name, headers={"User-Agent": UA})  # noqa: S310
            with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
                dest.write_bytes(resp.read())
            print(f"fetched  {name} ({dest.stat().st_size:,} bytes)")

    manifest = pd.read_csv(args.manifest)
    present = manifest[manifest["file"].map(lambda f: (RAW / f).exists())]
    missing = manifest[~manifest["file"].isin(present["file"])]
    if len(present):
        checked = verify_manifest(present, root=RAW)
        for row in checked.itertuples():
            print(f"{'ok      ' if row.ok else 'MISMATCH'} {row.file}")
    for name in missing["file"]:
        print(f"missing  {name}")
        for key, how in MANUAL.items():
            if name.startswith(key):
                print(f"         -> {how}")
    bad = int((~checked["ok"]).sum()) if len(present) else 0
    print(
        f"\n{len(present) - bad} verified, {bad} mismatched, {len(missing)} missing "
        f"(manifest: {Path(args.manifest).name})"
    )
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
