# jev-eval

Reproducible CLI benchmark for Jev (TypeSafe AI System One): measures Choice, Noul and Score
performance on Banking77, BoolQ and Yelp. See `PREMISE.md` for the full spec.

## Install

```
uv sync
```

## Configure

- `TYPESAFE_API_KEY` — required, read from the environment, never logged.
- `JEV_BASE_URL` — optional, defaults to `https://api.typesafe.ai`.

## Usage

```
uv run jev-eval run --limit 20
uv run pytest -q
```

More milestones (experiments, metrics, plots, report) land in later sprints — see `sprints/`.
