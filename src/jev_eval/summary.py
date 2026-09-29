"""Derive summary.csv from predictions.jsonl and the frozen data, offline, with every metric
from the Metrics table, its 95% bootstrap CI where it applies, and its baseline.

Re-derivable at any time from an existing predictions.jsonl without any network access —
this module never calls the client.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from . import baselines, metrics

FROZEN_DIR = Path("data/frozen")

COLUMNS = [
    "experiment", "condition", "n",
    "accuracy", "accuracy_lo", "accuracy_hi",
    "macro_f1", "macro_f1_lo", "macro_f1_hi",
    "brier", "brier_lo", "brier_hi",
    "ece",
    "p_true_below_001_rate",
    "auroc", "auroc_lo", "auroc_hi",
    "mae", "mae_lo", "mae_hi",
    "exact_accuracy", "exact_accuracy_lo", "exact_accuracy_hi",
    "spearman", "spearman_lo", "spearman_hi",
    "coverage_at_90", "coverage_at_95",
    "latency_p50_ms", "latency_p95_ms", "latency_p99_ms", "latency_ratio_5v1_p50",
    "baseline_accuracy", "baseline_mae", "baseline_exact_accuracy", "baseline_brier",
]


def _blank_row(experiment: str, condition: str, n: int) -> dict:
    row = {c: "" for c in COLUMNS}
    row.update(experiment=experiment, condition=condition, n=n)
    return row


def load_predictions(run_dir: Path) -> list[dict]:
    path = run_dir / "predictions.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def load_latency_samples(run_dir: Path) -> list[dict]:
    path = run_dir / "latency_samples.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def _frozen_rows(name: str) -> dict[str, dict]:
    path = FROZEN_DIR / f"{name}.jsonl"
    return {row["id"]: row for row in (json.loads(line) for line in path.read_text().splitlines())}


def _percentile(values: list[float], p: float) -> float:
    import numpy as np
    return float(np.percentile(values, p)) if values else float("nan")


def summarize_e1(predictions: list[dict]) -> list[dict]:
    e1_preds = [p for p in predictions if p["id"].startswith("b77-") and p["error"] is None]
    if not e1_preds:
        return []
    frozen = _frozen_rows("banking77_sweep")

    rows = []
    for k in sorted({frozen[p["id"]]["k"] for p in e1_preds}):
        group = [p for p in e1_preds if frozen[p["id"]]["k"] == k]
        y_true = [frozen[p["id"]]["label"] for p in group]
        y_pred = [p["answer"] for p in group]
        probs = [p["probabilities"] for p in group]
        max_probs = [max(p.values()) for p in probs]
        correct = [t == pr for t, pr in zip(y_true, y_pred)]

        row = _blank_row("e1", f"k={k}", len(group))
        row["accuracy"] = metrics.choice_accuracy(y_true, y_pred)
        row["accuracy_lo"], row["accuracy_hi"] = metrics.bootstrap_ci(
            len(group), lambda idx: metrics.choice_accuracy([y_true[i] for i in idx], [y_pred[i] for i in idx])
        )
        row["macro_f1"] = metrics.choice_macro_f1(y_true, y_pred)
        row["macro_f1_lo"], row["macro_f1_hi"] = metrics.bootstrap_ci(
            len(group), lambda idx: metrics.choice_macro_f1([y_true[i] for i in idx], [y_pred[i] for i in idx])
        )
        row["brier"] = metrics.choice_brier(y_true, probs)
        row["brier_lo"], row["brier_hi"] = metrics.bootstrap_ci(
            len(group), lambda idx: metrics.choice_brier([y_true[i] for i in idx], [probs[i] for i in idx])
        )
        row["ece"] = metrics.choice_ece(max_probs, correct)
        row["p_true_below_001_rate"] = metrics.choice_p_true_below(probs, y_true)
        row["baseline_accuracy"] = baselines.chance_accuracy(k)
        rows.append(row)
    return rows


def summarize_e2(predictions: list[dict]) -> list[dict]:
    e2_preds = [p for p in predictions if p["id"].startswith("boolq-") and p["error"] is None]
    if not e2_preds:
        return []
    frozen = _frozen_rows("boolq")
    y_true = [frozen[p["id"]]["label"] for p in e2_preds]
    p_yes = [p["probabilities"]["yes"] for p in e2_preds]

    row = _blank_row("e2", "all", len(e2_preds))
    row["accuracy"] = metrics.noul_accuracy(y_true, p_yes)
    row["accuracy_lo"], row["accuracy_hi"] = metrics.bootstrap_ci(
        len(e2_preds), lambda idx: metrics.noul_accuracy([y_true[i] for i in idx], [p_yes[i] for i in idx])
    )
    row["brier"] = metrics.noul_brier(y_true, p_yes)
    row["brier_lo"], row["brier_hi"] = metrics.bootstrap_ci(
        len(e2_preds), lambda idx: metrics.noul_brier([y_true[i] for i in idx], [p_yes[i] for i in idx])
    )
    row["auroc"] = metrics.noul_auroc(y_true, p_yes)
    row["auroc_lo"], row["auroc_hi"] = metrics.bootstrap_ci(
        len(e2_preds), lambda idx: metrics.noul_auroc([y_true[i] for i in idx], [p_yes[i] for i in idx])
    )
    row["baseline_accuracy"], row["baseline_brier"] = baselines.noul_baseline()
    return [row]


def summarize_e3(predictions: list[dict]) -> list[dict]:
    e3_preds = [p for p in predictions if p["id"].startswith("yelp-") and p["error"] is None]
    if not e3_preds:
        return []
    frozen = _frozen_rows("yelp")
    y_true = [frozen[p["id"]]["stars"] for p in e3_preds]
    pred_stars = [p["answer"] for p in e3_preds]
    # The continuous score (1..5 scale) is the argmax star's probability-weighted position;
    # recovered here as sum(level * p) since predictions.jsonl stores probabilities, not score.
    pred_score = [sum(int(k) * v for k, v in p["probabilities"].items()) for p in e3_preds]

    row = _blank_row("e3", "all", len(e3_preds))
    row["mae"] = metrics.score_mae(y_true, pred_score)
    row["mae_lo"], row["mae_hi"] = metrics.bootstrap_ci(
        len(e3_preds), lambda idx: metrics.score_mae([y_true[i] for i in idx], [pred_score[i] for i in idx])
    )
    row["exact_accuracy"] = metrics.score_exact_accuracy(y_true, pred_stars)
    row["exact_accuracy_lo"], row["exact_accuracy_hi"] = metrics.bootstrap_ci(
        len(e3_preds), lambda idx: metrics.score_exact_accuracy([y_true[i] for i in idx], [pred_stars[i] for i in idx])
    )
    row["spearman"] = metrics.score_spearman(y_true, pred_score)
    row["spearman_lo"], row["spearman_hi"] = metrics.bootstrap_ci(
        len(e3_preds), lambda idx: metrics.score_spearman([y_true[i] for i in idx], [pred_score[i] for i in idx])
    )
    row["baseline_mae"], row["baseline_exact_accuracy"] = baselines.score_always_baseline(y_true)
    return [row]


def summarize_e4(predictions: list[dict]) -> list[dict]:
    """Selective prediction: reuses E1 (k=20, 77) and E2 predictions already in hand, no new calls."""
    frozen_b77 = _frozen_rows("banking77_sweep")
    frozen_boolq = _frozen_rows("boolq")
    rows = []

    for k in (20, 77):
        group = [
            p for p in predictions
            if p["id"].startswith("b77-") and p["error"] is None and frozen_b77[p["id"]]["k"] == k
        ]
        if not group:
            continue
        confidence = [max(p["probabilities"].values()) for p in group]
        correct = [p["answer"] == frozen_b77[p["id"]]["label"] for p in group]
        row = _blank_row("e4", f"e1_k={k}", len(group))
        row["coverage_at_90"] = metrics.coverage_at_accuracy(confidence, correct, 0.90)
        row["coverage_at_95"] = metrics.coverage_at_accuracy(confidence, correct, 0.95)
        rows.append(row)

    e2_group = [p for p in predictions if p["id"].startswith("boolq-") and p["error"] is None]
    if e2_group:
        confidence = [max(p["probabilities"].values()) for p in e2_group]
        correct = [p["answer"] == frozen_boolq[p["id"]]["label"] for p in e2_group]
        row = _blank_row("e4", "e2", len(e2_group))
        row["coverage_at_90"] = metrics.coverage_at_accuracy(confidence, correct, 0.90)
        row["coverage_at_95"] = metrics.coverage_at_accuracy(confidence, correct, 0.95)
        rows.append(row)

    return rows


def summarize_e5(latency_samples: list[dict]) -> list[dict]:
    if not latency_samples:
        return []
    by_kind: dict[str, list[float]] = {}
    for s in latency_samples:
        by_kind.setdefault(s["kind"], []).append(s["latency_ms"])

    rows = []
    for kind, values in sorted(by_kind.items()):
        row = _blank_row("e5", kind, len(values))
        row["latency_p50_ms"] = _percentile(values, 50)
        row["latency_p95_ms"] = _percentile(values, 95)
        row["latency_p99_ms"] = _percentile(values, 99)
        rows.append(row)

    if "multi1" in by_kind and "multi5" in by_kind:
        ratio = _percentile(by_kind["multi5"], 50) / _percentile(by_kind["multi1"], 50)
        for row in rows:
            if row["condition"] == "multi5":
                row["latency_ratio_5v1_p50"] = ratio
    return rows


def write_summary(run_dir: Path) -> Path:
    predictions = load_predictions(run_dir)
    latency_samples = load_latency_samples(run_dir)

    rows = (
        summarize_e1(predictions)
        + summarize_e2(predictions)
        + summarize_e3(predictions)
        + summarize_e4(predictions)
        + summarize_e5(latency_samples)
    )

    path = run_dir / "summary.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path
