# CIPA API

API dedicada do plugin **CIPA** (Comissão Interna de Prevenção de Acidentes).

## Escopo v1

- Atas de reunião (CRUD, versionamento, participantes, signatários)
- Assinatura manuscrita (PNG) vinculada ao hash da versão
- Auditoria de domínio, exportação PDF, isolamento por filial `01`/`02`

## Rotas

- Health: `GET /health` → via gateway `/apps/cipa-api/health`
- Atas: `/minutes` (ver OpenAPI `/docs`)

## Stack

FastAPI · Postgres (`schema cipa`) · `delpi_auth` · bleach · ReportLab

## Desenvolvimento

```bash
cd cipa-api
pip install -r requirements.txt
pip install -e ../shared[fastapi]
pytest -q
```

Migrations: `CIPA_RUN_MIGRATIONS_ON_STARTUP=true` no Compose.

Volumes persistentes: `cipa/signatures`, `cipa/attachments`, `cipa/pdfs` sob `DELPI_DATA_HOST_DIR`.
