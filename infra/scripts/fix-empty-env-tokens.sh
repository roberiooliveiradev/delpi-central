#!/usr/bin/env bash
# Corrige chaves vazias em infra/.env (ex.: após append com .env.prod inexistente).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-${SCRIPT_DIR}/../.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Arquivo não encontrado: $ENV_FILE" >&2
  exit 1
fi

fix_if_empty() {
  local key="$1"
  local current
  current="$(grep -m1 "^${key}=" "$ENV_FILE" 2>/dev/null | cut -d= -f2- || true)"
  if [[ -z "${current// }" ]]; then
    local value
    value="$(openssl rand -hex 32)"
    if grep -q "^${key}=" "$ENV_FILE"; then
      sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
    else
      printf '%s=%s\n' "$key" "$value" >>"$ENV_FILE"
    fi
    echo "  corrigido $key (valor gerado)"
  else
    echo "  ok       $key (já tinha valor)"
  fi
}

echo "Arquivo: $ENV_FILE"
fix_if_empty "API_DELPI_INTERNAL_SERVICE_TOKEN"
fix_if_empty "CORE_API_INTEGRATIONS_SERVICE_TOKEN"
echo "Concluído."
