# Decisions

One line per non-obvious choice, with the reason.

## Sprint 1

- The package is `jev_eval` (`module-name = "jev_eval"` in `[tool.uv.build-backend]`, matching the `src/jev_eval` directory), while the console script and CLI prog name are the hyphenated `jev-eval`, since hyphens aren't valid in a Python module name but are the normal CLI convention.
- `datasets` moved to a dev dependency group: only `prep_data.py` needs it, the benchmark itself doesn't. The unused `pytorch-cpu` index is removed (no torch anywhere in this project).
- `Config.api_key` is `field(repr=False)` and `__repr__`/`__str__` are overridden to print only `base_url`; the `Authorization` header is built on demand by `auth_headers()` and never stored on the object, so no dump of a config can leak the key.
- The key is `.strip()`ped; a whitespace-only key counts as unset (catches a trailing newline from `export KEY=$(cat file)`).
- Argparse usage errors (`--limit`, `--experiments`) exit 2 before the key is even read; a missing key also exits 2 via `parser.exit`. A frozen-data failure exits 1, naming the offending file.
- Frozen data is verified with `hashlib.file_digest` over files opened `rb` only; nothing under `data/frozen/` is ever opened for writing (tested by spying on `Path.open`).
- `questions.py` is hashed as raw file bytes, so any edit to instructions, criteria or state builders changes `questions_hash()`. Question text must never change in response to results.
- Yelp Score levels are 0-based on the wire (level i is i + 1 stars); the five level texts are fixed before any results exist.
- Banking77 criteria are label-name-only (`{opt: opt}`), a deliberate zero-shot choice, called out as a caveat later in the report.
- `tests/conftest.py` blocks non-loopback network access via `pytest.fail` (a `BaseException`), so a retry loop that catches `Exception` can't hide an accidental live call.

## Sprint 2

- **Cache key / model-version scheme:** the key is `sha256(requested_model + "\n" + canonical_body)`, where `requested_model` is the request's own `model` field (e.g. `jev-latest`) and `canonical_body` is `json.dumps(body, sort_keys=True, separators=(',',':'))`. The *returned* version isn't known until a response arrives, so it can't be part of the key — instead every entry stores it, and every response (live or cached) feeds the run's model-version guard, so a stale entry from another version aborts the run instead of silently mixing versions.
- Cache entries hold only `key`, `requested_model`, `model`, `latency_ms` and the response — never headers or the request body. Writes are temp-file-then-`os.replace` so a reader never sees a half-written file; an unreadable or malformed entry is treated as a miss, not an error.
- `--no-cache` builds the client with `cache=None`, so `cache/` is never even created, let alone read or written.
- Retry: 429, 5xx and `httpx.TransportError` retry up to 5 attempts with `min(2**(attempt-1), 30)` s backoff plus jitter (0-1s, both injectable so tests never wait); `Retry-After` (seconds form only) replaces the backoff base, capped at 60s so a hostile header can't stall a run. 401/403 raise `AuthError` on the first attempt with no retry — retrying an auth failure wastes 4 attempts on something that will never succeed.
- One `threading.Lock` inside `RunContext` guards the sent counter, the model-version guard and the per-experiment failure counts. `reserve()` checks the guard *before* every attempt, so once a model change is recorded no thread starts a new request — only requests already in flight can still land, and their models are still recorded.
- Preflight (`GET /v1/models`) never retries: retrying a broken endpoint for ~15s before telling the user helps nobody. Any non-200 or connection error exits `run` with 1, naming the URL and status/exception type but never the key.

## Sprint 3

- The `/v1/systemone` wire format (learned from docs.typesafe.ai, not in PREMISE.md) is `{"state": ..., "model": ..., "questions": {qid: {"type": ..., "instructions": ..., "criteria": ...}}}`. Response answers are keyed by the same `qid`; Choice returns `choice`/`probabilities`/`confidence`, Noul returns a single `noul` (p(yes), no separate confidence), Score returns `score`/`probabilities`/`confidence`/`legend`, with probability keys and `score` itself 0-based on the wire.
- Question ids (`intent`, `answer`, `stars`) live in `questions.py` next to the builders that use them, so a runner never hardcodes a magic string to index into a response.
- Fixtures (`tests/fixtures/*_request.json`, `*_response.json`) are captured live via `./capture_fixtures.sh` against the real API — not hand-written — so parser tests are checked against a shape Jev actually returns. `capture_fixtures.sh` is safe to rerun; it only ever appends fresh captures.
- Score's exact-level accuracy uses the argmax over `probabilities` (the model's most likely level), not `round(score)`; MAE uses `score + 1` on the 1..5 stars scale. Both derive from probabilities/score, never from `confidence`.
- `--limit N` for E1 is stratified by round-robin across every `(k, draw)` group in sorted order, taking one row per group per round — so even `--limit 10` (fewer than the 10 groups) still touches every condition once it can, and the same `--limit` always picks the same rows.
- `run_experiment()` in `runner.py` is dataset-agnostic: it takes rows plus a `request_fn`/`parse_fn` pair and knows nothing about Banking77 specifically. E2/E3 (next sprint) reuse it unchanged; only `e1.py`'s dataset-specific twin needs writing.
- If `RunContext` raises `ModelChangedError` or `RequestCapError` mid-run, `run` reports the error and exits 1 without writing `predictions.jsonl` for that invocation — no partial-run manifest yet. Abort-path manifests (a `manifest.json` with an `aborted` reason) are deferred to the plots/report sprint, where the acceptance criteria actually require them.
