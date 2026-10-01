# Sprint 1

Built the `jev-eval` package skeleton: a CLI (`jev-eval run` with `--limit`, `--no-cache`,
`--experiments`, all validated before any network or key access), a `Config` that reads
`TYPESAFE_API_KEY`/`JEV_BASE_URL` and never leaks the key through `repr`/`str`, frozen-data
sha256 verification against `manifest.json`, and the `protocol/questions.py` module (instructions,
criteria and state builders for Banking77, BoolQ and Yelp, plus a stable `questions_hash()`).

Tested config redaction and validation, frozen-data verification (bad hash, missing file,
missing/invalid manifest, and a spy proving nothing is opened for writing), the question
builders against golden rows from the real frozen data, and CLI exit codes for bad flags
and a missing key — all offline, with a `conftest.py` that blocks non-loopback network calls.
No HTTP client yet — that's next.
