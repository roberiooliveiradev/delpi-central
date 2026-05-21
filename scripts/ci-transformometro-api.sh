#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/transformometro-api"
PY="${PY:-python3}"
if [ ! -d .venv ]; then
  "$PY" -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt
PYTHONPATH="$ROOT/transformometro-api:$ROOT/shared" .venv/bin/pytest tests/ -q
