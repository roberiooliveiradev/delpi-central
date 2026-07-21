#!/usr/bin/env sh
# Processa agendas vencidas do Delpi Reports (report_schedules.next_run_at).
#
# Uso em cron (host WSL/Linux), ex.:
#   */15 * * * * /home/michael/projetos/delpi-central/api-delpi/scripts/process-pending-report-schedules.sh >>/tmp/delpi-reports-cron.log 2>&1
#
# Variáveis (opcionais se existirem em infra/.env):
#   API_DELPI_BASE_URL — default http://127.0.0.1/apps/api-delpi (gateway no host)
#   API_DELPI_INTERNAL_SERVICE_TOKEN — token S2S
#   DELPI_ENV_FILE — path do .env (default <repo>/infra/.env)
#   REPORTS_PROCESS_PENDING_LIMIT — lote (default 20)

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
ENV_FILE="${DELPI_ENV_FILE:-$REPO_ROOT/infra/.env}"

_load_env_var() {
  key=$1
  if [ ! -f "$ENV_FILE" ]; then
    return 0
  fi
  # Lê só KEY=... (sem source do .env inteiro — evita valores com espaços quebrarem o shell).
  line=$(grep -E "^${key}=" "$ENV_FILE" | head -1 || true)
  if [ -z "$line" ]; then
    return 0
  fi
  printf '%s' "$line" | cut -d= -f2- | tr -d '"' | tr -d "'"
}

BASE_URL="${API_DELPI_BASE_URL:-}"
TOKEN="${API_DELPI_INTERNAL_SERVICE_TOKEN:-}"
LIMIT="${REPORTS_PROCESS_PENDING_LIMIT:-20}"

if [ -z "$BASE_URL" ]; then
  BASE_URL=$(_load_env_var API_DELPI_BASE_URL || true)
fi
# No host, URL interna Docker (http://api-delpi:…) não resolve — usar gateway.
case "${BASE_URL}" in
  http://api-delpi*|http://delpi-api-delpi*|"" )
    BASE_URL="http://127.0.0.1/apps/api-delpi"
    ;;
esac

if [ -z "$TOKEN" ]; then
  TOKEN=$(_load_env_var API_DELPI_INTERNAL_SERVICE_TOKEN || true)
fi

if [ -z "$TOKEN" ]; then
  echo "API_DELPI_INTERNAL_SERVICE_TOKEN is required (env or $ENV_FILE)" >&2
  exit 1
fi

echo "$(date -Iseconds) process-pending limit=${LIMIT} base=${BASE_URL}"
curl -fsS -X POST "${BASE_URL%/}/reports/schedules/process-pending?limit=${LIMIT}" \
  -H "X-Delpi-Service-Token: ${TOKEN}" \
  -H "Content-Type: application/json"

echo ""
