# twin-bench (phase 1: Jev only)

## Goal

Build a reproducible CLI benchmark that measures how well Jev, TypeSafe AI's hosted System One model, handles typed decisions, and visualises where it succeeds and fails across three question types.

- Endpoint: `POST {JEV_BASE_URL}/v1/systemone`
- Primitives under test: Choice, Noul, Score
- Questions answered by the output:
  - How does Choice accuracy and calibration degrade as the number of options grows?
  - Are Jev's probabilities calibrated, i.e. is 0.8 right about 80% of the time?
  - How much work can be auto-handled at a target accuracy if low-confidence cases escalate?
  - What does latency look like from this machine, and how much of it is network?

## Non-goals

- No fine-tuning and no prompt or criteria tuning based on results. Zero-shot only.
- No vendor SDK. Use raw HTTP against the `/v1/systemone` contract.
- No second model in this phase. Keep the client parameterised by base URL and auth header so another `/v1/systemone`-compatible backend can be added later, but implement nothing for it.
- No UI. CLI plus files on disk.

## Environment (fixed)

| Item | Value |
|---|---|
| OS | Ubuntu laptop, Intel i5-1135G7 CPU, ~7 GB RAM, no GPU |
| Python | managed by `uv`. No torch or other ML frameworks are needed; do not add them |
| Auth | `TYPESAFE_API_KEY` exported in the environment |
| Endpoint | `JEV_BASE_URL`, default `https://api.typesafe.ai` |

Before any run, check `GET {JEV_BASE_URL}/v1/models` succeeds. If it fails, stop with a clear message.

## Inputs (read-only)

`data/frozen/` was produced by `prep_data.py` and must never be modified. At startup, verify every file's sha256 against `data/frozen/manifest.json` and abort on mismatch.

| File | Rows | Fields | Primitive |
|---|---|---|---|
| banking77_sweep.jsonl | 1440 | id, k, draw, text, label, options | Choice |
| boolq.jsonl | 300 (150 yes, 150 no) | id, question, passage, label (bool) | Noul |
| yelp.jsonl | 300 (60 per star) | id, text, stars (1-5) | Score |

In banking77_sweep, `k` is the number of options (2, 5, 20 or 77) and `draw` identifies which random label subset was used (3 draws for k below 77).

`tests/fixtures/` holds real captured Jev requests and responses (choice, noul, models list). These are the source of truth for response shapes. Do not edit the human-captured files.

## Question design

All question text lives in one module imported by every experiment. Record its hash in each run manifest.

- Banking77: state `{"message": text}`. Choice. Instructions: "Which banking intent does this customer message express?" Criteria map each option name in the row's `options` to itself.
- BoolQ: state `{"passage": ..., "question": ...}`. Noul. Instructions: "According to `passage`, is the answer to `question` yes?"
- Yelp: state `{"review": text}`. Score with 5 ordered levels, each describing a concrete situation (1 star = very negative experience ... 5 stars = excellent experience). Read the Score schema from the live docs (docs.typesafe.ai/primitives/score.md), then capture one real Score request and response into `tests/fixtures/score_*.json` in M1 before writing Score parsing.

## Experiments

| ID | What | Data |
|---|---|---|
| E1 | Label-count sweep: accuracy and calibration vs number of options | banking77_sweep, all 1440 rows |
| E2 | Yes/no calibration | boolq, 300 rows |
| E3 | Ordinal scoring | yelp, 300 rows |
| E4 | Selective prediction: accuracy vs coverage as a confidence threshold sweeps from 0 to 1 | reuses E1 (k = 20 and 77) and E2 predictions, no new calls |
| E5 | Latency | 100 sequential single-question requests after 10 warmups; 30 `GET /v1/models` calls as a network baseline; the same state sent with 1 and with 5 independent questions (30 each) to test the parallel-questions claim |

Latency is never read from cache. E5 runs with concurrency 1.

## Baselines (so every number has a reference)

| Experiment | Baseline |
|---|---|
| E1 | chance accuracy 1/k per condition |
| E2 | 0.5 accuracy (balanced set); Brier 0.25 for always predicting 0.5 |
| E3 | always predict 3 stars (report its MAE and exact accuracy) |

Plot baselines on the same axes as Jev's results.

## Metrics

| Primitive | Metrics |
|---|---|
| Choice | accuracy, macro-F1, multiclass Brier, ECE (15 equal-width bins on max probability), rate of p(true label) below 0.01 |
| Noul | accuracy at threshold 0.5, Brier, ECE (15 bins), AUROC |
| Score | MAE of returned score vs true stars, exact-level accuracy, Spearman correlation |
| Selective | coverage at 90% and 95% accuracy |
| Latency | client wall-clock p50, p95, p99 in ms; network baseline p50; ratio of 5-question to 1-question p50 |

Every accuracy-type metric gets a 95% bootstrap CI (1000 resamples, fixed seed). Compute ECE and selective curves from probabilities, not the `confidence` field; the docs define confidence as distribution concentration, not correctness.

## Engineering requirements

- Disk response cache under `cache/`, keyed by sha256 of the returned model version and request body. Reruns hit the cache; `--no-cache` bypasses it.
- Up to 4 concurrent requests for E1 to E3.
- Retry 429 and 5xx with exponential backoff, max 5 attempts. Count and report failures.
- Hard cap: abort if one invocation would send more than 4000 requests.
- `--limit N` flag for smoke runs (N rows per experiment).
- Record the `model` field of every response. Abort if the model version changes mid-run.
- `uv run pytest` runs fully offline using fixtures and a fake local HTTP server. Mocks exist only in tests, never in `run`.
- Keep a `DECISIONS.md` log: one line per non-obvious choice, with the reason.

## Outputs

`results/<run_id>/`, with a `results/latest` symlink:

- `predictions.jsonl`: one row per item, with answer, full probabilities, confidence, latency_ms, model version and cache-hit flag
- `summary.csv`: one row per (experiment, condition) with every metric and CI bounds
- `plots/label_sweep.png`: accuracy and ECE vs k with CI bars, chance line overlaid
- `plots/reliability_choice.png`: one panel per k
- `plots/reliability_noul.png`
- `plots/confusions_k77.png`: the 15 most frequent confusion pairs at k = 77, as a horizontal bar chart
- `plots/score_confusion.png`: 5x5 true vs predicted stars
- `plots/selective.png`: accuracy vs coverage curves for E1 (k = 20, 77) and E2
- `plots/latency.png`: latency distributions for single-question, 5-question and network baseline
- `manifest.json`: git commit, model version, dataset hashes, seed, question-module hash, start and end time
- `REPORT.md`

## Acceptance criteria (all must pass)

1. `uv run pytest` passes with networking disabled.
2. `uv run twinbench run --limit 20` completes against live Jev in under 5 minutes.
3. `uv run twinbench run` completes the full set with at most 1% failed requests per experiment, with failures reported.
4. `summary.csv` contains every (experiment, condition) row with all metrics from the Metrics table.
5. All nine plot files listed in Outputs exist and are non-empty.
6. `REPORT.md` has results tables, and one paragraph per experiment stating the finding with CIs and the baseline it beats. It also has:
   - a "Where Jev fails" section with at least 10 concrete misclassified examples drawn from predictions.jsonl
   - a Caveats section covering label-name-only criteria, network RTT from this machine, single run date and model version, and filtered input lengths
7. `manifest.json` has every field listed in Outputs.

## Guardrails

- Never print, log, cache or commit `TYPESAFE_API_KEY` or any header containing it.
- Never modify `data/frozen/` or the human-captured fixtures.
- Never change question text in response to results.
- If Jev is unreachable or returns auth errors, stop and report. Never substitute a mock to get a green run.

## Milestones

1. M1: client, config, manifest verification, Score fixture capture, offline tests green
2. M2: E1 end-to-end on `--limit 20`
3. M3: E2, E3, E5 end-to-end on `--limit 20`
4. M4: metrics, CIs, baselines, E4, all plots, summary.csv
5. M5: full run, REPORT.md, acceptance criteria verified