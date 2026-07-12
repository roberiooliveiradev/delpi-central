#!/usr/bin/env bash
# Typecheck tv-dashboard ignorando erros só em plugins/vite/* (deps do host MF).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLUGIN_DIR="${PLUGIN_DIR:-$ROOT/plugins/tv-dashboard}"

cd "$PLUGIN_DIR"
OUT="$(npx tsc --noEmit -p tsconfig.build.json --pretty false 2>&1 || true)"
FILTERED="$(echo "$OUT" | grep "error TS" | grep -vE '(^|/|\.\./)vite/' || true)"

if [ -n "$FILTERED" ]; then
  echo "$FILTERED"
  echo "[ERRO] Typecheck tv-dashboard falhou ($(echo "$FILTERED" | wc -l) erros)."
  exit 1
fi

echo "[OK] Typecheck tv-dashboard (src + presentation/plugin-ui via paths)."
