# Deploy — Transformômetro API

## Docker

| Item | Valor |
|------|-------|
| Dockerfile | `transformometro-api/Dockerfile` (contexto = raiz do monorepo) |
| Container | `delpi-transformometro-api` |
| Porta interna | `8000` |
| `root-path` | `TM_API_ROOT_PATH` → `/apps/transformometro-api` |
| Health `phase` | `4-melhorias` |

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
| `TM_RUN_MIGRATIONS_ON_STARTUP` | `false` (`true` em prod compose) | Aplica V001–V005 no boot |
| `PLUGINS_DB_*` | — | Postgres schema `transformometro` |
| `TRANSFORMA_MAIS_SHEET_ID` + `TRANSFORMA_MAIS_GID_*` | — | Import Google Sheets |
| `JWT_SECRET` / Keycloak | — | `delpi_auth` |
| `API_DELPI_INTERNAL_SERVICE_TOKEN` | — | Auth S2S nas rotas `/integrations/engineering/*` (mesmo valor em SI e api-delpi) |
| `TRANSFORMOMETRO_API_BASE_URL` | `http://transformometro-api:8000` | Só nos **consumidores** (SI, api-delpi), não neste serviço |
| `TM_NOTIFICATIONS_ENABLED` | `false` | Dispara alertas no portal ao submeter/aprovar/rejeitar revisão |
| `TM_CORE_API_URL` | `http://core-api:8000` | Base da Core API na rede Docker (`POST …/integrations/notifications`) |
| `CORE_API_INTEGRATIONS_SERVICE_TOKEN` | — | Mesmo valor de `infra/.env` / Core API (`X-Delpi-Service-Token`) |
| `TM_PORTAL_ROUTE` | `/apps/transformometro` | `action.target` + prefixo do deep link |
| `TM_WORKFLOW_APPROVER_EMAILS` | — | Destinatários na submissão (CSV) |
| `TM_WORKFLOW_APPROVER_ROLE_IDS` | — | Papéis RBAC na submissão (CSV de UUIDs) |

## Testes antes do deploy

```bash
./scripts/ci-transformometro-api.sh
```

## Migrations

```bash
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner status
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner up
```

Versões: ver [migrations/README.md](../migrations/README.md) (V001–V005).

## Checklist produção

1. `TM_RUN_MIGRATIONS_ON_STARTUP=true` (ou `up` manual antes do tráfego)
2. Rebuild **API + MFE** após cada release: `docker compose build transformometro-api transformometro && docker compose up -d --force-recreate transformometro-api transformometro`
3. Registrar manifesto na Core API: `plugins/transformometro/scripts/register-manifest.sh` (inclui rota `/recursos`)
4. RBAC: `transformometro.shared-resources.manage` para quem edita o catálogo
5. Health: `GET /apps/transformometro-api/transformometro/health` → `db_ready: true`
6. Import inicial (se necessário): `python scripts/migrate_transforma_mais_sheet.py --apply --replace` (ver [OPERATIONS.md](../../docs/12-roadmap-e-evolucao/transformometro-app/OPERATIONS.md))
7. Integração (rede Docker): `curl -H "X-Delpi-Service-Token: $API_DELPI_INTERNAL_SERVICE_TOKEN" http://transformometro-api:8000/transformometro/integrations/engineering/transforma-mais/processes/summary`
