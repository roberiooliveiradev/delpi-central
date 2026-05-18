#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"
START_DATE="${START_DATE:-2025-01-01}"
END_DATE="${END_DATE:-2026-12-31}"

API_PREFIX="$BASE_URL/apps/api-delpi/commercial"
MFE_PREFIX="$BASE_URL/apps/dashboard-commercial"

echo "[1/4] remoteEntry.js"
curl -fsSI "$MFE_PREFIX/assets/remoteEntry.js" | head -n 5

if [ -z "$TOKEN" ]; then
  echo "[AVISO] TOKEN não definido — pulando API."
  exit 0
fi

AUTH=(-H "Authorization: Bearer $TOKEN")
QUERY="?start_date=$START_DATE&end_date=$END_DATE"

echo "[2/4] Meta ROL matriz"
curl -fsS "${AUTH[@]}" "$API_PREFIX/head_office_rol_target_pct$QUERY" | python3 -m json.tool

echo "[3/4] Taxa de conversão"
curl -fsS "${AUTH[@]}" "$API_PREFIX/closing-rate$QUERY" | python3 -m json.tool

echo "[4/4] Clientes novos"
curl -fsS "${AUTH[@]}" "$API_PREFIX/new-clients-average$QUERY" | python3 -m json.tool

echo "[OK] Homologação dashboard-commercial concluída."
