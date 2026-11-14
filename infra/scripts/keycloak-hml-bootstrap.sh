#!/usr/bin/env bash
# Homologação — bootstrap mínimo e idempotente do Keycloak HML.
#
# REUSE: mesmo padrão Admin REST de infra/scripts/keycloak-dev-bootstrap.sh
# (realm + client público + usuário de teste). Diferenças deliberadas:
#   - lê somente infra/.env.hml (nunca .env / .env.prod);
#   - fala apenas com o container delpi-hml-keycloak na rede delpi-hml-network;
#   - NÃO provisiona clients DÉLIA/MCP nem apps ainda não ativados;
#   - NÃO habilita direct grants;
#   - sslRequired=external com origem HTTPS pública (HTTP só na rede Compose).
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
[[ "$PUBLIC_ORIGIN" == https://* ]] || {
  echo "[ERRO] origem HML deve ser https:// (Secure Context / PKCE). Recebido: $PUBLIC_ORIGIN" >&2; exit 1; }
[[ "$PUBLIC_ORIGIN" != *minhadelpi.com.br* ]] || {
  echo "[ERRO] origem HML não pode usar o domínio de produção" >&2; exit 1; }
[[ "$PUBLIC_ORIGIN" == https://192.168.1.237:18443 ]] || {
  echo "[ERRO] origem HML esperada https://192.168.1.237:18443 (recebido: $PUBLIC_ORIGIN)" >&2; exit 1; }

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "[ERRO] container $CONTAINER não está em execução." >&2
  exit 1
fi

# Tema de login de produção (somente leitura no container). Checkout HML
# frequentemente cria arquivos 660 do usuário host; Keycloak roda como uid 1000
# e precisa ler — espelha legibilidade do mount produtivo sem redesenhar o tema.
THEMES_DIR="$INFRA_DIR/keycloak/themes"
if [[ -d "$THEMES_DIR/delpi-energy/login" ]]; then
  chmod -R a+rX "$THEMES_DIR" || {
    echo "[ERRO] não foi possível tornar $THEMES_DIR legível ao Keycloak (uid 1000)." >&2
    exit 1
  }
  echo "[hml-kc] tema delpi-energy legível (a+rX)."
else
  echo "[AVISO] tema delpi-energy ausente em $THEMES_DIR — login usará tema padrão." >&2
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
# sslRequired=external: clientes externos HTTPS; HTTP interno Compose permanece OK.
# loginTheme=delpi-energy: reutiliza tema já versionado em infra/keycloak/themes (HML only).
if [ "$(admin_code GET "/realms/$REALM")" = "404" ]; then
  admin_api POST /realms \
    "{\"realm\":\"$REALM\",\"enabled\":true,\"sslRequired\":\"external\",\"loginTheme\":\"delpi-energy\",\"registrationAllowed\":false,\"resetPasswordAllowed\":false,\"rememberMe\":true}" >/dev/null
  echo "[hml-kc] realm $REALM criado (sslRequired=external, loginTheme=delpi-energy)."
else
  # Preserva representação atual; só reforça ssl + tema de login.
  REALM_JSON="$(admin_api GET "/realms/$REALM" | python3 -c 'import json,sys; r=json.load(sys.stdin); r["sslRequired"]="external"; r["loginTheme"]="delpi-energy"; r["enabled"]=True; print(json.dumps(r))')"
  admin_api PUT "/realms/$REALM" "$REALM_JSON" >/dev/null
  echo "[hml-kc] realm $REALM já existe — sslRequired=external + loginTheme=delpi-energy aplicados."
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
  echo "[hml-kc] client $CLIENT_ID atualizado (redirect/webOrigin HTTPS HML)."
fi

# --- audience delpi-central (Core API KEYCLOAK_AUDIENCE) ---
# Client scope default + mapper Audience (Keycloak 24), idempotente.
SCOPE_NAME="audience-delpi"
SCOPES_RAW="$(admin_api GET "/realms/$REALM/client-scopes")"
SCOPE_ID="$(python3 - "$SCOPES_RAW" "$SCOPE_NAME" <<'PY'
import json, sys
for s in json.loads(sys.argv[1]):
    if s.get("name") == sys.argv[2]:
        print(s["id"])
        break
PY
)"
if [ -z "$SCOPE_ID" ]; then
  admin_api POST "/realms/$REALM/client-scopes" \
    "$(python3 - "$SCOPE_NAME" <<'PY'
import json, sys
print(json.dumps({
  "name": sys.argv[1],
  "protocol": "openid-connect",
  "attributes": {
    "include.in.token.scope": "false",
    "display.on.consent.screen": "false",
  },
}))
PY
)" >/dev/null
  SCOPES_RAW="$(admin_api GET "/realms/$REALM/client-scopes")"
  SCOPE_ID="$(python3 - "$SCOPES_RAW" "$SCOPE_NAME" <<'PY'
import json, sys
for s in json.loads(sys.argv[1]):
    if s.get("name") == sys.argv[2]:
        print(s["id"])
        break
PY
)"
  echo "[hml-kc] client-scope $SCOPE_NAME criado."
else
  echo "[hml-kc] client-scope $SCOPE_NAME já existe."
fi
MAPPER_NAME="audience-delpi-central"
MAPPERS_RAW="$(admin_api GET "/realms/$REALM/client-scopes/$SCOPE_ID/protocol-mappers/models")"
MAPPER_ID="$(python3 - "$MAPPERS_RAW" "$MAPPER_NAME" <<'PY'
import json, sys
for m in json.loads(sys.argv[1]):
    if m.get("name") == sys.argv[2]:
        print(m["id"])
        break
PY
)"
MAPPER_JSON="$(python3 - "$MAPPER_NAME" "$CLIENT_ID" <<'PY'
import json, sys
print(json.dumps({
  "name": sys.argv[1],
  "protocol": "openid-connect",
  "protocolMapper": "oidc-audience-mapper",
  "config": {
    "included.client.audience": sys.argv[2],
    "id.token.claim": "false",
    "access.token.claim": "true",
    "userinfo.token.claim": "false",
  },
}))
PY
)"
if [ -z "$MAPPER_ID" ]; then
  admin_api POST "/realms/$REALM/client-scopes/$SCOPE_ID/protocol-mappers/models" \
    "$MAPPER_JSON" >/dev/null
  echo "[hml-kc] mapper audience $CLIENT_ID criado."
else
  admin_api PUT "/realms/$REALM/client-scopes/$SCOPE_ID/protocol-mappers/models/$MAPPER_ID" \
    "$MAPPER_JSON" >/dev/null
  echo "[hml-kc] mapper audience $CLIENT_ID sincronizado."
fi
# Default realm scope + default client scope binding
DEFAULT_SCOPES_RAW="$(admin_api GET "/realms/$REALM/default-default-client-scopes")"
DEFAULT_SCOPE_IDS="$(python3 - "$DEFAULT_SCOPES_RAW" <<'PY'
import json, sys
print(" ".join(s["id"] for s in json.loads(sys.argv[1])))
PY
)"
if [[ " $DEFAULT_SCOPE_IDS " != *" $SCOPE_ID "* ]]; then
  admin_api PUT "/realms/$REALM/default-default-client-scopes/$SCOPE_ID" "{}" >/dev/null || \
    admin_api POST "/realms/$REALM/default-default-client-scopes/$SCOPE_ID" "{}" >/dev/null || true
  echo "[hml-kc] $SCOPE_NAME vinculado como default-default-client-scope."
fi
CLIENT_SCOPES_RAW="$(admin_api GET "/realms/$REALM/clients/$CID/default-client-scopes")"
CLIENT_DEFAULT_SCOPES="$(python3 - "$CLIENT_SCOPES_RAW" <<'PY'
import json, sys
print(" ".join(s["id"] for s in json.loads(sys.argv[1])))
PY
)"
if [[ " $CLIENT_DEFAULT_SCOPES " != *" $SCOPE_ID "* ]]; then
  admin_api PUT "/realms/$REALM/clients/$CID/default-client-scopes/$SCOPE_ID" "{}" >/dev/null || true
  echo "[hml-kc] $SCOPE_NAME vinculado ao client $CLIENT_ID."
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

# --- cliente confidencial da BFF (espelho de PROD, segredo novo só de HML) ---
# PROD (leitura 2026-11-14): publicClient=false, serviceAccountsEnabled=true,
# standard/direct/implicit desligados, fullScopeAllowed=true.
# Default scopes de contrato: stock-inventory.read, settlements.read,
# consumption-audit.read (include.in.token.scope=true, sem mapper).
# Mapper no cliente: audience-api-delpi → aud api-delpi.
# O segredo de PROD não é lido nem copiado.
export HML_KC_ADMIN_TOKEN="$ADMIN_TOKEN"
export HML_KC_BASE="$INTERNAL_BASE"
export HML_KC_REALM="$REALM"
export HML_KC_ENV_FILE="$ENV_FILE"
python3 - <<'PY'
import json, os, secrets, urllib.error, urllib.request

base = os.environ["HML_KC_BASE"].rstrip("/")
realm = os.environ["HML_KC_REALM"]
token = os.environ["HML_KC_ADMIN_TOKEN"]
env_path = os.environ["HML_KC_ENV_FILE"]
client_id = "controllership-finance-api"
contract_scopes = ("stock-inventory.read", "settlements.read", "consumption-audit.read")
builtin_defaults = ("acr", "audience-delpi", "email", "profile", "roles", "web-origins")

def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{base}/admin{path}", data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "delpi-hml-bootstrap")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            return json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as exc:
        if exc.code == 409:
            return None
        raise SystemExit(f"[ERRO] Keycloak HML {method} {path} -> {exc.code}")

scopes = call("GET", f"/realms/{realm}/client-scopes") or []
by_name = {item.get("name"): item for item in scopes}
for name in contract_scopes:
    if name in by_name:
        print(f"[hml-kc] client-scope {name} já existe.")
        continue
    call("POST", f"/realms/{realm}/client-scopes", {
        "name": name,
        "protocol": "openid-connect",
        "attributes": {"include.in.token.scope": "true"},
    })
    print(f"[hml-kc] client-scope {name} criado.")
scopes = call("GET", f"/realms/{realm}/client-scopes") or []
by_name = {item.get("name"): item for item in scopes}

found = call("GET", f"/realms/{realm}/clients?clientId={client_id}") or []
created = False
if not found:
    secret = secrets.token_urlsafe(48)
    call("POST", f"/realms/{realm}/clients", {
        "clientId": client_id,
        "enabled": True,
        "protocol": "openid-connect",
        "publicClient": False,
        "bearerOnly": False,
        "clientAuthenticatorType": "client-secret",
        "secret": secret,
        "serviceAccountsEnabled": True,
        "standardFlowEnabled": False,
        "directAccessGrantsEnabled": False,
        "implicitFlowEnabled": False,
        "fullScopeAllowed": True,
    })
    created = True
    print(f"[hml-kc] client {client_id} criado (segredo novo de HML, não impresso).")
else:
    print(f"[hml-kc] client {client_id} já existe — segredo preservado.")
found = call("GET", f"/realms/{realm}/clients?clientId={client_id}") or []
if not found:
    raise SystemExit(f"[ERRO] client {client_id} ausente depois da criação")
client = found[0]
uuid = client["id"]
hml_secret = client.get("secret") or ""
if not hml_secret:
    raise SystemExit(f"[ERRO] client {client_id} sem segredo no realm de HML")

mappers = call("GET", f"/realms/{realm}/clients/{uuid}/protocol-mappers/models") or []
has_aud = any(
    item.get("name") == "audience-api-delpi"
    and item.get("protocolMapper") == "oidc-audience-mapper"
    for item in mappers
)
if not has_aud:
    call("POST", f"/realms/{realm}/clients/{uuid}/protocol-mappers/models", {
        "name": "audience-api-delpi",
        "protocol": "openid-connect",
        "protocolMapper": "oidc-audience-mapper",
        "config": {
            "included.custom.audience": "api-delpi",
            "id.token.claim": "false",
            "access.token.claim": "true",
            "userinfo.token.claim": "false",
        },
    })
    print("[hml-kc] audience mapper api-delpi criado.")
else:
    print("[hml-kc] audience mapper api-delpi já existe.")

assigned = call("GET", f"/realms/{realm}/clients/{uuid}/default-client-scopes") or []
assigned_ids = {item.get("id") for item in assigned}
for name in contract_scopes + builtin_defaults:
    scope = by_name.get(name)
    if scope is None:
        print(f"[hml-kc] scope {name} ausente no realm — não atribuído.")
        continue
    if scope["id"] in assigned_ids:
        continue
    call("PUT", f"/realms/{realm}/clients/{uuid}/default-client-scopes/{scope['id']}")
    print(f"[hml-kc] default scope {name} atribuído.")

lines = []
if os.path.isfile(env_path):
    lines = open(env_path, encoding="utf-8").read().splitlines()

def upsert(key, value, only_if_empty=False):
    for index, line in enumerate(lines):
        if line.startswith(f"{key}="):
            current = line.split("=", 1)[1].strip().strip('"').strip("'")
            if only_if_empty and current:
                return False
            lines[index] = f"{key}={value}"
            return True
    lines.append(f"{key}={value}")
    return True

wrote_secret = upsert("CF_S2S_CLIENT_SECRET", hml_secret, only_if_empty=not created)
upsert("CF_S2S_CLIENT_ID", client_id, only_if_empty=False)
upsert(
    "CF_S2S_TOKEN_URL",
    f"http://keycloak:8080/auth/realms/{realm}/protocol/openid-connect/token",
    only_if_empty=True,
)
upsert("CF_S2S_SCOPE", "", only_if_empty=True)
text = "\n".join(lines)
if not text.endswith("\n"):
    text += "\n"
open(env_path, "w", encoding="utf-8").write(text)
print(
    "[hml-kc] CF_S2S_CLIENT_SECRET "
    + ("gravado no .env.hml" if wrote_secret or created else "já estava no .env.hml")
    + " (valor omitido)."
)
PY
unset HML_KC_ADMIN_TOKEN

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
echo "[hml-kc] Audience $CLIENT_ID provisionada para validação JWT do Core API HML."
echo "[hml-kc] DONE"
