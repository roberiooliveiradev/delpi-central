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

Ver [migrations/README.md](migrations/README.md) (**V001–V038**). Startup automático: `TM_RUN_MIGRATIONS_ON_STARTUP=true`.

```bash
PLUGINS_DB_HOST=localhost PLUGINS_DB_PORT=5433 ...
python -m tm_app.infrastructure.persistence.plugins.migrations_runner status
python -m tm_app.infrastructure.persistence.plugins.migrations_runner up
```

## Testes

```bash
make test
# ou na raiz do monorepo:
./scripts/ci-transformometro-api.sh
```

## Endpoints principais

| Grupo | Exemplos |
|-------|----------|
| Filiais / setores | `/filiais`, `/setores`, `GET /options` (UUID + `codigo_*`) |
| Instâncias | `GET/POST /processos/{id}/instancias`, `POST /instancias/{id}/duplicar` |
| Processos / revisões | `/processos`, `/revisoes`, `POST /revisoes/{id}/ativar`, `POST /revisoes/{id}/duplicar` |
| Matriz impacto×esforço | `GET/PUT /revisoes/{id}/matriz-impacto-esforco`, `GET /instancias/{id}/matriz-impacto-esforco` |
| Recursos | `/recursos-compartilhados` (`escopo_recurso`), vínculos |
| Dashboard | `/dashboard/*` (`view`, `filial_id`, `setor_id`), `POST /recalcular`, snapshot |
| Options | `GET /options` — catálogos + `access_scope` (RBAC filial) |
| Integração | `/integrations/engineering/transforma-mais/*` (`id` = `instancia_id`) |

## Cadastro de dados

Processos, revisões, medições e recursos são mantidos pelo CRUD e pelas telas do plugin. Backup/restauração: `GET /transformometro/data/export`, `POST /transformometro/data/import/preview` e `POST /transformometro/data/import/apply` (modos `merge` e `replace`). O export inclui processos/recursos referenciados por FK mesmo se estiverem marcados como deletados. **Substituir tudo** apaga o cadastro e recria somente o que está no JSON.

## Integração engenharia / SI

Contrato **público** (SI, dashboard-engineering): **api-delpi** `GET /engineering/transforma-mais/processes` e `.../summary`.

Backend interno (S2S):

- `GET /transformometro/integrations/engineering/transforma-mais/processes`
- `GET /transformometro/integrations/engineering/transforma-mais/processes/summary`

Detalhes: [`docs/integration-contracts.md`](docs/integration-contracts.md) · consumidores: `shared/transformometro_client` + gateway api-delpi + `API_DELPI_INTERNAL_SERVICE_TOKEN`.

## Documentação

- [docs/playbook-18-implementation-status.md](docs/playbook-18-implementation-status.md) — Playbook 18 (S1–S12 + MFE §9)
- [docs/regras-de-calculo.md](docs/regras-de-calculo.md) — fórmulas e escopo de recurso
- [docs/12-roadmap-e-evolucao/transformometro-app/](../docs/12-roadmap-e-evolucao/transformometro-app/README.md) — índice completo
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
