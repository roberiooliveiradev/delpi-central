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
- Cadastro de dados somente via CRUD da API (sem importação de planilha)

## Gateway

| Rota pública | Backend |
|--------------|---------|
| `/apps/transformometro-api/` | `transformometro-api:8000` |
| `/apps/transformometro/` | MFE estático `delpi-transformometro` |

## Variáveis principais

| Variável | Default | Descrição |
|----------|---------|-----------|
| `TM_API_ROOT_PATH` | `/apps/transformometro-api` | Prefixo FastAPI |
| `TM_RUN_MIGRATIONS_ON_STARTUP` | `false` no código; **`true` no compose** | Aplica **V001–V018** pendentes no boot |
| `PLUGINS_DB_*` | — | Postgres schema `transformometro` |
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

Versões: ver [migrations/README.md](../migrations/README.md) (**V001–V018**).

### Pós-migration Playbook 18

1. Export JSON do cadastro (backup).
2. Subir API com migrations automáticas.
3. `bootstrap_filiais_from_cadastro.py` (V011 sem seed).
4. Recalc full dashboard (V017 trunca `dashboard_calculos`).
5. Rebuild MFE + registrar manifesto (RBAC filial).

Ver [playbook-18-implementation-status.md](playbook-18-implementation-status.md) e [status-atual.md](../../docs/12-roadmap-e-evolucao/transformometro-app/status-atual.md).

## Checklist produção

1. `TM_RUN_MIGRATIONS_ON_STARTUP=true` (ou `up` manual antes do tráfego)
2. Rebuild **API + MFE** após cada release: `docker compose build transformometro-api transformometro && docker compose up -d --force-recreate transformometro-api transformometro`
3. Registrar manifesto na Core API: `plugins/transformometro/scripts/register-manifest.sh` (inclui rota `/recursos`)
4. RBAC: `transformometro.shared-resources.manage` para quem edita o catálogo
5. Health: `GET /apps/transformometro-api/transformometro/health` → `db_ready: true`
6. Integração (rede Docker): `curl -H "X-Delpi-Service-Token: $API_DELPI_INTERNAL_SERVICE_TOKEN" http://transformometro-api:8000/transformometro/integrations/engineering/transforma-mais/processes/summary`
