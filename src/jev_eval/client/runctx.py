"""Thread-safe run bookkeeping: request cap, model-version guard, per-experiment failure counts."""
from __future__ import annotations

import threading
from collections import defaultdict

from .http import JevClient, ModelChangedError, RequestCapError, Result


class RunContext:
    def __init__(self, client: JevClient, cap: int = 4000) -> None:
        self._client = client
        self._cap = cap
        self._lock = threading.Lock()
        self._sent = 0
        self._model: str | None = None
        self._aborted: Exception | None = None
        self._failures: dict[str, int] = defaultdict(int)

    @property
    def client(self) -> JevClient:
        return self._client

    @property
    def model(self) -> str | None:
        return self._model

    @property
    def sent(self) -> int:
        return self._sent

    @property
    def remaining_cap(self) -> int:
        return self._cap - self._sent

    def failures(self, experiment: str) -> int:
        return self._failures[experiment]

    def reserve(self) -> None:
        with self._lock:
            if self._aborted is not None:
                raise self._aborted
            if self._sent >= self._cap:
                raise RequestCapError(f"reached cap of {self._cap} requests")
            self._sent += 1

    def _record_model(self, model: str | None) -> None:
        if model is None:
            return
        abort: Exception | None = None
        with self._lock:
            if self._model is None:
                self._model = model
            elif self._model != model and self._aborted is None:
                self._aborted = ModelChangedError(f"model changed from {self._model} to {model}")
                abort = self._aborted
        if abort is not None:
            raise abort

    def run(self, experiment: str, body: dict) -> Result:
        self.reserve()
        result = self._client.request(body)
        self._record_model(result.model)
        if not result.ok:
            with self._lock:
                self._failures[experiment] += 1
        return result
