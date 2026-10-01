"""Naive baselines so every number in the report has a reference point.

E2 and E3's baselines are computed from the actual true labels in the sample, not
hard-coded, even though the E2 numbers happen to be constants regardless of the data.
"""
from __future__ import annotations

import numpy as np


def chance_accuracy(k: int) -> float:
    return 1.0 / k


def noul_baseline() -> tuple[float, float]:
    """Always predicting p(yes) = 0.5 on a balanced set: accuracy and Brier score."""
    return 0.5, 0.25


def score_always_baseline(y_true_stars: list[int], constant: int = 3) -> tuple[float, float]:
    """Always predicting `constant` stars: MAE and exact-level accuracy."""
    y = np.asarray(y_true_stars)
    mae = float(np.mean(np.abs(y - constant)))
    exact_accuracy = float(np.mean(y == constant))
    return mae, exact_accuracy
