#!/usr/bin/env bash
# Pós-deploy: reimport OpenAPI api-delpi → catálogo TV (tv_data_routes.json).
#
# Uso local (stack Docker no host):
#   ./scripts/homologacao/sync-api-delpi-openapi-tv.sh
#
# Homolog/prod (via SSH após deploy):
#   BASE_URL=https://homolog.exemplo.com ./scripts/homologacao/sync-api-delpi-openapi-tv.sh
#
# Variáveis:
#   BASE_URL              — gateway público (default: http://localhost)
#   TV_API_CONTAINER      — container tv-dashboard-api (default: delpi-tv-dashboard-api)
#   API_DELPI_CONTAINER   — container api-delpi (default: delpi-api-delpi)
#   WAIT_SECONDS          — timeout health api-delpi (default: 180)
#   SKIP_HEALTH_WAIT      — 1 pula espera de health
#   USE_HTTP_SYNC         — 1 usa POST /data/openapi/sync (precisa token); default 0 = docker exec
#   TV_MANAGE_BEARER      — Bearer JWT com tv-dashboard.manage (só se USE_HTTP_SYNC=1)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASE_URL="${BASE_URL:-http://localhost}"
TV_API_CONTAINER="${TV_API_CONTAINER:-delpi-tv-dashboard-api}"
API_DELPI_CONTAINER="${API_DELPI_CONTAINER:-delpi-api-delpi}"
WAIT_SECONDS="${WAIT_SECONDS:-180}"
SKIP_HEALTH_WAIT="${SKIP_HEALTH_WAIT:-0}"
USE_HTTP_SYNC="${USE_HTTP_SYNC:-0}"
REPORT_FILE="${REPORT_FILE:-/tmp/sync-api-delpi-openapi-tv-report.json}"

API_HEALTH_URL="${API_HEALTH_URL:-${BASE_URL%/}/apps/api-delpi/health}"

fail() {
  echo "[ERRO] $*" >&2
  exit 1
}

ok() {
  echo "[OK] $*"
}

warn() {
  echo "[AVISO] $*" >&2
}

container_running() {
  docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null | grep -q true
}

wait_api_delpi_health() {
  if [ "$SKIP_HEALTH_WAIT" = "1" ]; then
    warn "SKIP_HEALTH_WAIT=1 — pulando espera de health da api-delpi."
    return 0
  fi

  echo "[1/4] Aguardando api-delpi saudável (até ${WAIT_SECONDS}s) — ${API_HEALTH_URL}"
  local deadline=$((SECONDS + WAIT_SECONDS))

  while [ "$SECONDS" -lt "$deadline" ]; do
    if curl -fsS "$API_HEALTH_URL" >/dev/null 2>&1; then
      ok "api-delpi respondeu em ${API_HEALTH_URL}"
      return 0
    fi
    if container_running "$API_DELPI_CONTAINER"; then
      if docker exec "$API_DELPI_CONTAINER" curl -fsS "http://localhost:8000/health" >/dev/null 2>&1; then
        ok "api-delpi saudável via docker exec (${API_DELPI_CONTAINER})"
        return 0
      fi
    fi
    sleep 3
  done

  fail "api-delpi não ficou saudável em ${WAIT_SECONDS}s (${API_HEALTH_URL})"
}

wait_tv_api_container() {
  echo "[2/4] Verificando container do TV (${TV_API_CONTAINER})"
  local deadline=$((SECONDS + 60))
  while [ "$SECONDS" -lt "$deadline" ]; do
    if container_running "$TV_API_CONTAINER"; then
      ok "Container ${TV_API_CONTAINER} em execução"
      return 0
    fi
    sleep 2
  done
  fail "Container ${TV_API_CONTAINER} não está rodando"
}

run_sync_docker_exec() {
  echo "[3/4] Executando sync OpenAPI dentro do TV (docker exec)"
  docker exec -e PYTHONPATH=/app "$TV_API_CONTAINER" python3 - <<'PY' > "$REPORT_FILE"
import json
from tv_app.application.services.tv_openapi_catalog_sync_service import TvOpenApiCatalogSyncService

report = TvOpenApiCatalogSyncService().sync_from_live_api()
print(json.dumps(report, ensure_ascii=False, indent=2))
PY
  python3 -m json.tool "$REPORT_FILE" >/dev/null
  cat "$REPORT_FILE"
}

run_sync_http() {
  echo "[3/4] Executando POST /apps/tv-dashboard-api/data/openapi/sync"
  if [ -z "${TV_MANAGE_BEARER:-}" ]; then
    fail "USE_HTTP_SYNC=1 exige TV_MANAGE_BEARER"
  fi
  curl -fsS -X POST \
    -H "Authorization: Bearer ${TV_MANAGE_BEARER}" \
    -H "Content-Type: application/json" \
    "${BASE_URL%/}/apps/tv-dashboard-api/data/openapi/sync" \
    > "$REPORT_FILE"
  python3 -m json.tool "$REPORT_FILE" >/dev/null
  cat "$REPORT_FILE"
}

validate_report() {
  echo "[4/4] Validando relatório"
  python3 - "$REPORT_FILE" <<'PY'
import json
import sys

path = sys.argv[1]
raw = json.load(open(path, encoding="utf-8"))
# Envelope ok() → { success, data } ou relatório direto do docker exec
report = raw.get("data") if isinstance(raw, dict) and "data" in raw else raw
if not isinstance(report, dict):
    print("[ERRO] relatório inválido", file=sys.stderr)
    sys.exit(1)
if not report.get("ok"):
    print(f"[ERRO] sync falhou: {report.get('error') or report}", file=sys.stderr)
    sys.exit(1)
routes = int(report.get("routesWritten") or 0)
if routes <= 0:
    print("[ERRO] routesWritten=0", file=sys.stderr)
    sys.exit(1)
print("[OK] Sync TV validado:", json.dumps({
    "routesWritten": routes,
    "routesPath": report.get("routesPath"),
    "source": report.get("source"),
}, ensure_ascii=False))
PY
}

echo "== Pós-deploy: sync OpenAPI api-delpi → TV =="
echo "BASE_URL=${BASE_URL}"
echo "TV_API_CONTAINER=${TV_API_CONTAINER}"
echo

wait_api_delpi_health
wait_tv_api_container
if [ "$USE_HTTP_SYNC" = "1" ]; then
  run_sync_http
else
  run_sync_docker_exec
fi
validate_report

ok "Pós-deploy sync-api-delpi-openapi-tv concluído."
