#!/usr/bin/env bash
# Pós-deploy: reimport OpenAPI do provider api-delpi no chat (embeddings + catálogo MD).
#
# Uso local (stack Docker no host):
#   ./scripts/homologacao/sync-api-delpi-openapi.sh
#
# Homolog/prod (via SSH após deploy):
#   BASE_URL=https://homolog.exemplo.com ./scripts/homologacao/sync-api-delpi-openapi.sh
#
# Variáveis:
#   BASE_URL              — gateway público (default: http://localhost)
#   CHAT_API_CONTAINER    — container minha-delpi-ai-api (default: delpi-minha-delpi-ai-api)
#   API_DELPI_CONTAINER   — container api-delpi (opcional; usado se health HTTP falhar)
#   PROVIDER_KEY          — provider OpenAPI (default: api-delpi)
#   WAIT_SECONDS          — timeout aguardando saúde api-delpi (default: 180)
#   SKIP_HEALTH_WAIT      — 1 pula espera de health
#   SYNC_EXTRA_ARGS       — args extras para sync_api_delpi_openapi.py (ex.: --from-file)
#   COMPOSE_DIR           — diretório infra/ com compose (default: auto-detect)
#   COMPOSE_FILE          — arquivo compose prod (default: docker-compose.yml)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_DIR="${COMPOSE_DIR:-$ROOT_DIR/infra}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
BASE_URL="${BASE_URL:-http://localhost}"
CHAT_API_CONTAINER="${CHAT_API_CONTAINER:-delpi-minha-delpi-ai-api}"
API_DELPI_CONTAINER="${API_DELPI_CONTAINER:-delpi-api-delpi}"
PROVIDER_KEY="${PROVIDER_KEY:-api-delpi}"
WAIT_SECONDS="${WAIT_SECONDS:-180}"
SKIP_HEALTH_WAIT="${SKIP_HEALTH_WAIT:-0}"
SYNC_EXTRA_ARGS="${SYNC_EXTRA_ARGS:-}"

API_HEALTH_URL="${API_HEALTH_URL:-${BASE_URL%/}/apps/api-delpi/health}"
REPORT_FILE="${REPORT_FILE:-/tmp/sync-api-delpi-openapi-report.json}"

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

  echo "[1/5] Aguardando api-delpi saudável (até ${WAIT_SECONDS}s) — ${API_HEALTH_URL}"
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

wait_chat_api_container() {
  echo "[2/5] Verificando container do chat (${CHAT_API_CONTAINER})"
  local deadline=$((SECONDS + 60))

  while [ "$SECONDS" -lt "$deadline" ]; do
    if container_running "$CHAT_API_CONTAINER"; then
      ok "Container ${CHAT_API_CONTAINER} em execução"
      return 0
    fi
    sleep 2
  done

  fail "Container ${CHAT_API_CONTAINER} não está rodando"
}

run_sync_in_container() {
  echo "[3/5] Executando sync_api_delpi_openapi.py (provider=${PROVIDER_KEY})"

  # shellcheck disable=SC2086
  docker exec "$CHAT_API_CONTAINER" python3 scripts/sync_api_delpi_openapi.py \
    --provider-key "$PROVIDER_KEY" \
    $SYNC_EXTRA_ARGS \
    > "$REPORT_FILE"

  python3 -m json.tool "$REPORT_FILE" >/dev/null
  cat "$REPORT_FILE"
}

validate_report() {
  echo "[4/5] Validando relatório JSON"
  python3 - "$REPORT_FILE" <<'PY'
import json
import sys

path = sys.argv[1]
report = json.load(open(path, encoding="utf-8"))

errors: list[str] = []

import_result = report.get("import")
if isinstance(import_result, dict):
    if import_result.get("found") is False:
        errors.append("import.found=false — provider não cadastrado no chat")
    actions_imported = import_result.get("actionsImported")
    if actions_imported is not None and int(actions_imported) <= 0:
        errors.append("import.actionsImported=0 — schema vazio ou inválido")

actions_in_db = int(report.get("actionsInDatabase") or 0)
if actions_in_db <= 0:
    errors.append("actionsInDatabase=0 — nenhuma action persistida")

reindex = report.get("reindex")
if isinstance(reindex, dict):
    indexed = reindex.get("indexed") or reindex.get("updated") or reindex.get("actionsIndexed")
    if indexed is not None and int(indexed) < 0:
        errors.append("reindex retornou contagem negativa")

if errors:
    for item in errors:
        print(f"[ERRO] {item}", file=sys.stderr)
    sys.exit(1)

print("[OK] Sync validado:", json.dumps({
    "actionsInDatabase": actions_in_db,
    "actionsImported": (import_result or {}).get("actionsImported"),
    "catalogOperations": report.get("catalogOperations"),
    "catalogPath": report.get("catalogPath"),
}, ensure_ascii=False))
PY
}

echo "== Pós-deploy: sync OpenAPI api-delpi → chat =="
echo "BASE_URL=${BASE_URL}"
echo "CHAT_API_CONTAINER=${CHAT_API_CONTAINER}"
echo

wait_api_delpi_health
wait_chat_api_container
run_sync_in_container
validate_report

echo "[5/5] Readiness operacional (Playbook 16)"
docker exec "$CHAT_API_CONTAINER" python3 scripts/check_operational_action_readiness.py

ok "Pós-deploy sync-api-delpi-openapi concluído."
echo
echo "Próximo passo (opcional): reindexar RAG docs/knowledge/api-delpi-rotas-agente.md na base do agente."
