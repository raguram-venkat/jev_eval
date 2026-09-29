"""Generate plots/*.png for a run. Agg backend throughout — no display needed, and this
must stay importable and usable in a headless test environment.

PREMISE.md's Outputs section names exactly seven plot files; its acceptance criterion 5
says "nine" without naming two more anywhere, which looks like a slip in the spec rather
than two undocumented plots. This module produces the seven that are actually named and
described (see DECISIONS.md).
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from . import metrics  # noqa: E402
from .summary import frozen_rows, load_latency_samples, load_predictions  # noqa: E402

PLOT_NAMES = [
    "label_sweep.png",
    "reliability_choice.png",
    "reliability_noul.png",
    "confusions_k77.png",
    "score_confusion.png",
    "selective.png",
    "latency.png",
]


def _e1_grouped(predictions: list[dict]) -> dict[int, list[tuple[dict, dict]]]:
    frozen = frozen_rows("banking77_sweep")
    by_k: dict[int, list[tuple[dict, dict]]] = {}
    for p in predictions:
        if not p["id"].startswith("b77-") or p["error"] is not None:
            continue
        row = frozen[p["id"]]
        by_k.setdefault(row["k"], []).append((p, row))
    return by_k


def _e2_list(predictions: list[dict]) -> list[tuple[dict, dict]]:
    frozen = frozen_rows("boolq")
    return [(p, frozen[p["id"]]) for p in predictions if p["id"].startswith("boolq-") and p["error"] is None]


def _e3_list(predictions: list[dict]) -> list[tuple[dict, dict]]:
    frozen = frozen_rows("yelp")
    return [(p, frozen[p["id"]]) for p in predictions if p["id"].startswith("yelp-") and p["error"] is None]


def _reliability_bins(confidence: list[float], correct: list[bool], n_bins: int = 10):
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    conf = np.asarray(confidence)
    corr = np.asarray(correct, dtype=float)
    xs, ys, ns = [], [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (conf > lo) & (conf <= hi) if lo > 0 else (conf >= lo) & (conf <= hi)
        if mask.any():
            xs.append(conf[mask].mean())
            ys.append(corr[mask].mean())
            ns.append(int(mask.sum()))
    return xs, ys, ns


def plot_label_sweep(path: Path, summary_rows: list[dict]) -> None:
    e1_rows = sorted((r for r in summary_rows if r["experiment"] == "e1"), key=lambda r: int(r["condition"].split("=")[1]))
    ks = [int(r["condition"].split("=")[1]) for r in e1_rows]
    acc = [float(r["accuracy"]) for r in e1_rows]
    acc_err = [
        [float(r["accuracy"]) - float(r["accuracy_lo"]) for r in e1_rows],
        [float(r["accuracy_hi"]) - float(r["accuracy"]) for r in e1_rows],
    ]
    ece = [float(r["ece"]) for r in e1_rows]
    chance = [float(r["baseline_accuracy"]) for r in e1_rows]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 7), sharex=True)
    if ks:
        ax1.errorbar(ks, acc, yerr=acc_err, marker="o", capsize=4, label="Jev accuracy")
        ax1.plot(ks, chance, "--", color="grey", label="chance (1/k)")
        ax1.legend()

        ax2.plot(ks, ece, marker="o", color="tab:orange")
        ax2.set_xscale("log")
        ax2.xaxis.set_minor_formatter(plt.NullFormatter())
        ax2.set_xticks(ks)
        ax2.set_xticklabels([str(k) for k in ks])
    else:
        ax1.text(0.5, 0.5, "no E1 data", ha="center", va="center", transform=ax1.transAxes)
    ax1.set_ylabel("accuracy")
    ax1.set_ylim(0, 1.05)
    ax1.set_title("E1: Banking77 label-count sweep")
    ax2.set_ylabel("ECE")
    ax2.set_xlabel("number of options (k)")

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_reliability_choice(path: Path, predictions: list[dict]) -> None:
    by_k = _e1_grouped(predictions)
    ks = sorted(by_k)
    fig, axes = plt.subplots(1, max(len(ks), 1), figsize=(4 * max(len(ks), 1), 4), squeeze=False)
    for ax, k in zip(axes[0], ks):
        pairs = by_k[k]
        confidence = [max(p["probabilities"].values()) for p, _ in pairs]
        correct = [p["answer"] == row["label"] for p, row in pairs]
        xs, ys, ns = _reliability_bins(confidence, correct)
        ax.plot([0, 1], [0, 1], "--", color="grey")
        ax.plot(xs, ys, marker="o")
        ax.set_title(f"k={k} (n={len(pairs)})")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel("confidence")
    axes[0][0].set_ylabel("empirical accuracy")
    fig.suptitle("E1: Choice reliability")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_reliability_noul(path: Path, predictions: list[dict]) -> None:
    pairs = _e2_list(predictions)
    p_yes = [p["probabilities"]["yes"] for p, _ in pairs]
    is_yes = [row["label"] for _, row in pairs]
    xs, ys, ns = _reliability_bins(p_yes, is_yes)

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], "--", color="grey")
    ax.plot(xs, ys, marker="o")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("p(yes)")
    ax.set_ylabel("empirical fraction actually yes")
    ax.set_title(f"E2: Noul reliability (n={len(pairs)})")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_confusions_k77(path: Path, predictions: list[dict]) -> None:
    by_k = _e1_grouped(predictions)
    pairs = by_k.get(77, [])
    counts: dict[tuple[str, str], int] = {}
    for p, row in pairs:
        if p["answer"] != row["label"]:
            key = (row["label"], p["answer"])
            counts[key] = counts.get(key, 0) + 1
    top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:15]

    fig, ax = plt.subplots(figsize=(8, max(3, 0.4 * len(top) + 1)))
    if top:
        labels = [f"{t} → {p}" for (t, p), _ in top]
        values = [c for _, c in top]
        ax.barh(range(len(top)), values)
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(labels, fontsize=8)
        ax.invert_yaxis()
    else:
        ax.text(0.5, 0.5, "no misclassifications at k=77", ha="center", va="center")
        ax.set_xticks([])
        ax.set_yticks([])
    ax.set_xlabel("count")
    ax.set_title(f"E1 k=77: most frequent confusions (n={len(pairs)})")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_score_confusion(path: Path, predictions: list[dict]) -> None:
    pairs = _e3_list(predictions)
    matrix = np.zeros((5, 5), dtype=int)
    for p, row in pairs:
        matrix[row["stars"] - 1][p["answer"] - 1] += 1

    fig, ax = plt.subplots(figsize=(5, 5))
    im = ax.imshow(matrix, cmap="Blues")
    for i in range(5):
        for j in range(5):
            ax.text(j, i, str(matrix[i, j]), ha="center", va="center", fontsize=9)
    ax.set_xticks(range(5))
    ax.set_yticks(range(5))
    ax.set_xticklabels(range(1, 6))
    ax.set_yticklabels(range(1, 6))
    ax.set_xlabel("predicted stars")
    ax.set_ylabel("true stars")
    ax.set_title(f"E3: Yelp score confusion (n={len(pairs)})")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _selective_curve(confidence: list[float], correct: list[bool]) -> tuple[list[float], list[float]]:
    order = np.argsort(confidence)[::-1]
    correct_sorted = np.asarray(correct, dtype=float)[order]
    n = len(correct_sorted)
    cum = np.cumsum(correct_sorted)
    coverage = [(i + 1) / n for i in range(n)]
    accuracy = [cum[i] / (i + 1) for i in range(n)]
    return coverage, accuracy


def plot_selective(path: Path, predictions: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    by_k = _e1_grouped(predictions)
    any_curve = False
    for k in (20, 77):
        pairs = by_k.get(k, [])
        if not pairs:
            continue
        confidence = [max(p["probabilities"].values()) for p, _ in pairs]
        correct = [p["answer"] == row["label"] for p, row in pairs]
        coverage, accuracy = _selective_curve(confidence, correct)
        ax.plot(coverage, accuracy, label=f"E1 k={k} (n={len(pairs)})")
        any_curve = True

    e2_pairs = _e2_list(predictions)
    if e2_pairs:
        confidence = [max(p["probabilities"].values()) for p, _ in e2_pairs]
        correct = [p["answer"] == row["label"] for p, row in e2_pairs]
        coverage, accuracy = _selective_curve(confidence, correct)
        ax.plot(coverage, accuracy, label=f"E2 (n={len(e2_pairs)})")
        any_curve = True

    ax.axhline(0.90, ls=":", color="grey")
    ax.axhline(0.95, ls=":", color="grey")
    ax.set_xlabel("coverage")
    ax.set_ylabel("accuracy on kept items")
    ax.set_ylim(0, 1.05)
    ax.set_title("E4: selective prediction")
    if any_curve:
        ax.legend()
    else:
        ax.text(0.5, 0.5, "no E1 k=20/77 or E2 data", ha="center", va="center", transform=ax.transAxes)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_latency(path: Path, latency_samples: list[dict]) -> None:
    by_kind: dict[str, list[float]] = {}
    for s in latency_samples:
        by_kind.setdefault(s["kind"], []).append(s["latency_ms"])

    wanted = [("single", "1 question"), ("multi5", "5 questions"), ("models", "network baseline")]
    fig, ax = plt.subplots(figsize=(7, 5))
    data = [by_kind.get(kind, []) for kind, _ in wanted]
    labels = [label for _, label in wanted]
    non_empty = [(d, l) for d, l in zip(data, labels) if d]
    if non_empty:
        ax.boxplot([d for d, _ in non_empty], tick_labels=[l for _, l in non_empty], showfliers=False)
    else:
        ax.text(0.5, 0.5, "no latency samples", ha="center", va="center")
    ax.set_ylabel("latency (ms)")
    ax.set_title("E5: latency distributions")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def generate_all(run_dir: Path) -> list[Path]:
    predictions = load_predictions(run_dir)
    latency_samples = load_latency_samples(run_dir)
    summary_path = run_dir / "summary.csv"
    summary_rows = list(csv.DictReader(summary_path.open())) if summary_path.exists() else []

    plots_dir = run_dir / "plots"
    plots_dir.mkdir(exist_ok=True)

    plot_label_sweep(plots_dir / "label_sweep.png", summary_rows)
    plot_reliability_choice(plots_dir / "reliability_choice.png", predictions)
    plot_reliability_noul(plots_dir / "reliability_noul.png", predictions)
    plot_confusions_k77(plots_dir / "confusions_k77.png", predictions)
    plot_score_confusion(plots_dir / "score_confusion.png", predictions)
    plot_selective(plots_dir / "selective.png", predictions)
    plot_latency(plots_dir / "latency.png", latency_samples)

    return [plots_dir / name for name in PLOT_NAMES]
