#!/usr/bin/env bash
# Sobe stack mínimo DELPI dev (portal + api-delpi), sem plugins/MFEs pesados.
# Plugins sob demanda: --profile plugins up -d <nome-do-servico>
set -euo pipefail

COMPOSE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$COMPOSE_DIR"

COMPOSE=(docker compose -f docker-compose.dev.yml -f docker-compose.minimal.yml --env-file .env)

RESTORE=false
BUILD=false
for arg in "$@"; do
  case "$arg" in
    --restore) RESTORE=true ;;
    --build) BUILD=true ;;
  esac
done

MINIMAL_SERVICES=(
  postgres-core
  keycloak-db
  keycloak
  postgres-plugins
  core-api
  api-delpi
  portal
  gateway
)

echo "=== Fase 1: bancos PostgreSQL ==="
"${COMPOSE[@]}" up -d postgres-core keycloak-db postgres-plugins

wait_pg() {
  local container="$1"
  local user="$2"
  local db="$3"
  echo "Aguardando $container..."
  for _ in $(seq 1 60); do
    if docker exec "$container" pg_isready -U "$user" -d "$db" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "Timeout aguardando $container" >&2
  exit 1
}

wait_pg delpi-postgres-core delpi delpi_core
wait_pg delpi-keycloak-db keycloak keycloak
wait_pg delpi-postgres-plugins plugins_user plugins_hub

if [[ "$RESTORE" == true ]]; then
  bash scripts/restore-delpi-backups.sh
fi

echo "=== Fase 2: stack mínimo (${#MINIMAL_SERVICES[@]} serviços) ==="
UP_ARGS=(-d)
if [[ "$BUILD" == true ]]; then
  UP_ARGS+=(--build)
  export COMPOSE_PARALLEL_LIMIT="${COMPOSE_PARALLEL_LIMIT:-2}"
  echo "Build com COMPOSE_PARALLEL_LIMIT=${COMPOSE_PARALLEL_LIMIT} (evita OOM em máquinas ~8 GB)"
fi
"${COMPOSE[@]}" up "${UP_ARGS[@]}" "${MINIMAL_SERVICES[@]}"

echo "=== Parando serviços opcionais (se subiram por dependência antiga) ==="
docker stop delpi-searxng delpi-languagetool 2>/dev/null || true

echo ""
echo "Stack mínimo no ar: http://localhost"
echo "Serviços: ${MINIMAL_SERVICES[*]}"
echo "Chat:     ${COMPOSE[*]} --profile chat up -d"
echo "Chat RAM: ${COMPOSE[*]} --profile chat up -d  # já inclui override minimal (sem LanguageTool/SearXNG)"
echo "Plugin:   ${COMPOSE[*]} --profile plugins up -d <servico>"
echo "Sem: dashboards, MFEs, strategic-indicators, transformometro, maintenance (profile plugins)"
echo ""
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep delpi || true
