"""The seal: commit to a file's content without publishing the file.

The 2026 protocol drafts playbooks alongside the predictions and commits them
SEALED, revealing them only after the November scorecard. In a public
repository a committed file is a published file, so the seal is a hash: the
SHA-256 manifest of the playbook files is committed by the registration
deadline, the files stay out of git until the unseal, and verify_manifest
proves in December that what is revealed is byte-for-byte what was sealed.
Git history is the notary; the hash is the wax.
"""

import hashlib
from collections.abc import Iterable
from pathlib import Path

import pandas as pd


def sha256_manifest(paths: Iterable[Path], *, root: Path) -> pd.DataFrame:
    """One row per file: path relative to `root`, SHA-256 hex digest, size."""
    rows = []
    for path in paths:
        data = Path(path).read_bytes()
        rows.append(
            {
                "file": Path(path).relative_to(root).as_posix(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
    return pd.DataFrame(rows, columns=["file", "sha256", "bytes"])


def verify_manifest(manifest: pd.DataFrame, *, root: Path) -> pd.DataFrame:
    """Re-hash every file named in `manifest` under `root`; `ok` is True only
    when the digest matches the sealed one exactly."""
    current = sha256_manifest([root / f for f in manifest["file"]], root=root)
    out = manifest[["file", "sha256"]].merge(
        current.rename(columns={"sha256": "sha256_now"}), on="file"
    )
    out["ok"] = out["sha256"] == out["sha256_now"]
    return out[["file", "sha256", "sha256_now", "ok"]]
