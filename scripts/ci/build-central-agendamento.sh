#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLUGIN="$ROOT/plugins/central-agendamento"

cd "$PLUGIN"
npm ci
npm run ci

echo "[OK] build-central-agendamento"
