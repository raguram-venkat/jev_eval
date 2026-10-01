"""Parse /v1/systemone responses into normalized predictions, one function per primitive.

A response with a missing answer, wrong type, or non-numeric probabilities raises
ParseError; callers record the row with an error and exclude it from metrics.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


class ParseError(ValueError):
    pass


@dataclass
class ChoiceParsed:
    answer: str | None
    probabilities: dict[str, float]
    confidence: float | None
    is_argmax: bool


@dataclass
class NoulParsed:
    p_yes: float
    p_no: float


@dataclass
class ScoreParsed:
    stars: int  # argmax level, 1-based
    score: float  # returned score shifted onto the 1..len(levels) stars scale
    confidence: float | None
    probabilities: dict[int, float]  # 1-based stars -> probability


def _answer(response: dict[str, Any], qid: str) -> dict[str, Any]:
    try:
        answer = response["answers"][qid]
    except (KeyError, TypeError) as e:
        raise ParseError(f"missing answers[{qid!r}]") from e
    if not isinstance(answer, dict):
        raise ParseError(f"answers[{qid!r}] is not an object")
    return answer


def _clip_and_normalize(values: dict[Any, float], qid: str) -> dict[Any, float]:
    """Clip each value to [0, 1], then rescale so the set sums to 1."""
    clipped = {}
    for k, v in values.items():
        c = min(1.0, max(0.0, v))
        if c != v:
            logger.warning("probability for %r in %r clipped from %r to %r", k, qid, v, c)
        clipped[k] = c
    total = sum(clipped.values())
    if total <= 0:
        raise ParseError(f"answers[{qid!r}].probabilities sum to 0")
    if abs(total - 1.0) > 1e-9:
        logger.warning("probabilities for %r summed to %r, renormalised", qid, total)
        clipped = {k: v / total for k, v in clipped.items()}
    return clipped


def parse_choice(response: dict[str, Any], qid: str, options: list[str]) -> ChoiceParsed:
    answer = _answer(response, qid)
    if answer.get("type") != "choice":
        raise ParseError(f"answers[{qid!r}].type is not 'choice'")
    raw = answer.get("probabilities")
    if not isinstance(raw, dict):
        raise ParseError(f"answers[{qid!r}].probabilities is not an object")

    values: dict[str, float] = {}
    for opt in options:
        if opt not in raw:
            logger.warning("choice probabilities missing option %r for %r, treated as 0", opt, qid)
        try:
            values[opt] = float(raw.get(opt, 0.0))
        except (TypeError, ValueError):
            raise ParseError(f"answers[{qid!r}].probabilities[{opt!r}] is not numeric")

    probs = _clip_and_normalize(values, qid)
    argmax_option = max(probs, key=probs.get)
    given = answer.get("choice")
    return ChoiceParsed(
        answer=given,
        probabilities=probs,
        confidence=answer.get("confidence"),
        is_argmax=(given == argmax_option),
    )


def parse_noul(response: dict[str, Any], qid: str) -> NoulParsed:
    answer = _answer(response, qid)
    if answer.get("type") != "noul":
        raise ParseError(f"answers[{qid!r}].type is not 'noul'")
    try:
        p_yes = float(answer["noul"])
    except (KeyError, TypeError, ValueError) as e:
        raise ParseError(f"answers[{qid!r}].noul is missing or non-numeric") from e
    p_yes = min(1.0, max(0.0, p_yes))
    return NoulParsed(p_yes=p_yes, p_no=1.0 - p_yes)


def parse_score(response: dict[str, Any], qid: str, num_levels: int) -> ScoreParsed:
    answer = _answer(response, qid)
    if answer.get("type") != "score":
        raise ParseError(f"answers[{qid!r}].type is not 'score'")
    raw = answer.get("probabilities")
    if not isinstance(raw, dict):
        raise ParseError(f"answers[{qid!r}].probabilities is not an object")

    values: dict[int, float] = {}
    for level in range(num_levels):
        if str(level) not in raw:
            logger.warning("score probabilities missing level %d for %r, treated as 0", level, qid)
        try:
            values[level] = float(raw.get(str(level), 0.0))
        except (TypeError, ValueError):
            raise ParseError(f"answers[{qid!r}].probabilities[{level!r}] is not numeric")

    by_level = _clip_and_normalize(values, qid)
    probs = {level + 1: p for level, p in by_level.items()}  # 1-based stars

    try:
        score = float(answer["score"])
    except (KeyError, TypeError, ValueError) as e:
        raise ParseError(f"answers[{qid!r}].score is missing or non-numeric") from e

    stars = max(probs, key=probs.get)
    return ScoreParsed(stars=stars, score=score + 1.0, confidence=answer.get("confidence"), probabilities=probs)
