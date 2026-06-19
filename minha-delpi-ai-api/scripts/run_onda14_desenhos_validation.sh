#!/usr/bin/env bash
# Validação Onda 14 — OCR hierárquico de desenhos DELPI
#
# Uso local:
#   cd minha-delpi-ai-api && ./scripts/run_onda14_desenhos_validation.sh
#
# Container:
#   docker compose -f infra/docker-compose.dev.yml exec -T -e PYTHONPATH=/app minha-delpi-ai-api \
#     bash scripts/run_onda14_desenhos_validation.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-/app:${ROOT}}"

PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  if [[ -x "${ROOT}/.venv/bin/python" ]]; then
    PYTHON="${ROOT}/.venv/bin/python"
  else
    PYTHON="python3"
  fi
fi

echo "== Onda 14.1 — pytest (contrato + bundle) =="
"$PYTHON" -m pytest \
  tests/unit/domain/services/test_drawing_stamp_content.py \
  tests/unit/domain/services/test_chat_drawing_region_service.py \
  tests/unit/domain/services/test_chat_drawing_stamp_extraction_service.py \
  tests/unit/domain/services/test_chat_drawing_pdf_extraction_stamp.py \
  tests/unit/fixtures/test_drawing_hierarchical_regression_cases.py \
  tests/unit/domain/services/test_chat_drawing_product_code_resolution_service.py \
  tests/unit/domain/services/test_chat_document_vision_bom_service.py \
  tests/unit/domain/services/test_chat_drawing_dimensions_extraction_service.py \
  tests/unit/domain/services/test_drawing_hierarchical_pipeline_regression.py \
  -q

echo ""
echo "== Onda 14 — regressão drawing + vision (smoke unitário) =="
"$PYTHON" -m pytest \
  tests/unit/domain/services/test_drawing_analysis_skill.py \
  tests/unit/application/services/test_chat_document_vision_service.py \
  -q --tb=no

echo ""
echo "== Onda 14 — batch local desenhos/ (opcional se pasta existir) =="
"$PYTHON" scripts/onda14_desenhos_batch_validation.py
BATCH_EXIT=$?

if [[ "$BATCH_EXIT" -eq 2 ]]; then
  echo "Falha: regressão abaixo do baseline 4/13." >&2
  exit 2
fi

if [[ "$BATCH_EXIT" -eq 3 ]]; then
  echo "Aviso: abaixo da meta 14.8 (≥10/13) — esperado até concluir fases 14.2–14.8." >&2
fi

echo ""
echo "Onda 14: validação concluída (baseline preservado)."
