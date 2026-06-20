#!/usr/bin/env bash
# Sobe stack mínimo DELPI dev (chat + desenho + api-delpi), sem serviços pesados opcionais.
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
  ollama
  minha-delpi-ai-api
  minha-delpi-chat
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
fi
"${COMPOSE[@]}" up "${UP_ARGS[@]}" "${MINIMAL_SERVICES[@]}"

echo "=== Parando serviços opcionais (se subiram por dependência antiga) ==="
docker stop delpi-searxng delpi-languagetool 2>/dev/null || true

echo "=== Fase 3: modelos Ollama (chat leve) ==="
MODEL="${OLLAMA_MODEL:-qwen2.5:1.5b}"
EMBED="${EMBEDDING_MODEL:-bge-m3}"
for _ in $(seq 1 30); do
  if docker exec delpi-ollama ollama list >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
docker exec delpi-ollama ollama pull "$MODEL" || true
docker exec delpi-ollama ollama pull "$EMBED" || true

echo ""
echo "Stack mínimo no ar: http://localhost"
echo "Serviços: ${MINIMAL_SERVICES[*]}"
echo "Sem: searxng, languagetool, dashboards, strategic-indicators, transformometro, maintenance"
echo ""
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep delpi || true
