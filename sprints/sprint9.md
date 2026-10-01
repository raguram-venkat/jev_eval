# Sprint 9

Refactored `src/jev_eval/` from a flat 22-file directory into four subpackages by concern:
`protocol/` (the `/v1/systemone` wire format — building requests, parsing responses),
`client/` (talking to Jev — HTTP, cache, run bookkeeping), `experiments/` (one module per
dataset plus the shared runner and sampling), `analysis/` (metrics, baselines, summary.csv,
plots, REPORT.md). `cli.py`, `config.py`, `frozen.py`, `results.py` and `capture_fixtures.py`
stayed at the top level. No behavior changed — every import was traced and rewritten by hand,
with no `__init__.py` re-exports, so the import path always matches the file on disk.

Every markdown file with a reference to a moved module got updated too — `DECISIONS.md`,
`INDEX.md`, and the sprint notes that named a now-relocated file — so none of them point
somewhere stale. 119 tests pass unchanged, the CLI and `capture_fixtures.py` both still
resolve and run, and a live smoke run confirmed the restructured package works end to end.
