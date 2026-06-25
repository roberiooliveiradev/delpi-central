#!/usr/bin/env bash
# Smoke — plugin PAC Qualidade (assets + API dashboard/lista).
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"

echo "[check] remoteEntry.js"
curl -fsSI "${BASE_URL}/apps/quality-action-plans/assets/remoteEntry.js" | head -1

if [ -n "$TOKEN" ]; then
  echo "[check] dashboard PAC"
  curl -fsS \
    "${BASE_URL}/apps/api-delpi/quality/action-plans/dashboard" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "X-Delpi-Caller-App: quality-action-plans" \
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
  curl -fsS \
    "${BASE_URL}/apps/api-delpi/quality/action-plans?page_size=1" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "X-Delpi-Caller-App: quality-action-plans" \
    | python3 -c "
import json, sys
body = json.load(sys.stdin)
assert body.get('success'), body
data = body.get('data') or {}
assert 'items' in data and 'pagination' in data
print('OK list', data['pagination'].get('total', 0), 'planos')
"
else
  echo "[skip] API PAC (defina TOKEN para validar JWT)"
fi

echo "[OK] check-quality-action-plans"
