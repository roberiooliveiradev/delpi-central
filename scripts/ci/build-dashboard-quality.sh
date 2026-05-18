#!/usr/bin/env bash
# Build de verificação do plugin dashboard-quality (lint + TypeScript + Vite).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLUGIN_DIR="${PLUGIN_DIR:-$ROOT/plugins/dashboard-quality}"

if [ ! -f "$PLUGIN_DIR/package.json" ]; then
  echo "[ERRO] package.json não encontrado em: $PLUGIN_DIR"
  exit 1
fi

echo "[CI] dashboard-quality em $PLUGIN_DIR"
cd "$PLUGIN_DIR"

if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

npm run ci

echo "[OK] Build dashboard-quality concluído."
