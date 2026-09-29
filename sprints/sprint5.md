# Sprint 5

Built `metrics.py` (accuracy, macro-F1, multiclass Brier, ECE, Noul accuracy/Brier/AUROC,
Score MAE/exact-accuracy/Spearman, selective-prediction coverage) and a single generic
`bootstrap_ci()` every metric reuses for its 95% CI (1000 resamples, fixed seed 1729).
Added `baselines.py` (chance 1/k, 0.5/Brier-0.25 for Noul, always-3-stars for Score,
computed from the actual sample) and `summary.py`, which derives `summary.csv` — one row
per (experiment, condition) with every metric, CI and baseline — straight from an existing
run's `predictions.jsonl`, no network needed. E4 (selective prediction) reuses saved E1/E2
predictions and sends zero requests. Wired a `jev-eval summarize <run_dir>` subcommand and
auto-summary at the end of `run`.

Tested every metric against hand-computed small examples, the degenerate cases (single-class
AUROC/Spearman, coverage that's never reached — all NaN, not a crash), bootstrap determinism,
and the full summary.csv pipeline against real frozen-data rows. 106 tests pass offline.

Live at `--limit 30` across all five experiments: E1 accuracy 1.0 through k=20, dropping to
0.67 at k=77; E2 hit 0.97 vs a 0.5 baseline; E3 MAE 0.25 vs baseline 1.2; E5's 5-question p50
(337ms) came in under the 1-question p50 (409ms) — first real evidence the parallel-questions
claim holds, though the sample here is still small.
