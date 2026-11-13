#!/usr/bin/env bash
# INT-1 instrumented eval: OpenRouter qwen/qwen3-14b (profile openrouter_qwen).
# - No openrouter_local_egress_proxy
# - No docker exec printenv from production
# - Selective keys from infra/.env (LLM + exchange + DEV portal)
# - Host-persistent traces under delia-api/.battery/
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EVAL_NAME="delpi-delia-eval-int1-or-qwen14b"
ARTIFACT_DIR="${REPO_ROOT}/delia-api/.battery/int1-openrouter-qwen14b-eval"
TRACE_DIR="${REPO_ROOT}/delia-api/.battery/int1-secure-decision-trace"
EVAL_ENV="$(mktemp /tmp/delia-eval-or-env.XXXXXX)"
PROD_STARTED_BEFORE="$(docker inspect -f '{{.State.StartedAt}}' delpi-delia-api 2>/dev/null || echo missing)"

mkdir -p "${ARTIFACT_DIR}" "${TRACE_DIR}"
chmod 700 "${ARTIFACT_DIR}" "${TRACE_DIR}" || true
# Ensure artifact dir exists before any host-side tee (set -e safe).
: >"${ARTIFACT_DIR}/harness-run.log"

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

echo "=== INT-1 OpenRouter qwen14b instrumented eval ==="
echo "PROD_STARTED_BEFORE=${PROD_STARTED_BEFORE}"

# --- Build clean eval env (no prod printenv dump) ---
: >"${EVAL_ENV}"
chmod 600 "${EVAL_ENV}"

# Structural non-secret defaults from compose contract
{
  echo "DELIA_ENV=development"
  echo "DELIA_EVAL_EGRESS_AUTHORIZED=1"
  echo "DELIA_EVAL_ALLOWED_LLM_HOSTS=openrouter.ai"
  echo "DELIA_RUNTIME_PROFILE=openrouter_qwen"
  echo "DELIA_LLM_BASE_URL=https://openrouter.ai/api/v1"
  echo "KEYCLOAK_URL=http://keycloak:8080/auth"
  echo "KEYCLOAK_REALM=delpi"
  # Issuer must match gateway-minted subject tokens (Portal path).
  echo "KEYCLOAK_ISSUER=http://localhost/auth/realms/delpi"
  echo "KEYCLOAK_JWKS_URL=http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/certs"
  echo "KEYCLOAK_AUDIENCE=delpi-central"
  echo "KC_GATEWAY_TOKEN_BASE=http://delpi-gateway/auth"
  echo "CORE_API_URL=http://core-api:8000"
  echo "DELPI_AUTH_CORE_API_URL=http://core-api:8000"
  # INT-1 evals may point each owner at an isolated patched container
  # (DELIA_EVAL_*_BASE_URL) without touching the running shared
  # services. Endpoint-egress trust is an explicit env allowlist:
  # non-default hosts are declared in this ephemeral eval env only
  # (never in infra/.env or code).
  _TRUSTED_HOSTS=""
  _add_trusted_host() {
    local host
    host="$(python3 -c "from urllib.parse import urlparse;print(urlparse('${1}').hostname or '')")"
    if [[ -n "${host}" && "${host}" != "${2}" ]]; then
      if [[ -n "${_TRUSTED_HOSTS}" ]]; then
        _TRUSTED_HOSTS="${_TRUSTED_HOSTS},${host}"
      else
        _TRUSTED_HOSTS="${host}"
      fi
    fi
  }
  _DAVI_URL="${DELIA_EVAL_DAVI_BASE_URL:-http://delpi-api-delpi:8000/mcp}"
  echo "DELIA_MCP_DAVI_BASE_URL=${_DAVI_URL}"
  _add_trusted_host "${_DAVI_URL}" "delpi-api-delpi"
  echo "DELIA_MCP_DAVI_ENABLED=true"
  echo "DELIA_MCP_DAVI_HOST_HEADER=${DELIA_EVAL_DAVI_HOST_HEADER:-localhost:8000}"
  _TEO_URL="${DELIA_EVAL_TEO_BASE_URL:-http://transformometro-api:8000/mcp}"
  echo "DELIA_MCP_TEO_BASE_URL=${_TEO_URL}"
  _add_trusted_host "${_TEO_URL}" "transformometro-api"
  echo "DELIA_MCP_TEO_ENABLED=true"
  echo "DELIA_MCP_TEO_HOST_HEADER=${DELIA_EVAL_TEO_HOST_HEADER:-localhost:8000}"
  _VISTA_URL="${DELIA_EVAL_VISTA_BASE_URL:-http://tv-dashboard-api:8000/mcp}"
  echo "DELIA_MCP_VISTA_BASE_URL=${_VISTA_URL}"
  _add_trusted_host "${_VISTA_URL}" "tv-dashboard-api"
  echo "DELIA_MCP_VISTA_ENABLED=true"
  echo "DELIA_MCP_VISTA_HOST_HEADER=${DELIA_EVAL_VISTA_HOST_HEADER:-localhost:8000}"
  if [[ -n "${_TRUSTED_HOSTS}" ]]; then
    echo "DELIA_MCP_TRUSTED_ENDPOINT_HOSTS=${_TRUSTED_HOSTS}"
  fi
  echo "DELIA_MCP_PROVIDER_REGISTRY_MODE=core"
  echo "DELIA_C4_DAVI_PRODUCT_READ_ENABLED=1"
  echo "DELIA_C4_TEO_DASHBOARD_ANALYZE_ENABLED=1"
  echo "DELIA_EXCHANGE_CLIENT_ID=delia-api"
  echo "DELIA_TOKEN_EXCHANGE_URL=http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/token"
  echo "VITE_KC_CLIENT_ID=delpi-central"
  echo "DELIA_APP_ROOT=/app"
} >>"${EVAL_ENV}"

# Selective secrets from gitignored infra/.env (LLM + exchange + portal).
# OpenRouter eval requires a real provider key: when DELIA_LLM_API_KEY is a
# local placeholder, reuse the OpenRouter key already present as
# KIMI_API_KEY / DELIA_STT_API_KEY in the same .env (never printed).
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

# Optional subject override for AUTH-DENY evaluations: when
# DELIA_EVAL_SUBJECT_USERNAME/PASSWORD are exported, they replace the
# canonical DEV_PORTAL_* subject for this isolated run only. The .env
# file is never modified; overrides exist solely inside the ephemeral
# eval container env file.
import os as _os
_ovr_user = _os.environ.get("DELIA_EVAL_SUBJECT_USERNAME", "").strip()
_ovr_pass = _os.environ.get("DELIA_EVAL_SUBJECT_PASSWORD", "").strip()
if _ovr_user and _ovr_pass:
    values["DEV_PORTAL_USERNAME"] = _ovr_user
    values["DEV_PORTAL_PASSWORD"] = _ovr_pass
    print("SUBJECT_OVERRIDE=e2e_restricted")
else:
    print("SUBJECT_OVERRIDE=none")

emit_keys = [
    "DELIA_LLM_API_KEY",
    "DELIA_EXCHANGE_CLIENT_SECRET",
    "KEYCLOAK_REALM",
    "DEV_PORTAL_USERNAME",
    "DEV_PORTAL_PASSWORD",
]
found = set()
with dst.open("a", encoding="utf-8") as fh:
    for key in emit_keys:
        val = values.get(key, "")
        if not val:
            continue
        fh.write(f"{key}={val}\\n")
        found.add(key)
optional = {"KEYCLOAK_REALM"}
required = set(emit_keys) - optional
missing = required - found
print("SELECTIVE_KEYS_LOADED=" + ",".join(sorted(found)) if found else "SELECTIVE_KEYS_LOADED=NONE")
print(f"LLM_KEY_SOURCE={llm_source}")
print(f"LLM_KEY_SHAPE=openrouter" if _is_openrouter_key(llm_key) else "LLM_KEY_SHAPE=non_openrouter")
if missing:
    raise SystemExit(
        "missing required keys in infra/.env: " + ",".join(sorted(missing))
    )
if not _is_openrouter_key(llm_key):
    raise SystemExit(
        "missing OpenRouter API key in infra/.env "
        "(DELIA_LLM_API_KEY/KIMI_API_KEY/DELIA_STT_API_KEY)"
    )
PY

# Detect docker network used by prod delia (name only)
NETWORK="$(docker inspect delpi-delia-api --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')"
echo "DOCKER_NETWORK=${NETWORK}"

if docker inspect "${EVAL_NAME}" >/dev/null 2>&1; then
  docker rm -f "${EVAL_NAME}" >/dev/null
fi

docker run -d \
  --name "${EVAL_NAME}" \
  --network "${NETWORK}" \
  --env-file "${EVAL_ENV}" \
  -e "DELIA_EVAL_TRACE_DIR=/traces" \
  -e "DELIA_EVAL_ARTIFACT_DIR=/traces/artifacts" \
  -v "${REPO_ROOT}/delia-api:/app" \
  -v "${TRACE_DIR}:/traces" \
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

# Baseline: security gate + settings
docker exec -i -e DELIA_APP_ROOT=/app "${EVAL_NAME}" python - <<'PY'
from app.infrastructure.config.settings import Settings
from urllib.parse import urlsplit
import pydantic_ai
s = Settings()
host = urlsplit(s.llm_base_url or "").hostname or ""
print("baseline_env", s.environment)
print("baseline_profile", s.runtime_profile)
print("baseline_model", s.llm_model)
print("baseline_fp", s.runtime_config_fingerprint)
print("baseline_host", host)
print("baseline_egress", s.llm_egress_blocked_reason or "allowed")
print("baseline_pydantic_ai", pydantic_ai.__version__)
assert s.environment == "development"
assert s.runtime_profile == "openrouter_qwen"
assert s.llm_model == "qwen/qwen3-14b"
assert host == "openrouter.ai"
assert s.llm_egress_blocked_reason is None
assert s.llm_api_key
print("BASELINE_CONFIG=OK")
PY

docker exec -i -e DELIA_APP_ROOT=/app "${EVAL_NAME}" \
  python scripts/int1_secure_decision_trace.py --check-security-gate \
  | tee "${ARTIFACT_DIR}/security-gate.json"
# exit 2 from script means BLOCKED — require READY
python3 - <<PY
import json, pathlib, sys
raw = pathlib.Path("${ARTIFACT_DIR}/security-gate.json").read_text()
# file may contain only JSON object
data = json.loads(raw)
gate = data.get("SECURE_EVAL_GATE")
print("SECURE_EVAL_GATE", gate)
if gate != "READY_FOR_ISOLATED_EVAL":
    print("BLOCKERS", data.get("BLOCKERS"))
    sys.exit(5)
PY

# Dry-run persistence still PASS inside container (writes to mounted /traces)
docker exec -i -e DELIA_APP_ROOT=/app -e DELIA_EVAL_TRACE_DIR=/traces \
  "${EVAL_NAME}" python scripts/int1_secure_decision_trace.py --dry-run \
  | tee "${ARTIFACT_DIR}/dry-run.json"

# Real instrumented eval. Optional filter (default: historical full list).
# G1/P1-only INT-1 runs: export DELIA_EVAL_SCENARIO_IDS before invoking.
SCENARIO_IDS="${DELIA_EVAL_SCENARIO_IDS:-}"
docker exec -i \
  -e DELIA_APP_ROOT=/app \
  -e DELIA_EVAL_TRACE_DIR=/traces \
  -e DELIA_EVAL_ARTIFACT_DIR=/traces/artifacts \
  -e "DELIA_EVAL_SCENARIO_IDS=${SCENARIO_IDS}" \
  "${EVAL_NAME}" \
  python scripts/int1_openrouter_qwen14b_instrumented_eval.py \
  | tee "${ARTIFACT_DIR}/eval-output.jsonl"

echo "EVAL_COMPLETE=YES"
echo "ARTIFACT_DIR=${ARTIFACT_DIR}"
echo "TRACE_DIR=${TRACE_DIR}"
# Container writes as root into the bind mount — reclaim for host user.
if command -v docker >/dev/null 2>&1; then
  docker run --rm \
    -v "${REPO_ROOT}/delia-api/.battery:/b" \
    alpine chown -R "$(id -u):$(id -g)" \
    /b/int1-secure-decision-trace /b/int1-openrouter-qwen14b-eval \
    >/dev/null 2>&1 || true
fi
ls -la "${TRACE_DIR}" | head -20
