"""Write predictions.jsonl, manifest.json and the results/latest symlink for a run."""
from __future__ import annotations

import json
import subprocess
import time
from dataclasses import asdict
from pathlib import Path

from . import questions
from .e5 import LatencySample
from .runner import Prediction

RESULTS_DIR = Path("results")
SEED = 1729


def git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, timeout=5
        )
        return out.stdout.strip()
    except Exception:
        return "unknown"


def new_run_dir(now: float | None = None) -> Path:
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(now))
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_predictions(run_dir: Path, predictions: list[Prediction]) -> None:
    with (run_dir / "predictions.jsonl").open("w") as f:
        for p in predictions:
            f.write(json.dumps(asdict(p)) + "\n")


def write_manifest(
    run_dir: Path,
    model: str | None,
    frozen_manifest_path: Path,
    start_time: float,
    end_time: float,
    aborted: str | None = None,
) -> None:
    frozen_manifest = json.loads(frozen_manifest_path.read_text())
    manifest = {
        "git_commit": git_commit(),
        "model": model,
        "dataset_hashes": {name: info["sha256"] for name, info in frozen_manifest["files"].items()},
        "seed": SEED,
        "questions_hash": questions.questions_hash(),
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_time)),
        "end_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(end_time)),
    }
    if aborted is not None:
        manifest["aborted"] = aborted
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))


def write_latency_samples(run_dir: Path, samples: list[LatencySample]) -> None:
    with (run_dir / "latency_samples.jsonl").open("w") as f:
        for s in samples:
            f.write(json.dumps(asdict(s)) + "\n")


def point_latest(run_dir: Path) -> None:
    latest = RESULTS_DIR / "latest"
    if latest.exists() or latest.is_symlink():
        latest.unlink()
    latest.symlink_to(run_dir.name)
