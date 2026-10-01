# Sprint 4

Added E2 (BoolQ yes/no) and E3 (Yelp scoring), reusing sprint 3's dataset-agnostic runner —
each is just a `load_rows`/`build_request`/`parse_result` module now, plus a shared
`experiments/sampling.py` for stratified `--limit` (balanced yes/no for E2, every star rating for E3).
Added E5 (latency): warmups, 100 sequential single-question calls, 30 single- vs 30 five-
question comparisons, and a `/v1/models` network baseline, all on a cache-disabled client
since a latency number from disk isn't a latency number. All three are wired into `jev-eval run`.

Tested the sampling balance, request shapes, and end-to-end parsing for E2/E3 against a fake
server, and E5's per-kind sample counts and question-count scaling under `--limit`. 84 tests
pass offline. Caught and fixed a real bug along the way: an old test unknowingly started
writing 600 garbage entries into the real `cache/` directory once E2/E3 existed — fixed with
an autouse fixture that isolates every CLI test's cache/results I/O, and purged the pollution.

Live: `--limit 15` on E2/E3/E5 all succeeded (0 failures), and the 5-question vs 1-question
latency came back close (326ms vs 307-372ms) — the parallel-questions claim holds up so far.
