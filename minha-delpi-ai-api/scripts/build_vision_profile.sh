#!/usr/bin/env bash
# Rebuild permanente da API com extras de visão (EasyOCR + Docling + modelos EasyOCR).
#
# Dev: Dockerfile.dev + compose já fixam INSTALL_VISION_EXTRAS=true em todo build.
# Prod: use target prod + docker-compose.prod.vision.yml
#
# Uso:
#   ./minha-delpi-ai-api/scripts/build_vision_profile.sh [dev|prod]
#   NO_CACHE=1 ./minha-delpi-ai-api/scripts/build_vision_profile.sh dev

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET="${1:-dev}"
export INSTALL_VISION_EXTRAS=true

cd "$ROOT/infra"

BUILD_ARGS=(--build-arg "INSTALL_VISION_EXTRAS=true")
if [ "${NO_CACHE:-0}" = "1" ]; then
  BUILD_ARGS+=(--no-cache)
fi

case "$TARGET" in
  dev)
    COMPOSE_FILES=(-f docker-compose.dev.yml)
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

echo "== Build permanente com extras de visão ($TARGET) — pode levar vários minutos =="
docker compose "${COMPOSE_FILES[@]}" "${COMPOSE_PROFILE[@]}" build "${BUILD_ARGS[@]}" minha-delpi-ai-api

echo "== Recreate minha-delpi-ai-api =="
docker compose "${COMPOSE_FILES[@]}" "${COMPOSE_PROFILE[@]}" up -d --force-recreate minha-delpi-ai-api

docker compose "${COMPOSE_FILES[@]}" "${COMPOSE_PROFILE[@]}" exec -T minha-delpi-ai-api \
  python3 scripts/check_vision_profile_deps.py --require-easyocr --require-easyocr-models

echo "Profile vision ($TARGET): extras permanentes na imagem — OK."
