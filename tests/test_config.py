import pytest

from jev_eval.config import DEFAULT_BASE_URL, Config, MissingApiKeyError, load_config


def test_default_base_url(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "sentinel-key")
    monkeypatch.delenv("JEV_BASE_URL", raising=False)
    assert load_config().base_url == DEFAULT_BASE_URL


def test_trailing_slash_stripped(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "sentinel-key")
    monkeypatch.setenv("JEV_BASE_URL", "https://example.com/")
    assert load_config().base_url == "https://example.com"


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    with pytest.raises(MissingApiKeyError):
        load_config()


def test_whitespace_key_counts_as_unset(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "   ")
    with pytest.raises(MissingApiKeyError):
        load_config()


def test_key_is_stripped(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", " sentinel-key \n")
    assert load_config().api_key == "sentinel-key"


def test_repr_and_str_never_leak_key_or_header():
    cfg = Config(api_key="sentinel-key-xyz")
    assert "sentinel-key-xyz" not in repr(cfg)
    assert "sentinel-key-xyz" not in str(cfg)
    assert "Authorization" not in repr(cfg)
    assert "Authorization" not in str(cfg)


def test_auth_headers_built_on_demand():
    cfg = Config(api_key="sentinel-key-xyz")
    assert cfg.auth_headers() == {"Authorization": "Bearer sentinel-key-xyz"}
