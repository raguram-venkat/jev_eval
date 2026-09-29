from jev_eval import e5
from jev_eval.client import JevClient
from jev_eval.runctx import RunContext


def test_scaled_counts_default():
    assert e5.scaled_counts(None) == (10, 100, 30)


def test_scaled_counts_scale_down_with_limit():
    assert e5.scaled_counts(5) == (5, 5, 5)
    assert e5.scaled_counts(50) == (10, 50, 30)


def test_rows_needed_matches_scaled_counts():
    warmups, singles, group_size = e5.scaled_counts(20)
    assert e5.rows_needed(20) == warmups + singles + 2 * group_size


def test_run_sends_expected_counts_per_kind(fake_server):
    question_counts = []

    def responder(seen, n, body):
        question_counts.append(len(body["questions"]))
        return (200, {"model": "jev-1.0.0", "answers": {
            qid: {"type": "choice", "choice": "x", "probabilities": {}} for qid in body["questions"]
        }}, {})

    fake_server.set_responder("/v1/systemone", responder)
    fake_server.set_responder("/v1/models", lambda seen, n, body: (200, {"models": []}, {}))

    client = JevClient(base_url=fake_server.base_url, api_key="sentinel-key", sleep=lambda s: None)
    ctx = RunContext(client)
    try:
        samples = e5.run(ctx, limit=5)
    finally:
        client.close()

    by_kind = {}
    for s in samples:
        by_kind.setdefault(s.kind, 0)
        by_kind[s.kind] += 1

    # limit=5 scales: warmups=5, singles=5, group_size=5 (each of multi1/multi5/models)
    assert by_kind == {"single": 5, "multi1": 5, "multi5": 5, "models": 5}
    # warmups (5) + singles (5) + multi1 (5) go through as single-question requests;
    # multi5 requests carry 5 questions each.
    assert question_counts.count(1) == 15
    assert question_counts.count(5) == 5
    assert fake_server.hits("/v1/models") == 5
