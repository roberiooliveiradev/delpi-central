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

# --- DÉLIA user-delegated MCP identity (C3-MCP-INTEROP-01R1A) ---
# Materializes the approved exchange model in the dev realm:
#   * generic client scope `mcp:tools`;
#   * one resource client + one resource-audience scope per approved
#     specialist (mcp-api-delpi / mcp-transformometro / mcp-tv-dashboard);
#   * ONE confidential requester client `delia-api`
#     (standard.token.exchange.enabled, no service account);
#   * requester audience `delia-api` on the Portal client (required by
#     KC26 token exchange — NOT an MCP audience on the Portal token);
#   * per-target `token-exchange` scope permission bound to a clients
#     policy containing only `delia-api` (requires the dev-only
#     admin-fine-grained-authz feature flag);
#   * DELIA_EXCHANGE_CLIENT_SECRET upserted into gitignored infra/.env.
KC_SECRET_STORE="$INFRA_DIR/.env"
ADMIN_TOKEN="$ADMIN_TOKEN" KC_BASE="$KC_BASE" REALM="$REALM" \
  PORTAL_CLIENT_ID="$CLIENT_ID" KC_SECRET_STORE="$KC_SECRET_STORE" \
  python3 <<'PY'
import json, os, urllib.request, urllib.parse

KC = os.environ["KC_BASE"].rstrip("/")
REALM = os.environ["REALM"]
ADMIN = os.environ["ADMIN_TOKEN"]
PORTAL = os.environ["PORTAL_CLIENT_ID"]
SECRET_STORE = os.environ["KC_SECRET_STORE"]

SPECIALISTS = [
    ("mcp-api-delpi", "mcp-audience-api-delpi",
     "https://minhadelpi.com.br/apps/api-delpi/mcp"),
    ("mcp-transformometro", "mcp-audience-transformometro",
     "https://minhadelpi.com.br/apps/transformometro-api/mcp"),
    ("mcp-tv-dashboard", "mcp-audience-tv-dashboard",
     "https://minhadelpi.com.br/apps/tv-dashboard-api/mcp"),
]
REQUESTER = "delia-api"


def api(method, path, body=None, tolerate=()):
    r = urllib.request.Request(KC + "/admin" + path, method=method)
    r.add_header("Authorization", "Bearer " + ADMIN)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        r.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(r, data=data, timeout=20)
        raw = resp.read()
        return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        if e.code in tolerate:
            e.read()
            return e.code, None
        raise SystemExit(
            f"[kc-bootstrap][delia-exchange] {method} {path} -> {e.code}: "
            f"{(e.read() or b'')[:200].decode('utf-8', 'replace')}"
        )


def client_uuid(client_id):
    st, rows = api("GET", f"/realms/{REALM}/clients?clientId={client_id}")
    return rows[0]["id"] if rows else ""


def ensure_client_scope(name):
    st, scopes = api("GET", f"/realms/{REALM}/client-scopes")
    found = next((s for s in scopes if s["name"] == name), None)
    if found is None:
        api("POST", f"/realms/{REALM}/client-scopes", {
            "name": name, "protocol": "openid-connect",
            "attributes": {"include.in.token.scope": "true",
                           "display.on.consent.screen": "false"},
        }, tolerate=(409,))
        st, scopes = api("GET", f"/realms/{REALM}/client-scopes")
        found = next(s for s in scopes if s["name"] == name)
    return found["id"]


def ensure_audience_mapper(scope_id, aud):
    st, mappers = api(
        "GET",
        f"/realms/{REALM}/client-scopes/{scope_id}/protocol-mappers/models")
    for m in mappers:
        if (m["protocolMapper"] == "oidc-audience-mapper"
                and m.get("config", {}).get("included.custom.audience") == aud):
            return
    api("POST",
        f"/realms/{REALM}/client-scopes/{scope_id}/protocol-mappers/models",
        {"name": f"{aud.rsplit('/', 1)[-2]}-resource-aud",
         "protocol": "openid-connect",
         "protocolMapper": "oidc-audience-mapper",
         "config": {"included.custom.audience": aud,
                    "id.token.claim": "false",
                    "access.token.claim": "true"}})


def ensure_default_scope(client_uuid_, scope_id):
    st, defaults = api(
        "GET", f"/realms/{REALM}/clients/{client_uuid_}/default-client-scopes")
    if scope_id not in {s["id"] for s in defaults}:
        api("PUT",
            f"/realms/{REALM}/clients/{client_uuid_}/default-client-scopes/{scope_id}",
            tolerate=(404,))


def ensure_confidential_client(client_id):
    uuid_ = client_uuid(client_id)
    if not uuid_:
        api("POST", f"/realms/{REALM}/clients", {
            "clientId": client_id, "enabled": True,
            "protocol": "openid-connect", "publicClient": False,
            "standardFlowEnabled": False, "implicitFlowEnabled": False,
            "directAccessGrantsEnabled": False,
            "serviceAccountsEnabled": False,
        }, tolerate=(409,))
        uuid_ = client_uuid(client_id)
    return uuid_


mcp_tools_id = ensure_client_scope("mcp:tools")
delpi_aud_scope = ensure_client_scope("audience-delpi")
# ^ reuses the canonical scope that keeps `delpi-central` in aud

for client_id, scope_name, resource_url in SPECIALISTS:
    scope_id = ensure_client_scope(scope_name)
    ensure_audience_mapper(scope_id, resource_url)
    cuuid = ensure_confidential_client(client_id)
    ensure_default_scope(cuuid, mcp_tools_id)
    ensure_default_scope(cuuid, delpi_aud_scope)
    ensure_default_scope(cuuid, scope_id)
    print(f"[kc-bootstrap] resource client {client_id} ok.")

# --- single DÉLIA requester client ---
requester_uuid = client_uuid(REQUESTER)
if not requester_uuid:
    api("POST", f"/realms/{REALM}/clients", {
        "clientId": REQUESTER, "enabled": True,
        "protocol": "openid-connect", "publicClient": False,
        "standardFlowEnabled": False, "implicitFlowEnabled": False,
        "directAccessGrantsEnabled": False,
        "serviceAccountsEnabled": False,
        "attributes": {"standard.token.exchange.enabled": "true"},
    }, tolerate=(409,))
    requester_uuid = client_uuid(REQUESTER)
else:
    st, full = api("GET", f"/realms/{REALM}/clients/{requester_uuid}")
    attrs = full.get("attributes", {})
    if attrs.get("standard.token.exchange.enabled") != "true":
        attrs["standard.token.exchange.enabled"] = "true"
        full["attributes"] = attrs
        api("PUT", f"/realms/{REALM}/clients/{requester_uuid}", full)
print(f"[kc-bootstrap] requester client {REQUESTER} ok.")

# --- Portal subject eligibility: delia-api audience on portal token ---
portal_uuid = client_uuid(PORTAL)
st, mappers = api(
    "GET", f"/realms/{REALM}/clients/{portal_uuid}/protocol-mappers/models")
if not any(
    m["protocolMapper"] == "oidc-audience-mapper"
    and m.get("config", {}).get("included.custom.audience") == REQUESTER
    for m in mappers
):
    api("POST",
        f"/realms/{REALM}/clients/{portal_uuid}/protocol-mappers/models",
        {"name": "delia-requester-audience",
         "protocol": "openid-connect",
         "protocolMapper": "oidc-audience-mapper",
         "config": {"included.custom.audience": REQUESTER,
                    "id.token.claim": "false",
                    "access.token.claim": "true"}})
    print("[kc-bootstrap] portal token now carries delia-api requester aud.")

# --- per-target token-exchange permission bound to delia-api ---
rm_uuid = client_uuid("realm-management")
st, existing = api(
    "GET",
    f"/realms/{REALM}/clients/{rm_uuid}/authz/resource-server/policy"
    "?name=delia-exchange-requester")
policy_id = existing[0]["id"] if existing else None
if policy_id is None:
    st, pol = api(
        "POST",
        f"/realms/{REALM}/clients/{rm_uuid}/authz/resource-server/policy/client",
        {"name": "delia-exchange-requester", "type": "client",
         "logic": "POSITIVE", "decisionStrategy": "UNANIMOUS",
         "clients": [requester_uuid]}, tolerate=(409,))
    policy_id = pol["id"] if isinstance(pol, dict) else client_uuid(REQUESTER) and \
        api("GET",
            f"/realms/{REALM}/clients/{rm_uuid}/authz/resource-server/policy"
            "?name=delia-exchange-requester")[1][0]["id"]
print("[kc-bootstrap] delia-exchange-requester policy ok.")

for client_id, _scope, _url in SPECIALISTS:
    cuuid = client_uuid(client_id)
    api("PUT", f"/realms/{REALM}/clients/{cuuid}/management/permissions",
        {"enabled": True})
    st, mgmt = api(
        "GET", f"/realms/{REALM}/clients/{cuuid}/management/permissions")
    perm_id = mgmt["scopePermissions"]["token-exchange"]
    resource_id = mgmt["resource"]
    st, assoc = api(
        "GET",
        f"/realms/{REALM}/clients/{rm_uuid}/authz/resource-server/"
        f"permission/scope/{perm_id}/associatedPolicies")
    if any(p["id"] == policy_id for p in (assoc or [])):
        print(f"[kc-bootstrap] {client_id} token-exchange permission already bound.")
        continue
    st, scopes = api(
        "GET",
        f"/realms/{REALM}/clients/{rm_uuid}/authz/resource-server/"
        f"permission/scope/{perm_id}/scopes")
    scope_ids = [s["id"] for s in (scopes or [])]
    api(
        "PUT",
        f"/realms/{REALM}/clients/{rm_uuid}/authz/resource-server/"
        f"permission/scope/{perm_id}",
        {"id": perm_id,
         "name": f"token-exchange.permission.client.{cuuid}",
         "type": "scope", "logic": "POSITIVE",
         "decisionStrategy": "UNANIMOUS",
         "policies": [p["id"] for p in (assoc or [])] + [policy_id],
         "resources": [resource_id],
         "scopes": scope_ids})
    print(f"[kc-bootstrap] {client_id} token-exchange permission bound to delia-api.")

# --- requester secret → gitignored infra/.env ---
st, sec = api("GET", f"/realms/{REALM}/clients/{requester_uuid}/client-secret")
secret = sec["value"]
lines = []
try:
    with open(SECRET_STORE, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
except FileNotFoundError:
    pass
key = "DELIA_EXCHANGE_CLIENT_SECRET"
out, replaced = [], False
for line in lines:
    if line.startswith(key + "="):
        out.append(f"{key}={secret}")
        replaced = True
    else:
        out.append(line)
if not replaced:
    out.append(f"{key}={secret}")
with open(SECRET_STORE, "w", encoding="utf-8") as fh:
    fh.write("\n".join(out) + "\n")
print("[kc-bootstrap] DELIA_EXCHANGE_CLIENT_SECRET upserted in infra/.env.")
PY

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
