# Sprint 3

First real numbers. Learned the actual `/v1/systemone` wire format from the live docs (not
in PREMISE.md), added request builders to `protocol/questions.py`, and captured real
Choice/Noul/Score/models fixtures via a new `capture_fixtures.sh`. Built
`protocol/parsers.py` (normalizing, clipping and renormalizing probabilities per primitive),
a dataset-agnostic `run_experiment()` runner, and E1 — the Banking77 label-count sweep —
wired into `jev-eval run`, writing `predictions.jsonl`, `manifest.json` and a
`results/latest` symlink.

Tested the parsers against both the captured fixtures and hand-built edge cases (missing
answers, wrong type, non-numeric or missing probability keys, clipping/renormalizing), the
stratified `--limit` sampling for full group coverage, and the whole CLI path end-to-end
against a fake server that echoes a request-dependent answer. 73 tests pass offline.

Then ran it for real: `jev-eval run --limit 20 --experiments e1` against the live Jev API —
19/20 correct, one miss at k=77. First actual signal out of the benchmark.
