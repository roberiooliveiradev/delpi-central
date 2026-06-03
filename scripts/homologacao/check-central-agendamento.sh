#!/usr/bin/env bash
# Smoke — plugin central-agendamento (assets + API recursos).
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"

echo "[check] remoteEntry.js"
curl -fsSI "${BASE_URL}/apps/central-agendamento/assets/remoteEntry.js" | head -1

if [ -n "$TOKEN" ]; then
  echo "[check] resources API (Filial ES)"
  curl -fsS \
    "${BASE_URL}/apps/api-delpi/scheduling/resources?branch=ES" \
    -H "Authorization: Bearer ${TOKEN}" \
    | python3 -c "import json,sys; b=json.load(sys.stdin); assert b.get('success'), b; print('OK resources', len(b.get('data',[])))"
else
  echo "[skip] API resources (defina TOKEN para validar JWT)"
fi

echo "[OK] check-central-agendamento"
