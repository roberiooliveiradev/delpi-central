#!/usr/bin/env bash
# Build tv-dashboard + gate de bibliotecas compartilhadas no Docker.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "[CI] Gate bibliotecas compartilhadas (Docker)"
python3 "$ROOT/scripts/ci/check_plugin_docker_shared_libraries.py" --check

echo "[CI] Gate duplicação @delpi/plugin-ui"
python3 "$ROOT/scripts/ci/audit_plugin_ui_duplication.py" --check

resolve_regression_base() {
  if [ -n "${PLATFORM_GUARDRAILS_BASE_SHA:-}" ]; then
    printf '%s\n' "$PLATFORM_GUARDRAILS_BASE_SHA"
    return
  fi
  if git -C "$ROOT" rev-parse --verify --quiet origin/main >/dev/null; then
    git -C "$ROOT" merge-base HEAD origin/main
    return
  fi
  git -C "$ROOT" rev-parse HEAD^
}

echo "[CI] Gate CSS — regressão incremental (MFE_PLUGIN_UI_OVERRIDE)"
REGRESSION_BASE="$(resolve_regression_base)"
echo "[CI] base da regressão: $REGRESSION_BASE"
python3 "$ROOT/scripts/ci/audit_platform_guardrails.py" --check --base "$REGRESSION_BASE"

echo "[CI] Inventário da dívida CSS histórica (não bloqueia este build)"
python3 "$ROOT/scripts/ci/audit_mfe_plugin_ui_css.py" --base "$REGRESSION_BASE"

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

echo "[CI] Gate CSS anti-vazamento (tv-dashboard)"
python3 "$ROOT/scripts/ci/check_tv_dashboard_css_scope.py" --check

echo "[CI] Gate imports circulares (tv-dashboard)"
(cd "$PLUGIN_DIR" && npm run check:circular)

echo "[CI] Testes unitários (tv-dashboard + presentation)"
(cd "$PRESENTATION_DIR" && npm test)
(cd "$PLUGIN_DIR" && npm test)

echo "[CI] tv-dashboard em $PLUGIN_DIR"
cd "$PLUGIN_DIR"
npm ci 2>/dev/null || npm install
npm run build

echo "[OK] Build tv-dashboard concluído."
