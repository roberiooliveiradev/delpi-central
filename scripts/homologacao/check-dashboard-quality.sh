#!/usr/bin/env bash
# Smoke test HTTP do Dashboard Qualidade (api-delpi + assets do MFE).
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"
DATE_START="${DATE_START:-}"
DATE_END="${DATE_END:-}"

API_PREFIX="$BASE_URL/apps/api-delpi/quality"
MFE_PREFIX="$BASE_URL/apps/dashboard-quality"

echo "[1/6] remoteEntry.js (MFE)"
curl -fsSI "$MFE_PREFIX/assets/remoteEntry.js" | head -n 5

if [ -z "$TOKEN" ]; then
  echo "[AVISO] TOKEN não definido — pulando chamadas autenticadas da API."
  echo "Para testar a API: TOKEN=<jwt> ./scripts/homologacao/check-dashboard-quality.sh"
  echo "[OK] Homologação parcial (assets) concluída."
  exit 0
fi

AUTH=(-H "Authorization: Bearer $TOKEN")
QUERY=""

if [ -n "$DATE_START" ]; then
  QUERY="?date_start=$DATE_START"
  if [ -n "$DATE_END" ]; then
    QUERY="${QUERY}&date_end=$DATE_END"
  fi
fi

echo "[2/6] Filiais do período"
curl -fsS "${AUTH[@]}" "$API_PREFIX/branches$QUERY" | python3 -m json.tool

echo "[3/6] PPM interno — resumo"
curl -fsS "${AUTH[@]}" "$API_PREFIX/ppm/internal/summary$QUERY" | python3 -m json.tool

SERIES_Q="granularity=month"
if [ -n "$DATE_START" ]; then
  SERIES_Q="${SERIES_Q}&date_start=${DATE_START}"
fi
if [ -n "$DATE_END" ]; then
  SERIES_Q="${SERIES_Q}&date_end=${DATE_END}"
fi

echo "[4/6] PPM interno — série (mês)"
curl -fsS "${AUTH[@]}" "$API_PREFIX/ppm/internal/series?$SERIES_Q" | python3 -m json.tool

echo "[5/6] NC — série (mês)"
curl -fsS "${AUTH[@]}" "$API_PREFIX/nonconformities/series?type=all&$SERIES_Q" | python3 -m json.tool

echo "[6/6] Kaizen e 5S — resumo"
curl -fsS "${AUTH[@]}" "$API_PREFIX/kaizens/summary$QUERY" | python3 -m json.tool
curl -fsS "${AUTH[@]}" "$API_PREFIX/audit-5s/summary$QUERY" | python3 -m json.tool

echo "[OK] Homologação HTTP do Dashboard Qualidade concluída."
