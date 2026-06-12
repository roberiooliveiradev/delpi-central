#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/maintenance-api"
PY="${PY:-python3}"
if [ ! -d .venv ]; then
  "$PY" -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt
.venv/bin/pip install -q -e "$ROOT/shared[fastapi]"
PYTHONPATH="$ROOT/maintenance-api:$ROOT/shared" .venv/bin/pytest tests/ -q
