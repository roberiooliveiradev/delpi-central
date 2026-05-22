#!/usr/bin/env bash
# Adiciona ao infra/.env as chaves que faltam em produção (sem sobrescrever as existentes).
# Uso (no servidor): cd ~/projetos/delpi-central/infra && ../scripts/append-missing-env-production.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ENV_FILE:-${INFRA_DIR}/.env}"
# Opcional: outro arquivo só para copiar tokens (ex.: backup). Em produção costuma existir só .env.
REF_FILE="${REF_FILE:-}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Arquivo não encontrado: $ENV_FILE" >&2
  exit 1
fi

if [[ -z "$REF_FILE" && -f "${INFRA_DIR}/.env.prod" ]]; then
  REF_FILE="${INFRA_DIR}/.env.prod"
fi

has_key() {
  grep -q "^${1}=" "$ENV_FILE" 2>/dev/null
}

get_ref_or_generate() {
  local key="$1"
  if [[ -f "$REF_FILE" ]]; then
    local line
    line="$(grep -m1 "^${key}=" "$REF_FILE" 2>/dev/null || true)"
    if [[ -n "$line" ]]; then
      echo "${line#*=}"
      return
    fi
  fi
  openssl rand -hex 32
}

append_kv() {
  local key="$1"
  local value="$2"
  if has_key "$key"; then
    echo "  já existe  $key"
    return
  fi
  printf '\n%s=%s\n' "$key" "$value" >>"$ENV_FILE"
  echo "  adicionado $key"
}

BACKUP="${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)"
cp "$ENV_FILE" "$BACKUP"
echo "Backup: $BACKUP"
if [[ -n "$REF_FILE" && -f "$REF_FILE" ]]; then
  echo "Referência (tokens): ${REF_FILE}"
else
  echo "Referência (tokens): nenhuma — gerando com openssl rand -hex 32"
fi
echo

# --- bloco a anexar (comentário de seção uma vez) ---
needs_section=false
for key in \
  API_DELPI_INTERNAL_SERVICE_TOKEN \
  CORE_API_INTEGRATIONS_SERVICE_TOKEN \
  STRATEGIC_INDICATORS_API_PORT \
  API_DELPI_BASE_URL \
  CORE_API_BASE_URL \
  STRATEGIC_INDICATORS_API_BASE_URL \
  STRATEGIC_INDICATORS_PROXY_MEASUREMENTS \
  STRATEGIC_INDICATORS_DOCKERFILE \
  STRATEGIC_INDICATORS_PYTHONPATH \
  SI_MEASUREMENTS_BACKEND \
  SI_MEASUREMENTS_STUB
do
  if ! has_key "$key"; then
    needs_section=true
    break
  fi
done

if [[ "$needs_section" == true ]]; then
  cat >>"$ENV_FILE" <<'EOF'

# ============================
# INTEGRAÇÃO / INDICADORES ESTRATÉGICOS (append automático)
# ============================
EOF
fi

append_kv "API_DELPI_INTERNAL_SERVICE_TOKEN" "$(get_ref_or_generate API_DELPI_INTERNAL_SERVICE_TOKEN)"
append_kv "CORE_API_INTEGRATIONS_SERVICE_TOKEN" "$(get_ref_or_generate CORE_API_INTEGRATIONS_SERVICE_TOKEN)"
append_kv "STRATEGIC_INDICATORS_API_PORT" "8010"
append_kv "API_DELPI_BASE_URL" "http://api-delpi:8000"
append_kv "CORE_API_BASE_URL" "http://core-api:8000"
# Rede Docker: container escuta na porta 8000 (ver docker-compose + gateway)
append_kv "STRATEGIC_INDICATORS_API_BASE_URL" "http://strategic-indicators-api:8000"
append_kv "STRATEGIC_INDICATORS_PROXY_MEASUREMENTS" "false"
append_kv "STRATEGIC_INDICATORS_DOCKERFILE" "Dockerfile"
append_kv "STRATEGIC_INDICATORS_PYTHONPATH" "/app"
append_kv "SI_MEASUREMENTS_BACKEND" "api_delpi_http"
append_kv "SI_MEASUREMENTS_STUB" "false"
append_kv "TRANSFORMOMETRO_API_BASE_URL" "http://transformometro-api:8000"
append_kv "TM_RUN_MIGRATIONS_ON_STARTUP" "true"
append_kv "TM_NOTIFICATIONS_ENABLED" "false"
append_kv "TM_CORE_API_URL" "http://core-api:8000"
append_kv "TM_PORTAL_ROUTE" "/apps/transformometro"
append_kv "TM_WORKFLOW_APPROVER_EMAILS" ""
append_kv "TM_WORKFLOW_APPROVER_ROLE_IDS" ""

echo
echo "Concluído. Recrie os serviços que leem .env:"
echo "  docker compose -f docker-compose.yml up -d --force-recreate api-delpi core-api strategic-indicators-api"
echo "  docker compose -f docker-compose.yml restart gateway"
