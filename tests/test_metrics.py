import math

import pytest

from jev_eval.analysis import baselines, metrics


def test_choice_accuracy():
    assert metrics.choice_accuracy(["a", "b", "a"], ["a", "a", "a"]) == pytest.approx(2 / 3)


def test_choice_macro_f1_hand_computed():
    # class a: TP=1 FP=1 FN=1 -> F1=0.5; class b: TP=1 FP=1 FN=1 -> F1=0.5; macro=0.5
    f1 = metrics.choice_macro_f1(["a", "a", "b", "b"], ["a", "b", "b", "a"])
    assert f1 == pytest.approx(0.5)


def test_choice_brier_hand_computed():
    brier = metrics.choice_brier(["a"], [{"a": 0.7, "b": 0.3}])
    assert brier == pytest.approx((0.7 - 1) ** 2 + (0.3 - 0) ** 2)


def test_choice_brier_sums_over_each_rows_own_options():
    # different rows can have different option sets (e.g. Banking77 draws); each row
    # must be scored against its own distribution, not a shared label list.
    brier = metrics.choice_brier(["a", "x"], [{"a": 1.0, "b": 0.0}, {"x": 1.0, "y": 0.0}])
    assert brier == pytest.approx(0.0)


def test_choice_ece_hand_computed_two_bins():
    ece = metrics.choice_ece([0.9, 0.9, 0.4, 0.4], [True, False, True, False], n_bins=2)
    # bin(0,0.5]: conf=0.4 acc=0.5 weight 0.5 -> 0.05; bin(0.5,1.0]: conf=0.9 acc=0.5 weight 0.5 -> 0.2
    assert ece == pytest.approx(0.25)


def test_choice_p_true_below_threshold():
    rate = metrics.choice_p_true_below([{"a": 0.005}, {"a": 0.5}], ["a", "a"], threshold=0.01)
    assert rate == pytest.approx(0.5)


def test_noul_accuracy_and_brier():
    y_true = [True, False, True]
    p_yes = [0.6, 0.6, 0.3]
    assert metrics.noul_accuracy(y_true, p_yes) == pytest.approx(1 / 3)
    assert metrics.noul_brier(y_true, p_yes) == pytest.approx(((0.4) ** 2 + 0.36 + 0.49) / 3)


def test_noul_auroc_perfect_separation():
    assert metrics.noul_auroc([True, False], [0.8, 0.2]) == pytest.approx(1.0)


def test_noul_auroc_single_class_is_nan():
    assert math.isnan(metrics.noul_auroc([True, True, True], [0.9, 0.8, 0.7]))


def test_score_mae_and_exact_accuracy():
    assert metrics.score_mae([1, 5], [2, 4]) == pytest.approx(1.0)
    assert metrics.score_exact_accuracy([1, 5], [1, 4]) == pytest.approx(0.5)


def test_score_spearman_perfect_and_degenerate():
    assert metrics.score_spearman([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)
    assert math.isnan(metrics.score_spearman([1, 1, 1], [1, 2, 3]))


def test_coverage_at_accuracy_differs_by_target():
    confidence = list(range(10, 0, -1))
    correct = [True] * 9 + [False]  # 9/10 right, the least-confident one wrong
    assert metrics.coverage_at_accuracy(confidence, correct, 0.90) == pytest.approx(1.0)
    assert metrics.coverage_at_accuracy(confidence, correct, 0.95) == pytest.approx(0.9)


def test_coverage_at_accuracy_nan_when_never_reached():
    assert math.isnan(metrics.coverage_at_accuracy([0.9, 0.1], [False, False], 0.5))


def test_bootstrap_ci_is_deterministic():
    values = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]

    def stat_fn(idx):
        return sum(values[i] for i in idx) / len(idx)

    first = metrics.bootstrap_ci(len(values), stat_fn)
    second = metrics.bootstrap_ci(len(values), stat_fn)
    assert first == second


def test_bootstrap_ci_bounds_the_point_estimate_reasonably():
    values = [1] * 8 + [0] * 2  # accuracy 0.8

    def stat_fn(idx):
        return sum(values[i] for i in idx) / len(idx)

    lo, hi = metrics.bootstrap_ci(len(values), stat_fn)
    assert lo <= 0.8 <= hi


def test_bootstrap_ci_empty_is_nan():
    assert metrics.bootstrap_ci(0, lambda idx: 0.0) == (float("nan"), float("nan")) or all(
        math.isnan(x) for x in metrics.bootstrap_ci(0, lambda idx: 0.0)
    )


def test_chance_accuracy():
    assert baselines.chance_accuracy(5) == pytest.approx(0.2)


def test_noul_baseline():
    assert baselines.noul_baseline() == (0.5, 0.25)


def test_score_always_baseline_computed_from_data():
    mae, exact_accuracy = baselines.score_always_baseline([1, 2, 3, 4, 5], constant=3)
    assert mae == pytest.approx(1.2)
    assert exact_accuracy == pytest.approx(0.2)
