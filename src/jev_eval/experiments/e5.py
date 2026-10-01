"""E5: latency. Client wall-clock for single- vs 5-question requests, plus a network baseline.

Always sequential (concurrency 1) and never cached — a latency number that came from disk
isn't a latency number. Uses Banking77 rows purely as realistic request content; the point
here is timing, not accuracy.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from . import e1
from ..client.runctx import RunContext
from ..protocol.questions import BANKING77_INSTRUCTIONS, BANKING77_QID, MODEL

WARMUPS = 10
SINGLES = 100
GROUP_SIZE = 30


@dataclass
class LatencySample:
    kind: str  # "single", "multi1", "multi5", "models"
    latency_ms: float


def scaled_counts(limit: int | None) -> tuple[int, int, int]:
    if limit is None:
        return WARMUPS, SINGLES, GROUP_SIZE
    return min(WARMUPS, limit), limit, min(GROUP_SIZE, limit)


def _choice_question(row: dict) -> dict:
    return {
        "type": "choice",
        "instructions": BANKING77_INSTRUCTIONS,
        "criteria": {opt: opt for opt in row["options"]},
    }


def _body(row: dict, n_questions: int) -> dict:
    q = _choice_question(row)
    return {
        "state": {"message": row["text"]},
        "model": MODEL,
        "questions": {f"q{i}": q for i in range(n_questions)},
    }


def rows_needed(limit: int | None) -> int:
    warmups, singles, group_size = scaled_counts(limit)
    return warmups + singles + 2 * group_size


def run(ctx: RunContext, limit: int | None) -> list[LatencySample]:
    warmups, singles, group_size = scaled_counts(limit)
    rows = e1.load_rows()
    needed = rows_needed(limit)
    if len(rows) < needed:
        raise ValueError(f"need {needed} distinct rows for E5, got {len(rows)}")
    pool = iter(rows)

    for _ in range(warmups):
        ctx.run("e5", _body(next(pool), 1))  # excluded from stats

    samples: list[LatencySample] = []
    for _ in range(singles):
        result = ctx.run("e5", _body(next(pool), 1))
        samples.append(LatencySample("single", result.latency_ms))

    for _ in range(group_size):
        result = ctx.run("e5", _body(next(pool), 1))
        samples.append(LatencySample("multi1", result.latency_ms))

    for _ in range(group_size):
        result = ctx.run("e5", _body(next(pool), 5))
        samples.append(LatencySample("multi5", result.latency_ms))

    client = ctx.client
    for _ in range(group_size):
        start = time.perf_counter()
        client.list_models()
        samples.append(LatencySample("models", (time.perf_counter() - start) * 1000))

    return samples
