# Delpi Reports — API

> **Plugin MFE:** `plugins/reports/`  
> **Schema Postgres:** `reports` (`migrations/plugins/reports/`)  
> **Roadmap:** `docs/12-roadmap-e-evolucao/delpi-reports/`

## Base

`/apps/api-delpi/reports`

## Endpoints

| Método | Path | `operationId` | Permissão |
|--------|------|---------------|-----------|
| `GET` | `/definitions` | `list_report_definitions` | follow-up read (`notes.manage` ok) |
| `POST` | `/definitions` | `create_report_definition` | write |
| `GET` | `/definitions/{id}` | `get_report_definition` | follow-up read |
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
| `GET` | `/providers/safety_stock_shortage_30d/preview` | `preview_report_provider_safety_stock_shortage_30d` | follow-up read + filial |
| `GET` | `/providers/management_revenue_monthly/preview` | `preview_report_provider_management_revenue_monthly` | follow-up read |
| `POST` | `/schedules/process-pending` | `process_pending_report_schedules` | write **ou** service token |
| `GET` | `/personal-subscriptions/{providerKey}` | `get_personal_report_subscription` | **service token** (Portal PCP) |
| `PUT` | `/personal-subscriptions/{providerKey}` | `upsert_personal_report_subscription` | **service token** (Portal PCP) |
| `GET` | `/definitions/{id}/item-notes` | `list_report_shortage_item_notes` | follow-up read + filial |
| `PUT` | `/definitions/{id}/item-notes/{productCode}` | `upsert_report_shortage_item_note` | `reports.notes.manage` **ou** manage + view filial |
| `DELETE` | `/definitions/{id}/item-notes/{productCode}` | `delete_report_shortage_item_note` | `reports.notes.manage` **ou** manage + view filial |

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
  "scheduleKind": "monthly",
  "hour": 8,
  "minute": 0,
  "dayOfMonth": 1,
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
| `monthly` | Dia do mês (`dayOfMonth` 1–28; default 1) |

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

## Acompanhamento por item (Observação)

Notas humanas por produto — **não** ocultam o e-mail; na Fase 3 entram na coluna Observação.

```http
GET  /reports/definitions/{id}/item-notes
PUT  /reports/definitions/{id}/item-notes/{productCode}
DELETE /reports/definitions/{id}/item-notes/{productCode}
```

Body do `PUT`:

```json
{
  "noteText": "Previsão confirmada com o fornecedor",
  "authorDisplayName": "Maria Silva",
  "expectedReceiptDate": "2026-08-05"
}
```

`authorUserId` vem do JWT. Filial = `params.branch` da definição.

**Permissão de gravação:** `reports.notes.manage` **e** view da filial, **ou** `reports.manage` / `manage.filial-*`.  
Admins da definição não precisam da permissão nova.

### Link no e-mail (rodapé)

Com `PUBLIC_BASE_URL` configurado, o run injeta `meta.followUpPortalUrl`:

`{PUBLIC_BASE_URL}/apps/reports/acompanhamentos/{definitionId}`

O HTML do e-mail inclui o CTA «Abrir acompanhamentos no Delpi Reports». Sem `PUBLIC_BASE_URL`, o e-mail segue sem o link (warning no log).

Playbook: `docs/12-roadmap-e-evolucao/delpi-reports/PLAYBOOK-acompanhamento-observacao-ruptura.md`.

## Preview — rupturas 30 dias

`GET /reports/providers/safety_stock_shortage_30d/preview`

Query opcional `definitionId`: quando informado, a coluna **Observação** inclui
acompanhamentos gravados na definição (`item-notes`), no mesmo formato do e-mail
agendado / «Enviar agora».

```
GET /reports/providers/safety_stock_shortage_30d/preview?branch=01&horizonDays=30&definitionId=<uuid>
```

Critério: `first_shortage_date` ∈ `[as_of, as_of + horizonDays]` via `build_stock_projection` (3 SQL/filial).

## RBAC

`REPORTS_READ_PERMISSIONS`, `REPORTS_FOLLOW_UP_READ_PERMISSIONS` (inclui `notes.manage`),
`REPORTS_WRITE_PERMISSIONS`, `REPORTS_NOTES_WRITE_PERMISSIONS`,
`REPORTS_BRANCH_VIEW_PERMS`.

Permissão operacional de notas: `reports.notes.manage` (manifest do plugin `reports`).

## Migration

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin reports
```

## Smoke

```bash
docker exec delpi-api-delpi python -m pytest \
  tests/test_reports_routes_smoke.py \
  tests/test_report_schedule_and_run.py \
  tests/test_safety_stock_shortage_30d_provider.py \
  tests/test_shortage_item_notes_repository.py \
  tests/test_shortage_item_notes_use_cases.py \
  tests/test_shortage_item_note_observation_enrichment.py \
  tests/test_report_follow_up_portal_url.py \
  tests/test_reports_branch_access.py -q
```
