#!/bin/sh
set -e

export FLASK_APP="${FLASK_APP:-app.main:app}"

DB_WAIT_HOST="${PLUGINS_DB_HOST:-postgres-plugins}"
DB_WAIT_PORT="${PLUGINS_DB_PORT:-5432}"

echo "⏳ Aguardando banco (${DB_WAIT_HOST}:${DB_WAIT_PORT})..."
until nc -z "$DB_WAIT_HOST" "$DB_WAIT_PORT"; do
  sleep 2
done

if [ "${SKIP_DB_MIGRATIONS:-false}" = "true" ]; then
  echo "⏭️  SKIP_DB_MIGRATIONS=true — migrations ignoradas."
else
  echo "🚀 Rodando migrations..."
  flask --app "$FLASK_APP" db upgrade
fi

if [ "${SKIP_CHAT_INTELLIGENCE_SYNC:-false}" != "true" ]; then
  echo "🌱 Verificando defaults de plataforma do chat (admin prevalece)..."
  flask --app "$FLASK_APP" seed-chat-platform-settings
fi

# Extras de visão (EasyOCR/Docling) só no BUILD da imagem — nunca pip install aqui
# (bloqueava o Flask 10–20 min e gerava 502 no gateway).
if [ "${CHAT_VISION_EXTRAS_WARN:-true}" = "true" ]; then
  if ! python3 -c "import easyocr" >/dev/null 2>&1; then
    echo "⚠️  EasyOCR ausente — OCR regional usará só Tesseract até rebuild da imagem."
    echo "    Dev:  docker compose -f infra/docker-compose.dev.yml --profile chat build minha-delpi-ai-api"
    echo "    Prod: INSTALL_VISION_EXTRAS=true docker compose -f infra/docker-compose.yml build minha-delpi-ai-api"
  fi
fi

echo "🔥 Iniciando aplicação..."
exec "$@"
