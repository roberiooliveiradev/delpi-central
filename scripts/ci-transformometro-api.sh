#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/transformometro-api"
python -m pip install -q -r requirements.txt
pytest tests/ -q
