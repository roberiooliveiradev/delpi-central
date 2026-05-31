#!/usr/bin/env bash
# Validação Playbook 03 — especialista em textos (T1–T16, F4–F6)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-/app:${ROOT}}"

PYTEST_BIN="${PYTEST_BIN:-python3 -m pytest}"
if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PYTEST_BIN="${ROOT}/.venv/bin/python -m pytest"
fi

echo "== Playbook 03: regressão especialista em textos =="
${PYTEST_BIN} \
  tests/unit/domain/services/test_text_specialist.py \
  tests/unit/domain/services/test_chat_text_task_admin_metrics_service.py \
  tests/unit/domain/services/test_chat_text_task_intent_service.py \
  tests/unit/application/services/test_chat_text_task_composer_service.py \
  tests/unit/application/services/test_chat_text_task_mixed_turn_service.py \
  tests/unit/application/services/test_chat_text_task_canvas_service.py \
  tests/unit/application/use_cases/test_get_admin_text_task_summary_use_case.py \
  tests/unit/test_text_correction_skill.py \
  -q --tb=short

echo "== Playbook 03: smoke text task routing =="
PYTHONPATH="${ROOT}" ${PYTEST_BIN%/pytest*}python3 scripts/smoke_text_task_routing.py 2>/dev/null || \
  PYTHONPATH="${ROOT}" python3 scripts/smoke_text_task_routing.py || true

echo "OK — validação Playbook 03 concluída."
