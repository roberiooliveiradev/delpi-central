#!/usr/bin/env bash
# Smoke — plugin eficiencia-fabril (assets + API dashboard).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"

echo "[check] remoteEntry.js"
curl -fsSI "${BASE_URL}/apps/eficiencia-fabril/assets/remoteEntry.js" | head -1

if [ -n "$TOKEN" ]; then
  END=$(date -u +%Y-%m-%d)
  START=$(date -u -d '7 days ago' +%Y-%m-%d 2>/dev/null || date -u -v-7d +%Y-%m-%d)
  echo "[check] dashboard API"
  curl -fsS \
    "${BASE_URL}/apps/api-delpi/production/eficiencia-fabril/dashboard?start_date=${START}&end_date=${END}&branch=02" \
    -H "Authorization: Bearer ${TOKEN}" \
    | python3 -c "import json,sys; b=json.load(sys.stdin); assert b.get('success'), b; print('OK', b.get('data',{}).get('summary',{}).get('appointment_count'))"
else
  echo "[skip] API dashboard (defina TOKEN para validar JWT)"
fi

echo "[OK] check-eficiencia-fabril"
