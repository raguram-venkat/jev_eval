"""Disk response cache under cache/, keyed by sha256(requested model + canonical request body).

Entries are written as temp-file-then-os.replace so a reader never sees a half-written file.
Never stores headers or the request body — only what's needed to serve a hit and feed the
run's model-version guard.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


class Cache:
    def __init__(self, directory: Path) -> None:
        self._dir = Path(directory)

    def make_key(self, requested_model: str | None, canonical_body: str) -> str:
        return hashlib.sha256(f"{requested_model}\n{canonical_body}".encode()).hexdigest()

    def _path(self, key: str) -> Path:
        return self._dir / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        try:
            return json.loads(self._path(key).read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def put(self, key: str, requested_model: str | None, model: str, latency_ms: float, response: dict[str, Any]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "key": key,
            "requested_model": requested_model,
            "model": model,
            "latency_ms": latency_ms,
            "response": response,
        }
        path = self._path(key)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(entry))
        os.replace(tmp, path)
