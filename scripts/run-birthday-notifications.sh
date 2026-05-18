#!/usr/bin/env sh
# Dispara notificações de aniversário para usuários com birth_date = hoje.
# Agendar 1x/dia (ex.: 08:00).

set -eu

BASE_URL="${DELPI_API_BASE_URL:-http://127.0.0.1}"
TOKEN="${CORE_API_INTEGRATIONS_SERVICE_TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "CORE_API_INTEGRATIONS_SERVICE_TOKEN is required" >&2
  exit 1
fi

curl -fsS -X POST "${BASE_URL%/}/core-api/integrations/notifications/automation/birthdays" \
  -H "X-Delpi-Service-Token: ${TOKEN}" \
  -H "Content-Type: application/json"

echo ""
