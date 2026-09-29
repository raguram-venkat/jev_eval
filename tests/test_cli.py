import json

import pytest

from jev_eval import cli, questions, results
from jev_eval.cli import build_parser, main


@pytest.fixture(autouse=True)
def _isolate_cli_io(monkeypatch, tmp_path):
    """Every `run` writes to CACHE_DIR/RESULTS_DIR; never let a test touch the real ones."""
    monkeypatch.setattr(cli, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(results, "RESULTS_DIR", tmp_path / "results")


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


def test_run_e4_sends_no_requests(monkeypatch, fake_server, capsys):
    # e4 (selective prediction) is computed later, from saved E1/E2 predictions.
    fake_server.set_responder("/v1/models", lambda seen, n, body: (200, {"models": []}, {}))
    monkeypatch.setenv("TYPESAFE_API_KEY", "sentinel-key")
    monkeypatch.setenv("JEV_BASE_URL", fake_server.base_url)
    assert main(["run", "--experiments", "e4"]) == 0
    assert "no requests sent" in capsys.readouterr().out
    assert fake_server.hits("/v1/systemone") == 0


def test_run_exits_1_when_preflight_fails(monkeypatch, fake_server):
    fake_server.set_responder("/v1/models", lambda seen, n, body: (500, {}, {}))
    monkeypatch.setenv("TYPESAFE_API_KEY", "sentinel-key")
    monkeypatch.setenv("JEV_BASE_URL", fake_server.base_url)
    assert main(["run"]) == 1


def test_run_e1_end_to_end_against_fake_server(monkeypatch, fake_server, tmp_path):
    fake_server.set_responder("/v1/models", lambda seen, n, body: (200, {"models": []}, {}))

    def echo_first_option(seen, n, body):
        options = list(body["questions"][questions.BANKING77_QID]["criteria"])
        return (200, {
            "model": "jev-1.0.0",
            "answers": {questions.BANKING77_QID: {
                "type": "choice",
                "choice": options[0],
                "probabilities": {opt: 1.0 if i == 0 else 0.0 for i, opt in enumerate(options)},
            }},
        }, {})

    fake_server.set_responder("/v1/systemone", echo_first_option)
    monkeypatch.setenv("TYPESAFE_API_KEY", "sentinel-key")
    monkeypatch.setenv("JEV_BASE_URL", fake_server.base_url)

    assert main(["run", "--limit", "4", "--no-cache", "--experiments", "e1"]) == 0

    run_dirs = [d for d in (tmp_path / "results").iterdir() if d.name != "latest"]
    assert len(run_dirs) == 1
    lines = (run_dirs[0] / "predictions.jsonl").read_text().splitlines()
    assert len(lines) == 4
    for line in lines:
        row = json.loads(line)
        assert row["error"] is None
        assert row["model"] == "jev-1.0.0"
        assert row["probabilities"]

    manifest = json.loads((run_dirs[0] / "manifest.json").read_text())
    assert manifest["model"] == "jev-1.0.0"
    assert manifest["seed"] == 1729
    assert (tmp_path / "results" / "latest").resolve() == run_dirs[0].resolve()
    assert (run_dirs[0] / "summary.csv").exists()


def test_summarize_subcommand_rederives_offline(tmp_path):
    run_dir = tmp_path / "results" / "some-run"
    run_dir.mkdir(parents=True)
    (run_dir / "predictions.jsonl").write_text("")

    assert main(["summarize", str(run_dir)]) == 0
    assert (run_dir / "summary.csv").exists()


def test_run_auth_error_mid_run_writes_aborted_manifest_no_report(monkeypatch, fake_server, tmp_path):
    fake_server.set_responder("/v1/models", lambda seen, n, body: (200, {"models": []}, {}))
    fake_server.set_responder("/v1/systemone", lambda seen, n, body: (401, {}, {}))
    monkeypatch.setenv("TYPESAFE_API_KEY", "sentinel-key")
    monkeypatch.setenv("JEV_BASE_URL", fake_server.base_url)

    assert main(["run", "--limit", "3", "--experiments", "e1"]) == 1

    run_dirs = [d for d in (tmp_path / "results").iterdir() if d.name != "latest"]
    assert len(run_dirs) == 1
    manifest = json.loads((run_dirs[0] / "manifest.json").read_text())
    assert "auth error" in manifest["aborted"]
    assert not (run_dirs[0] / "REPORT.md").exists()
    assert not (run_dirs[0] / "summary.csv").exists()
    assert not (run_dirs[0] / "plots").exists()


def test_run_e5_never_uses_cache_even_without_no_cache_flag(monkeypatch, fake_server, tmp_path):
    fake_server.set_responder("/v1/models", lambda seen, n, body: (200, {"models": []}, {}))
    fake_server.set_responder(
        "/v1/systemone",
        lambda seen, n, body: (200, {
            "model": "jev-1.0.0",
            "answers": {qid: {"type": "choice", "choice": "x", "probabilities": {}} for qid in body["questions"]},
        }, {}),
    )
    monkeypatch.setenv("TYPESAFE_API_KEY", "sentinel-key")
    monkeypatch.setenv("JEV_BASE_URL", fake_server.base_url)

    assert main(["run", "--limit", "5", "--experiments", "e5"]) == 0  # note: no --no-cache

    run_dirs = [d for d in (tmp_path / "results").iterdir() if d.name != "latest"]
    samples = (run_dirs[0] / "latency_samples.jsonl").read_text().splitlines()
    assert len(samples) == 20  # 5 single + 5 multi1 + 5 multi5 + 5 models, limit=5
    assert not (tmp_path / "cache").exists()
