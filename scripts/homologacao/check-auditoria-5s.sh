#!/usr/bin/env bash
# Smoke — plugin auditoria-5s (assets + API critérios).
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"

echo "[check] remoteEntry.js"
curl -fsSI "${BASE_URL}/apps/auditoria-5s/assets/remoteEntry.js" | head -1

if [ -n "$TOKEN" ]; then
  echo "[check] criteria API"
  curl -fsS \
    "${BASE_URL}/apps/api-delpi/quality/audit-5s/criteria" \
    -H "Authorization: Bearer ${TOKEN}" \
    | python3 -c "import json,sys; b=json.load(sys.stdin); assert b.get('success'), b; print('OK criteria', len(b.get('data',[])))"
else
  echo "[skip] API criteria (defina TOKEN para validar JWT)"
fi

echo "[OK] check-auditoria-5s"
