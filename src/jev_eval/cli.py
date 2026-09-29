"""CLI: `jev-eval run [--limit N] [--no-cache] [--experiments e1,e2,...]`."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import e1
from .cache import Cache
from .client import JevClient, ModelChangedError, PreflightError, RequestCapError
from .config import Config, MissingApiKeyError, load_config
from .frozen import FrozenDataError, verify
from .results import new_run_dir, point_latest, write_manifest, write_predictions
from .runctx import RunContext
from .runner import Prediction, run_experiment

VALID_EXPERIMENTS = {"e1", "e2", "e3", "e4", "e5"}
FROZEN_DIR = Path("data/frozen")
CACHE_DIR = Path("cache")

# Only experiments with a runner module registered here are implemented; the rest are
# valid CLI names (so scripts can pass the full list) that print a note and are skipped.
EXPERIMENTS = {"e1": e1}


def make_client(config: Config, no_cache: bool) -> JevClient:
    cache = None if no_cache else Cache(CACHE_DIR)
    return JevClient(base_url=config.base_url, api_key=config.api_key, cache=cache)


def _experiments(value: str) -> list[str]:
    names = value.split(",")
    unknown = [n for n in names if n not in VALID_EXPERIMENTS]
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown experiment(s) {unknown}, choose from {sorted(VALID_EXPERIMENTS)}"
        )
    return names


def _positive_int(value: str) -> int:
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"--limit must be an integer, got {value!r}")
    if n <= 0:
        raise argparse.ArgumentTypeError(f"--limit must be positive, got {n}")
    return n


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jev-eval")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run the benchmark")
    run.add_argument("--limit", type=_positive_int, default=None, help="rows per experiment, for smoke runs")
    run.add_argument("--no-cache", action="store_true", help="bypass the disk response cache")
    run.add_argument("--experiments", type=_experiments, default=sorted(VALID_EXPERIMENTS))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    assert args.command == "run"

    try:
        config = load_config()
    except MissingApiKeyError as e:
        parser.exit(2, f"error: {e}\n")

    try:
        verify(FROZEN_DIR)
    except FrozenDataError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    client = make_client(config, args.no_cache)
    try:
        client.preflight()
    except PreflightError as e:
        print(f"error: {e}", file=sys.stderr)
        client.close()
        return 1

    start_time = time.time()
    ctx = RunContext(client)
    predictions: list[Prediction] = []
    exit_code = 0

    try:
        for name in args.experiments:
            module = EXPERIMENTS.get(name)
            if module is None:
                print(f"{name}: lands in a later sprint, skipped")
                continue

            rows = module.stratified_sample(module.load_rows(), args.limit)
            bodies = [module.build_request(r) for r in rows]
            try:
                client.plan(bodies, cap=ctx.remaining_cap)
                exp_predictions = run_experiment(name, rows, module.build_request, module.parse_result, ctx)
            except (RequestCapError, ModelChangedError) as e:
                print(f"error: {e}", file=sys.stderr)
                exit_code = 1
                break

            predictions.extend(exp_predictions)
            failed = sum(1 for p in exp_predictions if p.error)
            print(f"{name}: {len(exp_predictions)} rows, {failed} failed")
    finally:
        client.close()

    if predictions:
        run_dir = new_run_dir()
        write_predictions(run_dir, predictions)
        model = next((p.model for p in predictions if p.model), None)
        write_manifest(run_dir, model, FROZEN_DIR / "manifest.json", start_time, time.time())
        point_latest(run_dir)
        print(f"results: {run_dir}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
