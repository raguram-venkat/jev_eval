"""Metrics for each primitive, plus a generic bootstrap CI helper.

Every accuracy-type metric here is computed from probabilities/scores, never from the
`confidence` field — the docs define confidence as distribution concentration, not
correctness, so it must not leak into a metric that's supposed to measure correctness.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
from scipy import stats as scipy_stats
from sklearn.metrics import f1_score, roc_auc_score

BOOTSTRAP_RESAMPLES = 1000
BOOTSTRAP_SEED = 1729


def bootstrap_ci(n_items: int, stat_fn: Callable[[np.ndarray], float]) -> tuple[float, float]:
    """95% CI via `n_items` case resampling. `stat_fn(idx)` computes the statistic on
    the resampled indices; the caller closes over whatever arrays it needs."""
    if n_items == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    values = np.empty(BOOTSTRAP_RESAMPLES)
    for i in range(BOOTSTRAP_RESAMPLES):
        idx = rng.integers(0, n_items, size=n_items)
        values[i] = stat_fn(idx)
    lo, hi = np.percentile(values, [2.5, 97.5])
    return float(lo), float(hi)


# ---- Choice ----------------------------------------------------------------

def choice_accuracy(y_true: list[str], y_pred: list[str]) -> float:
    return float(np.mean([t == p for t, p in zip(y_true, y_pred)]))


def choice_macro_f1(y_true: list[str], y_pred: list[str]) -> float:
    return float(f1_score(y_true, y_pred, average="macro", zero_division=0))


def choice_brier(y_true: list[str], probs: list[dict[str, float]]) -> float:
    """Multiclass Brier score: mean squared distance between each row's own probability
    vector and its one-hot true label. Each row sums over its own option set, since
    Banking77 rows pooled across draws (even at the same k) can have different options."""
    total = 0.0
    for t, p in zip(y_true, probs):
        total += sum((prob - (1.0 if opt == t else 0.0)) ** 2 for opt, prob in p.items())
    return total / len(y_true)


def choice_ece(max_probs: list[float], correct: list[bool], n_bins: int = 15) -> float:
    """Equal-width bins on the max probability."""
    max_probs = np.asarray(max_probs)
    correct = np.asarray(correct, dtype=float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    n = len(max_probs)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        in_bin = (max_probs > lo) & (max_probs <= hi) if lo > 0 else (max_probs >= lo) & (max_probs <= hi)
        if not in_bin.any():
            continue
        bin_conf = max_probs[in_bin].mean()
        bin_acc = correct[in_bin].mean()
        ece += (in_bin.sum() / n) * abs(bin_conf - bin_acc)
    return float(ece)


def choice_p_true_below(probs: list[dict[str, float]], y_true: list[str], threshold: float = 0.01) -> float:
    below = [p.get(t, 0.0) < threshold for p, t in zip(probs, y_true)]
    return float(np.mean(below))


# ---- Noul --------------------------------------------------------------------

def noul_accuracy(y_true: list[bool], p_yes: list[float], threshold: float = 0.5) -> float:
    pred = [p >= threshold for p in p_yes]
    return float(np.mean([t == pr for t, pr in zip(y_true, pred)]))


def noul_brier(y_true: list[bool], p_yes: list[float]) -> float:
    return float(np.mean([(p - float(t)) ** 2 for t, p in zip(y_true, p_yes)]))


def noul_auroc(y_true: list[bool], p_yes: list[float]) -> float:
    if len(set(y_true)) < 2:
        return float("nan")
    return float(roc_auc_score(y_true, p_yes))


# ---- Score ---------------------------------------------------------------------

def score_mae(y_true_stars: list[int], pred_score: list[float]) -> float:
    return float(np.mean([abs(t - p) for t, p in zip(y_true_stars, pred_score)]))


def score_exact_accuracy(y_true_stars: list[int], pred_stars: list[int]) -> float:
    return float(np.mean([t == p for t, p in zip(y_true_stars, pred_stars)]))


def score_spearman(y_true_stars: list[int], pred_score: list[float]) -> float:
    if len(set(y_true_stars)) < 2 or len(set(pred_score)) < 2:
        return float("nan")
    rho, _ = scipy_stats.spearmanr(y_true_stars, pred_score)
    return float(rho)


# ---- Selective prediction (E4) ---------------------------------------------------

def coverage_at_accuracy(confidence: list[float], correct: list[bool], target: float) -> float:
    """Max coverage (fraction of items kept) at which accuracy on the kept items is
    still >= target, sweeping a confidence threshold from 1 down to 0. NaN if the target
    is never reached (e.g. even keeping only the single most confident item falls short)."""
    order = np.argsort(confidence)[::-1]  # most confident first
    correct_sorted = np.asarray(correct, dtype=float)[order]
    n = len(correct_sorted)
    cum_correct = np.cumsum(correct_sorted)
    best_coverage = float("nan")
    for kept in range(1, n + 1):
        acc = cum_correct[kept - 1] / kept
        if acc >= target:
            best_coverage = kept / n
    return best_coverage
