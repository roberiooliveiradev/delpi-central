#!/usr/bin/env bash
# Isolated OpenRouter eval container + real HTTP two-turn E2E.
# Reuses the env contract of run_int1_openrouter_qwen14b_instrumented_eval.sh.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL_NAME="delpi-delia-eval-http-mt"
ARTIFACT_DIR="${REPO_ROOT}/delia-api/.battery/c3-t2-http-multiturn-live"
EVAL_ENV="$(mktemp /tmp/delia-eval-http-mt-env.XXXXXX)"
PROD_STARTED_BEFORE="$(docker inspect -f '{{.State.StartedAt}}' delpi-delia-api 2>/dev/null || echo missing)"

mkdir -p "${ARTIFACT_DIR}"
chmod 700 "${ARTIFACT_DIR}" || true

cleanup() {
  set +e
  if docker inspect "${EVAL_NAME}" >/dev/null 2>&1; then
    docker rm -f "${EVAL_NAME}" >/dev/null 2>&1 || true
  fi
  rm -f "${EVAL_ENV}"
  PROD_STARTED_AFTER="$(docker inspect -f '{{.State.StartedAt}}' delpi-delia-api 2>/dev/null || echo missing)"
  echo "PROD_STARTED_BEFORE=${PROD_STARTED_BEFORE}"
  echo "PROD_STARTED_AFTER=${PROD_STARTED_AFTER}"
  if [[ "${PROD_STARTED_BEFORE}" == "${PROD_STARTED_AFTER}" ]]; then
    echo "PROD_CONTAINER_UNTOUCHED=YES"
  else
    echo "PROD_CONTAINER_UNTOUCHED=NO"
  fi
}
trap cleanup EXIT

: >"${EVAL_ENV}"
chmod 600 "${EVAL_ENV}"

{
  echo "DELIA_ENV=development"
  echo "DELIA_EVAL_EGRESS_AUTHORIZED=1"
  echo "DELIA_EVAL_ALLOWED_LLM_HOSTS=openrouter.ai"
  echo "DELIA_RUNTIME_PROFILE=openrouter_qwen"
  echo "DELIA_TWO_AGENT_EXPERIMENT=${DELIA_EVAL_TWO_AGENT:-true}"
  echo "DELIA_LLM_BASE_URL=https://openrouter.ai/api/v1"
  echo "KEYCLOAK_URL=http://keycloak:8080/auth"
  echo "KEYCLOAK_REALM=delpi"
  echo "KEYCLOAK_ISSUER=${DELIA_EVAL_KEYCLOAK_ISSUER:-http://localhost/auth/realms/delpi}"
  echo "KEYCLOAK_JWKS_URL=http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/certs"
  echo "KEYCLOAK_AUDIENCE=delpi-central"
  echo "KC_GATEWAY_TOKEN_BASE=${DELIA_EVAL_KC_GATEWAY_TOKEN_BASE:-http://delpi-gateway/auth}"
  echo "DELIA_EVAL_TOKEN_HOST=${DELIA_EVAL_TOKEN_HOST:-localhost}"
  echo "CORE_API_URL=http://core-api:8000"
  echo "DELPI_AUTH_CORE_API_URL=http://core-api:8000"
  echo "DELIA_MCP_DAVI_BASE_URL=${DELIA_EVAL_DAVI_BASE_URL:-http://delpi-api-delpi:8000/mcp}"
  echo "DELIA_MCP_DAVI_ENABLED=true"
  echo "DELIA_MCP_DAVI_HOST_HEADER=localhost:8000"
  echo "DELIA_MCP_TEO_BASE_URL=${DELIA_EVAL_TEO_BASE_URL:-http://transformometro-api:8000/mcp}"
  echo "DELIA_MCP_TEO_ENABLED=true"
  echo "DELIA_MCP_TEO_HOST_HEADER=localhost:8000"
  echo "DELIA_MCP_VISTA_BASE_URL=${DELIA_EVAL_VISTA_BASE_URL:-http://tv-dashboard-api:8000/mcp}"
  echo "DELIA_MCP_VISTA_ENABLED=true"
  echo "DELIA_MCP_VISTA_HOST_HEADER=localhost:8000"
  echo "DELIA_MCP_PROVIDER_REGISTRY_MODE=core"
  echo "DELIA_C4_DAVI_PRODUCT_READ_ENABLED=1"
  echo "DELIA_C4_TEO_DASHBOARD_ANALYZE_ENABLED=1"
  echo "DELIA_EXCHANGE_CLIENT_ID=delia-api"
  echo "DELIA_TOKEN_EXCHANGE_URL=${DELIA_EVAL_TOKEN_EXCHANGE_URL:-http://delpi-gateway/auth/realms/delpi/protocol/openid-connect/token}"
  echo "VITE_KC_CLIENT_ID=delpi-central"
  echo "DELIA_APP_ROOT=/app"
} >>"${EVAL_ENV}"

python3 - <<PY
from pathlib import Path
src = Path("${REPO_ROOT}") / "infra" / ".env"
dst = Path("${EVAL_ENV}")
wanted = {
    "DELIA_LLM_API_KEY",
    "DELIA_EXCHANGE_CLIENT_SECRET",
    "KEYCLOAK_REALM",
    "DEV_PORTAL_USERNAME",
    "DEV_PORTAL_PASSWORD",
    "KIMI_API_KEY",
    "DELIA_STT_API_KEY",
    "CORE_API_INTEGRATIONS_SERVICE_TOKEN",
    "DELIA_CORE_INTEGRATIONS_SERVICE_TOKEN",
}
values = {}
if src.is_file():
    for line in src.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key in wanted and val.strip():
            values[key] = val.strip()

def _is_openrouter_key(raw: str) -> bool:
    return raw.startswith("sk-or-") and len(raw) >= 20

llm_key = values.get("DELIA_LLM_API_KEY", "")
llm_source = "DELIA_LLM_API_KEY"
if not _is_openrouter_key(llm_key):
    for alt in ("KIMI_API_KEY", "DELIA_STT_API_KEY"):
        cand = values.get(alt, "")
        if _is_openrouter_key(cand):
            llm_key = cand
            llm_source = alt
            break
values["DELIA_LLM_API_KEY"] = llm_key
emit_keys = [
    "DELIA_LLM_API_KEY",
    "DELIA_EXCHANGE_CLIENT_SECRET",
    "KEYCLOAK_REALM",
    "DEV_PORTAL_USERNAME",
    "DEV_PORTAL_PASSWORD",
    "CORE_API_INTEGRATIONS_SERVICE_TOKEN",
    "DELIA_CORE_INTEGRATIONS_SERVICE_TOKEN",
]
found = set()
with dst.open("a", encoding="utf-8") as fh:
    for key in emit_keys:
        val = values.get(key, "")
        if not val:
            continue
        fh.write(f"{key}={val}\\n")
        found.add(key)
print("SELECTIVE_KEYS_LOADED=" + ",".join(sorted(found)))
print(f"LLM_KEY_SOURCE={llm_source}")
if not _is_openrouter_key(llm_key):
    raise SystemExit("missing OpenRouter API key")
required = {
    "DELIA_LLM_API_KEY",
    "DELIA_EXCHANGE_CLIENT_SECRET",
    "DEV_PORTAL_USERNAME",
    "DEV_PORTAL_PASSWORD",
}
missing = required - found
if missing:
    raise SystemExit("missing keys: " + ",".join(sorted(missing)))
if (
    "CORE_API_INTEGRATIONS_SERVICE_TOKEN" not in found
    and "DELIA_CORE_INTEGRATIONS_SERVICE_TOKEN" not in found
):
    raise SystemExit("missing CORE integrations service token")
print(
    "INTEGRATIONS_TOKEN=present"
)
PY

NETWORK="$(docker inspect delpi-delia-api --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')"
if docker inspect "${EVAL_NAME}" >/dev/null 2>&1; then
  docker rm -f "${EVAL_NAME}" >/dev/null
fi

docker run -d \
  --name "${EVAL_NAME}" \
  --network "${NETWORK}" \
  --env-file "${EVAL_ENV}" \
  -v "${REPO_ROOT}/delia-api:/app" \
  -w /app \
  infra-delia-api \
  sleep infinity >/dev/null

EVAL_ID="$(docker inspect -f '{{.Id}}' "${EVAL_NAME}" | cut -c1-12)"
PROD_ID="$(docker inspect -f '{{.Id}}' delpi-delia-api | cut -c1-12)"
echo "EVAL_CONTAINER=${EVAL_NAME} id=${EVAL_ID}"
echo "PROD_CONTAINER_ID=${PROD_ID}"
if [[ "${EVAL_ID}" == "${PROD_ID}" ]]; then
  echo "DEV_RUNTIME_ISOLATION=FAIL"
  exit 4
fi
echo "DEV_RUNTIME_ISOLATION=PROVEN_PROCESS_SEPARATION"

docker exec -i -e DELIA_APP_ROOT=/app "${EVAL_NAME}" python - <<'PY'
from app.infrastructure.config.settings import Settings
from urllib.parse import urlsplit
s = Settings()
host = urlsplit(s.llm_base_url or "").hostname or ""
print("baseline_model", s.llm_model)
print("baseline_host", host)
print("baseline_fp", s.runtime_config_fingerprint)
print("two_agent", s.two_agent_experiment)
assert host == "openrouter.ai"
assert s.llm_model == "qwen/qwen3-14b"
assert s.llm_egress_blocked_reason is None
print("BASELINE_CONFIG=OK")
PY

# Unset DELIA_EVAL_HTTP_BASE so the script boots local WSGI create_app().
docker exec -i \
  -e DELIA_APP_ROOT=/app \
  -e DELIA_TWO_AGENT_EXPERIMENT=true \
  "${EVAL_NAME}" \
  env -u DELIA_EVAL_HTTP_BASE \
  python scripts/c3_t2_http_multiturn_live_eval.py \
  | tee "${ARTIFACT_DIR}/http-multiturn-live.json"

echo "ARTIFACT=${ARTIFACT_DIR}/http-multiturn-live.json"
echo "EVAL_COMPLETE=YES"
