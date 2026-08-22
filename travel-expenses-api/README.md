# Travel Expenses API

API dedicada do plugin **Despesas de Viagem**. Bounded context próprio — não entra no `financial-api` (BFF TOTVS) nem na api-delpi.

## Escopo P0

- Prestações em rascunho (`draft`) com numeração `TE-YYYY-NNNN` por unidade/ano
- Despesas em BRL + categorias seed
- Cupons persistentes (JPEG/PNG/WebP/PDF) em volume
- Checklist de prontidão (`TravelReportCompletenessService`)
- PDF do pacote (ReportLab) sob demanda
- RBAC: dono vê os próprios; `manage` vê a unidade; `admin` vê todas

A coluna `status` já aceita `submitted` / `returned` / `approved` / `in_finance` / `closed`. **Não há rota de transição** neste P0.

## Rotas

Base via gateway: `/apps/travel-expenses-api`

| Método | Path |
|--------|------|
| GET | `/health`, `/access`, `/categories` |
| GET/POST | `/reports` |
| GET/PATCH/DELETE | `/reports/{id}` |
| GET | `/reports/{id}/audit`, `/reports/{id}/package.pdf` |
| POST/PATCH/DELETE | `/reports/{id}/expenses[/{expenseId}]` |
| POST/DELETE/GET file | `/reports/{id}/expenses/{id}/receipts[/{receiptId}]` |

Envelope: `{ success, message, data }`.

## Stack

FastAPI · Postgres (`schema travel_expenses`) · `delpi_auth` · ReportLab

## Storage

Metadado no banco + binário no disco. Volumes Compose:

| Env | Path no container |
|-----|-------------------|
| `TRAVEL_EXPENSES_RECEIPT_UPLOAD_DIR` | `/app/data/travel-expenses/receipts` |
| `TRAVEL_EXPENSES_PACKAGE_UPLOAD_DIR` | `/app/data/travel-expenses/packages` |

Host: `${DELPI_DATA_HOST_DIR}/travel-expenses/...`. Recreate do container **não** apaga cupons.

Migrations: só `up` em ambiente com dados. `TRAVEL_EXPENSES_RUN_MIGRATIONS_ON_STARTUP=true` no Compose.

## Desenvolvimento

```bash
cd travel-expenses-api
pip install -r requirements.txt
pip install -e ../shared[fastapi]
pytest tests -q
```
