#!/usr/bin/env bash
# Captura screenshots do admin para baseline Playbook 12 (Fase 0).
# Uso: ADMIN_BASE_URL=https://... ./scripts/capture-admin-baseline.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${BASELINE_DIR:-$ROOT/../../minha-delpi-ai-api/docs/roadmap/melhorias/playbooks_melhoria_minha_delpi_chat/12_admin_ui_refatoracao_componentes/baseline/screenshots}"

if [[ -z "${ADMIN_BASE_URL:-}" ]]; then
  echo "Defina ADMIN_BASE_URL (ex.: http://localhost:5173/apps/minha-delpi-chat/admin)" >&2
  exit 1
fi

mkdir -p "$OUT/1440" "$OUT/768"

echo "Baseline: salvar capturas manualmente em:"
echo "  $OUT"
echo ""
echo "URLs sugeridas (ajuste slugs conforme adminNavigation):"
echo "  $ADMIN_BASE_URL/painel"
echo "  $ADMIN_BASE_URL/conhecimento/documentos"
echo "  $ADMIN_BASE_URL/agentes/especializacao"
echo "  $ADMIN_BASE_URL/qualidade/metricas"
echo "  $ADMIN_BASE_URL/plataforma/ferramentas"
echo "  $ADMIN_BASE_URL/governanca/auditoria"
echo ""
echo "Playwright não está no package.json — use DevTools ou integre npx playwright depois."
