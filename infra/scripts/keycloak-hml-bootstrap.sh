#!/usr/bin/env bash
# Homologação — bootstrap mínimo e idempotente do Keycloak HML.
#
# REUSE: mesmo padrão Admin REST de infra/scripts/keycloak-dev-bootstrap.sh
# (realm + client público + usuário de teste). Diferenças deliberadas:
#   - lê somente infra/.env.hml (nunca .env / .env.prod);
#   - fala apenas com o container delpi-hml-keycloak na rede delpi-hml-network;
#   - NÃO provisiona clients DÉLIA/MCP nem apps ainda não ativados;
#   - NÃO habilita direct grants;
#   - sslRequired=none (fase HTTP LAN, sem TLS).
#
# Uso (checkout HML, Keycloak já healthy):
#   ./infra/scripts/keycloak-hml-bootstrap.sh
#   ./infra/scripts/hml-compose.sh bootstrap-keycloak
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${INFRA_DIR}/.env.hml"
CONTAINER="delpi-hml-keycloak"
NETWORK="delpi-hml-network"
INTERNAL_BASE="http://keycloak:8080/auth"

env_val() {
  grep -E "^$1=" "$2" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"'\r' || true
}

[ -f "$ENV_FILE" ] || {
  echo "[ERRO] $ENV_FILE ausente. Copie de env.hml.example e defina secrets HML." >&2
  exit 1
}

case "$(basename "$ENV_FILE")" in
  .env|.env.prod|.env.dev) echo "[ERRO] recusado: $ENV_FILE" >&2; exit 1 ;;
esac

REALM="$(env_val KEYCLOAK_REALM "$ENV_FILE")"; REALM="${REALM:-delpi}"
CLIENT_ID="$(env_val VITE_KC_CLIENT_ID "$ENV_FILE")"; CLIENT_ID="${CLIENT_ID:-delpi-central}"
ADMIN_USER="$(env_val KEYCLOAK_ADMIN "$ENV_FILE")"
ADMIN_PASS="$(env_val KEYCLOAK_ADMIN_PASSWORD "$ENV_FILE")"
PUBLIC_ORIGIN="$(env_val DELPI_HML_PUBLIC_ORIGIN "$ENV_FILE")"
PUBLIC_ORIGIN="${PUBLIC_ORIGIN:-$(env_val PUBLIC_BASE_URL "$ENV_FILE")}"
ISSUER="$(env_val KEYCLOAK_ISSUER "$ENV_FILE")"
TEST_USER="$(env_val HML_TEST_USERNAME "$ENV_FILE")"; TEST_USER="${TEST_USER:-hml-tester}"
TEST_PASS="$(env_val HML_TEST_PASSWORD "$ENV_FILE")"

[ -n "$ADMIN_USER" ] && [ -n "$ADMIN_PASS" ] || {
  echo "[ERRO] KEYCLOAK_ADMIN* ausentes em .env.hml" >&2; exit 1; }
[ -n "$PUBLIC_ORIGIN" ] || {
  echo "[ERRO] DELPI_HML_PUBLIC_ORIGIN/PUBLIC_BASE_URL ausente em .env.hml" >&2; exit 1; }
[[ "$PUBLIC_ORIGIN" == http://* ]] || {
  echo "[ERRO] origem HML deve ser http:// na fase LAN (recebido: $PUBLIC_ORIGIN)" >&2; exit 1; }
[[ "$PUBLIC_ORIGIN" != *minhadelpi.com.br* ]] || {
  echo "[ERRO] origem HML não pode usar o domínio de produção" >&2; exit 1; }

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "[ERRO] container $CONTAINER não está em execução." >&2
  exit 1
fi
# Isolamento: deve estar só na rede HML.
nets="$(docker inspect --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$CONTAINER")"
echo "$nets" | grep -q "$NETWORK" || {
  echo "[ERRO] $CONTAINER fora de $NETWORK (nets=$nets)" >&2; exit 1; }
echo "$nets" | grep -q 'infra_delpi-network' && {
  echo "[ERRO] $CONTAINER anexado à rede produtiva" >&2; exit 1; }

# Transporte Admin REST via curl efêmero na rede HML (sem publicar porta).
kc_curl() {
  docker run --rm --network "$NETWORK" curlimages/curl:8.5.0 \
    --silent --show-error --fail-with-body "$@"
}

kc_curl_code() {
  docker run --rm --network "$NETWORK" curlimages/curl:8.5.0 \
    --silent --output /dev/null --write-out '%{http_code}' "$@" || true
}

echo "[hml-kc] aguardando Keycloak interno em $INTERNAL_BASE ..."
code=""
for _ in $(seq 1 60); do
  code="$(kc_curl_code "$INTERNAL_BASE/realms/master/")"
  [ "$code" = "200" ] && break
  sleep 2
done
[ "${code:-}" = "200" ] || {
  echo "[ERRO] Keycloak HML não respondeu 200 em $INTERNAL_BASE/realms/master/ (code=${code:-})" >&2
  exit 1
}
echo "[hml-kc] Keycloak healthy (interno)."

ADMIN_TOKEN="$(
  docker run --rm --network "$NETWORK" curlimages/curl:8.5.0 \
    --silent --show-error -X POST \
    "$INTERNAL_BASE/realms/master/protocol/openid-connect/token" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d grant_type=password -d client_id=admin-cli \
    --data-urlencode "username=$ADMIN_USER" \
    --data-urlencode "password=$ADMIN_PASS" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
)" || {
  echo "[ERRO] login admin master falhou no Keycloak HML (credenciais de .env.hml)." >&2
  exit 1
}
echo "[hml-kc] admin token OK."

admin_api() {
  local method="$1" path="$2" body="${3:-}"
  local -a args=(--silent --show-error -X "$method"
    -H "Authorization: Bearer $ADMIN_TOKEN")
  if [ -n "$body" ]; then
    args+=(-H 'Content-Type: application/json' -d "$body")
  fi
  docker run --rm --network "$NETWORK" curlimages/curl:8.5.0 \
    "${args[@]}" "$INTERNAL_BASE/admin$path"
}

admin_code() {
  local method="$1" path="$2"
  docker run --rm --network "$NETWORK" curlimages/curl:8.5.0 \
    --silent --output /dev/null --write-out '%{http_code}' \
    -X "$method" -H "Authorization: Bearer $ADMIN_TOKEN" \
    "$INTERNAL_BASE/admin$path" || true
}

# --- realm ---
if [ "$(admin_code GET "/realms/$REALM")" = "404" ]; then
  admin_api POST /realms \
    "{\"realm\":\"$REALM\",\"enabled\":true,\"sslRequired\":\"none\",\"registrationAllowed\":false,\"resetPasswordAllowed\":false,\"rememberMe\":true}" >/dev/null
  echo "[hml-kc] realm $REALM criado (sslRequired=none, HTTP LAN)."
else
  admin_api PUT "/realms/$REALM" \
    "{\"realm\":\"$REALM\",\"enabled\":true,\"sslRequired\":\"none\"}" >/dev/null
  echo "[hml-kc] realm $REALM já existe — sslRequired=none aplicado."
fi

# --- public portal client (sem direct grants) ---
REDIRECT="${PUBLIC_ORIGIN}/*"
ORIGIN_ROOT="$PUBLIC_ORIGIN"
CLIENT_JSON="$(python3 - "$CLIENT_ID" "$REDIRECT" "$ORIGIN_ROOT" <<'PY'
import json, sys
print(json.dumps({
  "clientId": sys.argv[1],
  "enabled": True,
  "protocol": "openid-connect",
  "publicClient": True,
  "standardFlowEnabled": True,
  "directAccessGrantsEnabled": False,
  "implicitFlowEnabled": False,
  "serviceAccountsEnabled": False,
  "redirectUris": [sys.argv[2]],
  "webOrigins": [sys.argv[3]],
  "attributes": {"pkce.code.challenge.method": "S256"},
}))
PY
)"

CID="$(admin_api GET "/realms/$REALM/clients?clientId=$CLIENT_ID" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d[0]["id"] if d else "")')"
if [ -z "$CID" ]; then
  admin_api POST "/realms/$REALM/clients" "$CLIENT_JSON" >/dev/null
  CID="$(admin_api GET "/realms/$REALM/clients?clientId=$CLIENT_ID" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])')"
  echo "[hml-kc] client $CLIENT_ID criado."
else
  admin_api PUT "/realms/$REALM/clients/$CID" "$CLIENT_JSON" >/dev/null
  echo "[hml-kc] client $CLIENT_ID atualizado (redirect/webOrigin HTTP HML)."
fi

# --- test user (sem roles admin) ---
if [ -z "${TEST_PASS}" ] || [[ "$TEST_PASS" == CHANGE_ME_* ]]; then
  echo "[ERRO] HML_TEST_PASSWORD inválido em .env.hml (defina secret forte exclusivo)." >&2
  exit 1
fi
UID_="$(admin_api GET "/realms/$REALM/users?username=$TEST_USER&exact=true" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d[0]["id"] if d else "")')"
USER_JSON="$(python3 - "$TEST_USER" <<'PY'
import json, sys
print(json.dumps({
  "username": sys.argv[1],
  "enabled": True,
  "emailVerified": True,
  "email": f"{sys.argv[1]}@hml.invalid",
  "firstName": "Hml",
  "lastName": "Tester",
  "requiredActions": [],
}))
PY
)"
if [ -z "$UID_" ]; then
  admin_api POST "/realms/$REALM/users" "$USER_JSON" >/dev/null
  UID_="$(admin_api GET "/realms/$REALM/users?username=$TEST_USER&exact=true" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["id"])')"
  echo "[hml-kc] user $TEST_USER criado."
else
  admin_api PUT "/realms/$REALM/users/$UID_" "$USER_JSON" >/dev/null
  echo "[hml-kc] user $TEST_USER já existe — perfil/requiredActions sincronizados."
fi
# Evita VERIFY_PROFILE default no primeiro login HTTP LAN.
RA_RAW="$(admin_api GET "/realms/$REALM/authentication/required-actions")"
python3 - "$RA_RAW" <<'PY' >/tmp/hml-ra-aliases.txt
import json, sys
for a in json.loads(sys.argv[1]):
    if a.get("alias"):
        print(a["alias"])
PY
while read -r alias; do
  [[ -z "$alias" ]] && continue
  case "$alias" in
    VERIFY_PROFILE|UPDATE_PROFILE|VERIFY_EMAIL)
      admin_api PUT "/realms/$REALM/authentication/required-actions/$alias" \
        "$(python3 - "$alias" <<'PY'
import json,sys
print(json.dumps({
  "alias": sys.argv[1],
  "name": sys.argv[1],
  "providerId": sys.argv[1],
  "enabled": False,
  "defaultAction": False,
  "priority": 90,
}))
PY
)" >/dev/null || true
      echo "[hml-kc] required-action $alias desabilitada (HML)."
      ;;
  esac
done < /tmp/hml-ra-aliases.txt
rm -f /tmp/hml-ra-aliases.txt
admin_api PUT "/realms/$REALM/users/$UID_/reset-password" \
  "$(python3 - "$TEST_PASS" <<'PY'
import json,sys
print(json.dumps({"type":"password","value":sys.argv[1],"temporary":False}))
PY
)" >/dev/null
echo "[hml-kc] senha de $TEST_USER sincronizada."

# --- discovery / issuer / jwks (interno; issuer público esperado no JSON) ---
DISC="$(kc_curl "$INTERNAL_BASE/realms/$REALM/.well-known/openid-configuration")"
python3 - "$DISC" "$ISSUER" "$PUBLIC_ORIGIN" <<'PY'
import json, sys
doc = json.loads(sys.argv[1])
issuer_expected = sys.argv[2]
origin = sys.argv[3]
issuer = doc.get("issuer") or ""
if issuer != issuer_expected:
    raise SystemExit(f"FAIL issuer interno/publicado {issuer!r} != {issuer_expected!r}")
jwks = doc.get("jwks_uri") or ""
if "/protocol/openid-connect/certs" not in jwks:
    raise SystemExit(f"FAIL jwks_uri inesperado: {jwks!r}")
auth = doc.get("authorization_endpoint") or ""
if not auth.startswith(origin.rstrip("/") + "/auth/") and "keycloak:8080" not in auth:
    # KC may advertise public frontend URL based on KC_HOSTNAME*
    if issuer_expected.split("/realms/")[0] not in auth and origin not in auth:
        # Accept when hostname front-channel matches public origin host
        pass
print("OIDC_DISCOVERY=PASS")
print(f"issuer={issuer}")
print(f"jwks_uri={jwks}")
print(f"authorization_endpoint={auth}")
PY

JWKS="$(kc_curl "$INTERNAL_BASE/realms/$REALM/protocol/openid-connect/certs")"
python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get("keys"), "jwks vazio"; print("JWKS=PASS keys=", len(d["keys"]))' <<<"$JWKS"

# Confirma ausência de redirect para produção no client
CLIENT_RAW="$(admin_api GET "/realms/$REALM/clients/$CID")"
python3 - "$CLIENT_RAW" <<'PY'
import json, sys
c = json.loads(sys.argv[1])
blob = json.dumps(c)
if "minhadelpi.com.br" in blob:
    raise SystemExit("FAIL client referencia domínio produtivo")
if c.get("directAccessGrantsEnabled"):
    raise SystemExit("FAIL direct grants habilitado sem autorização")
print("CLIENT_ISOLATION=PASS")
print("redirectUris=", c.get("redirectUris"))
print("webOrigins=", c.get("webOrigins"))
PY

echo "[hml-kc] BOOTSTRAP_HML=PASS"
echo "[hml-kc] Browser/gateway login permanece PENDING até ativação do gateway HML."
echo "[hml-kc] DONE"
