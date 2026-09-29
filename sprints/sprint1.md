# Sprint 1

Replaced the abandoned `.loop` harness with a direct build. Renamed the package to
`twinbench`, wrote a CLI skeleton (`twinbench run` with `--limit`, `--no-cache`,
`--experiments`, validated before any network or key access), a `Config` that never
leaks `TYPESAFE_API_KEY` via `repr`/`str`, frozen-data sha256 verification against
`manifest.json`, and the `questions.py` module with instructions, criteria and state
builders for Banking77, BoolQ and Yelp plus a stable `questions_hash()`. 29 offline
tests pass with network blocked in `conftest.py`. No HTTP client yet — that's next.
