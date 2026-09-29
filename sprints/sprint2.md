# Sprint 2

Built the piece that actually talks to Jev: `JevClient` (retry on 429/5xx/transport errors with
capped exponential backoff and jitter, immediate `AuthError` on 401/403, a `preflight()` check
against `/v1/models`), a disk `Cache` keyed by request + requested model version with
atomic writes, and a thread-safe `RunContext` that caps total requests and aborts the run if
the model version changes mid-flight. Wired `--no-cache` and the preflight check into the CLI.

Tested all of it against a real loopback HTTP server (`tests/conftest.py`'s `fake_server`)
whose responses are scripted per test: retry-then-succeed and give-up-after-5 paths, the
auth-error short-circuit, cache hit/miss and bypass, a 4-thread race proving the model-change
guard stops new sends, the request-cap check, and preflight failure/success — plus a check that
no cache file or error message ever contains the API key. 52 tests pass offline. Still no live
call to the real Jev API — that starts once an experiment runner exists (next).
