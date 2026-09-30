# jev-eval

Reproducible CLI benchmark for Jev, TypeSafe AI's hosted System One model: measures Choice,
Noul and Score performance and calibration on Banking77, BoolQ and Yelp. Zero-shot, no
fine-tuning, no prompt tuning based on results. See `PREMISE.md` for the full spec and
`sprints/` for what was built when.

## Install

```
uv sync
```

Python 3.12 via `uv`; no torch or other ML frameworks (`datasets` is a dev-only dependency,
used solely by `prep_data.py` to build the frozen data, not by the benchmark itself).

## Configure

- `TYPESAFE_API_KEY` — required. Read from the environment, `.strip()`ped, never printed,
  logged or written to disk (including cache entries).
- `JEV_BASE_URL` — optional, defaults to `https://api.typesafe.ai`. Point it at any
  `/v1/systemone`-compatible backend.

## Where data lives

- `data/frozen/` — read-only input data (Banking77/BoolQ/Yelp), sha256-verified against
  `manifest.json` on every `run`. Never modified.
- `tests/fixtures/` — real captured Jev requests/responses, used by offline parser tests.
  Capture (or refresh) them with `./capture_fixtures.sh` (needs `TYPESAFE_API_KEY`).
- `cache/` — disk response cache, keyed by model + canonical request body. Safe to delete.
- `results/<run_id>/` — one directory per `run`, plus a `results/latest` symlink:
  `predictions.jsonl`, `manifest.json`, `summary.csv`, `plots/*.png`, `REPORT.md`.

## Cheatsheet

```
uv run jev-eval run                              # full benchmark, all five experiments
uv run jev-eval run --limit 20                    # smoke run, 20 rows/requests per experiment
uv run jev-eval run --no-cache                    # bypass the disk cache entirely
uv run jev-eval run --experiments e1,e2            # only Banking77 (Choice) and BoolQ (Noul)
uv run jev-eval summarize results/latest           # re-derive summary.csv, no network needed
uv run pytest -q                                   # full offline test suite (network blocked)
```

`--limit` is stratified per dataset (every `(k, draw)` group for E1, balanced yes/no for E2,
every star rating for E3) so even a small `--limit` covers every condition. E4 (selective
prediction) is derived from saved E1 (k=20, 77) and E2 predictions and never sends a request;
E5 (latency) always ignores the cache and runs sequentially, regardless of `--no-cache`.

## Error behaviour

| Situation | Exit code | Message names |
|---|---|---|
| `TYPESAFE_API_KEY` unset or blank | 2 | the variable, never its value |
| Bad `--limit`/`--experiments` | 2 | the bad flag and value (argparse usage) |
| `data/frozen/` hash mismatch, missing file/manifest | 1 | the offending file |
| Preflight `GET /v1/models` fails | 1 | the URL and status/exception, never the key |
| Live auth error (401/403) mid-run | 1 | the status; writes `manifest.json` with `aborted` set |
| Model version changes mid-run | 1 | old and new model; writes an aborted manifest |
| Planned requests exceed the 4000 cap | 1 | planned count vs. the cap; writes an aborted manifest |
| Missing test fixture | pytest failure | which fixture, and to run `capture_fixtures.sh` |

An aborted run never produces `summary.csv`, `plots/` or `REPORT.md` — only a `manifest.json`
that says so, plus whatever `predictions.jsonl` was collected before the abort.

## Non-goals

Zero-shot only, no fine-tuning or criteria tuning based on results. Raw HTTP against
`/v1/systemone`, no vendor SDK. One model in this phase (the client is parameterized by
base URL and key so a second `/v1/systemone`-compatible backend could be added later, but
nothing is implemented for it). CLI and files on disk — no UI.

## Guardrails

`data/frozen/` and `tests/fixtures/` are never written to by anything in `src/`. The API key
never appears in a log line, cache file, error message or `repr()`/`str()` of any object that
holds it. `run` never substitutes a mock to force a green result — if Jev is unreachable or
rejects the key, it stops and says so.
