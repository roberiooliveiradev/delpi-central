#!/usr/bin/env bash
# Obtém access_token JWT do Keycloak (dev local).
# Credenciais DEV_*: fonte canônica infra/.env (template .env.dev.example);
# infra/.env.local (legado, opcional) sobrescreve se existir.
# Uso:
#   export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
#   bash plugins/cultura-delpi/scripts/register-manifest.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$INFRA_DIR/.env"
ENV_LOCAL="$INFRA_DIR/.env.local"

if [ ! -f "$ENV_FILE" ] && [ ! -f "$ENV_LOCAL" ]; then
  echo "[ERRO] Nenhum env encontrado. Copie infra/.env.dev.example → infra/.env" >&2
  exit 1
fi

# shellcheck disable=SC1090
set -a
[ -f "$ENV_FILE" ] && source "$ENV_FILE"
[ -f "$ENV_LOCAL" ] && source "$ENV_LOCAL"
set +a

BASE_URL="${DEV_BASE_URL:-http://localhost}"
REALM="${DEV_KC_REALM:-delpi}"
CLIENT_ID="${DEV_KC_CLIENT_ID:-delpi-central}"
USERNAME="${DEV_PORTAL_USERNAME:-}"
PASSWORD="${DEV_PORTAL_PASSWORD:-}"

if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
  echo "[ERRO] Defina DEV_PORTAL_USERNAME e DEV_PORTAL_PASSWORD em infra/.env (ver .env.dev.example)" >&2
  exit 1
fi

fetch_token() {
  local base_url="$1"
  curl -sf -X POST "${base_url%/}/auth/realms/${REALM}/protocol/openid-connect/token" \
    -d "client_id=${CLIENT_ID}" \
    -d "username=${USERNAME}" \
    -d "password=${PASSWORD}" \
    -d "grant_type=password" \
    -d "scope=openid profile email"
}

RESP=""
if RESP=$(fetch_token "$BASE_URL"); then
  :
elif [ "$BASE_URL" = "http://localhost" ] || [ "$BASE_URL" = "http://localhost/" ]; then
  FALLBACK_URL="http://localhost:9080"
  RESP=$(fetch_token "$FALLBACK_URL") || {
    echo "[ERRO] Falha ao obter token em ${BASE_URL} e ${FALLBACK_URL}/auth/realms/${REALM}/..." >&2
    exit 1
  }
else
  echo "[ERRO] Falha ao obter token em ${BASE_URL}/auth/realms/${REALM}/..." >&2
  exit 1
fi

python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])" <<<"$RESP"
