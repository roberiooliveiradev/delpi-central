#!/usr/bin/env bash
# Smoke HTTP do plugin api-delpi-console (MFE + rotas críticas da API).
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"

MFE_PREFIX="$BASE_URL/apps/api-delpi-console"
API_PREFIX="$BASE_URL/apps/api-delpi"

echo "[1/9] remoteEntry.js (MFE)"
curl -fsSI "$MFE_PREFIX/assets/remoteEntry.js" | head -n 5

echo "[2/9] Saúde pública"
curl -fsS "$API_PREFIX/health" | python3 -m json.tool

if [ -z "$TOKEN" ]; then
  echo "[AVISO] TOKEN não definido — pulando rotas autenticadas."
  echo "Para suite completa: TOKEN=<jwt> ./scripts/homologacao/check-api-delpi-console.sh"
  echo "[OK] Homologação parcial (assets + health) concluída."
  exit 0
fi

AUTH=(-H "Authorization: Bearer $TOKEN")

echo "[3/9] LMP — resumo"
curl -fsS "${AUTH[@]}" "$API_PREFIX/engineering/lmps/dashboard/summary?status=Todos" | python3 -m json.tool

echo "[4/9] Estoque — valor"
curl -fsS "${AUTH[@]}" "$API_PREFIX/supplies/stock-value?top_limit=5" | python3 -m json.tool

echo "[5/9] Qualidade — filiais"
curl -fsS "${AUTH[@]}" "$API_PREFIX/quality/branches" | python3 -m json.tool

echo "[6/9] PPM interno — resumo"
curl -fsS "${AUTH[@]}" "$API_PREFIX/quality/ppm/internal/summary" | python3 -m json.tool

echo "[7/9] Transforma Mais — resumo"
curl -fsS "${AUTH[@]}" "$API_PREFIX/engineering/transforma-mais/processes/summary" | python3 -m json.tool

echo "[8/9] Agendamento — recursos ES"
curl -fsS "${AUTH[@]}" "$API_PREFIX/scheduling/resources?branch=ES" | python3 -m json.tool

echo "[9/11] Smoke definitions (console)"
curl -fsS "${AUTH[@]}" "$API_PREFIX/system/smoke-definitions" | python3 -m json.tool

echo "[10/11] Query cache stats"
curl -fsS "${AUTH[@]}" "$API_PREFIX/system/query-cache/stats" | python3 -m json.tool

echo "[11/11] Observability snapshot"
curl -fsS "${AUTH[@]}" "$API_PREFIX/system/observability-snapshot?limit=10" | python3 -m json.tool

echo "[OK] Homologação api-delpi-console concluída."
