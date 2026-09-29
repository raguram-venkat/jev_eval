"""Generate REPORT.md from a run's summary.csv, predictions.jsonl and manifest.json."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .summary import FROZEN_DIR, frozen_rows, load_predictions

MIN_FAILURE_EXAMPLES = 10


def _fmt(value) -> str:
    if value == "" or value is None:
        return "-"
    if isinstance(value, (bool, int)):
        return str(value)
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return str(value)


def _cell(row: dict, column: str) -> str:
    value = row.get(column, "")
    return str(value) if column in ("id", "n") and value != "" else _fmt(value)


def _table(rows: list[dict], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = "\n".join("| " + " | ".join(_cell(r, c) for c in columns) + " |" for r in rows)
    return "\n".join([header, sep, body]) if rows else "_no data_"


def _e1_paragraph(rows: list[dict]) -> str:
    e1 = [r for r in rows if r["experiment"] == "e1"]
    if not e1:
        return "E1 (Banking77 label-count sweep): not run."
    parts = []
    for r in sorted(e1, key=lambda r: int(r["condition"].split("=")[1])):
        k = r["condition"].split("=")[1]
        parts.append(
            f"at k={k} accuracy was {_fmt(r['accuracy'])} "
            f"(95% CI {_fmt(r['accuracy_lo'])}-{_fmt(r['accuracy_hi'])}, n={r['n']}), "
            f"beating chance of {_fmt(r['baseline_accuracy'])}"
        )
    return "E1 (Banking77 label-count sweep): " + "; ".join(parts) + "."


def _e2_paragraph(rows: list[dict]) -> str:
    e2 = next((r for r in rows if r["experiment"] == "e2"), None)
    if e2 is None:
        return "E2 (BoolQ calibration): not run."
    return (
        f"E2 (BoolQ calibration): accuracy {_fmt(e2['accuracy'])} "
        f"(95% CI {_fmt(e2['accuracy_lo'])}-{_fmt(e2['accuracy_hi'])}, n={e2['n']}) "
        f"against a 0.5 baseline, Brier {_fmt(e2['brier'])} against a baseline of 0.25, "
        f"AUROC {_fmt(e2['auroc'])}."
    )


def _e3_paragraph(rows: list[dict]) -> str:
    e3 = next((r for r in rows if r["experiment"] == "e3"), None)
    if e3 is None:
        return "E3 (Yelp ordinal scoring): not run."
    return (
        f"E3 (Yelp ordinal scoring): MAE {_fmt(e3['mae'])} "
        f"(95% CI {_fmt(e3['mae_lo'])}-{_fmt(e3['mae_hi'])}) against an always-3-stars "
        f"baseline of {_fmt(e3['baseline_mae'])}, exact-level accuracy {_fmt(e3['exact_accuracy'])} "
        f"against a baseline of {_fmt(e3['baseline_exact_accuracy'])}, Spearman {_fmt(e3['spearman'])}."
    )


def _e4_paragraph(rows: list[dict]) -> str:
    e4 = [r for r in rows if r["experiment"] == "e4"]
    if not e4:
        return "E4 (selective prediction): not computed (needs E1 k=20/77 or E2 predictions)."
    parts = [f"{r['condition']}: coverage {_fmt(r['coverage_at_90'])} at 90% accuracy, "
             f"{_fmt(r['coverage_at_95'])} at 95%" for r in e4]
    return "E4 (selective prediction): " + "; ".join(parts) + "."


def _e5_paragraph(rows: list[dict]) -> str:
    e5 = {r["condition"]: r for r in rows if r["experiment"] == "e5"}
    if not e5:
        return "E5 (latency): not run."
    parts = []
    for cond in ("single", "multi5", "models"):
        r = e5.get(cond)
        if r:
            parts.append(f"{cond} p50={_fmt(r['latency_p50_ms'])}ms p95={_fmt(r['latency_p95_ms'])}ms")
    ratio = e5.get("multi5", {}).get("latency_ratio_5v1_p50", "")
    tail = f"; 5-question/1-question p50 ratio {_fmt(ratio)}" if ratio else ""
    return "E5 (latency): " + "; ".join(parts) + tail + "."


def _p_true(prediction_id: str, true, probabilities: dict) -> float | str:
    if prediction_id.startswith("boolq-"):
        return probabilities.get("yes" if true else "no", "")
    if prediction_id.startswith("yelp-"):
        return probabilities.get(str(true), "")
    return probabilities.get(true, "")  # banking77: true is the option string itself


def _failure_examples(predictions: list[dict], n: int = MIN_FAILURE_EXAMPLES) -> list[dict]:
    frozen = {**frozen_rows("banking77_sweep"), **frozen_rows("boolq"), **frozen_rows("yelp")}
    examples = []
    for p in predictions:
        if p["error"] is not None or p["id"] not in frozen:
            continue
        row = frozen[p["id"]]
        true = row.get("label", row.get("stars"))
        if p["answer"] != true:
            examples.append({
                "id": p["id"], "true": true, "predicted": p["answer"],
                "p_true": _p_true(p["id"], true, p["probabilities"]),
            })
    return examples[:n]


def write_report(run_dir: Path) -> Path:
    summary_path = run_dir / "summary.csv"
    summary_rows = list(csv.DictReader(summary_path.open())) if summary_path.exists() else []
    predictions = load_predictions(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text()) if (run_dir / "manifest.json").exists() else {}
    frozen_manifest = json.loads((FROZEN_DIR / "manifest.json").read_text())

    failures = _failure_examples(predictions)
    failures_section = (
        _table(failures, ["id", "true", "predicted", "p_true"])
        if len(failures) >= MIN_FAILURE_EXAMPLES
        else f"Fewer than {MIN_FAILURE_EXAMPLES} misclassified examples were available "
             f"in this run ({len(failures)} found):\n\n" + _table(failures, ["id", "true", "predicted", "p_true"])
    )

    lines = [
        "# jev-eval report",
        "",
        f"Run: `{run_dir.name}` — model `{manifest.get('model', 'unknown')}` — "
        f"generated `{manifest.get('start_time', '')}` to `{manifest.get('end_time', '')}`.",
        "",
        "## Results",
        "",
        _table(summary_rows, [
            "experiment", "condition", "n", "accuracy", "accuracy_lo", "accuracy_hi",
            "brier", "mae", "exact_accuracy", "auroc", "spearman",
            "coverage_at_90", "coverage_at_95", "latency_p50_ms", "baseline_accuracy",
        ]),
        "",
        "## Findings",
        "",
        _e1_paragraph(summary_rows),
        "",
        _e2_paragraph(summary_rows),
        "",
        _e3_paragraph(summary_rows),
        "",
        _e4_paragraph(summary_rows),
        "",
        _e5_paragraph(summary_rows),
        "",
        "## Where Jev fails",
        "",
        failures_section,
        "",
        "## Caveats",
        "",
        "- Banking77 criteria are label-name-only (`{opt: opt}`), zero-shot with no descriptions "
        "of what each intent means beyond its name.",
        "- Latency includes real network round-trip time from this machine to the Jev API; it is "
        "not a server-side-only measurement.",
        f"- This is a single run on {manifest.get('start_time', 'an unrecorded date')} against "
        f"model `{manifest.get('model', 'unknown')}`; the model may have since changed.",
        f"- BoolQ passages are filtered to at most {frozen_manifest['filters']['boolq_max_words']} words "
        f"and Yelp reviews to at most {frozen_manifest['filters']['yelp_max_words']} words "
        "(see data/frozen/manifest.json).",
        "",
    ]

    path = run_dir / "REPORT.md"
    path.write_text("\n".join(lines))
    return path
