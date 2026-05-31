#!/usr/bin/env bash
# Validação Onda 13 — visão/OCR de documentos (chat base)
#
# Uso local:
#   cd minha-delpi-ai-api && ./scripts/run_onda13_validation.sh
#
# Container:
#   docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
#     bash scripts/run_onda13_validation.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-/app:${ROOT}}"

echo "== Onda 13 — pytest =="
python3 -m pytest \
  tests/unit/application/services/test_chat_document_vision_service.py \
  tests/unit/application/services/test_chat_document_vision_metrics_service.py \
  tests/unit/application/services/test_chat_document_vision_attachment_metadata.py \
  tests/unit/application/services/test_chat_document_vision_neural_backend.py \
  tests/unit/application/services/test_chat_document_vision_regression.py \
  tests/unit/application/services/test_chat_attachment_context_service.py \
  tests/unit/domain/services/test_chat_document_vision_bom_service.py \
  tests/unit/domain/services/test_chat_document_vision_title_block_service.py \
  tests/unit/domain/services/test_chat_document_vision_tables_service.py \
  tests/unit/application/services/test_chat_document_vision_persist.py \
  tests/unit/domain/services/test_chat_attachment_document_intent_service.py \
  tests/unit/domain/services/test_chat_intent_router_service.py \
  -q

echo "== Onda 13 — smokes =="
python3 scripts/smoke_document_vision.py
python3 scripts/smoke_drawing_analyser.py
python3 scripts/smoke_intent_route.py || true

echo "== Onda 13 — profile vision (opcional) =="
python3 scripts/check_vision_profile_deps.py || true

echo ""
echo "Onda 13: validação concluída."
