#!/usr/bin/env bash
# Smoke HTTP do plugin api-delpi-console (MFE + rotas críticas da API).
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"

MFE_PREFIX="$BASE_URL/apps/api-delpi-console"
API_PREFIX="$BASE_URL/apps/api-delpi"

echo "[1/8] remoteEntry.js (MFE)"
curl -fsSI "$MFE_PREFIX/assets/remoteEntry.js" | head -n 5

echo "[2/8] Saúde pública"
curl -fsS "$API_PREFIX/health" | python3 -m json.tool

if [ -z "$TOKEN" ]; then
  echo "[AVISO] TOKEN não definido — pulando rotas autenticadas."
  echo "Para suite completa: TOKEN=<jwt> ./scripts/homologacao/check-api-delpi-console.sh"
  echo "[OK] Homologação parcial (assets + health) concluída."
  exit 0
fi

AUTH=(-H "Authorization: Bearer $TOKEN")

echo "[3/8] LMP — resumo"
curl -fsS "${AUTH[@]}" "$API_PREFIX/engineering/lmps/dashboard/summary?status=Todos" | python3 -m json.tool

echo "[4/8] Estoque — valor"
curl -fsS "${AUTH[@]}" "$API_PREFIX/supplies/stock-value?top_limit=5" | python3 -m json.tool

echo "[5/8] Qualidade — filiais"
curl -fsS "${AUTH[@]}" "$API_PREFIX/quality/branches" | python3 -m json.tool

echo "[6/8] PPM interno — resumo"
curl -fsS "${AUTH[@]}" "$API_PREFIX/quality/ppm/internal/summary" | python3 -m json.tool

echo "[7/8] Transforma Mais — resumo"
curl -fsS "${AUTH[@]}" "$API_PREFIX/engineering/transforma-mais/processes/summary" | python3 -m json.tool

echo "[8/8] Agendamento — recursos ES"
curl -fsS "${AUTH[@]}" "$API_PREFIX/scheduling/resources?branch=ES" | python3 -m json.tool

echo "[OK] Homologação api-delpi-console concluída."
