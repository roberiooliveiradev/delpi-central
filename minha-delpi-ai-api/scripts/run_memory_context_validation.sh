#!/usr/bin/env bash
# Validação — playbook memória e contexto (Fase 1+)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-$ROOT}"

PY="${PYTHON:-python3}"
if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
fi

echo "== Memória e contexto — testes unitários =="
"$PY" -m pytest \
  tests/unit/domain/services/test_memory_context.py \
  tests/unit/domain/services/test_chat_entity_tracker_service.py \
  tests/unit/domain/services/test_chat_session_memory.py \
  tests/unit/domain/services/test_chat_reference_resolution_service.py \
  -q

echo ""
echo "== Memória de sessão (legado playbook 01) =="
bash "$ROOT/scripts/run_session_memory_validation.sh"

echo ""
echo "OK — validação memória e contexto concluída."
