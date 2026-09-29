import hashlib
import json
from pathlib import Path

import pytest

from jev_eval.frozen import FrozenDataError, verify


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_manifest(tmp_path: Path, files: dict) -> None:
    (tmp_path / "manifest.json").write_text(json.dumps({"files": files}))


def test_verify_passes_on_real_frozen_data():
    verify(Path("data/frozen"))


def test_one_byte_change_aborts(tmp_path):
    data_file = tmp_path / "a.jsonl"
    data_file.write_text("hello\n")
    _write_manifest(tmp_path, {"a": {"file": "a.jsonl", "sha256": _sha256(data_file)}})
    data_file.write_text("hellp\n")
    with pytest.raises(FrozenDataError, match="hash mismatch"):
        verify(tmp_path)


def test_missing_data_file_aborts(tmp_path):
    _write_manifest(tmp_path, {"a": {"file": "missing.jsonl", "sha256": "deadbeef"}})
    with pytest.raises(FrozenDataError, match="missing data file"):
        verify(tmp_path)


def test_missing_manifest_aborts(tmp_path):
    with pytest.raises(FrozenDataError, match="missing manifest"):
        verify(tmp_path)


def test_invalid_json_manifest_aborts(tmp_path):
    (tmp_path / "manifest.json").write_text("{not json")
    with pytest.raises(FrozenDataError, match="invalid manifest JSON"):
        verify(tmp_path)


def test_never_opens_data_file_for_writing(tmp_path, monkeypatch):
    data_file = tmp_path / "a.jsonl"
    data_file.write_text("hello\n")
    _write_manifest(tmp_path, {"a": {"file": "a.jsonl", "sha256": _sha256(data_file)}})

    orig_open = Path.open

    def spy_open(self, mode="r", *args, **kwargs):
        if self == data_file and set("wa+").intersection(mode):
            raise AssertionError(f"opened {self} for writing")
        return orig_open(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", spy_open)
    verify(tmp_path)
