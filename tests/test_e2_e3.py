import pytest

from jev_eval import e2, e3, questions
from jev_eval.client import JevClient
from jev_eval.runctx import RunContext
from jev_eval.runner import run_experiment


def test_e2_stratified_sample_is_balanced():
    rows = e2.load_rows()
    sample = e2.stratified_sample(rows, limit=20)
    assert sum(1 for r in sample if r["label"]) == 10
    assert sum(1 for r in sample if not r["label"]) == 10


def test_e2_build_request_is_noul():
    row = e2.load_rows()[0]
    body = e2.build_request(row)
    assert body["questions"][questions.BOOLQ_QID]["type"] == "noul"


def test_e2_end_to_end_against_fake_server(fake_server):
    def responder(seen, n, body):
        return (200, {"model": "jev-1.0.0", "answers": {questions.BOOLQ_QID: {"type": "noul", "noul": 0.9}}}, {})

    fake_server.set_responder("/v1/systemone", responder)
    rows = e2.load_rows()[:4]
    client = JevClient(base_url=fake_server.base_url, api_key="sentinel-key")
    try:
        predictions = run_experiment("e2", rows, e2.build_request, e2.parse_result, RunContext(client))
    finally:
        client.close()

    assert len(predictions) == 4
    for pred in predictions:
        assert pred.error is None
        assert pred.answer is True
        assert pred.probabilities == pytest.approx({"yes": 0.9, "no": 0.1})


def test_e3_stratified_sample_covers_every_star_rating():
    rows = e3.load_rows()
    sample = e3.stratified_sample(rows, limit=5)
    assert {r["stars"] for r in sample} == {1, 2, 3, 4, 5}


def test_e3_build_request_is_score():
    row = e3.load_rows()[0]
    body = e3.build_request(row)
    assert body["questions"][questions.YELP_QID]["type"] == "score"
    assert body["questions"][questions.YELP_QID]["criteria"] == questions.YELP_LEVELS


def test_e3_end_to_end_against_fake_server(fake_server):
    def responder(seen, n, body):
        return (200, {
            "model": "jev-1.0.0",
            "answers": {questions.YELP_QID: {
                "type": "score", "score": 4.0,
                "probabilities": {"0": 0.0, "1": 0.0, "2": 0.0, "3": 0.0, "4": 1.0},
            }},
        }, {})

    fake_server.set_responder("/v1/systemone", responder)
    rows = e3.load_rows()[:4]
    client = JevClient(base_url=fake_server.base_url, api_key="sentinel-key")
    try:
        predictions = run_experiment("e3", rows, e3.build_request, e3.parse_result, RunContext(client))
    finally:
        client.close()

    assert len(predictions) == 4
    for pred in predictions:
        assert pred.error is None
        assert pred.answer == 5  # level 4 -> 5 stars
        assert pred.probabilities["5"] == 1.0
