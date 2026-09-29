import threading

import pytest

from jev_eval.client import AuthError, JevClient, ModelChangedError, PreflightError, RequestCapError
from jev_eval.runctx import RunContext


def _client(fake_server, **kwargs):
    return JevClient(base_url=fake_server.base_url, api_key="sentinel-key", sleep=lambda s: None, **kwargs)


def test_successful_request_returns_model_and_latency(fake_server):
    client = _client(fake_server)
    result = client.request({"model": "jev-latest"})
    assert result.ok
    assert result.model == "jev-1.0.0"
    assert result.latency_ms is not None and result.latency_ms >= 0
    assert result.cache_hit is False


def test_retries_429_then_succeeds(fake_server):
    fake_server.set_responder(
        "/v1/systemone",
        lambda seen, n: (429, {}, {}) if n == 1 else (200, {"model": "jev-1.0.0"}, {}),
    )
    client = _client(fake_server)
    result = client.request({"model": "jev-latest"})
    assert result.ok
    assert fake_server.hits("/v1/systemone") == 2


def test_retries_5xx_then_succeeds(fake_server):
    fake_server.set_responder(
        "/v1/systemone",
        lambda seen, n: (503, {}, {}) if n <= 2 else (200, {"model": "jev-1.0.0"}, {}),
    )
    client = _client(fake_server)
    result = client.request({"model": "jev-latest"})
    assert result.ok
    assert fake_server.hits("/v1/systemone") == 3


def test_gives_up_after_max_attempts_and_records_failure(fake_server):
    fake_server.set_responder("/v1/systemone", lambda seen, n: (503, "unavailable", {}))
    client = _client(fake_server)
    result = client.request({"model": "jev-latest"})
    assert not result.ok
    assert "503" in result.error
    assert fake_server.hits("/v1/systemone") == 5


@pytest.mark.parametrize("status", [401, 403])
def test_auth_error_aborts_after_exactly_one_attempt(fake_server, status):
    fake_server.set_responder("/v1/systemone", lambda seen, n: (status, {}, {}))
    client = _client(fake_server)
    with pytest.raises(AuthError):
        client.request({"model": "jev-latest"})
    assert fake_server.hits("/v1/systemone") == 1


def test_transport_error_retries_then_succeeds(fake_server):
    fake_server.set_responder(
        "/v1/systemone",
        lambda seen, n: None if n == 1 else (200, {"model": "jev-1.0.0"}, {}),
    )
    client = _client(fake_server)
    result = client.request({"model": "jev-latest"})
    assert result.ok
    assert fake_server.hits("/v1/systemone") == 2


def test_malformed_response_is_a_failure_not_retried(fake_server):
    fake_server.set_responder("/v1/systemone", lambda seen, n: (200, {"no_model_field": True}, {}))
    client = _client(fake_server)
    result = client.request({"model": "jev-latest"})
    assert not result.ok
    assert fake_server.hits("/v1/systemone") == 1


def test_retry_after_header_used_as_backoff_base(fake_server):
    sleeps = []
    fake_server.set_responder(
        "/v1/systemone",
        lambda seen, n: (429, {}, {"Retry-After": "5"}) if n == 1 else (200, {"model": "jev-1.0.0"}, {}),
    )
    client = JevClient(
        base_url=fake_server.base_url, api_key="sentinel-key",
        sleep=lambda s: sleeps.append(s), jitter=lambda: 0,
    )
    client.request({"model": "jev-latest"})
    assert sleeps == [5]


def test_key_never_appears_in_error_or_repr(fake_server):
    fake_server.set_responder("/v1/systemone", lambda seen, n: (500, "boom", {}))
    client = _client(fake_server)
    result = client.request({"model": "jev-latest"})
    assert "sentinel-key" not in repr(client)
    assert "sentinel-key" not in str(client)
    assert "sentinel-key" not in (result.error or "")
    assert "Authorization" not in repr(client)


def test_preflight_ok(fake_server):
    fake_server.set_responder("/v1/models", lambda seen, n: (200, {"models": []}, {}))
    _client(fake_server).preflight()


def test_preflight_bad_status_fails(fake_server):
    fake_server.set_responder("/v1/models", lambda seen, n: (500, {}, {}))
    with pytest.raises(PreflightError, match="500"):
        _client(fake_server).preflight()


def test_preflight_connection_refused_fails(dead_url):
    client = JevClient(base_url=dead_url, api_key="sentinel-key")
    with pytest.raises(PreflightError):
        client.preflight()


def test_preflight_never_retries(fake_server):
    fake_server.set_responder("/v1/models", lambda seen, n: (500, {}, {}))
    with pytest.raises(PreflightError):
        _client(fake_server).preflight()
    assert fake_server.hits("/v1/models") == 1


def test_plan_raises_when_over_cap(fake_server):
    client = _client(fake_server)
    bodies = [{"model": "jev-latest", "i": i} for i in range(5)]
    with pytest.raises(RequestCapError, match="planned 5.*cap of 3"):
        client.plan(bodies, cap=3)


def test_plan_only_counts_uncached_bodies(fake_server, tmp_path):
    from jev_eval.cache import Cache

    cache = Cache(tmp_path)
    client = JevClient(base_url=fake_server.base_url, api_key="sentinel-key", cache=cache)
    body = {"model": "jev-latest", "i": 0}
    client.request(body)  # populates the cache
    bodies = [body, {"model": "jev-latest", "i": 1}]
    assert client.plan(bodies, cap=10) == 1


def test_model_change_guard_stops_further_sends(fake_server):
    fake_server.set_responder(
        "/v1/systemone",
        lambda seen, n: (200, {"model": "jev-1.0.0" if n < 8 else "jev-2.0.0"}, {}),
    )
    client = JevClient(base_url=fake_server.base_url, api_key="sentinel-key")
    ctx = RunContext(client, cap=1000)
    errors = []

    def worker():
        for _ in range(10):
            try:
                ctx.run("e1", {"model": "jev-latest"})
            except ModelChangedError as e:
                errors.append(e)
                return

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors
    sent_before_next_call = ctx.sent
    with pytest.raises(ModelChangedError):
        ctx.reserve()
    assert ctx.sent == sent_before_next_call
