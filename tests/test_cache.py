import json

from jev_eval.client.cache import Cache
from jev_eval.client.http import JevClient


def test_second_identical_request_is_served_from_cache(fake_server, tmp_path):
    cache = Cache(tmp_path)
    client = JevClient(base_url=fake_server.base_url, api_key="sentinel-key", cache=cache)
    body = {"model": "jev-latest", "message": "hi"}

    first = client.request(body)
    second = client.request(body)

    assert first.cache_hit is False
    assert second.cache_hit is True
    assert second.model == first.model
    assert fake_server.hits("/v1/systemone") == 1


def test_no_cache_bypasses_reads_and_writes(fake_server, tmp_path):
    client = JevClient(base_url=fake_server.base_url, api_key="sentinel-key", cache=None)
    body = {"model": "jev-latest", "message": "hi"}

    client.request(body)
    client.request(body)

    assert fake_server.hits("/v1/systemone") == 2
    assert not tmp_path.exists() or not list(tmp_path.iterdir())


def test_cache_entries_never_contain_key_or_authorization(fake_server, tmp_path):
    cache = Cache(tmp_path)
    client = JevClient(base_url=fake_server.base_url, api_key="sentinel-key-xyz", cache=cache)
    client.request({"model": "jev-latest", "message": "hi"})

    files = list(tmp_path.glob("*.json"))
    assert files
    for f in files:
        text = f.read_text()
        assert "sentinel-key-xyz" not in text
        assert "Authorization" not in text


def test_malformed_cache_entry_is_treated_as_miss(fake_server, tmp_path):
    cache = Cache(tmp_path)
    key = cache.make_key("jev-latest", '{"model":"jev-latest"}')
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / f"{key}.json").write_text("{not json")

    client = JevClient(base_url=fake_server.base_url, api_key="sentinel-key", cache=cache)
    result = client.request({"model": "jev-latest"})
    assert result.ok
    assert result.cache_hit is False
    assert fake_server.hits("/v1/systemone") == 1


def test_put_leaves_no_stray_tmp_file(tmp_path):
    cache = Cache(tmp_path)
    cache.put("k1", "jev-latest", "jev-1.0.0", 12.3, {"model": "jev-1.0.0"})
    names = {p.name for p in tmp_path.iterdir()}
    assert names == {"k1.json"}
    assert json.loads((tmp_path / "k1.json").read_text())["model"] == "jev-1.0.0"
