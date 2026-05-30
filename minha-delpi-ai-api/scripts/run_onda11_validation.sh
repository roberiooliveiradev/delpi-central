#!/usr/bin/env bash
# Validação Onda 11 — regressão + smoke operacional + E2E HTTP (11.5.1)
#
# Uso local (host, com stack docker up):
#   cd minha-delpi-ai-api && ./scripts/run_onda11_validation.sh
#
# Uso no container dev:
#   docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
#     bash scripts/run_onda11_validation.sh
#
# Variáveis opcionais:
#   SMOKE_USER=rober  SMOKE_PASSWORD=1234  SMOKE_BASE_URL=http://localhost
#   SMOKE_SKIP_HTTP_E2E=1  — pula E2E HTTP (útil se gateway indisponível no container)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-/app:${ROOT}}"

SMOKE_USER="${SMOKE_USER:-rober}"
SMOKE_PASSWORD="${SMOKE_PASSWORD:-1234}"
SMOKE_BASE_URL="${SMOKE_BASE_URL:-http://localhost}"
SMOKE_CLIENT_ID="${SMOKE_CLIENT_ID:-delpi-central}"
SMOKE_REALM="${SMOKE_REALM:-delpi}"

_resolve_smoke_context() {
  if ! command -v curl >/dev/null 2>&1 || ! command -v python3 >/dev/null 2>&1; then
    echo "Aviso: curl/python3 indisponível — smoke usará sessão existente no banco." >&2
    return 0
  fi

  local token_payload token me_payload agent_id session_payload
  token_payload=$(curl -sf -X POST \
    "${SMOKE_BASE_URL}/auth/realms/${SMOKE_REALM}/protocol/openid-connect/token" \
    -d "client_id=${SMOKE_CLIENT_ID}" \
    -d "username=${SMOKE_USER}" \
    -d "password=${SMOKE_PASSWORD}" \
    -d "grant_type=password" || true)

  if [[ -z "${token_payload}" ]]; then
    echo "Aviso: não foi possível obter token Keycloak (${SMOKE_USER})." >&2
    return 0
  fi

  export SMOKE_TOKEN
  SMOKE_TOKEN=$(python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])" <<<"${token_payload}")

  me_payload=$(curl -sf -H "Authorization: Bearer ${SMOKE_TOKEN}" \
    "${SMOKE_BASE_URL}/core-api/me" || true)
  export SMOKE_USER_ID
  SMOKE_USER_ID=$(python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id',''))" <<<"${me_payload}" 2>/dev/null || echo "")

  agent_id=$(curl -sf -H "Authorization: Bearer ${SMOKE_TOKEN}" \
    "${SMOKE_BASE_URL}/apps/minha-delpi-ai/api/chat/agents?limit=20" \
    | python3 -c "
import json,sys
d=json.load(sys.stdin)
items=d if isinstance(d,list) else d.get('items',[])
for a in items:
    if a.get('enabled') and a.get('visibility')=='system':
        print(a['id']); break
else:
    print(items[0]['id'] if items else '')
" 2>/dev/null || echo "")

  if [[ -n "${agent_id}" && -n "${SMOKE_USER_ID}" ]]; then
    session_payload=$(curl -sf -X POST \
      -H "Authorization: Bearer ${SMOKE_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{\"title\":\"Smoke Onda 11 validation\",\"agentId\":\"${agent_id}\"}" \
      "${SMOKE_BASE_URL}/apps/minha-delpi-ai/api/chat/sessions" || true)
    export SMOKE_SESSION_ID
    SMOKE_SESSION_ID=$(python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))" <<<"${session_payload}" 2>/dev/null || echo "")
  fi

  export SMOKE_USER SMOKE_PASSWORD SMOKE_BASE_URL
}

echo "== Onda 11 — regressão inteligência =="
pytest \
  tests/unit/infrastructure/config/test_llm_latency_profile.py \
  tests/unit/domain/services/test_chat_intelligence_regression.py \
  tests/unit/domain/services/test_chat_operational_refinement_service.py \
  tests/unit/domain/services/test_chat_pagination_consolidation_service.py \
  tests/unit/application/services/test_external_action_selection_service.py \
  tests/unit/application/services/test_external_action_selection_sql_refinement.py \
  tests/unit/domain/services/test_chat_sql_query_refinement_service.py \
  tests/unit/domain/services/test_chat_web_search_intent_service.py \
  tests/unit/domain/services/test_web_search_query_service.py \
  tests/unit/infrastructure/gateways/test_web_search_http_gateway.py \
  tests/unit/infrastructure/gateways/test_web_search_providers.py \
  tests/unit/application/services/test_chat_web_search_blocks_external_actions.py \
  tests/unit/domain/services/test_chat_web_search_direct_answer_service.py \
  tests/unit/domain/services/test_web_search_portuguese_content_service.py \
  tests/unit/application/services/test_chat_web_search_synthesis_service.py \
  tests/unit/domain/services/test_admin_rbac_profile_catalog_service.py \
  tests/unit/application/services/test_chat_turn_preparation_direct_answer_skip_rag.py \
  tests/unit/application/services/test_chat_tool_context_service_direct_response.py \
  tests/unit/application/use_cases/test_chat_stock_refinement_stream_send.py \
  tests/unit/application/services/test_chat_stream_checkpoint_service.py \
  tests/unit/application/use_cases/test_stream_incremental_persistence.py \
  tests/unit/domain/services/test_chat_agentic_catalog_service.py \
  tests/unit/domain/services/test_chat_agentic_action_schema_service.py \
  tests/unit/application/services/test_chat_agentic_tool_loop_service.py \
  -q

echo "== Onda 11 — utility + typos + admin timings =="
pytest \
  tests/unit/application/services/test_chat_utility_direct_answer_service.py \
  tests/unit/domain/services/test_chat_message_normalization_service.py \
  tests/unit/domain/services/test_chat_agent_intelligence_policy_service.py \
  tests/unit/application/services/test_chat_native_tool_calling_service.py \
  tests/unit/application/services/test_chat_admin_debug_service.py \
  -q

echo "== Onda 11 — contexto / memória / assertividade (Fase 5) =="
pytest \
  tests/unit/domain/services/test_chat_context_assertiveness_service.py \
  tests/unit/domain/services/test_chat_context_assertiveness_regression.py \
  tests/unit/domain/services/test_chat_working_memory_service.py \
  tests/unit/domain/services/test_chat_follow_up_intent_service.py \
  tests/unit/domain/services/test_chat_reference_resolution_service.py \
  tests/unit/domain/services/test_chat_text_task_intent_service.py \
  tests/unit/application/services/test_chat_text_task_composer_service.py \
  tests/unit/domain/services/test_external_action_result_presenter_guide.py \
  tests/unit/domain/services/test_prompt_policy_service.py \
  -q

_resolve_smoke_context

echo ""
echo "== Onda 11 — smoke operacional (preparação de turno) =="
if [[ -n "${SMOKE_USER_ID:-}" && -n "${SMOKE_SESSION_ID:-}" ]]; then
  python scripts/smoke_operational_questions.py "${SMOKE_USER_ID}" "${SMOKE_SESSION_ID}"
else
  python scripts/smoke_operational_questions.py
fi

if [[ "${SMOKE_SKIP_HTTP_E2E:-0}" != "1" ]]; then
  echo ""
  echo "== Onda 11 — E2E persistência incremental stream =="
  python scripts/validate_stream_incremental_persistence_e2e.py

  echo ""
  echo "== Onda 11 — E2E HTTP (${SMOKE_USER}@${SMOKE_BASE_URL}) =="
  python scripts/run_onda11_api_e2e.py

  echo ""
  echo "== Onda 11 — smoke assertividade multi-turno (Fase 5) =="
  python scripts/smoke_context_assertiveness_multiturn.py
fi

echo ""
echo "Onda 11 validation: OK"
