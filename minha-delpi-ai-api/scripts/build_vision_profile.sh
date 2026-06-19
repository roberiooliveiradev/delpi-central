#!/usr/bin/env bash
# Rebuild da API com extras de visão (EasyOCR + Docling).
#
# Desde jun/2026 o Dockerfile.dev já instala requirements-vision.txt.
# Este script permanece para prod (INSTALL_VISION_EXTRAS) e fluxos explícitos.
#
# Uso:
#   ./minha-delpi-ai-api/scripts/build_vision_profile.sh [dev|prod]

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET="${1:-dev}"

cd "$ROOT/infra"

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

echo "== Build com extras de visão ($TARGET) — EasyOCR/Docling + modelos; pode levar vários minutos =="
docker compose "${COMPOSE_FILES[@]}" "${COMPOSE_PROFILE[@]}" build --no-cache minha-delpi-ai-api

echo "== Recreate minha-delpi-ai-api =="
docker compose "${COMPOSE_FILES[@]}" "${COMPOSE_PROFILE[@]}" up -d --force-recreate minha-delpi-ai-api

docker compose "${COMPOSE_FILES[@]}" "${COMPOSE_PROFILE[@]}" exec -T minha-delpi-ai-api \
  python3 scripts/check_vision_profile_deps.py --require-easyocr --require-easyocr-models

echo "Profile vision ($TARGET): build concluído."
