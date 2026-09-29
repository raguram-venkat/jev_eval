"""E2: BoolQ yes/no calibration (Noul)."""
from __future__ import annotations

import json
from pathlib import Path

from . import questions
from .client import Result
from .parsers import parse_noul
from .runner import Prediction
from .sampling import stratified_sample as _stratified_sample

FROZEN_FILE = Path("data/frozen/boolq.jsonl")


def load_rows() -> list[dict]:
    return [json.loads(line) for line in FROZEN_FILE.read_text().splitlines()]


def stratified_sample(rows: list[dict], limit: int | None) -> list[dict]:
    return _stratified_sample(rows, limit, group_key=lambda r: r["label"])


def build_request(row: dict) -> dict:
    return questions.boolq_request(row)


def parse_result(row: dict, result: Result) -> Prediction:
    parsed = parse_noul(result.data, questions.BOOLQ_QID)
    return Prediction(
        id=row["id"],
        answer=parsed.p_yes >= 0.5,
        probabilities={"yes": parsed.p_yes, "no": parsed.p_no},
        confidence=None,  # Noul has no separate confidence field on the wire
        latency_ms=result.latency_ms,
        model=result.model,
        cache_hit=result.cache_hit,
        error=None,
    )
