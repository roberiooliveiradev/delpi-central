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

Ver [migrations/README.md](migrations/README.md) (V001–V005).

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
| Processos / revisões | `/processos`, `/revisoes`, `/revisoes/{id}/ativar` |
| Workflow | `POST /revisoes/{id}/workflow/submeter`, `/aprovar`, `/rejeitar` |
| Recursos | `/recursos-compartilhados`, vínculos `/revisao-recursos-compartilhados` |
| Dashboard | `/dashboard/resumo`, `/alertas`, `/export.csv`, `/export.xls`, `POST /recalcular` (full ou `?processo_id=` / `?revisao_id=` / competências) |
| Integração | `/integrations/engineering/transforma-mais/processes` |

## Importação da planilha (Transforma+)

Variáveis (mesmos GIDs do `api-delpi` / `infra/.env`):

- `TRANSFORMA_MAIS_SHEET_ID`
- `TRANSFORMA_MAIS_GID_PROCESSOS`, `_REVISAO`, `_MEDICOES`, `_INVESTIMENTOS`, `_RECURSOS_COMPARTILHADOS`, `_REVISAO_RECURSOS_COMPARTILHADOS`

CLI:

```bash
python scripts/migrate_transforma_mais_sheet.py --preview
python scripts/migrate_transforma_mais_sheet.py --apply --replace   # truncate + import + recalc
python scripts/migrate_transforma_mais_sheet.py --apply             # merge por codigo_processo
```

HTTP (JWT): `GET /import/preview`, `POST /import/apply`

## Integração engenharia / SI

- `GET /transformometro/integrations/engineering/transforma-mais/processes`
- `GET /transformometro/integrations/engineering/transforma-mais/processes/summary`

Consumidores: `shared/transformometro_client` + `API_DELPI_INTERNAL_SERVICE_TOKEN`.

## Documentação

- [docs/12-roadmap-e-evolucao/transformometro-app/](../docs/12-roadmap-e-evolucao/transformometro-app/README.md)
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
