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

## Testes

```bash
make test
# ou: ../../scripts/ci-transformometro-api.sh
```

## Importação da planilha (Transforma+)

Variáveis (mesmos GIDs do `api-delpi` / `infra/.env`):

- `TRANSFORMA_MAIS_SHEET_ID`
- `TRANSFORMA_MAIS_GID_PROCESSOS`, `_REVISAO`, `_MEDICOES`, `_INVESTIMENTOS`, `_RECURSOS_COMPARTILHADOS`, `_REVISAO_RECURSOS_COMPARTILHADOS`

CLI:

```bash
python scripts/migrate_transforma_mais_sheet.py --preview
python scripts/migrate_transforma_mais_sheet.py --apply --replace   # truncate + import + recalc
```

HTTP (JWT):

- `GET /transformometro/import/preview`
- `POST /transformometro/import/apply` — body `{ "replace_existing": false, "recalc_dashboard": true }`

Documentação: [docs/12-roadmap-e-evolucao/transformometro-app/](../docs/12-roadmap-e-evolucao/transformometro-app/README.md)
