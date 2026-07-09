#!/usr/bin/env bash
# Constrói a imagem delpi-plugins-shared-builder:local (plugin-ui + tv-dashboard-presentation).
# Rode UMA vez antes de build em massa dos MFEs — evita 26× npm install do plugin-ui.
set -euo pipefail

COMPOSE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$COMPOSE_DIR"

export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo "=== Build imagem compartilhada plugins (plugin-ui + tv-dashboard-presentation) ==="
docker compose -f docker-compose.dev.yml --profile build-base build plugins-shared-builder

echo ""
echo "Imagem pronta: delpi-plugins-shared-builder:local"
echo "Build de MFE (exemplo):"
echo "  export COMPOSE_PARALLEL_LIMIT=2"
echo "  docker compose -f docker-compose.dev.yml --profile plugins build controle-retrabalhos"
