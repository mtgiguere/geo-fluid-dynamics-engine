"""Tests for the seal - committing to a file's content without publishing it.

The 2026 protocol commits playbooks SEALED and reveals them after the
scorecard. In a public repository a committed file is a published file, so
the seal is a hash: commit the SHA-256 of each playbook now (the manifest),
keep the file itself out of git, commit the file in December and verify it
against the manifest. Git history is the notary; the hash is the wax.
"""

from pathlib import Path

from geofluid.seal import sha256_manifest, verify_manifest

# SHA-256 of the three bytes b"abc" - the standard test vector from FIPS 180-2.
_ABC_SHA256 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_manifest_records_sha256_and_size_per_file(tmp_path: Path) -> None:
    """One file holding b"abc": the manifest row carries its name relative to
    the root, the FIPS 180-2 test-vector digest, and 3 bytes."""
    (tmp_path / "playbook.csv").write_bytes(b"abc")

    manifest = sha256_manifest([tmp_path / "playbook.csv"], root=tmp_path)

    assert list(manifest["file"]) == ["playbook.csv"]
    assert list(manifest["sha256"]) == [_ABC_SHA256]
    assert list(manifest["bytes"]) == [3]


def test_verify_flags_a_changed_file(tmp_path: Path) -> None:
    """Seal b"abc", then change the file to b"abd": verification must report
    ok=False for it (and True for an untouched sibling). A seal that cannot
    detect a one-byte edit is decoration."""
    (tmp_path / "a.csv").write_bytes(b"abc")
    (tmp_path / "b.csv").write_bytes(b"xyz")
    manifest = sha256_manifest([tmp_path / "a.csv", tmp_path / "b.csv"], root=tmp_path)
    (tmp_path / "a.csv").write_bytes(b"abd")

    checked = verify_manifest(manifest, root=tmp_path).set_index("file")

    assert not bool(checked.loc["a.csv", "ok"])
    assert bool(checked.loc["b.csv", "ok"])
