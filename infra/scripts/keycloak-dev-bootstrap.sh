#!/usr/bin/env bash
# Canonical local-dev Keycloak bootstrap/repair (idempotent).
#
# Ensures, via Keycloak Admin REST only (no SQL, no manual hash):
#   1. realm `delpi` exists and is enabled;
#   2. public client `delpi-central` exists (standard flow + direct grants);
#   3. the dev portal user exists and its password matches infra/.env.local
#      (DEV_PORTAL_USERNAME / DEV_PORTAL_PASSWORD).
#
# Safe to re-run: existing realm/client/users are repaired in place, never
# wiped. Use when local login drifts (e.g. after volume/env divergence).
#
# Recovery path when the admin account itself is stale (ADMIN_TOKEN fails):
#   reset ONLY the keycloak volumes and re-run this script:
#     docker compose -f infra/docker-compose.dev.yml stop keycloak keycloak-db
#     docker volume rm infra_keycloak_data
#     bash infra/scripts/up-dev-sequential.sh keycloak
#     bash infra/scripts/keycloak-dev-bootstrap.sh
#
# Requires: infra/.env (KEYCLOAK_ADMIN*, POSTGRES_KC_*) and, for the dev user,
# infra/.env.local (DEV_PORTAL_USERNAME / DEV_PORTAL_PASSWORD).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

env_val() { # KEY file — tolerant to values with spaces/comments
  grep -E "^$1=" "$2" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"'\r' || true
}

KC_BASE="$(env_val KC_BASE_URL "$INFRA_DIR/.env")"; KC_BASE="${KC_BASE:-http://localhost}/auth"
REALM="$(env_val KEYCLOAK_REALM "$INFRA_DIR/.env")"; REALM="${REALM:-delpi}"
CLIENT_ID="$(env_val DEV_KC_CLIENT_ID "$INFRA_DIR/.env.local")"; CLIENT_ID="${CLIENT_ID:-delpi-central}"
ADMIN_USER="$(env_val KEYCLOAK_ADMIN "$INFRA_DIR/.env")"
ADMIN_PASS="$(env_val KEYCLOAK_ADMIN_PASSWORD "$INFRA_DIR/.env")"
DEV_USER="$(env_val DEV_PORTAL_USERNAME "$INFRA_DIR/.env.local")"
DEV_PASS="$(env_val DEV_PORTAL_PASSWORD "$INFRA_DIR/.env.local")"
[ -n "$ADMIN_USER" ] && [ -n "$ADMIN_PASS" ] || {
  echo "[ERRO] KEYCLOAK_ADMIN* ausentes em infra/.env" >&2; exit 1; }

# Fail closed: this script is for the local dev instance only.
case "$KC_BASE" in
  http://localhost*|http://127.0.0.1*) ;;
  *) echo "[ERRO] keycloak-dev-bootstrap só roda contra localhost ($KC_BASE)." >&2; exit 1 ;;
esac

echo "[kc-bootstrap] aguardando Keycloak em $KC_BASE ..."
for i in $(seq 1 60); do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$KC_BASE/realms/master/" || true)
  [ "$code" = "200" ] && break
  sleep 2
done
[ "${code:-}" = "200" ] || { echo "[ERRO] Keycloak não respondeu 200 em $KC_BASE/realms/master/" >&2; exit 1; }
echo "[kc-bootstrap] Keycloak healthy."

ADMIN_TOKEN=$(curl -sf -X POST \
  "$KC_BASE/realms/master/protocol/openid-connect/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d grant_type=password -d client_id=admin-cli \
  --data-urlencode "username=$ADMIN_USER" \
  --data-urlencode "password=$ADMIN_PASS" \
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["access_token"])') || {
    cat >&2 <<'EOF'
[ERRO] login admin falhou. O admin master está divergente de infra/.env.
Recuperação canônica (somente local):
  docker compose -f infra/docker-compose.dev.yml stop keycloak keycloak-db
  docker volume rm infra_keycloak_data
  bash infra/scripts/up-dev-sequential.sh keycloak
  bash infra/scripts/keycloak-dev-bootstrap.sh
EOF
    exit 1
  }
echo "[kc-bootstrap] admin token OK."

admin_api() { # method path [json]
  local method="$1" path="$2" body="${3:-}"
  local args=(-s -X "$method" -H "Authorization: Bearer $ADMIN_TOKEN")
  if [ -n "$body" ]; then
    args+=(-H 'Content-Type: application/json' -d "$body")
  fi
  curl "${args[@]}" "$KC_BASE/admin$path"
}

# --- realm ---
if [ "$(admin_api GET "/realms/$REALM" -o /dev/null -w '%{http_code}' || true)" = "404" ]; then
  admin_api POST /realms \
    "{\"realm\":\"$REALM\",\"enabled\":true,\"sslRequired\":\"external\"}" >/dev/null
  echo "[kc-bootstrap] realm $REALM criado."
else
  echo "[kc-bootstrap] realm $REALM já existe."
fi

# --- client ---
CID=$(admin_api GET "/realms/$REALM/clients?clientId=$CLIENT_ID" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d[0]["id"] if d else "")')
if [ -z "$CID" ]; then
  admin_api POST "/realms/$REALM/clients" "$(python3 - "$CLIENT_ID" <<'PY'
import json,sys
print(json.dumps({
  "clientId": sys.argv[1], "enabled": True, "protocol": "openid-connect",
  "publicClient": True, "standardFlowEnabled": True,
  "directAccessGrantsEnabled": True,
  "redirectUris": ["http://localhost/*", "http://127.0.0.1/*"],
  "webOrigins": ["http://localhost", "http://127.0.0.1"],
}))
PY
)" >/dev/null
  echo "[kc-bootstrap] client $CLIENT_ID criado."
else
  echo "[kc-bootstrap] client $CLIENT_ID já existe."
fi

# --- dev user (optional when .env.local not configured) ---
if [ -n "$DEV_USER" ] && [ -n "$DEV_PASS" ]; then
  UID_=$(admin_api GET "/realms/$REALM/users?username=$DEV_USER&exact=true" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d[0]["id"] if d else "")')
  if [ -z "$UID_" ]; then
    admin_api POST "/realms/$REALM/users" \
      "{\"username\":\"$DEV_USER\",\"enabled\":true}" >/dev/null
    UID_=$(admin_api GET "/realms/$REALM/users?username=$DEV_USER&exact=true" \
      | python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])')
    echo "[kc-bootstrap] user $DEV_USER criado."
  else
    admin_api PUT "/realms/$REALM/users/$UID_" '{"enabled":true}' >/dev/null
  fi
  # deterministic credential: always reset password to env value
  admin_api PUT "/realms/$REALM/users/$UID_/reset-password" \
    "$(python3 - "$DEV_PASS" <<'PY'
import json,sys
print(json.dumps({"type":"password","value":sys.argv[1],"temporary":False}))
PY
)" >/dev/null
  echo "[kc-bootstrap] senha de $DEV_USER sincronizada com infra/.env.local."

  TOKEN=$(curl -sf -X POST "$KC_BASE/realms/$REALM/protocol/openid-connect/token" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d grant_type=password -d "client_id=$CLIENT_ID" \
    --data-urlencode "username=$DEV_USER" --data-urlencode "password=$DEV_PASS" \
    -d scope=openid | python3 -c 'import json,sys;print(json.load(sys.stdin)["access_token"])' || true)
  if [ -n "${TOKEN:-}" ]; then
    echo "[kc-bootstrap] TOKEN_OK — login de $DEV_USER verificado."
  else
    echo "[ERRO] bootstrap concluído mas o password grant falhou." >&2; exit 1
  fi
else
  echo "[kc-bootstrap] DEV_PORTAL_* não definido em infra/.env.local — realm/client ok, usuário pulado."
fi

echo "[kc-bootstrap] DONE"
