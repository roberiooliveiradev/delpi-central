#!/usr/bin/env bash
# EVAL-ONLY driver: isolated delia-api container + localhost OpenRouter proxy.
# Does NOT restart/reconfigure production delpi-delia-api.
# Reversible: stops eval container and proxy on exit.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL_NAME="delpi-delia-eval-int1"
PROXY_PORT=18765
PROXY_PID=""
PROD_STARTED_BEFORE="$(docker inspect -f '{{.State.StartedAt}}' delpi-delia-api)"
EVAL_ENV="$(mktemp /tmp/delia-eval-env.XXXXXX)"
SCENARIOS_JSON="$(mktemp /tmp/delia-eval-scenarios.XXXXXX)"
ARTIFACT_DIR="${REPO_ROOT}/delia-api/.battery/int1-isolated-qwen-eval"
mkdir -p "${ARTIFACT_DIR}"

cleanup() {
  set +e
  if [[ -n "${PROXY_PID}" ]] && kill -0 "${PROXY_PID}" 2>/dev/null; then
    kill "${PROXY_PID}" 2>/dev/null || true
    wait "${PROXY_PID}" 2>/dev/null || true
  fi
  if docker inspect "${EVAL_NAME}" >/dev/null 2>&1; then
    docker rm -f "${EVAL_NAME}" >/dev/null 2>&1 || true
  fi
  rm -f "${EVAL_ENV}" "${SCENARIOS_JSON}"
  PROD_STARTED_AFTER="$(docker inspect -f '{{.State.StartedAt}}' delpi-delia-api 2>/dev/null || true)"
  echo "PROD_STARTED_BEFORE=${PROD_STARTED_BEFORE}"
  echo "PROD_STARTED_AFTER=${PROD_STARTED_AFTER}"
  if [[ "${PROD_STARTED_BEFORE}" == "${PROD_STARTED_AFTER}" ]]; then
    echo "PROD_CONTAINER_UNTOUCHED=YES"
  else
    echo "PROD_CONTAINER_UNTOUCHED=NO"
  fi
}
trap cleanup EXIT

echo "=== Gate A: isolation setup ==="
echo "PROD_STARTED_BEFORE=${PROD_STARTED_BEFORE}"

# 1) Local OpenRouter egress proxy (loopback host → external provider)
# Bind 0.0.0.0 so containers reaching host.docker.internal can connect;
# 127.0.0.1-only is invisible from the docker bridge.
python3 "${REPO_ROOT}/delia-api/scripts/openrouter_local_egress_proxy.py" \
  --host 0.0.0.0 --port "${PROXY_PORT}" \
  >"${ARTIFACT_DIR}/proxy.log" 2>&1 &
PROXY_PID=$!
sleep 1
if ! kill -0 "${PROXY_PID}" 2>/dev/null; then
  echo "PROXY_START=FAIL"
  cat "${ARTIFACT_DIR}/proxy.log" || true
  exit 3
fi
echo "PROXY_START=OK pid=${PROXY_PID} port=${PROXY_PORT} bind=0.0.0.0"

# 2) Env: copy structural/runtime env from prod process, then override for isolation
docker exec delpi-delia-api printenv | sed 's/\r$//' >"${EVAL_ENV}"
# Drop production identity markers that must not silently apply
grep -vE '^(DELIA_ENV|DELIA_LLM_BASE_URL|DELIA_RUNTIME_PROFILE|HOSTNAME|HOME|PWD|OLDPWD)=' \
  "${EVAL_ENV}" >"${EVAL_ENV}.clean"
mv "${EVAL_ENV}.clean" "${EVAL_ENV}"

# Portal DEV credentials (host-local .env.local) — never echoed
set -a
# shellcheck disable=SC1091
source "${REPO_ROOT}/infra/.env.local"
set +a
{
  echo "DELIA_ENV=development"
  echo "DELIA_RUNTIME_PROFILE=openrouter_qwen"
  echo "DELIA_LLM_BASE_URL=http://host.docker.internal:${PROXY_PORT}/api/v1"
  echo "KC_GATEWAY_TOKEN_BASE=http://delpi-gateway/auth"
  echo "DEV_PORTAL_USERNAME=${DEV_PORTAL_USERNAME}"
  echo "DEV_PORTAL_PASSWORD=${DEV_PORTAL_PASSWORD}"
} >>"${EVAL_ENV}"

chmod 600 "${EVAL_ENV}"

# 3) Temporary eval container — distinct name, same docker network, code mount
if docker inspect "${EVAL_NAME}" >/dev/null 2>&1; then
  docker rm -f "${EVAL_NAME}" >/dev/null
fi
docker run -d \
  --name "${EVAL_NAME}" \
  --network infra_delpi-network \
  --add-host=host.docker.internal:host-gateway \
  --env-file "${EVAL_ENV}" \
  -v "${REPO_ROOT}/delia-api:/app" \
  -v "${SCENARIOS_JSON}:/tmp/int1_scenarios.json:ro" \
  -w /app \
  infra-delia-api \
  sleep infinity >/dev/null

EVAL_ID="$(docker inspect -f '{{.Id}}' "${EVAL_NAME}" | cut -c1-12)"
EVAL_PROJECT_LABEL="$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "${EVAL_NAME}" 2>/dev/null || true)"
echo "EVAL_CONTAINER=${EVAL_NAME} id=${EVAL_ID} compose_project=${EVAL_PROJECT_LABEL:-none}"
echo "EVAL_DELIA_ENV=$(docker exec "${EVAL_NAME}" printenv DELIA_ENV)"
echo "EVAL_PROFILE=$(docker exec "${EVAL_NAME}" printenv DELIA_RUNTIME_PROFILE)"
echo "EVAL_LLM_HOST=$(docker exec "${EVAL_NAME}" printenv DELIA_LLM_BASE_URL | sed 's#https\?://##' | cut -d/ -f1)"

# Prove production identity distinct
PROD_ID="$(docker inspect -f '{{.Id}}' delpi-delia-api | cut -c1-12)"
echo "PROD_CONTAINER_ID=${PROD_ID}"
if [[ "${EVAL_ID}" == "${PROD_ID}" ]]; then
  echo "DEV_RUNTIME_ISOLATION=FAIL reason=same_container_id"
  exit 4
fi
echo "DEV_RUNTIME_ISOLATION=PROVEN_PROCESS_SEPARATION"

# 4) Scenarios: P1 P2 P3 + generalization reword (tool-rename MCP absent → semantic holdout)
cat >"${SCENARIOS_JSON}" <<'JSON'
[
  {"id": "P1_product_structure", "question": "Qual é a estrutura do produto 90260921?"},
  {"id": "P2_transformometro_processes", "question": "Quais processos estão cadastrados no Transformômetro?"},
  {"id": "P3_visualization_formats", "question": "Quais formatos de visualização de dados estão disponíveis?"},
  {"id": "G1_semantic_reword_structure", "question": "Mostre a árvore de componentes e relações do item 90260921."}
]
JSON

# 5) Baseline: model + pydantic + egress allow via proxy host
docker exec -i -e DELIA_APP_ROOT=/app "${EVAL_NAME}" python - <<'PY'
from app.infrastructure.config.settings import Settings
s = Settings()
print("baseline_env", s.environment)
print("baseline_profile", s.runtime_profile)
print("baseline_model", s.llm_model)
print("baseline_fp", s.runtime_config_fingerprint)
print("baseline_egress", s.llm_egress_blocked_reason or "allowed")
print("baseline_base_host", (s.llm_base_url or "").split("://", 1)[-1].split("/", 1)[0])
print("baseline_key_set", bool(s.llm_api_key))
import pydantic_ai
print("baseline_pydantic_ai", pydantic_ai.__version__)
assert s.environment != "production"
assert s.llm_model == "qwen/qwen3-14b"
assert s.llm_egress_blocked_reason is None
assert s.llm_api_key
print("BASELINE_CONFIG=OK")
PY

# Tiny real-model ping (no MCP) — proves Qwen path through proxy
docker exec -i -e DELIA_APP_ROOT=/app "${EVAL_NAME}" python - <<'PY'
from app.infrastructure.config.settings import Settings
from openai import OpenAI
s = Settings()
client = OpenAI(base_url=s.llm_base_url, api_key=s.llm_api_key, timeout=60.0)
resp = client.chat.completions.create(
    model=s.llm_model,
    messages=[{"role": "user", "content": "Responda apenas: pong"}],
    max_tokens=16,
)
text = (resp.choices[0].message.content or "").strip()
print("MODEL_PING", text[:80])
print("MODEL_PING_OK", bool(text))
PY

# 6) Full investigation harness (real Agent + MCP)
SCENARIO_PAYLOAD="$(cat "${SCENARIOS_JSON}")"
docker exec \
  -e DELIA_APP_ROOT=/app \
  -e "DELIA_EVAL_SCENARIOS_JSON=${SCENARIO_PAYLOAD}" \
  "${EVAL_NAME}" \
  python scripts/native_mcptoolset_direct_eval.py \
  | tee "${ARTIFACT_DIR}/eval-output.jsonl"

echo "EVAL_COMPLETE=YES"
echo "ARTIFACT_DIR=${ARTIFACT_DIR}"
