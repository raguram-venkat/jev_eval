"""Sync HTTP client for POST {base_url}/v1/systemone: retry, typed errors, optional cache."""
from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from typing import Any, Callable

import httpx

from .cache import Cache

MAX_ATTEMPTS = 5
MAX_BACKOFF_S = 30.0
MAX_RETRY_AFTER_S = 60.0
REQUEST_CAP = 4000


class AuthError(RuntimeError):
    pass


class ModelChangedError(RuntimeError):
    pass


class RequestCapError(RuntimeError):
    pass


class PreflightError(RuntimeError):
    pass


@dataclass
class Result:
    ok: bool
    model: str | None = None
    data: dict[str, Any] | None = None
    latency_ms: float | None = None
    cache_hit: bool = False
    error: str | None = None


def canonical_body(body: dict[str, Any]) -> str:
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


class JevClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        cache: Cache | None = None,
        sleep: Callable[[float], None] = time.sleep,
        jitter: Callable[[], float] = random.random,
        max_attempts: int = MAX_ATTEMPTS,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._cache = cache
        self._sleep = sleep
        self._jitter = jitter
        self._max_attempts = max_attempts
        self._client = httpx.Client(transport=transport, timeout=30.0)

    def __repr__(self) -> str:
        return f"JevClient(base_url={self._base_url!r})"

    __str__ = __repr__

    def close(self) -> None:
        self._client.close()

    def preflight(self) -> None:
        url = f"{self._base_url}/v1/models"
        try:
            resp = self._client.get(url, headers=self._headers)
        except httpx.TransportError as e:
            raise PreflightError(f"preflight failed: GET {url}: {type(e).__name__}") from e
        if resp.status_code != 200:
            raise PreflightError(f"preflight failed: GET {url}: status {resp.status_code}")

    def plan(self, bodies: list[dict[str, Any]], cap: int = REQUEST_CAP) -> int:
        if self._cache is None:
            planned = len(bodies)
        else:
            planned = sum(
                1 for b in bodies
                if self._cache.get(self._cache.make_key(b.get("model"), canonical_body(b))) is None
            )
        if planned > cap:
            raise RequestCapError(f"planned {planned} requests exceeds cap of {cap}")
        return planned

    def request(self, body: dict[str, Any]) -> Result:
        requested_model = body.get("model")
        key = None
        if self._cache is not None:
            key = self._cache.make_key(requested_model, canonical_body(body))
            cached = self._cache.get(key)
            if cached is not None:
                return Result(
                    ok=True, model=cached["model"], data=cached["response"],
                    latency_ms=cached["latency_ms"], cache_hit=True,
                )

        url = f"{self._base_url}/v1/systemone"
        last_error = "no attempts made"
        for attempt in range(1, self._max_attempts + 1):
            start = time.perf_counter()
            try:
                resp = self._client.post(url, headers=self._headers, json=body)
            except httpx.TransportError as e:
                last_error = f"{type(e).__name__}: {e}"
                if attempt < self._max_attempts:
                    self._sleep(self._backoff(attempt, None))
                continue

            latency_ms = (time.perf_counter() - start) * 1000

            if resp.status_code in (401, 403):
                raise AuthError(f"auth error: status {resp.status_code}")

            if resp.status_code == 429 or resp.status_code >= 500:
                last_error = f"status {resp.status_code}: {resp.text[:200]}"
                if attempt < self._max_attempts:
                    self._sleep(self._backoff(attempt, resp.headers.get("Retry-After")))
                continue

            if resp.status_code != 200:
                return Result(ok=False, error=f"status {resp.status_code}: {resp.text[:200]}")

            try:
                data = resp.json()
                model = data["model"]
                if not isinstance(model, str):
                    raise TypeError
            except (json.JSONDecodeError, KeyError, TypeError):
                return Result(ok=False, error="malformed response: missing string 'model' field")

            if self._cache is not None and key is not None:
                self._cache.put(key, requested_model, model, latency_ms, data)
            return Result(ok=True, model=model, data=data, latency_ms=latency_ms)

        return Result(ok=False, error=last_error)

    def _backoff(self, attempt: int, retry_after: str | None) -> float:
        if retry_after is not None:
            try:
                return min(float(retry_after), MAX_RETRY_AFTER_S) + self._jitter()
            except ValueError:
                pass
        return min(2 ** (attempt - 1), MAX_BACKOFF_S) + self._jitter()
