#!/usr/bin/env bash
# Constrói delpi-plugins-shared-builder:local (tv-dashboard-presentation bundled).
# @delpi/plugin-ui é remote Module Federation — não entra mais nesta imagem.
set -euo pipefail

COMPOSE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$COMPOSE_DIR"

export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo "=== Build imagem compartilhada plugins (tv-dashboard-presentation) ==="
docker compose -f docker-compose.dev.yml --profile build-base build plugins-shared-builder

echo ""
echo "Imagem pronta: delpi-plugins-shared-builder:local"
echo "Build de MFE federado (exemplo):"
echo "  export COMPOSE_PARALLEL_LIMIT=2"
echo "  docker compose -f docker-compose.dev.yml --profile plugins up -d plugin-ui controle-retrabalhos"
