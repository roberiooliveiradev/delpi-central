#!/usr/bin/env bash
# Smoke — API PAC em produção (health + OpenAPI Onda 1 completo para H2).
set -euo pipefail

PAC_API_URL="${PAC_API_URL:-https://pac-api.minhadelpi.com.br}"

echo "[check] GET ${PAC_API_URL}/health"
curl -fsS "${PAC_API_URL}/health" | python3 -c "
import json, sys
body = json.load(sys.stdin)
assert body.get('status') in ('ok', 'healthy') or body.get('plugins_database') == 'ok', body
print('OK health', body.get('service'), body.get('plugins_database'))
"

echo "[check] OpenAPI — rotas Onda 1 (agente GPT / H2)"
curl -fsS "${PAC_API_URL}/openapi.json" | python3 -c "
import json, sys
paths = json.load(sys.stdin).get('paths') or {}
required = [
    '/quality/action-plans',
    '/quality/action-plans/intelligence/similar-cases',
    '/quality/action-plans/{plan_id}',
    '/quality/action-plans/{plan_id}/ishikawa',
    '/quality/action-plans/{plan_id}/five-whys',
    '/quality/action-plans/{plan_id}/actions',
    '/quality/action-plans/{plan_id}/rnc-8d',
    '/quality/action-plans/{plan_id}/export/rnc-8d',
    '/quality/action-plans/{plan_id}/evidences',
]
missing = [p for p in required if p not in paths]
if missing:
    print('FALTANDO no OpenAPI publicado:', ', '.join(missing), file=sys.stderr)
    print('paths atuais:', len(paths), file=sys.stderr)
    print('Ação: deploy api-pac-quality no srv-api (docker compose up -d --build)', file=sys.stderr)
    sys.exit(1)
print('OK openapi Onda 1', len(required), 'rotas obrigatórias')
"

if [ -n "${PAC_QUALITY_API_KEY:-}" ]; then
  echo "[check] POST similar-cases (auth API key)"
  curl -fsS -X POST "${PAC_API_URL}/quality/action-plans/intelligence/similar-cases" \
    -H "Authorization: Bearer ${PAC_QUALITY_API_KEY}" \
    -H "Content-Type: application/json" \
    -H "User-Agent: Delpi-PAC-Homologation/1.0" \
    -d '{"problem_description":"smoke check pac homologação","product_code":"14297268","branch_code":"01"}' \
    | python3 -c "
import json, sys
body = json.load(sys.stdin)
assert body.get('success') is True, body
print('OK similar-cases auth')
"
else
  echo "[skip] POST similar-cases (defina PAC_QUALITY_API_KEY para validar auth)"
fi

echo "[OK] check-pac-api-server"
