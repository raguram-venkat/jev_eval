"""Freeze twin-bench eval sets. Run ONCE before starting the loop.

The loop treats data/frozen/ as read-only and verifies manifest.json hashes at startup.
Usage:  uv run python prep_data.py
"""
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from datasets import load_dataset

SEED = 1729
OUT = Path("data/frozen")
BANKING_URL = (
    "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/"
    "master/banking_data/test.csv"
)
SWEEP_K = (2, 5, 20, 77)
DRAWS_PER_K = 3          # label-subset draws for k < 77
CAP_SUBSET = 150         # max examples per draw for k < 77
CAP_FULL = 300           # examples for k = 77
BOOLQ_PER_CLASS = 150    # balanced yes/no
BOOLQ_MAX_WORDS = 250    # keeps passages inside Laya's 512-token context
YELP_PER_STAR = 60
YELP_MAX_WORDS = 150


def readable(label: str) -> str:
    return label.replace("_", " ").lower()


def write(name: str, rows: list[dict]) -> dict:
    path = OUT / f"{name}.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {
        "file": path.name,
        "rows": len(rows),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def banking_sweep() -> list[dict]:
    df = pd.read_csv(BANKING_URL)
    labels = sorted(df["category"].unique())
    assert len(labels) == 77, f"expected 77 labels, got {len(labels)}"
    rng = random.Random(SEED)
    rows = []
    for k in SWEEP_K:
        full = k == len(labels)
        for d in range(1 if full else DRAWS_PER_K):
            subset = labels if full else sorted(rng.sample(labels, k))
            pool = df[df["category"].isin(subset)]
            n = min(CAP_FULL if full else CAP_SUBSET, len(pool))
            pool = pool.sample(n=n, random_state=SEED + d)
            for i, r in enumerate(pool.itertuples(index=False)):
                rows.append({
                    "id": f"b77-k{k}-d{d}-{i}",
                    "k": k,
                    "draw": d,
                    "text": r.text,
                    "label": readable(r.category),
                    "options": [readable(x) for x in subset],
                })
    return rows


def boolq() -> list[dict]:
    df = load_dataset("google/boolq", split="validation").to_pandas()
    df = df[df["passage"].str.split().str.len() <= BOOLQ_MAX_WORDS]
    parts = [
        df[df["answer"] == v].sample(n=BOOLQ_PER_CLASS, random_state=SEED)
        for v in (True, False)
    ]
    df = pd.concat(parts).sample(frac=1, random_state=SEED)
    return [
        {"id": f"boolq-{i}", "question": r.question, "passage": r.passage, "label": bool(r.answer)}
        for i, r in enumerate(df.itertuples(index=False))
    ]


def yelp() -> list[dict]:
    df = load_dataset("Yelp/yelp_review_full", split="test").to_pandas()
    df = df[df["text"].str.split().str.len() <= YELP_MAX_WORDS]
    parts = [
        df[df["label"] == s].sample(n=YELP_PER_STAR, random_state=SEED)
        for s in range(5)
    ]
    df = pd.concat(parts).sample(frac=1, random_state=SEED)
    return [
        {"id": f"yelp-{i}", "text": r.text, "stars": int(r.label) + 1}
        for i, r in enumerate(df.itertuples(index=False))
    ]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "sources": {
            "banking77": BANKING_URL,
            "boolq": "hf:google/boolq@validation",
            "yelp": "hf:Yelp/yelp_review_full@test",
        },
        "filters": {"boolq_max_words": BOOLQ_MAX_WORDS, "yelp_max_words": YELP_MAX_WORDS},
        "files": {
            "banking77_sweep": write("banking77_sweep", banking_sweep()),
            "boolq": write("boolq", boolq()),
            "yelp": write("yelp", yelp()),
        },
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    for name, info in manifest["files"].items():
        print(f"{name:16} {info['rows']:5} rows  {info['sha256'][:12]}")


if __name__ == "__main__":
    main()