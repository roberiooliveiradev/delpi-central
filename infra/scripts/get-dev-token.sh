#!/usr/bin/env bash
# Obtém access_token JWT do Keycloak (dev local) usando infra/.env.local.
# Uso:
#   export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
#   bash plugins/cultura-delpi/scripts/register-manifest.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_LOCAL="$INFRA_DIR/.env.local"

if [ ! -f "$ENV_LOCAL" ]; then
  echo "[ERRO] $ENV_LOCAL não encontrado. Copie infra/env.local.example → infra/.env.local" >&2
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$ENV_LOCAL"
set +a

BASE_URL="${DEV_BASE_URL:-http://localhost}"
REALM="${DEV_KC_REALM:-delpi}"
CLIENT_ID="${DEV_KC_CLIENT_ID:-delpi-central}"
USERNAME="${DEV_PORTAL_USERNAME:-}"
PASSWORD="${DEV_PORTAL_PASSWORD:-}"

if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
  echo "[ERRO] Defina DEV_PORTAL_USERNAME e DEV_PORTAL_PASSWORD em $ENV_LOCAL" >&2
  exit 1
fi

RESP=$(curl -sf -X POST "${BASE_URL}/auth/realms/${REALM}/protocol/openid-connect/token" \
  -d "client_id=${CLIENT_ID}" \
  -d "username=${USERNAME}" \
  -d "password=${PASSWORD}" \
  -d "grant_type=password") || {
  echo "[ERRO] Falha ao obter token em ${BASE_URL}/auth/realms/${REALM}/..." >&2
  exit 1
}

python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])" <<<"$RESP"
