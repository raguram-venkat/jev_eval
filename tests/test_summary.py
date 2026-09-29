import csv
import json
from pathlib import Path

from jev_eval import summary

FROZEN = Path("data/frozen")


def _rows(name: str, predicate) -> list[dict]:
    all_rows = [json.loads(line) for line in (FROZEN / f"{name}.jsonl").read_text().splitlines()]
    return [r for r in all_rows if predicate(r)]


def _e1_prediction(row: dict, correct: bool = True) -> dict:
    others = [o for o in row["options"] if o != row["label"]]
    answer = row["label"] if correct else (others[0] if others else row["label"])
    probabilities = {opt: (0.9 if opt == answer else 0.1 / max(1, len(row["options"]) - 1)) for opt in row["options"]}
    return {
        "id": row["id"], "answer": answer, "probabilities": probabilities, "confidence": 0.9,
        "latency_ms": 100.0, "model": "jev-1.0.0", "cache_hit": False, "error": None,
    }


def _e2_prediction(row: dict) -> dict:
    p_yes = 0.9 if row["label"] else 0.1
    return {
        "id": row["id"], "answer": row["label"], "probabilities": {"yes": p_yes, "no": 1 - p_yes},
        "confidence": None, "latency_ms": 100.0, "model": "jev-1.0.0", "cache_hit": False, "error": None,
    }


def _e3_prediction(row: dict) -> dict:
    probs = {str(s): (1.0 if s == row["stars"] else 0.0) for s in range(1, 6)}
    return {
        "id": row["id"], "answer": row["stars"], "probabilities": probs, "confidence": 0.9,
        "latency_ms": 100.0, "model": "jev-1.0.0", "cache_hit": False, "error": None,
    }


def _write_run(run_dir: Path, predictions: list[dict], latency_samples: list[dict]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "predictions.jsonl").open("w") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")
    if latency_samples:
        with (run_dir / "latency_samples.jsonl").open("w") as f:
            for s in latency_samples:
                f.write(json.dumps(s) + "\n")


def test_write_summary_covers_every_experiment(tmp_path):
    b77_k2 = _rows("banking77_sweep", lambda r: r["k"] == 2)[:2]
    b77_k20 = _rows("banking77_sweep", lambda r: r["k"] == 20)[:3]
    boolq_rows = _rows("boolq", lambda r: True)[:4]
    yelp_rows = _rows("yelp", lambda r: True)[:4]

    predictions = (
        [_e1_prediction(r) for r in b77_k2]
        + [_e1_prediction(r) for r in b77_k20]
        + [_e2_prediction(r) for r in boolq_rows]
        + [_e3_prediction(r) for r in yelp_rows]
    )
    latency_samples = (
        [{"kind": "single", "latency_ms": ms} for ms in [100, 110, 120]]
        + [{"kind": "multi1", "latency_ms": ms} for ms in [100, 100, 100]]
        + [{"kind": "multi5", "latency_ms": ms} for ms in [150, 150, 150]]
        + [{"kind": "models", "latency_ms": ms} for ms in [50, 50, 50]]
    )

    run_dir = tmp_path / "run"
    _write_run(run_dir, predictions, latency_samples)

    path = summary.write_summary(run_dir)
    rows = list(csv.DictReader(path.open()))
    by_key = {(r["experiment"], r["condition"]): r for r in rows}

    assert ("e1", "k=2") in by_key
    assert float(by_key[("e1", "k=2")]["accuracy"]) == 1.0
    assert float(by_key[("e1", "k=2")]["baseline_accuracy"]) == 0.5

    assert ("e1", "k=20") in by_key
    assert float(by_key[("e1", "k=20")]["baseline_accuracy"]) == 0.05

    assert ("e2", "all") in by_key
    assert float(by_key[("e2", "all")]["accuracy"]) == 1.0
    assert float(by_key[("e2", "all")]["baseline_accuracy"]) == 0.5

    assert ("e3", "all") in by_key
    assert float(by_key[("e3", "all")]["exact_accuracy"]) == 1.0

    assert ("e4", "e1_k=20") in by_key
    assert ("e4", "e2") in by_key

    assert ("e5", "single") in by_key
    assert ("e5", "multi5") in by_key
    assert float(by_key[("e5", "multi5")]["latency_ratio_5v1_p50"]) == 1.5


def test_write_summary_on_empty_run_produces_header_only(tmp_path):
    run_dir = tmp_path / "empty"
    _write_run(run_dir, [], [])
    path = summary.write_summary(run_dir)
    rows = list(csv.DictReader(path.open()))
    assert rows == []
