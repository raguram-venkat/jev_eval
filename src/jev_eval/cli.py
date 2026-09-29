"""CLI: `jev-eval run [--limit N] [--no-cache] [--experiments e1,e2,...]`."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cache import Cache
from .client import JevClient, PreflightError
from .config import Config, MissingApiKeyError, load_config
from .frozen import FrozenDataError, verify

VALID_EXPERIMENTS = {"e1", "e2", "e3", "e4", "e5"}
FROZEN_DIR = Path("data/frozen")
CACHE_DIR = Path("cache")


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
        return 1
    finally:
        client.close()

    print("preflight ok, frozen data verified, config loaded — experiment runners land in a later sprint")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
