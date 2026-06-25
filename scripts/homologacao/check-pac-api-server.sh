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

echo "[check] OpenAPI — fluxo analista (24 operações, máx. 30)"
curl -fsS "${PAC_API_URL}/openapi.json" | python3 -c "
import json, sys
schema = json.load(sys.stdin)
paths = schema.get('paths') or {}
ops = []
for path_item in paths.values():
    if not isinstance(path_item, dict):
        continue
    for operation in path_item.values():
        if isinstance(operation, dict):
            op_id = str(operation.get('operationId') or '').strip()
            if op_id:
                ops.append(op_id)
max_ops = 30
expected = 24
if len(ops) > max_ops:
    print(f'ERRO: OpenAPI tem {len(ops)} operações (máx {max_ops})', file=sys.stderr)
    sys.exit(1)
if len(ops) != expected:
    print(f'ERRO: esperado {expected} operações analista; obteve {len(ops)}', file=sys.stderr)
    sys.exit(1)
if '/health' in paths:
    print('ERRO: /health não deve aparecer no OpenAPI GPT', file=sys.stderr)
    sys.exit(1)
required = {
    'pac_create_action_plan',
    'pac_search_similar_cases',
    'pac_submit_effectiveness_review',
    'pac_download_plan_evidence',
}
missing = sorted(required - set(ops))
if missing:
    print('FALTANDO no openapi.json:', ', '.join(missing), file=sys.stderr)
    sys.exit(1)
forbidden = {
    'pac_approve_effectiveness_review',
    'pac_dispatch_notifications',
    'pac_get_quality_knowledge_graph',
}
present = sorted(forbidden & set(ops))
if present:
    print('ERRO: operações plugin-only no OpenAPI PAC:', ', '.join(present), file=sys.stderr)
    sys.exit(1)
print('OK openapi.json analista', len(ops), 'operações')
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
