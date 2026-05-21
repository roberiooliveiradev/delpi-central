# Deploy — Transformômetro API

## Docker

| Item | Valor |
|------|-------|
| Dockerfile | `transformometro-api/Dockerfile` (contexto = raiz do monorepo) |
| Container | `delpi-transformometro-api` |
| Porta interna | `8000` |
| `root-path` | `TM_API_ROOT_PATH` → `/apps/transformometro-api` |

```bash
docker build -f transformometro-api/Dockerfile -t transformometro-api:dev .
```

## Compose

Serviço em `infra/docker-compose.yml` e `infra/docker-compose.dev.yml`:

- `depends_on`: keycloak, postgres-plugins
- `env_file`: `infra/.env`
- Variáveis `TRANSFORMA_MAIS_*` repassadas para importação da planilha

## Gateway

| Rota pública | Backend |
|--------------|---------|
| `/apps/transformometro-api/` | `transformometro-api:8000` |
| `/apps/transformometro/` | MFE estático `delpi-transformometro` |

## Variáveis principais

| Variável | Default | Descrição |
|----------|---------|-----------|
| `TM_API_ROOT_PATH` | `/apps/transformometro-api` | Prefixo FastAPI |
| `TM_RUN_MIGRATIONS_ON_STARTUP` | `false` (`true` em prod compose) | Aplica V001–V003 no boot |
| `PLUGINS_DB_*` | — | Postgres schema `transformometro` |
| `TRANSFORMA_MAIS_SHEET_ID` + `TRANSFORMA_MAIS_GID_*` | — | Import Google Sheets |
| `JWT_SECRET` / Keycloak | — | `delpi_auth` |
| `API_DELPI_INTERNAL_SERVICE_TOKEN` | — | Auth S2S nas rotas `/integrations/engineering/*` (mesmo valor em SI e api-delpi) |
| `TRANSFORMOMETRO_API_BASE_URL` | `http://transformometro-api:8000` | Só nos **consumidores** (SI, api-delpi), não neste serviço |

## Testes antes do deploy

```bash
./scripts/ci-transformometro-api.sh
```

## Migrations

```bash
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner status
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner up
```

Versões: `V001` schema, `V002` cadastro, `V003` `dashboard_calculos`.

## Checklist produção

1. `TM_RUN_MIGRATIONS_ON_STARTUP=true` no primeiro deploy com V003
2. Rebuild **API + MFE** após cada release: `docker compose build transformometro-api transformometro && docker compose up -d`
3. Import inicial: `python scripts/migrate_transforma_mais_sheet.py --apply --replace` (ver [OPERATIONS.md](../../docs/12-roadmap-e-evolucao/transformometro-app/OPERATIONS.md))
4. Registrar manifesto na Core API: `plugins/transformometro/scripts/register-manifest.sh`
5. Health: `GET /apps/transformometro-api/transformometro/health` → `db_ready: true`
6. Integração (rede Docker): `curl -H "X-Delpi-Service-Token: $API_DELPI_INTERNAL_SERVICE_TOKEN" http://transformometro-api:8000/transformometro/integrations/engineering/transforma-mais/processes/summary`
