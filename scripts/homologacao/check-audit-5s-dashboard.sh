#!/usr/bin/env bash
# Homologação — Dashboard gerencial Auditoria 5S (API analytics).
# Uso:
#   export TOKEN="<jwt sem Bearer>"
#   bash ./scripts/homologacao/check-audit-5s-dashboard.sh
#
# Variáveis opcionais:
#   BASE_URL=http://localhost
#   BRANCH=01|02
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
API="${BASE_URL}/apps/api-delpi/quality/audit-5s/analytics/dashboard"
BRANCH="${BRANCH:-01}"
TOKEN="${TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "[ERRO] Defina TOKEN (JWT do Portal)." >&2
  exit 1
fi

DATE_END="$(date +%Y-%m-%d)"
DATE_START="$(date +%Y-%m-01)"

echo "==> GET dashboard analytics (${BRANCH}, ${DATE_START}..${DATE_END})"

BODY="$(curl -sS -w "\n%{http_code}" \
  -H "Authorization: Bearer ${TOKEN}" \
  "${API}?branch=${BRANCH}&start_date=${DATE_START}&end_date=${DATE_END}&granularity=month&page=1&page_size=20")"

HTTP_CODE="$(echo "$BODY" | tail -n1)"
JSON="$(echo "$BODY" | sed '$d')"

if [ "$HTTP_CODE" != "200" ]; then
  echo "[ERRO] HTTP ${HTTP_CODE}" >&2
  echo "$JSON" >&2
  exit 1
fi

python3 -c "
import json, sys
payload = json.loads(sys.argv[1])
assert payload.get('success') is True, payload
data = payload.get('data') or {}
assert 'summary' in data, data
assert 'charts' in data, data
assert 'items' in data, data
assert 'pagination' in data, data
charts = data['charts']
for key in ('score_by_period', 'score_by_area', 'score_by_senso', 'nc_by_status'):
    assert key in charts, charts
print('[OK] Dashboard analytics — contrato válido')
print('     audit_count:', data['summary'].get('audit_count'))
print('     items:', len(data.get('items') or []))
" "$JSON"

echo "[OK] check-audit-5s-dashboard.sh"
