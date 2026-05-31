#!/usr/bin/env bash
# Build da API com Dockerfile.vision.dev (Docling/Paddle em requirements-vision.txt).
#
# Pré-requisito: descomente pacotes em minha-delpi-ai-api/requirements-vision.txt
#
# Uso:
#   ./minha-delpi-ai-api/scripts/build_vision_profile.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET="${1:-dev}"

cd "$ROOT/infra"

case "$TARGET" in
  dev)
    COMPOSE_FILES=(-f docker-compose.dev.yml -f docker-compose.vision.yml)
    COMPOSE_PROFILE=(--profile chat)
    ;;
  prod)
    COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.prod.vision.yml)
    COMPOSE_PROFILE=()
    ;;
  *)
    echo "Uso: $0 [dev|prod]" >&2
    exit 1
    ;;
esac

echo "== Build profile vision ($TARGET) — pode levar vários minutos com Docling =="
docker compose "${COMPOSE_FILES[@]}" "${COMPOSE_PROFILE[@]}" build minha-delpi-ai-api

echo "== Recreate minha-delpi-ai-api =="
docker compose "${COMPOSE_FILES[@]}" "${COMPOSE_PROFILE[@]}" up -d --force-recreate minha-delpi-ai-api

docker compose "${COMPOSE_FILES[@]}" "${COMPOSE_PROFILE[@]}" exec -T minha-delpi-ai-api \
  python3 scripts/check_vision_profile_deps.py

echo "Profile vision ($TARGET): build concluído."
