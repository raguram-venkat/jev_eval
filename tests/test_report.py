import json
from pathlib import Path

from jev_eval import report, summary

FROZEN = Path("data/frozen")


def _rows(name: str, predicate) -> list[dict]:
    all_rows = [json.loads(line) for line in (FROZEN / f"{name}.jsonl").read_text().splitlines()]
    return [r for r in all_rows if predicate(r)]


def _e1_prediction(row: dict, correct: bool) -> dict:
    others = [o for o in row["options"] if o != row["label"]]
    answer = row["label"] if correct else (others[0] if others else row["label"])
    probabilities = {opt: (0.9 if opt == answer else 0.1 / max(1, len(row["options"]) - 1)) for opt in row["options"]}
    return {
        "id": row["id"], "answer": answer, "probabilities": probabilities, "confidence": 0.9,
        "latency_ms": 100.0, "model": "jev-1.0.0", "cache_hit": False, "error": None,
    }


def _build_run(run_dir: Path, n_wrong: int) -> None:
    b77 = _rows("banking77_sweep", lambda r: r["k"] == 2)[: n_wrong + 5]
    predictions = [_e1_prediction(r, correct=(i >= n_wrong)) for i, r in enumerate(b77)]

    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "predictions.jsonl").open("w") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")
    (run_dir / "manifest.json").write_text(json.dumps({
        "model": "jev-1.0.0", "start_time": "2026-01-01T00:00:00Z", "end_time": "2026-01-01T00:01:00Z",
    }))
    summary.write_summary(run_dir)


def test_write_report_with_at_least_ten_failures(tmp_path):
    run_dir = tmp_path / "run"
    _build_run(run_dir, n_wrong=12)

    path = report.write_report(run_dir)
    text = path.read_text()

    assert "## Where Jev fails" in text
    assert "## Caveats" in text
    assert "E1 (Banking77" in text
    assert "Fewer than" not in text  # 12 >= MIN_FAILURE_EXAMPLES, no caveat needed


def test_write_report_says_so_with_fewer_than_ten_failures(tmp_path):
    run_dir = tmp_path / "run"
    _build_run(run_dir, n_wrong=2)

    path = report.write_report(run_dir)
    text = path.read_text()

    assert "Fewer than 10 misclassified examples" in text


def test_write_report_caveats_mention_filtered_lengths(tmp_path):
    run_dir = tmp_path / "run"
    _build_run(run_dir, n_wrong=1)

    text = report.write_report(run_dir).read_text()
    assert "250 words" in text
    assert "150 words" in text
