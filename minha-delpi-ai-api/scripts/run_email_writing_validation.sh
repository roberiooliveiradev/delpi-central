#!/usr/bin/env bash
# Validação — escrita de e-mails (unit + smoke opcional)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-/app:${ROOT}}"
PY="${PYTHON:-python3}"
if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
fi

echo "== E-mail — testes unitários =="
"$PY" -m pytest \
  tests/unit/test_email_writing_skill.py \
  tests/unit/domain/services/test_chat_email_intent_service.py \
  tests/unit/domain/services/test_chat_email_quality_validator.py \
  tests/unit/domain/services/test_chat_email_preference_service.py \
  tests/unit/application/services/test_chat_email_follow_up_service.py \
  tests/unit/application/services/test_chat_email_answer_guard_service.py \
  tests/unit/application/services/test_chat_email_operational_composer_service.py \
  tests/unit/application/services/test_chat_text_task_composer_service.py \
  tests/unit/domain/services/test_chat_text_task_intent_service.py \
  -q

echo ""
echo "== E-mail — smoke (unit + API se gateway up) =="
"$PY" scripts/smoke_email_writing.py

echo ""
echo "OK run_email_writing_validation.sh"
