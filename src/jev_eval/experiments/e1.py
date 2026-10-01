"""E1: Banking77 label-count sweep (Choice)."""
from __future__ import annotations

import json
from pathlib import Path

from ..client.http import Result
from ..protocol import questions
from ..protocol.parsers import parse_choice
from .runner import Prediction
from .sampling import stratified_sample as _stratified_sample

FROZEN_FILE = Path("data/frozen/banking77_sweep.jsonl")


def load_rows() -> list[dict]:
    return [json.loads(line) for line in FROZEN_FILE.read_text().splitlines()]


def stratified_sample(rows: list[dict], limit: int | None) -> list[dict]:
    return _stratified_sample(rows, limit, group_key=lambda r: (r["k"], r["draw"]))


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
