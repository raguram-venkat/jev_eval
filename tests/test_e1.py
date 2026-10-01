from jev_eval.client.cache import Cache
from jev_eval.client.http import JevClient
from jev_eval.client.runctx import RunContext
from jev_eval.experiments import e1
from jev_eval.experiments.runner import run_experiment
from jev_eval.protocol import questions


def test_stratified_sample_covers_every_group():
    rows = e1.load_rows()
    groups = {(r["k"], r["draw"]) for r in rows}
    sample = e1.stratified_sample(rows, limit=len(groups))
    assert {(r["k"], r["draw"]) for r in sample} == groups
    assert len(sample) == len(groups)


def test_stratified_sample_returns_everything_when_limit_covers_all_rows():
    rows = e1.load_rows()
    assert e1.stratified_sample(rows, limit=None) == rows
    assert e1.stratified_sample(rows, limit=len(rows) + 100) == rows


def test_stratified_sample_is_deterministic():
    rows = e1.load_rows()
    assert e1.stratified_sample(rows, 20) == e1.stratified_sample(rows, 20)


def test_build_request_is_a_choice_question_keyed_by_options():
    row = e1.load_rows()[0]
    body = e1.build_request(row)
    q = body["questions"][questions.BANKING77_QID]
    assert q["type"] == "choice"
    assert set(q["criteria"]) == set(row["options"])
    assert body["state"] == {"message": row["text"]}


def _echo_first_option(seen, n, body):
    options = list(body["questions"][questions.BANKING77_QID]["criteria"])
    return (200, {
        "model": "jev-1.0.0",
        "answers": {questions.BANKING77_QID: {
            "type": "choice",
            "choice": options[0],
            "probabilities": {opt: 1.0 if i == 0 else 0.0 for i, opt in enumerate(options)},
        }},
    }, {})


def test_e1_end_to_end_against_fake_server(fake_server):
    fake_server.set_responder("/v1/systemone", _echo_first_option)
    rows = e1.load_rows()[:6]

    client = JevClient(base_url=fake_server.base_url, api_key="sentinel-key")
    try:
        predictions = run_experiment("e1", rows, e1.build_request, e1.parse_result, RunContext(client))
    finally:
        client.close()

    assert len(predictions) == len(rows)
    for row, pred in zip(rows, predictions):
        assert pred.id == row["id"]
        assert pred.error is None
        assert pred.model == "jev-1.0.0"
        assert pred.answer == row["options"][0]
        assert set(pred.probabilities) == set(row["options"])


def test_e1_reruns_are_served_from_cache(fake_server, tmp_path):
    fake_server.set_responder("/v1/systemone", _echo_first_option)
    rows = e1.load_rows()[:3]
    cache = Cache(tmp_path)
    client = JevClient(base_url=fake_server.base_url, api_key="sentinel-key", cache=cache)
    try:
        run_experiment("e1", rows, e1.build_request, e1.parse_result, RunContext(client))
        hits_after_first = fake_server.hits("/v1/systemone")

        predictions = run_experiment("e1", rows, e1.build_request, e1.parse_result, RunContext(client))
        assert fake_server.hits("/v1/systemone") == hits_after_first
        assert all(p.cache_hit for p in predictions)
    finally:
        client.close()
