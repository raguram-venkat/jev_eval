"""All question text: instructions, criteria and state builders for the three primitives.

Question text must never change in response to results (see PREMISE.md / DECISIONS.md).
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

BANKING77_INSTRUCTIONS = "Which banking intent does this customer message express?"
BOOLQ_INSTRUCTIONS = "According to `passage`, is the answer to `question` yes?"

# Level i (0-based on the wire) is i + 1 stars.
YELP_LEVELS = [
    "very negative experience",
    "negative experience",
    "mixed or neutral experience",
    "positive experience",
    "excellent experience",
]


def banking77_state(row: dict[str, Any]) -> dict[str, Any]:
    return {"message": row["text"]}


def banking77_criteria(row: dict[str, Any]) -> dict[str, str]:
    return {opt: opt for opt in row["options"]}


def boolq_state(row: dict[str, Any]) -> dict[str, Any]:
    return {"passage": row["passage"], "question": row["question"]}


def yelp_state(row: dict[str, Any]) -> dict[str, Any]:
    return {"review": row["text"]}


def questions_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
