#!/usr/bin/env bash
# Smoke — plugin PAC Qualidade (assets + API dashboard/lista + contratos 8D).
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"
PLAN_ID="${PLAN_ID:-}"

echo "[check] remoteEntry.js"
curl -fsSI "${BASE_URL}/apps/quality-action-plans/assets/remoteEntry.js" | head -1

echo "[check] OpenAPI — rotas Onda 1"
curl -fsS "${BASE_URL}/apps/api-delpi/openapi.json" | python3 -c "
import json, sys
spec = json.load(sys.stdin)
paths = spec.get('paths') or {}
required = [
    '/quality/action-plans/{plan_id}',
    '/quality/action-plans/{plan_id}/rnc-8d',
    '/quality/action-plans/{plan_id}/export/rnc-8d',
    '/quality/action-plans/{plan_id}/evidences',
    '/quality/action-plans/{plan_id}/actions',
    '/quality/action-plans/{plan_id}/ishikawa',
    '/quality/action-plans/{plan_id}/five-whys',
]
for path in required:
    assert path in paths, f'missing path {path}'
print('OK openapi paths', len(required))
"

if [ -n "$TOKEN" ]; then
  AUTH=(-H "Authorization: Bearer ${TOKEN}" -H "X-Delpi-Caller-App: quality-action-plans")

  echo "[check] dashboard PAC"
  curl -fsS "${BASE_URL}/apps/api-delpi/quality/action-plans/dashboard" "${AUTH[@]}" \
    | python3 -c "
import json, sys
body = json.load(sys.stdin)
assert body.get('success'), body
data = body.get('data') or {}
for key in ('open_plans', 'critical_open', 'overdue_actions'):
    assert key in data, f'missing {key}'
print('OK dashboard', data.get('open_plans'), 'abertos')
"

  echo "[check] listagem PAC"
  curl -fsS "${BASE_URL}/apps/api-delpi/quality/action-plans?page_size=1" "${AUTH[@]}" \
    | python3 -c "
import json, sys
body = json.load(sys.stdin)
assert body.get('success'), body
data = body.get('data') or {}
assert 'items' in data and 'pagination' in data
print('OK list', data['pagination'].get('total', 0), 'planos')
"

  if [ -n "$PLAN_ID" ]; then
    echo "[check] evidências do plano $PLAN_ID"
    curl -fsS "${BASE_URL}/apps/api-delpi/quality/action-plans/${PLAN_ID}/evidences" "${AUTH[@]}" \
      | python3 -c "
import json, sys
body = json.load(sys.stdin)
assert body.get('success'), body
items = body.get('data') or []
assert isinstance(items, list)
print('OK evidences', len(items), 'itens')
"

    echo "[check] export 8D (headers)"
    curl -fsSI "${BASE_URL}/apps/api-delpi/quality/action-plans/${PLAN_ID}/export/rnc-8d" "${AUTH[@]}" \
      | grep -qi 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    echo "OK export content-type"
  fi
else
  echo "[skip] API PAC autenticada (defina TOKEN; opcional PLAN_ID para evidências/export)"
fi

echo "[OK] check-quality-action-plans"
