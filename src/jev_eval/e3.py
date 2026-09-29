"""E3: Yelp ordinal scoring (Score)."""
from __future__ import annotations

import json
from pathlib import Path

from . import questions
from .client import Result
from .parsers import parse_score
from .runner import Prediction
from .sampling import stratified_sample as _stratified_sample

FROZEN_FILE = Path("data/frozen/yelp.jsonl")


def load_rows() -> list[dict]:
    return [json.loads(line) for line in FROZEN_FILE.read_text().splitlines()]


def stratified_sample(rows: list[dict], limit: int | None) -> list[dict]:
    return _stratified_sample(rows, limit, group_key=lambda r: r["stars"])


def build_request(row: dict) -> dict:
    return questions.yelp_request(row)


def parse_result(row: dict, result: Result) -> Prediction:
    parsed = parse_score(result.data, questions.YELP_QID, num_levels=len(questions.YELP_LEVELS))
    return Prediction(
        id=row["id"],
        answer=parsed.stars,
        probabilities={str(stars): p for stars, p in parsed.probabilities.items()},
        confidence=parsed.confidence,
        latency_ms=result.latency_ms,
        model=result.model,
        cache_hit=result.cache_hit,
        error=None,
    )
