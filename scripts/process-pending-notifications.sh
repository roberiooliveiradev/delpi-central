#!/usr/bin/env sh
# Processa envios de notificação agendados (notification_dispatches pending).
# Uso em cron, ex.: */5 * * * * /path/delpi-central/scripts/process-pending-notifications.sh
#
# Variáveis:
#   DELPI_API_BASE_URL  — base pública (default http://127.0.0.1)
#   CORE_API_INTEGRATIONS_SERVICE_TOKEN — token de integrações (obrigatório)

set -eu

BASE_URL="${DELPI_API_BASE_URL:-http://127.0.0.1}"
TOKEN="${CORE_API_INTEGRATIONS_SERVICE_TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "CORE_API_INTEGRATIONS_SERVICE_TOKEN is required" >&2
  exit 1
fi

curl -fsS -X POST "${BASE_URL%/}/core-api/integrations/notifications/process-pending" \
  -H "X-Delpi-Service-Token: ${TOKEN}" \
  -H "Content-Type: application/json"

echo ""
