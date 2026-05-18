#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLUGIN_DIR="${PLUGIN_DIR:-$ROOT/plugins/dashboard-commercial}"

cd "$PLUGIN_DIR"
if [ -f package-lock.json ]; then npm ci; else npm install; fi
npm run ci
echo "[OK] Build dashboard-commercial concluído."
