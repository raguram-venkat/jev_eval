import pytest

from jev_eval.cli import build_parser, main


def test_help_lists_run(capsys):
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--help"])
    assert exc.value.code == 0
    assert "run" in capsys.readouterr().out


@pytest.mark.parametrize("limit", ["0", "-3", "abc"])
def test_bad_limit_exits_2(limit):
    with pytest.raises(SystemExit) as exc:
        main(["run", "--limit", limit])
    assert exc.value.code == 2


def test_unknown_experiment_exits_2():
    with pytest.raises(SystemExit) as exc:
        main(["run", "--experiments", "e1,e9"])
    assert exc.value.code == 2


def test_missing_key_exits_2_before_frozen_check(monkeypatch, capsys):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc:
        main(["run"])
    assert exc.value.code == 2
    assert "TYPESAFE_API_KEY" in capsys.readouterr().err


def test_run_succeeds_with_key_valid_frozen_data_and_reachable_jev(monkeypatch, fake_server):
    fake_server.set_responder("/v1/models", lambda seen, n: (200, {"models": []}, {}))
    monkeypatch.setenv("TYPESAFE_API_KEY", "sentinel-key")
    monkeypatch.setenv("JEV_BASE_URL", fake_server.base_url)
    assert main(["run"]) == 0


def test_run_exits_1_when_preflight_fails(monkeypatch, fake_server):
    fake_server.set_responder("/v1/models", lambda seen, n: (500, {}, {}))
    monkeypatch.setenv("TYPESAFE_API_KEY", "sentinel-key")
    monkeypatch.setenv("JEV_BASE_URL", fake_server.base_url)
    assert main(["run"]) == 1
