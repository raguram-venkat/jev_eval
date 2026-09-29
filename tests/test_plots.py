import json
from pathlib import Path

from jev_eval import plots, summary

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


def _e2_prediction(row: dict) -> dict:
    p_yes = 0.9 if row["label"] else 0.1
    return {
        "id": row["id"], "answer": row["label"], "probabilities": {"yes": p_yes, "no": 1 - p_yes},
        "confidence": None, "latency_ms": 100.0, "model": "jev-1.0.0", "cache_hit": False, "error": None,
    }


def _e3_prediction(row: dict, correct: bool) -> dict:
    predicted = row["stars"] if correct else max(1, row["stars"] - 1)
    probs = {str(s): (1.0 if s == predicted else 0.0) for s in range(1, 6)}
    return {
        "id": row["id"], "answer": predicted, "probabilities": probs, "confidence": 0.9,
        "latency_ms": 100.0, "model": "jev-1.0.0", "cache_hit": False, "error": None,
    }


def _build_run(run_dir: Path) -> None:
    b77_k20 = _rows("banking77_sweep", lambda r: r["k"] == 20)[:5]
    b77_k77 = _rows("banking77_sweep", lambda r: r["k"] == 77)[:5]
    boolq_rows = _rows("boolq", lambda r: True)[:6]
    yelp_rows = _rows("yelp", lambda r: True)[:6]

    predictions = (
        [_e1_prediction(r, correct=(i % 3 != 0)) for i, r in enumerate(b77_k20)]
        + [_e1_prediction(r, correct=(i % 2 == 0)) for i, r in enumerate(b77_k77)]
        + [_e2_prediction(r) for r in boolq_rows]
        + [_e3_prediction(r, correct=(i % 2 == 0)) for i, r in enumerate(yelp_rows)]
    )
    latency_samples = (
        [{"kind": "single", "latency_ms": ms} for ms in [100, 110, 120, 130]]
        + [{"kind": "multi5", "latency_ms": ms} for ms in [150, 160, 170, 180]]
        + [{"kind": "models", "latency_ms": ms} for ms in [50, 55, 60, 65]]
    )

    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "predictions.jsonl").open("w") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")
    with (run_dir / "latency_samples.jsonl").open("w") as f:
        for s in latency_samples:
            f.write(json.dumps(s) + "\n")
    summary.write_summary(run_dir)


def test_generate_all_writes_seven_nonempty_pngs(tmp_path):
    run_dir = tmp_path / "run"
    _build_run(run_dir)

    paths = plots.generate_all(run_dir)

    assert len(paths) == len(plots.PLOT_NAMES) == 7
    for path in paths:
        assert path.exists()
        assert path.stat().st_size > 0


def test_confusions_k77_copes_with_zero_misclassifications(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    b77 = _rows("banking77_sweep", lambda r: r["k"] == 77)[:3]
    predictions = [_e1_prediction(r, correct=True) for r in b77]
    with (run_dir / "predictions.jsonl").open("w") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")

    path = run_dir / "confusions.png"
    plots.plot_confusions_k77(path, predictions)
    assert path.exists() and path.stat().st_size > 0
