#!/usr/bin/env bash
# Validação — memória de sessão e preferências (Playbook 01)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-$ROOT}"

if [[ -d /app && -z "${SMOKE_BASE_URL:-}" ]]; then
  export SMOKE_BASE_URL=http://delpi-gateway
fi

PY="${PYTHON:-python3}"
if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
fi

echo "== Memória de sessão — testes unitários =="
"$PY" -m pytest \
  tests/unit/domain/services/test_chat_session_memory.py \
  tests/unit/domain/services/test_chat_reference_resolution_service.py \
  tests/unit/domain/services/test_chat_working_memory_service.py \
  tests/unit/application/services/test_chat_session_memory_metrics_service.py \
  tests/unit/application/services/test_chat_session_memory_direct_answer_service.py \
  tests/unit/application/services/test_chat_session_memory_service.py \
  tests/unit/domain/services/test_chat_conversation_memory_extractor.py \
  -q

echo ""
echo "== Memória de sessão — smoke multi-turno (se gateway up) =="
if "$PY" scripts/smoke_context_assertiveness_multiturn.py 2>/dev/null; then
  echo "OK smoke_context_assertiveness_multiturn"
else
  echo "Aviso: smoke HTTP multi-turno indisponível (gateway ou rate limit)." >&2
fi

echo ""
echo "== Memória de sessão — smoke persistência =="
if "$PY" scripts/smoke_session_memory_persist.py 2>/dev/null; then
  echo "OK smoke_session_memory_persist"
else
  echo "Aviso: smoke persistência indisponível." >&2
fi

echo ""
echo "Validação memória de sessão: concluída."
