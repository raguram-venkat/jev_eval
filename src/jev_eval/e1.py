"""E1: Banking77 label-count sweep (Choice)."""
from __future__ import annotations

import json
from pathlib import Path

from . import questions
from .client import Result
from .parsers import parse_choice
from .runner import Prediction

FROZEN_FILE = Path("data/frozen/banking77_sweep.jsonl")


def load_rows() -> list[dict]:
    return [json.loads(line) for line in FROZEN_FILE.read_text().splitlines()]


def _group_key(row: dict) -> tuple[int, int]:
    return (row["k"], row["draw"])


def stratified_sample(rows: list[dict], limit: int | None) -> list[dict]:
    """Round-robin across (k, draw) groups so a small --limit still covers every condition."""
    if limit is None or limit >= len(rows):
        return rows

    groups: dict[tuple[int, int], list[dict]] = {}
    for row in rows:
        groups.setdefault(_group_key(row), []).append(row)
    ordered_keys = sorted(groups)

    picked: list[dict] = []
    idx = 0
    while len(picked) < limit:
        round_start = len(picked)
        for gk in ordered_keys:
            if idx < len(groups[gk]):
                picked.append(groups[gk][idx])
                if len(picked) == limit:
                    return picked
        if len(picked) == round_start:
            break  # every group exhausted
        idx += 1
    return picked


def build_request(row: dict) -> dict:
    return questions.banking77_request(row)


def parse_result(row: dict, result: Result) -> Prediction:
    parsed = parse_choice(result.data, questions.BANKING77_QID, row["options"])
    return Prediction(
        id=row["id"],
        answer=parsed.answer,
        probabilities=parsed.probabilities,
        confidence=parsed.confidence,
        latency_ms=result.latency_ms,
        model=result.model,
        cache_hit=result.cache_hit,
        error=None,
    )
