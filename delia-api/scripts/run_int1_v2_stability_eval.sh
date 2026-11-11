#!/usr/bin/env bash
# INT-1 v2 STABILITY diagnostic eval on OpenRouter qwen/qwen3-14b.
# Baseline-only; no instruction candidate; no functional Agent change.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL_NAME="delpi-delia-eval-int1-v2-stab"
ARTIFACT_DIR="${REPO_ROOT}/delia-api/.battery/int1-v2-stability"
TRACE_DIR="${REPO_ROOT}/delia-api/.battery/int1-secure-decision-trace"
EVAL_ENV="$(mktemp /tmp/delia-eval-stab-env.XXXXXX)"
PROD_STARTED_BEFORE="$(docker inspect -f '{{.State.StartedAt}}' delpi-delia-api 2>/dev/null || echo missing)"

mkdir -p "${ARTIFACT_DIR}" "${TRACE_DIR}"
chmod 700 "${ARTIFACT_DIR}" "${TRACE_DIR}" || true
: >"${ARTIFACT_DIR}/harness-run.log"

cleanup() {
  set +e
  docker rm -f "${EVAL_NAME}" >/dev/null 2>&1 || true
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

echo "=== INT-1 v2 STABILITY diagnostic eval (OpenRouter qwen14b) ==="
: >"${EVAL_ENV}"
chmod 600 "${EVAL_ENV}"
{
  echo "DELIA_ENV=development"
  echo "DELIA_EVAL_EGRESS_AUTHORIZED=1"
  echo "DELIA_EVAL_ALLOWED_LLM_HOSTS=openrouter.ai"
  echo "DELIA_RUNTIME_PROFILE=openrouter_qwen"
  echo "DELIA_LLM_BASE_URL=https://openrouter.ai/api/v1"
  echo "KEYCLOAK_URL=http://keycloak:8080/auth"
  echo "KEYCLOAK_REALM=delpi"
  echo "KEYCLOAK_ISSUER=http://localhost/auth/realms/delpi"
  echo "KEYCLOAK_JWKS_URL=http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/certs"
  echo "KEYCLOAK_AUDIENCE=delpi-central"
  echo "KC_GATEWAY_TOKEN_BASE=http://delpi-gateway/auth"
  echo "CORE_API_URL=http://core-api:8000"
  echo "DELPI_AUTH_CORE_API_URL=http://core-api:8000"
  echo "DELIA_MCP_DAVI_BASE_URL=http://delpi-api-delpi:8000/mcp"
  echo "DELIA_MCP_DAVI_ENABLED=true"
  echo "DELIA_MCP_DAVI_HOST_HEADER=localhost:8000"
  echo "DELIA_MCP_TEO_BASE_URL=http://transformometro-api:8000/mcp"
  echo "DELIA_MCP_TEO_ENABLED=true"
  echo "DELIA_MCP_TEO_HOST_HEADER=localhost:8000"
  echo "DELIA_MCP_VISTA_BASE_URL=http://tv-dashboard-api:8000/mcp"
  echo "DELIA_MCP_VISTA_ENABLED=true"
  echo "DELIA_MCP_VISTA_HOST_HEADER=localhost:8000"
  echo "DELIA_MCP_PROVIDER_REGISTRY_MODE=core"
  echo "DELIA_C4_DAVI_PRODUCT_READ_ENABLED=1"
  echo "DELIA_C4_TEO_DASHBOARD_ANALYZE_ENABLED=1"
  echo "DELIA_EXCHANGE_CLIENT_ID=delia-api"
  echo "DELIA_TOKEN_EXCHANGE_URL=http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/token"
  echo "VITE_KC_CLIENT_ID=delpi-central"
  echo "DELIA_APP_ROOT=/app"
  echo "DELIA_INVESTIGATION_INSTRUCTION_VERSION=generalist-semantic-v2"
} >>"${EVAL_ENV}"

python3 - <<PY
from pathlib import Path
src = Path("${REPO_ROOT}") / "infra" / ".env"
dst = Path("${EVAL_ENV}")
wanted = {"DELIA_LLM_API_KEY", "DELIA_EXCHANGE_CLIENT_SECRET", "KEYCLOAK_REALM"}
found = set()
for line in src.read_text(encoding="utf-8", errors="replace").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, _, val = line.partition("=")
    key = key.strip()
    if key in wanted and val.strip():
        dst.open("a", encoding="utf-8").write(f"{key}={val}\n")
        found.add(key)
print("SELECTIVE_KEYS_LOADED=" + ",".join(sorted(found)))
if "DELIA_LLM_API_KEY" not in found or "DELIA_EXCHANGE_CLIENT_SECRET" not in found:
    raise SystemExit("missing selective secrets")
PY

set -a
# shellcheck disable=SC1091
source "${REPO_ROOT}/infra/.env.local"
set +a
{
  echo "DEV_PORTAL_USERNAME=${DEV_PORTAL_USERNAME}"
  echo "DEV_PORTAL_PASSWORD=${DEV_PORTAL_PASSWORD}"
} >>"${EVAL_ENV}"

if [[ "$(docker inspect -f '{{.State.Status}}' delpi-keycloak 2>/dev/null || echo missing)" != "running" ]]; then
  docker start delpi-keycloak >/dev/null
  sleep 8
fi

NETWORK="$(docker inspect delpi-delia-api --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')"
docker rm -f "${EVAL_NAME}" >/dev/null 2>&1 || true
docker run -d \
  --name "${EVAL_NAME}" \
  --network "${NETWORK}" \
  --env-file "${EVAL_ENV}" \
  -e "DELIA_EVAL_TRACE_DIR=/traces" \
  -e "DELIA_EVAL_ARTIFACT_DIR=/traces/artifacts" \
  -v "${REPO_ROOT}/delia-api:/app" \
  -v "${TRACE_DIR}:/traces" \
  -v "${ARTIFACT_DIR}:/traces/artifacts" \
  -w /app \
  infra-delia-api \
  sleep infinity >/dev/null

EVAL_ID="$(docker inspect -f '{{.Id}}' "${EVAL_NAME}" | cut -c1-12)"
PROD_ID="$(docker inspect -f '{{.Id}}' delpi-delia-api | cut -c1-12)"
echo "DEV_RUNTIME_ISOLATION=PROVEN_PROCESS_SEPARATION eval=${EVAL_ID} prod=${PROD_ID}"
[[ "${EVAL_ID}" != "${PROD_ID}" ]]

docker exec -i -e DELIA_APP_ROOT=/app "${EVAL_NAME}" python - <<'PY'
from app.infrastructure.config.settings import Settings
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    load_selected_investigation_instructions,
)
from urllib.parse import urlsplit
import pydantic_ai
s = Settings()
assert s.environment == "development"
assert s.runtime_profile == "openrouter_qwen"
assert s.llm_model == "qwen/qwen3-14b"
assert urlsplit(s.llm_base_url or "").hostname == "openrouter.ai"
assert s.llm_egress_blocked_reason is None
assert pydantic_ai.__version__ == "2.50.0"
b = load_selected_investigation_instructions(
    instruction_version="generalist-semantic-v2"
)
assert b.text_fingerprint == "7dbc94c5035b0f19"
print("BASELINE_FP", b.text_fingerprint)
print("INSTRUCTION_ONLY_V2=OK")
print("BASELINE_CONFIG=OK")
PY

docker exec -i -e DELIA_APP_ROOT=/app "${EVAL_NAME}" \
  python scripts/int1_secure_decision_trace.py --check-security-gate \
  | tee "${ARTIFACT_DIR}/security-gate.json"
python3 - <<PY
import json, pathlib, sys
data = json.loads(pathlib.Path("${ARTIFACT_DIR}/security-gate.json").read_text())
if data.get("SECURE_EVAL_GATE") != "READY_FOR_ISOLATED_EVAL":
    print(data); sys.exit(5)
print("SECURITY_GATE=READY")
print("CREDENTIAL_SCOPE_RESIDUAL=", data.get("EVALUATION_CREDENTIAL_SCOPE"))
PY

EVALUATED_SHA="$(git -C "${REPO_ROOT}" rev-parse HEAD)"
RUNTIME_IMAGE_ID="$(docker inspect -f '{{.Image}}' delpi-delia-api)"
RUNTIME_IMAGE_DIGEST="$(docker image inspect "${RUNTIME_IMAGE_ID}" --format '{{index .RepoDigests 0}}' 2>/dev/null || true)"
if [[ -z "${RUNTIME_IMAGE_DIGEST}" ]]; then
  RUNTIME_IMAGE_DIGEST="infra-delia-api@${RUNTIME_IMAGE_ID}"
fi
RUNTIME_CONTAINER_ID="$(docker inspect -f '{{.Id}}' "${EVAL_NAME}")"
PROD_CONTAINER_ID="$(docker inspect -f '{{.Id}}' delpi-delia-api)"
echo "EVALUATED_SHA=${EVALUATED_SHA}"
echo "RUNTIME_IMAGE_ID=${RUNTIME_IMAGE_ID}"
echo "RUNTIME_IMAGE_DIGEST=${RUNTIME_IMAGE_DIGEST}"
echo "RUNTIME_CONTAINER_ID=${RUNTIME_CONTAINER_ID}"

python3 - <<PY
import json, pathlib
p = pathlib.Path("${ARTIFACT_DIR}") / "host-freeze.json"
p.write_text(json.dumps({
  "evaluated_sha": "${EVALUATED_SHA}",
  "runtime_image_id": "${RUNTIME_IMAGE_ID}",
  "runtime_image_digest": "${RUNTIME_IMAGE_DIGEST}",
  "runtime_container_id": "${RUNTIME_CONTAINER_ID}",
  "prod_container_id": "${PROD_CONTAINER_ID}",
  "instruction_version": "generalist-semantic-v2",
  "expected_fingerprint": "7dbc94c5035b0f19",
  "model_id": "qwen/qwen3-14b",
  "model_profile": "openrouter_qwen",
  "note": "Eval mounts host delia-api at /app; evaluated_sha is checkout SHA of mounted code, not image bake SHA.",
}, indent=2) + "\n", encoding="utf-8")
print("HOST_FREEZE", p)
PY

docker exec -i \
  -e DELIA_APP_ROOT=/app \
  -e "DELIA_EVALUATED_SHA=${EVALUATED_SHA}" \
  -e "DELIA_RUNTIME_IMAGE_ID=${RUNTIME_IMAGE_ID}" \
  -e "DELIA_RUNTIME_IMAGE_DIGEST=${RUNTIME_IMAGE_DIGEST}" \
  -e "DELIA_RUNTIME_CONTAINER_ID=${RUNTIME_CONTAINER_ID}" \
  -e DELIA_EVAL_TRACE_DIR=/traces \
  -e DELIA_EVAL_ARTIFACT_DIR=/traces/artifacts \
  -e DELIA_INVESTIGATION_INSTRUCTION_VERSION=generalist-semantic-v2 \
  "${EVAL_NAME}" \
  python scripts/int1_v2_stability_eval.py \
  | tee "${ARTIFACT_DIR}/stability-eval-output.jsonl"

docker run --rm -v "${REPO_ROOT}/delia-api/.battery:/b" alpine \
  chown -R "$(id -u):$(id -g)" /b/int1-secure-decision-trace /b/int1-v2-stability \
  >/dev/null 2>&1 || true

echo "STABILITY_EVAL_COMPLETE=YES"
ls -la "${ARTIFACT_DIR}" | head -20
