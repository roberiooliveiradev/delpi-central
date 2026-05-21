# Desenvolvimento — Transformômetro API

## Docker (recomendado)

```bash
cd infra
docker compose -f docker-compose.dev.yml up -d transformometro-api transformometro
```

Health:

```bash
curl -s http://localhost/apps/transformometro-api/health
curl -s http://localhost/apps/transformometro-api/transformometro/health
```

## Migrations

Com `TM_RUN_MIGRATIONS_ON_STARTUP=true` (padrão no compose dev), o schema é criado no boot.

Manual:

```bash
cd transformometro-api
export PLUGINS_DB_HOST=localhost PLUGINS_DB_PORT=5433 ...
python -m tm_app.infrastructure.persistence.plugins.migrations_runner up
```
