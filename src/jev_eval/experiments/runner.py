"""Generic concurrent experiment runner, shared by every dataset/primitive.

An experiment is just: a list of rows, a function that builds a request body from a row,
and a function that turns a successful client Result into a Prediction. Swapping in a new
dataset means writing those two functions, not touching this module.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable

from ..client.http import Result
from ..client.runctx import RunContext


@dataclass
class Prediction:
    id: str
    answer: Any
    probabilities: dict
    confidence: float | None
    latency_ms: float | None
    model: str | None
    cache_hit: bool
    error: str | None


def run_experiment(
    experiment: str,
    rows: list[dict],
    request_fn: Callable[[dict], dict],
    parse_fn: Callable[[dict, Result], Prediction],
    ctx: RunContext,
    concurrency: int = 4,
) -> list[Prediction]:
    def _one(row: dict) -> Prediction:
        result = ctx.run(experiment, request_fn(row))
        if not result.ok:
            return Prediction(
                id=row["id"], answer=None, probabilities={}, confidence=None,
                latency_ms=result.latency_ms, model=result.model,
                cache_hit=result.cache_hit, error=result.error,
            )
        try:
            return parse_fn(row, result)
        except Exception as e:
            return Prediction(
                id=row["id"], answer=None, probabilities={}, confidence=None,
                latency_ms=result.latency_ms, model=result.model,
                cache_hit=result.cache_hit, error=str(e),
            )

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        return list(pool.map(_one, rows))
