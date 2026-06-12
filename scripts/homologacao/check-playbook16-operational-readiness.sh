#!/usr/bin/env bash
# Playbook 16 — readiness pós-import + smoke chat S4 (programação de hoje).
#
# Uso:
#   ./scripts/homologacao/check-playbook16-operational-readiness.sh
#
# Variáveis:
#   CHAT_API_CONTAINER — default delpi-minha-delpi-ai-api
#   PROVIDER_KEY       — default api-delpi
#   SMOKE_BASE_URL     — gateway para smoke S4 (default: http://localhost)
#   SKIP_SMOKE_S4      — 1 pula smoke E2E (só readiness)
set -euo pipefail

CHAT_API_CONTAINER="${CHAT_API_CONTAINER:-delpi-minha-delpi-ai-api}"
PROVIDER_KEY="${PROVIDER_KEY:-api-delpi}"
SMOKE_BASE_URL="${SMOKE_BASE_URL:-http://localhost}"
SKIP_SMOKE_S4="${SKIP_SMOKE_S4:-0}"

echo "== Playbook 16: readiness + smoke S4 =="
echo "CHAT_API_CONTAINER=${CHAT_API_CONTAINER}"
echo "PROVIDER_KEY=${PROVIDER_KEY}"
echo

echo "[1/2] Readiness — actions críticas no catálogo"
docker exec "$CHAT_API_CONTAINER" python3 scripts/check_operational_action_readiness.py \
  --provider-key "$PROVIDER_KEY"

if [ "$SKIP_SMOKE_S4" = "1" ]; then
  echo "[2/2] SKIP_SMOKE_S4=1 — smoke S4 não executado."
  exit 0
fi

echo "[2/2] Smoke chat S4 — programados hoje"
docker exec "$CHAT_API_CONTAINER" env SMOKE_BASE_URL="$SMOKE_BASE_URL" \
  python3 scripts/smoke_playbook_production_operational.py --only-chat S4

echo "[OK] Playbook 16 readiness + smoke S4 concluídos."
