#!/usr/bin/env bash
# Smoke — API PAC em produção (health + OpenAPI Onda 1).
set -euo pipefail

PAC_API_URL="${PAC_API_URL:-https://pac-api.minhadelpi.com.br}"

echo "[check] GET ${PAC_API_URL}/health"
curl -fsS "${PAC_API_URL}/health" | python3 -c "
import json, sys
body = json.load(sys.stdin)
assert body.get('status') in ('ok', 'healthy') or body.get('plugins_database') == 'ok', body
print('OK health', body.get('service'), body.get('plugins_database'))
"

echo "[check] OpenAPI — rotas Onda 1 (agente GPT)"
curl -fsS "${PAC_API_URL}/openapi.json" | python3 -c "
import json, sys
paths = json.load(sys.stdin).get('paths') or {}
required = [
    '/quality/action-plans/{plan_id}',
    '/quality/action-plans/{plan_id}/rnc-8d',
    '/quality/action-plans/{plan_id}/export/rnc-8d',
    '/quality/action-plans/{plan_id}/evidences',
]
missing = [p for p in required if p not in paths]
if missing:
    print('FALTANDO no OpenAPI publicado:', ', '.join(missing), file=sys.stderr)
    print('paths atuais:', len(paths), file=sys.stderr)
    sys.exit(1)
print('OK openapi Onda 1', len(paths), 'paths')
"

echo "[OK] check-pac-api-server"
