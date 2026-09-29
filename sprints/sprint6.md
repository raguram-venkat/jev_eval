# Sprint 6

Built `plots.py` (the seven plots PREMISE.md actually names: label sweep with CI and
chance line, Choice/Noul reliability diagrams, k=77 confusion bar chart, Yelp 5x5 score
confusion matrix, E4 selective-prediction curves, E5 latency boxplots — all Agg backend,
non-empty even on missing data) and `report.py` (`REPORT.md`: a results table, one finding
paragraph per experiment with CIs and the baseline it beats, a "Where Jev fails" section
with real misclassified examples, and a caveats section). Also added abort-path handling:
a run that hits an auth error, model-version change or the request cap now writes a
`manifest.json` with an `aborted` reason and stops there — no partial `summary.csv`, plots
or `REPORT.md` pretending the run finished.

Fixed two real bugs the tests caught: a log-scale plot that crashed outright on zero E1
data, and `AuthError` not being one of the exceptions `run` treated as an abort (it would
have crashed with a raw traceback on a live 401). 112 tests pass offline.

Live at `--limit 30` across all five experiments: full pipeline end to end, all seven PNGs
and a complete `REPORT.md` generated from real Jev responses, git history scanned clean for
the API key.
