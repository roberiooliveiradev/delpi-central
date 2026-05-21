# Transformômetro API

API dedicada do plugin Transformômetro (Minha Delpi).

## URLs (gateway dev)

```text
Health:  http://localhost/apps/transformometro-api/health
Módulo:  http://localhost/apps/transformometro-api/transformometro/health
Docs:    http://localhost/apps/transformometro-api/docs
```

## Desenvolvimento local

```bash
cd transformometro-api
pip install -r requirements.txt
pip install -e ../shared[fastapi]
export TM_API_ROOT_PATH=/apps/transformometro-api
python -m uvicorn tm_app.main:app --reload --port 8010
```

## Migrations

```bash
PLUGINS_DB_HOST=localhost PLUGINS_DB_PORT=5433 ...
python -m tm_app.infrastructure.persistence.plugins.migrations_runner up
```

Documentação: [docs/12-roadmap-e-evolucao/transformometro-app/](../docs/12-roadmap-e-evolucao/transformometro-app/README.md)
