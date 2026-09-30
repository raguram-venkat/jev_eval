# Sprint 7

Wrote the real README: install, configuration, storage layout (`data/frozen/`,
`tests/fixtures/`, `cache/`, `results/<run_id>/`), a cheatsheet of every CLI command, an
error-behaviour table covering every exit code and what its message names, the non-goals,
and the key-handling guardrails. Added a test that extracts every `jev-eval` command from
the README's fenced blocks and dry-parses it with the real CLI parser, so the cheatsheet
can't silently drift from the actual flags, plus a check that the error table's rows each
name a real exit code. 119 tests pass offline.

This closes out the last of the original PREMISE.md milestones (M1-M7). Next: one full,
unrestricted live run and a proper demo of the results.
