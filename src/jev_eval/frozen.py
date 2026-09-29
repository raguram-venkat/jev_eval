"""Verify data/frozen/ against its manifest. Read-only, never opened for writing."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


class FrozenDataError(RuntimeError):
    pass


def verify(frozen_dir: Path) -> None:
    manifest_path = frozen_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text())
    except FileNotFoundError:
        raise FrozenDataError(f"missing manifest: {manifest_path}")
    except json.JSONDecodeError as e:
        raise FrozenDataError(f"invalid manifest JSON: {manifest_path}: {e}")

    for name, info in manifest["files"].items():
        path = frozen_dir / info["file"]
        if not path.exists():
            raise FrozenDataError(f"missing data file: {path}")
        actual = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
        if actual != info["sha256"]:
            raise FrozenDataError(f"hash mismatch for {path}: expected {info['sha256']}, got {actual}")
