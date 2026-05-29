#!/usr/bin/env bash
# Validação Onda 11 — regressão + smoke operacional (11.5.1)
#
# Uso local:
#   cd minha-delpi-ai-api && ./scripts/run_onda11_validation.sh
#
# Uso no container dev:
#   docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
#     bash scripts/run_onda11_validation.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-/app:${ROOT}}"

echo "== Onda 11 — regressão inteligência =="
pytest \
  tests/unit/infrastructure/config/test_llm_latency_profile.py \
  tests/unit/domain/services/test_chat_intelligence_regression.py \
  tests/unit/domain/services/test_chat_operational_refinement_service.py \
  tests/unit/domain/services/test_chat_pagination_consolidation_service.py \
  tests/unit/application/services/test_external_action_selection_service.py \
  tests/unit/application/services/test_chat_turn_preparation_direct_answer_skip_rag.py \
  tests/unit/application/services/test_chat_tool_context_service_direct_response.py \
  tests/unit/application/use_cases/test_chat_stock_refinement_stream_send.py \
  tests/unit/domain/services/test_chat_agentic_catalog_service.py \
  tests/unit/application/services/test_chat_agentic_tool_loop_service.py \
  -q

echo ""
echo "== Onda 11 — smoke operacional (preparação de turno) =="
python scripts/smoke_operational_questions.py

echo ""
echo "Onda 11 validation: OK"
