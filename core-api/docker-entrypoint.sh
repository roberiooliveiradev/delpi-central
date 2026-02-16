#!/bin/sh

echo "⏳ Aguardando banco..."

until nc -z $DB_HOST $DB_PORT; do
  sleep 2
done

echo "🚀 Rodando migrations..."
flask db upgrade

echo "🔥 Iniciando aplicação..."
python -m app.main
