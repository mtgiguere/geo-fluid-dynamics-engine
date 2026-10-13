"""Freeze the 2026 pre-registration: DRAFT -> REGISTERED, in one step.

The protocol (docs/MEASUREMENT_DESIGN.md s7) says the registered files are
never edited after the registration commit. This script is that commit's
only author: it copies every DRAFT product for a given draft date to its
REGISTERED name, renames the sealed playbooks to match, re-hashes them, and
writes the REGISTERED manifest with the tested `geofluid.seal` helper. It
never recomputes a prediction - what was drafted is what is registered.

Usage (from the repo root):
    uv run python scripts/register_predictions.py --draft-date 2026-09-16 \
        [--registered-date 2026-10-14] [--dry-run]

Thin orchestration: the hashing lives in `geofluid.seal`, the predictions in
the drafts. Nothing here is a model.
"""

import argparse
import shutil
from datetime import date
from pathlib import Path

from geofluid.seal import sha256_manifest, verify_manifest

PRED_DIR = Path(__file__).resolve().parents[1] / "data" / "predictions"
PUBLIC_PRODUCTS = (
    "mo_2026-11-03",
    "statewide_only_2026-11-03",
    "county_receipts_mo",
    "county_record_buckets_mo",
    "propositions_2026-11-03",
    "inputs_manifest",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--draft-date", required=True, help="date suffix of the DRAFT files")
    parser.add_argument("--registered-date", default=date.today().isoformat())
    parser.add_argument("--dry-run", action="store_true", help="print the plan, touch nothing")
    args = parser.parse_args()
    d, r = args.draft_date, args.registered_date

    # 1. The public products: one DRAFT per product, copied verbatim.
    copies: list[tuple[Path, Path]] = []
    for product in PUBLIC_PRODUCTS:
        src = PRED_DIR / f"{product}_DRAFT_{d}.csv"
        if not src.exists():
            raise SystemExit(f"missing draft: {src.name}")
        copies.append((src, PRED_DIR / f"{product}_REGISTERED_{r}.csv"))

    # 2. The sealed playbooks: renamed in place (still git-ignored), then
    #    re-hashed into the REGISTERED manifest. The DRAFT manifest must
    #    agree with the files on disk first - a draft that drifted is not
    #    what we meant to seal.
    sealed = PRED_DIR / "sealed"
    draft_manifest = PRED_DIR / f"SEALED_MANIFEST_DRAFT_{d}.csv"
    if not draft_manifest.exists():
        raise SystemExit(f"missing draft manifest: {draft_manifest.name}")
    import pandas as pd

    check = verify_manifest(pd.read_csv(draft_manifest), root=PRED_DIR)
    if not bool(check["ok"].all()):
        bad = ", ".join(check.loc[~check["ok"], "file"])
        raise SystemExit(f"sealed drafts no longer match their manifest: {bad}")
    renames = [
        (p, p.with_name(p.name.replace(f"_DRAFT_{d}", f"_REGISTERED_{r}")))
        for p in sorted(sealed.glob(f"playbook_*_DRAFT_{d}.csv"))
    ]
    if len(renames) != len(check):
        raise SystemExit(f"expected {len(check)} sealed playbooks, found {len(renames)}")

    print(f"REGISTER drafts of {d} as REGISTERED {r}:")
    for src, dst in copies:
        print(f"  copy    {src.name} -> {dst.name}")
    for src, dst in renames:
        print(f"  rename  sealed/{src.name} -> sealed/{dst.name}")
    print(f"  write   SEALED_MANIFEST_REGISTERED_{r}.csv ({len(renames)} playbooks)")
    if args.dry_run:
        print("dry run: nothing written")
        return 0

    for src, dst in copies:
        if dst.exists():
            raise SystemExit(f"refusing to overwrite a registered file: {dst.name}")
        shutil.copyfile(src, dst)
    for src, dst in renames:
        src.rename(dst)
    manifest = sha256_manifest([dst for _s, dst in renames], root=PRED_DIR)
    manifest.to_csv(PRED_DIR / f"SEALED_MANIFEST_REGISTERED_{r}.csv", index=False)
    print("registered. Commit data/predictions/*_REGISTERED_* and never edit them again.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
