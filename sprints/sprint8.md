# Sprint 8

Ran the real thing: `jev-eval run` unrestricted, all five experiments, 2,040 live predictions
against Jev plus 190 latency samples, zero failed requests, ~4.5 minutes wall clock. Verified
every acceptance criterion against real output: `summary.csv` covers every (experiment,
condition), all seven plots render non-empty, `REPORT.md` reads correctly with real findings
and failure examples, `manifest.json` has every field, and a full grep of the repo, `results/`
and git history for the API key comes back clean.

Built one final artifact from those real numbers — not a sprint-by-sprint demo, the single
results page for the whole project: headline finding (98.8% accuracy at k=2 down to 79.3% at
k=77), calibration for BoolQ and Yelp, the Yelp confusion matrix, real selective-prediction
curves computed from this run's own predictions, a latency comparison, and five genuine
misclassifications chosen to show the different shapes failure takes here, including a couple
where the dataset's own ground truth looks arguable. Caught and fixed three real bugs in the
page during review: an axis-label collision, an arithmetic error in the prose, and a chart
that was quietly pulling numbers from the wrong E5 sample group.

https://claude.ai/artifact/2poaNita7Sy29SMsNEcCiY
