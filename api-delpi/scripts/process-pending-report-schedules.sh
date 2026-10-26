#!/usr/bin/env sh
# Processa agendas vencidas do Delpi Reports (report_schedules.next_run_at).
#
# Preferência de destino (nesta ordem):
#   1. API_DELPI_BASE_URL (se apontar para host/gateway alcançável)
#   2. Container api-delpi via Docker (rede interna — não depende da porta do host)
#   3. Gateway no host em :9080 ou :80
#
# Uso em cron (host WSL/Linux), ex.:
#   */15 * * * * /home/michael/projetos/delpi-central/api-delpi/scripts/process-pending-report-schedules.sh >>/tmp/delpi-reports-cron.log 2>&1
#
# Variáveis (opcionais se existirem em infra/.env):
#   API_DELPI_BASE_URL
#   API_DELPI_INTERNAL_SERVICE_TOKEN
#   DELPI_ENV_FILE — path do .env (default <repo>/infra/.env)
#   REPORTS_PROCESS_PENDING_LIMIT — lote (default 20)
#   DELPI_GATEWAY_HOST_PORT — porta publicada do gateway (default 9080, fallback 80)

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
ENV_FILE="${DELPI_ENV_FILE:-$REPO_ROOT/infra/.env}"

_load_env_var() {
  key=$1
  if [ ! -f "$ENV_FILE" ]; then
    return 0
  fi
  line=$(grep -E "^${key}=" "$ENV_FILE" | head -1 || true)
  if [ -z "$line" ]; then
    return 0
  fi
  printf '%s' "$line" | cut -d= -f2- | tr -d '"' | tr -d "'"
}

BASE_URL="${API_DELPI_BASE_URL:-}"
TOKEN="${API_DELPI_INTERNAL_SERVICE_TOKEN:-}"
LIMIT="${REPORTS_PROCESS_PENDING_LIMIT:-20}"
GATEWAY_PORT="${DELPI_GATEWAY_HOST_PORT:-}"

if [ -z "$BASE_URL" ]; then
  BASE_URL=$(_load_env_var API_DELPI_BASE_URL || true)
fi
if [ -z "$TOKEN" ]; then
  TOKEN=$(_load_env_var API_DELPI_INTERNAL_SERVICE_TOKEN || true)
fi
if [ -z "$GATEWAY_PORT" ]; then
  GATEWAY_PORT=$(_load_env_var DELPI_GATEWAY_HOST_PORT || true)
fi
if [ -z "$GATEWAY_PORT" ]; then
  GATEWAY_PORT="9080"
fi

if [ -z "$TOKEN" ]; then
  echo "API_DELPI_INTERNAL_SERVICE_TOKEN is required (env or $ENV_FILE)" >&2
  exit 1
fi

_post() {
  url=$1
  echo "$(date -Iseconds) process-pending limit=${LIMIT} base=${url}"
  curl -fsS -X POST "${url%/}/reports/schedules/process-pending?limit=${LIMIT}" \
    -H "X-Delpi-Service-Token: ${TOKEN}" \
    -H "Content-Type: application/json"
  echo ""
}

# URL Docker interna no Compose não resolve no host.
case "${BASE_URL}" in
  http://api-delpi*|http://delpi-api-delpi*|"" )
    BASE_URL=""
    ;;
esac

if [ -n "$BASE_URL" ]; then
  if _post "$BASE_URL"; then
    exit 0
  fi
  echo "$(date -Iseconds) warn: falha em API_DELPI_BASE_URL=${BASE_URL}; tentando fallbacks" >&2
fi

# Preferir chamada na rede Docker (independe da porta publicada no host).
if command -v docker >/dev/null 2>&1; then
  if docker inspect delpi-api-delpi >/dev/null 2>&1; then
    echo "$(date -Iseconds) process-pending limit=${LIMIT} via=docker://delpi-api-delpi:8000"
    if docker exec delpi-api-delpi \
      curl -fsS -X POST \
      "http://127.0.0.1:8000/reports/schedules/process-pending?limit=${LIMIT}" \
      -H "X-Delpi-Service-Token: ${TOKEN}" \
      -H "Content-Type: application/json"; then
      echo ""
      exit 0
    fi
    echo "$(date -Iseconds) warn: falha via docker exec; tentando gateway no host" >&2
  fi
fi

for port in "$GATEWAY_PORT" 9080 80; do
  case "$port" in
    "" ) continue ;;
  esac
  url="http://127.0.0.1:${port}/apps/api-delpi"
  if _post "$url"; then
    exit 0
  fi
  echo "$(date -Iseconds) warn: falha em ${url}" >&2
done

echo "$(date -Iseconds) error: nenhum endpoint alcançável para process-pending" >&2
exit 1
