#!/usr/bin/env bash
# Build da API com Dockerfile.vision.dev (Docling/Paddle em requirements-vision.txt).
#
# Pré-requisito: descomente pacotes em minha-delpi-ai-api/requirements-vision.txt
#
# Uso:
#   ./minha-delpi-ai-api/scripts/build_vision_profile.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$ROOT/infra"

echo "== Build profile vision (pode levar vários minutos com Docling) =="
docker compose -f docker-compose.dev.yml -f docker-compose.vision.yml \
  --profile chat build minha-delpi-ai-api

echo "== Recreate container =="
docker compose -f docker-compose.dev.yml -f docker-compose.vision.yml \
  --profile chat up -d --force-recreate minha-delpi-ai-api

docker compose -f docker-compose.dev.yml exec -T minha-delpi-ai-api \
  python3 scripts/check_vision_profile_deps.py

echo "Profile vision: build concluído."
