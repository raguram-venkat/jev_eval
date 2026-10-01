"""All question text: instructions, criteria and state builders for the three primitives.

Question text must never change in response to results (see PREMISE.md / DECISIONS.md).
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

MODEL = "jev-latest"

BANKING77_INSTRUCTIONS = "Which banking intent does this customer message express?"
BOOLQ_INSTRUCTIONS = "According to `passage`, is the answer to `question` yes?"
YELP_INSTRUCTIONS = "How positive is this customer's review?"

# Question ids are for our code only; the API never shows them to the model.
BANKING77_QID = "intent"
BOOLQ_QID = "answer"
YELP_QID = "stars"

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


def banking77_request(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": banking77_state(row),
        "model": MODEL,
        "questions": {
            BANKING77_QID: {
                "type": "choice",
                "instructions": BANKING77_INSTRUCTIONS,
                "criteria": banking77_criteria(row),
            }
        },
    }


def boolq_state(row: dict[str, Any]) -> dict[str, Any]:
    return {"passage": row["passage"], "question": row["question"]}


def boolq_request(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": boolq_state(row),
        "model": MODEL,
        "questions": {
            BOOLQ_QID: {"type": "noul", "instructions": BOOLQ_INSTRUCTIONS}
        },
    }


def yelp_state(row: dict[str, Any]) -> dict[str, Any]:
    return {"review": row["text"]}


def yelp_request(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": yelp_state(row),
        "model": MODEL,
        "questions": {
            YELP_QID: {
                "type": "score",
                "instructions": YELP_INSTRUCTIONS,
                "criteria": YELP_LEVELS,
            }
        },
    }


def questions_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
