"""Capture one real Choice, Noul, Score and /v1/models request+response into tests/fixtures/.

Run via `./capture_fixtures.sh`. Requires TYPESAFE_API_KEY. Fixtures are the source of truth
for response shapes in offline tests — do not hand-edit them afterwards.
"""
from __future__ import annotations

import json
from pathlib import Path

from .client.http import JevClient
from .config import load_config
from .frozen import verify
from .protocol import questions

FIXTURES_DIR = Path("tests/fixtures")
FROZEN_DIR = Path("data/frozen")


def _row0(name: str) -> dict:
    path = FROZEN_DIR / f"{name}.jsonl"
    return json.loads(path.read_text().splitlines()[0])


def _capture(client: JevClient, name: str, body: dict) -> None:
    result = client.request(body)
    if not result.ok:
        raise RuntimeError(f"capture failed for {name}: {result.error}")
    (FIXTURES_DIR / f"{name}_request.json").write_text(json.dumps(body, indent=2) + "\n")
    (FIXTURES_DIR / f"{name}_response.json").write_text(json.dumps(result.data, indent=2) + "\n")
    print(f"captured {name}: model={result.model} latency_ms={result.latency_ms:.0f}")


def main() -> None:
    verify(FROZEN_DIR)
    config = load_config()
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    client = JevClient(base_url=config.base_url, api_key=config.api_key, cache=None)
    try:
        client.preflight()

        models = client.list_models()
        (FIXTURES_DIR / "models_response.json").write_text(json.dumps(models, indent=2) + "\n")
        print("captured models list")

        _capture(client, "choice", questions.banking77_request(_row0("banking77_sweep")))
        _capture(client, "noul", questions.boolq_request(_row0("boolq")))
        _capture(client, "score", questions.yelp_request(_row0("yelp")))
    finally:
        client.close()


if __name__ == "__main__":
    main()
