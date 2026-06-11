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
  echo "🔄 Sincronizando inteligência do chat a partir do .env..."
  flask --app "$FLASK_APP" sync-chat-intelligence-env
fi

echo "🔥 Iniciando aplicação..."
exec "$@"
