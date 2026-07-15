#!/usr/bin/env sh
# Typecheck do plugin, ignorando erros só em workspaces compartilhados
# puxados via paths/imports relativos (plugins/vite e plugins/plugin-ui).
# Mesmo critério de scripts/ci/typecheck_tv_dashboard.sh para plugins/vite/*.
set -eu

cd "$(dirname "$0")/.."

OUT="$(npx tsc -b --pretty false 2>&1 || true)"
FILTERED="$(printf '%s\n' "$OUT" | grep "error TS" | grep -vE '(^|/|\.\./)(vite|plugin-ui)/' || true)"

if [ -n "$FILTERED" ]; then
  printf '%s\n' "$FILTERED"
  COUNT="$(printf '%s\n' "$FILTERED" | grep -c . || true)"
  echo "[ERRO] Typecheck financeiro-inadimplencia falhou ($COUNT erros em src/)."
  exit 1
fi

echo "[OK] Typecheck financeiro-inadimplencia (código do plugin; host MF vite/plugin-ui excluídos)."
