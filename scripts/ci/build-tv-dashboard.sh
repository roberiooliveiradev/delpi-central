#!/usr/bin/env bash
# Build tv-dashboard + gate de bibliotecas compartilhadas no Docker.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "[CI] Gate bibliotecas compartilhadas (Docker)"
python3 "$ROOT/scripts/ci/check_plugin_docker_shared_libraries.py" --check

echo "[CI] Gate duplicação @delpi/plugin-ui"
python3 "$ROOT/scripts/ci/audit_plugin_ui_duplication.py" --check

PLUGIN_DIR="${PLUGIN_DIR:-$ROOT/plugins/tv-dashboard}"
PRESENTATION_DIR="$ROOT/plugins/tv-dashboard-presentation"
PLUGIN_UI_DIR="$ROOT/plugins/plugin-ui"

for dir in "$PLUGIN_DIR" "$PRESENTATION_DIR" "$PLUGIN_UI_DIR"; do
  if [ ! -f "$dir/package.json" ]; then
    echo "[ERRO] package.json ausente: $dir"
    exit 1
  fi
done

echo "[CI] npm install bibliotecas compartilhadas"
(cd "$PRESENTATION_DIR" && npm ci 2>/dev/null || npm install)
(cd "$PLUGIN_UI_DIR" && npm ci 2>/dev/null || npm install)

echo "[CI] Gate imports circulares (tv-dashboard)"
(cd "$PLUGIN_DIR" && npm run check:circular)

echo "[CI] tv-dashboard em $PLUGIN_DIR"
cd "$PLUGIN_DIR"
npm ci 2>/dev/null || npm install
npm run build

echo "[OK] Build tv-dashboard concluído."
