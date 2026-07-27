# Delpi Reports — schema Postgres

> **Migrations:** `V001__create_reports_core.sql`, `V002__reports_schedule_claim.sql`  
> **Schema:** `reports` (slug `--plugin reports`)  
> **ADR:** [ADR-001-fundacao.md](./ADR-001-fundacao.md)

Aplicar:

```bash
cd api-delpi
python scripts/run_plugins_migrations.py up --plugin reports
```

---

## Tabelas

### `report_definitions`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | `gen_random_uuid()` |
| `name` | VARCHAR(200) | obrigatório, não blank |
| `provider_key` | VARCHAR(100) | ex.: `safety_stock_shortage_30d` |
| `params` | JSONB | default `{}` |
| `active` | BOOLEAN | default `true` |
| `created_by_user_id` | VARCHAR(100) | Core user id |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

Índice: `(provider_key, active)`.

### `report_recipients`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `definition_id` | UUID FK → definitions | ON DELETE CASCADE |
| `user_id` | VARCHAR(100) | Core |
| `email` | VARCHAR(320) | snapshot resolvido |
| `active` | BOOLEAN | |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

Único: `(definition_id, user_id)`.

### `report_schedules`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `definition_id` | UUID FK | CASCADE |
| `schedule_kind` | VARCHAR(20) | `daily` \| `weekly` \| `weekdays` |
| `cron_expression` | VARCHAR(100) | opcional |
| `timezone` | VARCHAR(64) | default `America/Sao_Paulo` |
| `next_run_at` | TIMESTAMPTZ | avançado no **claim** (anti-duplicata) |
| `last_claimed_at` | TIMESTAMPTZ | auditoria do claim (V002) |
| `enabled` | BOOLEAN | |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

Único: `(definition_id)` (V002 — uma agenda por definição).  
Índice parcial: `next_run_at WHERE enabled`.

### `report_runs`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `definition_id` | UUID FK | CASCADE |
| `trigger` | VARCHAR(20) | `manual` \| `schedule` \| `event` (V002) |
| `status` | VARCHAR(20) | `pending` \| `running` \| `succeeded` \| `failed` |
| `started_at` / `finished_at` | TIMESTAMPTZ | |
| `summary` | JSONB | default `{}` |
| `error` | TEXT | |
| `created_at` | TIMESTAMPTZ | |

### `report_deliveries`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `run_id` | UUID FK → runs | CASCADE |
| `recipient_email` | VARCHAR(320) | |
| `status` | VARCHAR(20) | `pending` \| `sent` \| `failed` |
| `provider_message_id` | VARCHAR(200) | Graph, se disponível |
| `error` | TEXT | |
| `sent_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ | |
