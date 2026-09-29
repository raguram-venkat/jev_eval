# Decisions

One line per non-obvious choice, with the reason.

## Sprint 1

- Package and console script are both `twinbench`; `module-name = "twinbench"` is set explicitly in `[tool.uv.build-backend]` so the build backend can't drift from the source directory. The old `src/system_one` stub is deleted, not kept for compatibility.
- `datasets` moved to a dev dependency group: only `prep_data.py` needs it, the benchmark itself doesn't. The unused `pytorch-cpu` index is removed (no torch anywhere in this project).
- `Config.api_key` is `field(repr=False)` and `__repr__`/`__str__` are overridden to print only `base_url`; the `Authorization` header is built on demand by `auth_headers()` and never stored on the object, so no dump of a config can leak the key.
- The key is `.strip()`ped; a whitespace-only key counts as unset (catches a trailing newline from `export KEY=$(cat file)`).
- Argparse usage errors (`--limit`, `--experiments`) exit 2 before the key is even read; a missing key also exits 2 via `parser.exit`. A frozen-data failure exits 1, naming the offending file.
- Frozen data is verified with `hashlib.file_digest` over files opened `rb` only; nothing under `data/frozen/` is ever opened for writing (tested by spying on `Path.open`).
- `questions.py` is hashed as raw file bytes, so any edit to instructions, criteria or state builders changes `questions_hash()`. Question text must never change in response to results.
- Yelp Score levels are 0-based on the wire (level i is i + 1 stars); the five level texts are fixed before any results exist.
- Banking77 criteria are label-name-only (`{opt: opt}`), a deliberate zero-shot choice, called out as a caveat later in the report.
- `tests/conftest.py` blocks non-loopback network access via `pytest.fail` (a `BaseException`), so a retry loop that catches `Exception` can't hide an accidental live call.
