# jev-eval: how this actually came together

A guided walkthrough of how this project was built and what it measures, so you don't have
to reconstruct it from `DECISIONS.md`, `sprints/*.md` and the code. Start here; drop down to
those files only when you want the full detail behind something.

## What this is

**jev-eval** benchmarks Jev, TypeSafe AI's hosted typed-decision model, on three question
shapes it exposes — Choice (pick one of k options), Noul (yes/no), Score (1-5 ordinal) —
against three public datasets, zero-shot. The point isn't just "is it right," it's "does its
confidence mean anything": calibration (ECE, Brier, AUROC), not just accuracy. Full spec in
`PREMISE.md`; this file is about *how it got built* and *how it fits together*.

## How it got built

The project started with a different automation attempt — a custom "lathe" harness living in
a now-deleted `.loop/` directory, driving the work through its own planning/task files. It
didn't work out, so it was scrapped outright: the branch it lived on was deleted, and the
code it had produced was thrown away and rebuilt directly, sprint by sprint, with a plain git
history and one short note per sprint in `sprints/`. No upfront plan document, no task
tracker — each sprint just did the next load-bearing piece and moved on.

The eight sprints, in the order they actually happened and why that order:

1. **Foundation** — package skeleton, `Config` (reads the API key, never leaks it),
   `frozen.py` (verifies `data/frozen/` against its sha256 manifest), and `questions.py`
   (the instructions/criteria text for each dataset). Nothing here talks to the network —
   it's the stuff that has to be right before a single request is sent.
2. **Talk to Jev** — `JevClient` (retry, typed errors, a `/v1/models` preflight), a disk
   `Cache`, and `RunContext` (the request cap and model-version guard). Still no live calls;
   all tested against a fake loopback HTTP server. This had to exist before any experiment
   could run, which is why it came before E1.
3. **First real numbers** — this is where the actual `/v1/systemone` wire format got learned
   (it's not in `PREMISE.md`; see "the request/response shape" below), `parsers.py` got
   written against real captured fixtures, and E1 (Banking77) ran live for the first time.
   One milestone, one real number — proof the whole pipeline works before building four more
   copies of it.
4. **E2 and E3** reused sprint 3's runner unchanged (see "the dataset-agnostic runner"
   below) — only the dataset-specific pieces needed writing. **E5** (latency) came in the
   same sprint because it shares nothing with E1-E3's machinery; it's a different, simpler
   shape (sequential, no cache) and was quick once the client existed.
5. **Metrics, baselines, E4, `summary.csv`** — now that real predictions existed to test
   against, it made sense to build the numbers layer. E4 (selective prediction) turned out to
   need no new code path at all, just a derivation from E1/E2 predictions already on disk.
6. **Plots and `REPORT.md`** — the human-readable output, built last because it depends on
   everything above actually working.
7. **README** — once the CLI's shape had stopped changing, it was safe to document it without
   the docs immediately going stale.
8. **The full live run and this project's one results artifact** — 2,040 real predictions,
   zero failures, and the final demo page (link in `sprints/sprint8.md`, and in the table
   below).

Each sprint's commit and `sprints/sprintN.md` note says what shipped; `DECISIONS.md` has one
line per non-obvious call, with the reason, grouped the same way.

## The experiment design

Three datasets, each mapped to one Jev primitive:

| Dataset | Primitive | What's asked | Rows |
|---|---|---|---|
| Banking77 | Choice | which of k intents does this message express | 1,440 (k swept across 2/5/20/77) |
| BoolQ | Noul | is the answer to this question, given this passage, yes | 300 (balanced yes/no) |
| Yelp | Score | how positive is this review, on 5 ordered levels | 300 (60 per star) |

Five experiments:

- **E1** sweeps Banking77's k (2→77) to see how accuracy *and calibration* degrade as the
  decision gets harder — this is the headline chart, because it's the one place the dataset
  itself varies in difficulty on purpose.
- **E2** and **E3** each run once, scored against a baseline that isn't Jev: 0.5
  accuracy/0.25 Brier for a coin-flip Noul predictor, and an always-guess-3-stars predictor
  for Score. The point of a baseline is to make "91% accuracy" mean something — it's 41
  points better than guessing, not just a number in isolation.
- **E4** asks a product question, not a model question: if low-confidence answers escalate to
  a human, how much traffic can still be auto-handled at 90%/95% accuracy? It costs nothing
  extra — it's a re-sort of E1/E2's own predictions by confidence, no new requests.
- **E5** isolates one engineering claim (batching several questions against one state is
  close to free) from the accuracy experiments entirely, because mixing a timing measurement
  into a concurrency-4 accuracy run would make the timing meaningless.

Every accuracy-type number carries a 95% bootstrap CI (1000 resamples, fixed seed) — one
generic `bootstrap_ci()` helper in `metrics.py` that every metric closes over, so a new metric
gets a CI for free instead of a bespoke interval routine.

## How a request actually flows

Tracing `uv run jev-eval run --experiments e1`:

1. `cli.py` parses flags, loads `Config` (exits 2 if the key's missing), verifies
   `data/frozen/` (exits 1 on a hash mismatch) — all before any network call.
2. Builds a `JevClient` (cached unless `--no-cache`) and runs its `/v1/models` preflight
   (exits 1 if that fails).
3. For E1: `e1.load_rows()` reads the frozen jsonl, `e1.stratified_sample()` applies
   `--limit` (round-robin across every `(k, draw)` group so even a small limit touches every
   condition), then `questions.banking77_request()` builds each request body.
4. `runner.run_experiment()` fans those out through a `ThreadPoolExecutor` (concurrency 4).
   Each request goes through `RunContext.run()`, which reserves a slot against the 4000
   request cap, calls `JevClient.request()` (cache check → POST with retry/backoff → record
   model version), and folds a failure into that experiment's failure count.
5. `JevClient.request()` checks the cache first; on a miss it POSTs, retries 429/5xx with
   backoff, raises `AuthError` immediately on 401/403 (no retry), and on success writes the
   response into the cache keyed by `sha256(requested_model + canonical_body)`.
6. A successful `Result` gets handed to `e1.parse_result()`, which calls
   `parsers.parse_choice()` (clips/renormalizes probabilities, checks the answer equals the
   argmax) and returns a `Prediction`.
7. Back in `cli.py`: `results.write_predictions()`, `write_manifest()`, then
   `summary.write_summary()` (metrics + CIs + baselines → `summary.csv`), `plots.generate_all()`
   (7 PNGs), `report.write_report()` (`REPORT.md`), and `results/latest` gets repointed.

If step 4 or 5 raises `ModelChangedError`, `RequestCapError` or `AuthError`, that whole
sequence stops: `manifest.json` gets written with an `aborted` reason and no
`summary.csv`/`plots/`/`REPORT.md` — a partial run can never look like a finished one.

## Decisions that mattered more than the rest

The full list is in `DECISIONS.md`. These are the ones that shaped everything downstream:

- **The dataset-agnostic runner.** `runner.run_experiment()` knows nothing about Banking77,
  BoolQ or Yelp — it takes rows plus a `request_fn`/`parse_fn` pair. E2 and E3 are each about
  60 lines because of this; adding a fourth dataset later would be the same shape again.
- **The cache key is `sha256(requested_model + canonical_body)`, not the returned model
  version** — the version you get back isn't known until the response arrives, so it can't be
  part of the key. Every cache entry stores the version it came from, and every response (live
  or cached) feeds the model-version guard, so a stale entry from a different model version
  aborts the run instead of silently mixing results.
- **Predictions aren't tagged with which experiment produced them** — `summary.py` and
  `plots.py` bucket `predictions.jsonl` rows by id prefix (`b77-`/`boolq-`/`yelp-`) instead,
  since the prefix already does that job reliably.
- **Choice's Brier/ECE sum over each row's own probability dict**, not a shared label list —
  Banking77 rows pooled across draws (even at the same k) can have completely different
  option subsets, so there's no single shared label space to score against.
- **`AuthError` is an abort, same as a model change or the request cap.** This was originally
  missed (only the latter two were caught) and would have crashed with a raw traceback on a
  live 401; caught by writing a test for it before it happened live.

## Where to go for more

| Question | Answer lives in |
|---|---|
| What's the full original spec? | `PREMISE.md` |
| Why was X done this way? | `DECISIONS.md` |
| What happened in sprint N? | `sprints/sprintN.md` |
| How do I run it? | `README.md` |
| What did the last full run actually find? | `results/latest/REPORT.md`, or the [results artifact](https://claude.ai/artifact/2poaNita7Sy29SMsNEcCiY) |
| How does module X work? | the module's own docstring — each one states its job in one line at the top |
