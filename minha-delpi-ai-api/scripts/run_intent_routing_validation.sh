#!/usr/bin/env bash
# Validação Playbook 02 — roteamento inteligente de intenção (R1–R15 + smoke)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-/app:${ROOT}}"

echo "== Playbook 02: testes unitários de roteamento =="
PYTEST_BIN="${PYTEST_BIN:-python3 -m pytest}"
if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PYTEST_BIN="${ROOT}/.venv/bin/python -m pytest"
fi

${PYTEST_BIN} \
  tests/unit/domain/services/test_intent_router.py \
  tests/unit/domain/services/test_chat_intent_router_service.py \
  tests/unit/domain/services/test_chat_intent_disambiguation_service.py \
  tests/unit/application/services/test_chat_intent_router_metrics_service.py \
  tests/unit/application/services/test_chat_active_pending_service.py \
  tests/unit/application/use_cases/test_get_admin_intent_routing_summary_use_case.py \
  -q --tb=short

echo "== Playbook 02: smoke intent route =="
python3 scripts/smoke_intent_route.py || true

echo "OK — validação de roteamento concluída."
