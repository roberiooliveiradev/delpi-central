#!/usr/bin/env bash
# Validação — correção de texto (unit + smoke roteamento)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-$ROOT}"

PY="${PYTHON:-python3}"
if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
fi

echo "== Correção de texto — testes unitários =="
"$PY" -m pytest \
  tests/unit/test_text_correction_skill.py \
  tests/unit/domain/services/test_chat_text_correction_intelligence_regression.py \
  tests/unit/application/services/test_chat_text_correction_metrics_service.py \
  tests/unit/domain/services/test_chat_text_correction_preference_service.py \
  tests/unit/infrastructure/persistence/test_postgres_chat_session_memory_text_correction.py \
  tests/unit/domain/services/test_chat_text_task_intent_service.py \
  tests/unit/domain/services/test_prompt_policy_service.py \
  -q

echo ""
echo "== Correção de texto — smoke roteamento text_task =="
"$PY" scripts/smoke_text_task_routing.py

echo ""
echo "== Correção de texto — smoke intent (correction) =="
"$PY" scripts/smoke_text_correction.py

echo ""
echo "Validação correção de texto: concluída."
