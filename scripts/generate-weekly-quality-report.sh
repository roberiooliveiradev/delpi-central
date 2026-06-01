#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/minha-delpi-ai-api"

python3 scripts/generate_weekly_quality_report.py "$@"
