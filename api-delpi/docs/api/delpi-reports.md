# Delpi Reports — API

> **Plugin MFE:** `plugins/reports/`  
> **Schema Postgres:** `reports` (`migrations/plugins/reports/`)  
> **Roadmap:** `docs/12-roadmap-e-evolucao/delpi-reports/`

## Base

`/apps/api-delpi/reports`

## Endpoints

| Método | Path | `operationId` | Permissão |
|--------|------|---------------|-----------|
| `GET` | `/definitions` | `list_report_definitions` | read |
| `POST` | `/definitions` | `create_report_definition` | write |
| `GET` | `/definitions/{id}` | `get_report_definition` | read |
| `PATCH` | `/definitions/{id}` | `update_report_definition` | write |
| `GET` | `/definitions/{id}/recipients` | `list_report_recipients` | read |
| `PUT` | `/definitions/{id}/recipients` | `replace_report_recipients` | write |
| `GET` | `/definitions/{id}/schedule` | `get_report_schedule` | read |
| `PUT` | `/definitions/{id}/schedule` | `upsert_report_schedule` | write |
| `DELETE` | `/definitions/{id}/schedule` | `delete_report_schedule` | write |
| `POST` | `/definitions/{id}/run` | `run_report_definition` | write |
| `GET` | `/runs` | `list_report_runs` | read |
| `GET` | `/runs/{id}` | `get_report_run` | read |
| `GET` | `/providers` | `list_report_providers` | read |
| `GET` | `/providers/safety_stock_shortage_30d/preview` | `preview_report_provider_safety_stock_shortage_30d` | read + filial |
| `POST` | `/schedules/process-pending` | `process_pending_report_schedules` | write **ou** service token |

### Create body

```json
{
  "name": "Rupturas próximos 30 dias",
  "providerKey": "safety_stock_shortage_30d",
  "params": { "branch": "01", "horizonDays": 30 },
  "active": true
}
```

### Recipients (`PUT`)

```json
{ "items": [{ "userId": "…", "email": "user@delpi.com.br" }] }
```

### Schedule (`PUT`)

```json
{
  "scheduleKind": "weekdays",
  "hour": 8,
  "minute": 0,
  "weekday": null,
  "enabled": true,
  "timezone": "America/Sao_Paulo"
}
```

`scheduleKind`:

| Valor | Comportamento |
|-------|----------------|
| `daily` | Todos os dias (inclui sábado e domingo) |
| `weekdays` | Segunda a sexta (pula fim de semana; **não** considera feriados) |
| `weekly` | Um dia da semana (`weekday` obrigatório) |

`weekday`: 0=segunda … 6=domingo (obrigatório se `weekly`).

### Run

`POST /definitions/{id}/run?trigger=manual|schedule|event` — pipeline `collect` → `render_email` → artefato HTML → Graph (`GRAPH_REPORTS_*`, lotes + retry) → `report_runs` + `report_deliveries`.

Hook interno: `trigger=event` (mesmo endpoint).

### Graph Reports (env)

Credenciais **próprias** (não usam `GRAPH_MAIL_*` do canal-denúncia):

```bash
GRAPH_REPORTS_TENANT_ID=…
GRAPH_REPORTS_CLIENT_ID=…
GRAPH_REPORTS_CLIENT_SECRET=…
GRAPH_REPORTS_MAIL_SENDER=minhadelpi@delpi.com.br
REPORTS_MAIL_BATCH_SIZE=40
REPORTS_RUN_ARTIFACTS_DIR=/app/data/reports-runs
```

Runbook: `docs/12-roadmap-e-evolucao/delpi-reports/OPS.md`.

### Cron (host)

```bash
export API_DELPI_BASE_URL=http://127.0.0.1/apps/api-delpi
export API_DELPI_INTERNAL_SERVICE_TOKEN=…
./api-delpi/scripts/process-pending-report-schedules.sh
```

Claim atômico (`FOR UPDATE SKIP LOCKED`) + avanço de `next_run_at` no claim (anti-duplicata). Sugestão crontab: `*/15 * * * *`.

## Preview — rupturas 30 dias

```
GET /reports/providers/safety_stock_shortage_30d/preview?branch=01&horizonDays=30
```

Critério: `first_shortage_date` ∈ `[as_of, as_of + horizonDays]` via `build_stock_projection` (3 SQL/filial).

## RBAC

`REPORTS_READ_PERMISSIONS`, `REPORTS_WRITE_PERMISSIONS`, `REPORTS_BRANCH_VIEW_PERMS`.

## Migration

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin reports
```

## Smoke

```bash
docker exec delpi-api-delpi python -m pytest \
  tests/test_reports_routes_smoke.py \
  tests/test_report_schedule_and_run.py \
  tests/test_safety_stock_shortage_30d_provider.py -q
```
