#!/usr/bin/env bash
# Validação Fase 0 — view vw_Apontamentos_Eficiencia (requer delpi-api-delpi + TOTVS).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT="${ROOT}/docs/12-roadmap-e-evolucao/eficiencia-fabril/FASE0-VALIDACAO.md"

if ! docker ps --format '{{.Names}}' | grep -qx 'delpi-api-delpi'; then
  echo "ERRO: container delpi-api-delpi não está em execução." >&2
  exit 1
fi

docker exec delpi-api-delpi python scripts/validate_eficiencia_fabril_view.py \
  --markdown /tmp/FASE0-VALIDACAO.md
docker cp delpi-api-delpi:/tmp/FASE0-VALIDACAO.md "${REPORT}"

echo "Relatório atualizado: ${REPORT}"
