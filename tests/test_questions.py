import json
from pathlib import Path

from jev_eval.protocol.questions import (
    BANKING77_QID,
    BOOLQ_QID,
    YELP_LEVELS,
    YELP_QID,
    banking77_criteria,
    banking77_request,
    banking77_state,
    boolq_request,
    boolq_state,
    questions_hash,
    yelp_request,
    yelp_state,
)


def test_banking77_state_is_message_only():
    row = {"text": "I want a refund", "options": ["refund", "top up"]}
    assert banking77_state(row) == {"message": "I want a refund"}


def test_banking77_criteria_maps_options_to_themselves_in_order():
    row = {"options": ["b", "a", "c"]}
    criteria = banking77_criteria(row)
    assert criteria == {"b": "b", "a": "a", "c": "c"}
    assert list(criteria) == ["b", "a", "c"]


def test_boolq_state_keys():
    row = {"passage": "p", "question": "q"}
    assert boolq_state(row) == {"passage": "p", "question": "q"}


def test_yelp_state():
    assert yelp_state({"text": "great"}) == {"review": "great"}


def test_yelp_has_five_ordered_levels():
    assert len(YELP_LEVELS) == 5
    assert all(isinstance(level, str) for level in YELP_LEVELS)


def test_questions_hash_is_stable():
    assert questions_hash() == questions_hash()


def test_golden_banking77_request_row0():
    row = json.loads(Path("data/frozen/banking77_sweep.jsonl").read_text().splitlines()[0])
    assert row["id"] == "b77-k2-d0-0"
    assert banking77_state(row) == {"message": "I want this amount reversed out of my account."}
    assert banking77_criteria(row) == {"automatic top up": "automatic top up", "request refund": "request refund"}


def test_golden_boolq_request_row0():
    row = json.loads(Path("data/frozen/boolq.jsonl").read_text().splitlines()[0])
    assert row["id"] == "boolq-0"
    assert boolq_state(row) == {
        "passage": row["passage"],
        "question": "did the brewers make it to the world series",
    }


def test_banking77_request_shape():
    row = {"text": "hi", "options": ["a", "b"]}
    body = banking77_request(row)
    assert body["state"] == {"message": "hi"}
    assert body["questions"][BANKING77_QID]["type"] == "choice"
    assert body["questions"][BANKING77_QID]["criteria"] == {"a": "a", "b": "b"}


def test_boolq_request_shape():
    row = {"passage": "p", "question": "q"}
    body = boolq_request(row)
    assert body["state"] == {"passage": "p", "question": "q"}
    assert body["questions"][BOOLQ_QID]["type"] == "noul"
    assert "criteria" not in body["questions"][BOOLQ_QID]


def test_yelp_request_shape():
    row = {"text": "great stay"}
    body = yelp_request(row)
    assert body["state"] == {"review": "great stay"}
    assert body["questions"][YELP_QID]["type"] == "score"
    assert body["questions"][YELP_QID]["criteria"] == YELP_LEVELS
