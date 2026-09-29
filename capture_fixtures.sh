#!/usr/bin/env bash
# Captures one real Choice, Noul, Score and /v1/models request+response from the live
# Jev API into tests/fixtures/, used as offline test fixtures. Requires TYPESAFE_API_KEY.
# Run once; do not edit the captured files afterwards.
set -euo pipefail
cd "$(dirname "$0")"
uv run python -m jev_eval.capture_fixtures
