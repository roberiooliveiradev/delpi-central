#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/api-pac-quality"
PY="${PY:-python3}"
if [ ! -d .venv ]; then
  "$PY" -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt
PYTHONPATH="$ROOT/api-pac-quality" .venv/bin/pytest tests/ -q
