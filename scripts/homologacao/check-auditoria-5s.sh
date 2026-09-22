#!/usr/bin/env bash
# Smoke — plugin auditoria-5s (assets + API critérios).
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"

echo "[check] api-delpi upstream (não pode ser TV/outro serviço)"
curl -fsS "${BASE_URL}/apps/api-delpi/health" | python3 -c "
import json, sys
body = json.load(sys.stdin)
assert body.get('status') == 'online', body
assert 'service' not in body, (
    'upstream errado em /apps/api-delpi/health: %r — rode: docker restart delpi-gateway' % (body,)
)
print('OK api-delpi health', body)
"

echo "[check] remoteEntry.js"
curl -fsSI "${BASE_URL}/apps/auditoria-5s/assets/remoteEntry.js" | head -1

echo "[check] socket.io handshake (api-delpi)"
curl -fsS "${BASE_URL}/apps/api-delpi/socket.io/?EIO=4&transport=polling" | python3 -c "import sys; b=sys.stdin.read(); assert b.startswith('0'), b[:80]; print('OK socket.io handshake')"

echo "[check] audit-5s areas route exists (401 sem JWT = rota ok; 404 = gateway/upstream)"
code="$(curl -s -o /dev/null -w '%{http_code}' "${BASE_URL}/apps/api-delpi/quality/audit-5s/areas?branch=01")"
python3 -c "
code = int('${code}')
assert code in (401, 403), (
    'esperava 401/403 em audit-5s/areas, veio %s — se 404: docker restart delpi-gateway' % code
)
print('OK audit-5s/areas status', code)
"

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
