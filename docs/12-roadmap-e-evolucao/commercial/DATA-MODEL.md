# Portal Comercial — modelo de dados (`commercial-api`)

> **Schema Postgres proposto:** `commercial`  
> **Produto:** Portal Comercial (`id` técnico `commercial`)  
> **Status:** especificação física (ago/2026) — ainda **não** aplicada como migration  
> **Playbook:** [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md) § 8  
> **Fronteiras:** [PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md)  
> **ADR:** [adr/ADR-001-commercial-api.md](./adr/ADR-001-commercial-api.md)

**Fora deste documento:** tabelas TOTVS (SC5/SC6/SA1/AD*…). Pedidos, propostas e cadastro de cliente continuam na api-delpi; aqui só há **referências** (`customer_code`+`customer_store`, `order_branch`+`order_number`+`line_item`, etc.).

---

## 1. Convenções

| Regra | Valor |
|-------|--------|
| Nomes de tabela/coluna | **English** snake_case |
| PK | `UUID` · `gen_random_uuid()` (extensão `pgcrypto`) |
| Tempo | `TIMESTAMPTZ` em **UTC** |
| Usuário | `user_id` / `*_user_id` = Keycloak `sub` (`TEXT`) |
| Cliente TOTVS | `customer_code` + `customer_store` (trim); chave lógica `code\|store` |
| Pedido TOTVS | `order_branch` + `order_number` + `line_item` (quando linha) |
| Concorrência | `version INT NOT NULL DEFAULT 1` em entidades editáveis (optimistic lock) |
| Soft delete | `deleted_at TIMESTAMPTZ NULL` quando histórico obrigatório |
| Motivo sensível | `reason_code` (FK lógica → `reference_reasons.code`) + `reason_note TEXT` |
| JSON flexível | `JSONB` só para metadados/extensões — campos de filtro ficam tipados |
| Money | `NUMERIC(18,2)` |
| Percentuais | `NUMERIC(5,2)` (0–100) ou `NUMERIC(7,4)` se probabilidade 0–1 — ver coluna |
| Binários | metadado na tabela + arquivo em volume Compose (`persistent-upload-storage`) |
| **Escalabilidade** | Índices nas chaves de lista/filtro desde M1; outbox para side-effects; sem denormalizar TOTVS em massa — ver playbook § 14 |

### Ondas de migration

| Onda | Fase | Tabelas |
|------|------|---------|
| **M1** | F2 | Carteira + avatars (+ `audit_log` mínimo) |
| **M2** | F5 | Tasks, activities, worklist support, visits leves, outbox |
| **M3** | F6 | Opportunities, pipeline refs, forecast |
| **M4** | F7 | Samples, order confirmations, delivery exceptions |
| **M5** | Admin | `reference_*`, `sla_policies`, account plans, data quality |

---

## 2. Diagrama de relacionamentos (núcleo)

```mermaid
erDiagram
  seller_portfolios ||--o{ seller_customers : has
  seller_customers }o--|| customer_ref : "code+store"
  customer_avatars }o--|| customer_ref : "code+store"

  opportunities ||--o{ opportunity_stage_history : tracks
  opportunities ||--o{ opportunity_products : has
  opportunities ||--o{ tasks : spawns
  opportunities ||--o{ activities : logs
  opportunities ||--o{ forecast_items : may_include

  forecast_cycles ||--o{ forecast_submissions : has
  forecast_submissions ||--o{ forecast_items : has
  forecast_submissions ||--o{ forecast_adjustments : has
  forecast_submissions ||--o{ forecast_approvals : has
  forecast_cycles ||--o{ forecast_snapshots : has

  sample_developments ||--o{ sample_stage_history : tracks
  order_confirmation_cases ||--o{ order_confirmation_stage_history : tracks
  delivery_exceptions ||--o{ delivery_exception_actions : has

  reference_reasons ||--o{ opportunity_stage_history : classifies
  sla_policies ||--o{ tasks : may_govern
```

`customer_ref` não é tabela — é o par TOTVS referenciado.

---

## 3. Onda M1 — Carteira e avatar (F2)

Origem legada: schema `pedidos_venda_abertos` (`sellers`, `seller_customers`, `customer_avatars`).  
No alvo: schema `commercial`, nomes EN alinhados ao playbook.

### 3.1 `seller_portfolios`

Carteira de um usuário Minha DELPI (antes: `pedidos_venda_abertos.sellers`).

| Coluna | Tipo | Constraints / notas |
|--------|------|---------------------|
| `id` | UUID | PK, default `gen_random_uuid()` |
| `user_id` | TEXT | NOT NULL, **UNIQUE** — Keycloak sub |
| `display_name` | TEXT | NOT NULL — nome exibido |
| `active` | BOOLEAN | NOT NULL, default `TRUE` |
| `created_by_user_id` | TEXT | NULL |
| `created_at` | TIMESTAMPTZ | NOT NULL, default `NOW()` |
| `updated_at` | TIMESTAMPTZ | NOT NULL, default `NOW()` |
| `version` | INT | NOT NULL, default `1` |
| `deleted_at` | TIMESTAMPTZ | NULL — soft deactivate preferencial via `active=false`; `deleted_at` se purge lógico |

**Índices:** `(active)`; `(user_id)` já único.

**Migração:** `INSERT … SELECT` de `pedidos_venda_abertos.sellers` → mapear `id` preservado se possível (mesmo UUID).

### 3.2 `seller_customers`

Vínculo carteira ↔ cliente TOTVS (antes: `seller_customers`).

| Coluna | Tipo | Constraints / notas |
|--------|------|---------------------|
| `id` | UUID | PK |
| `seller_portfolio_id` | UUID | NOT NULL, FK → `seller_portfolios(id)` ON DELETE CASCADE |
| `customer_code` | TEXT | NOT NULL |
| `customer_store` | TEXT | NOT NULL |
| `customer_name` | TEXT | NULL — cache de exibição; fonte canônica TOTVS |
| `created_at` | TIMESTAMPTZ | NOT NULL, default `NOW()` |
| `created_by_user_id` | TEXT | NULL |

**Único:** `(seller_portfolio_id, customer_code, customer_store)`.  
**Índices:** `(seller_portfolio_id)`; `(customer_code, customer_store)`.

### 3.3 `customer_avatars`

Metadado do logo; bytes no volume (ex.: `/app/data/commercial-avatars/{code}_{store}`).

| Coluna | Tipo | Constraints / notas |
|--------|------|---------------------|
| `id` | UUID | PK |
| `customer_code` | TEXT | NOT NULL |
| `customer_store` | TEXT | NOT NULL |
| `file_name` | TEXT | NOT NULL — nome original |
| `storage_key` | TEXT | NOT NULL — path relativo no volume (novo vs legado) |
| `content_type` | TEXT | NOT NULL |
| `byte_size` | BIGINT | NULL |
| `uploaded_by_user_id` | TEXT | NULL |
| `created_at` | TIMESTAMPTZ | NOT NULL, default `NOW()` |
| `updated_at` | TIMESTAMPTZ | NOT NULL, default `NOW()` |
| `version` | INT | NOT NULL, default `1` |

**Único:** `(customer_code, customer_store)`.  
**Índice:** `(customer_code, customer_store)`.

> Legado V002 não tinha `storage_key`/`byte_size` — preencher no backfill (`storage_key` = convenção antiga do path).

### 3.4 `audit_log` (mínimo M1; expandido depois)

Trilha imutável (append-only).

| Coluna | Tipo | Constraints / notas |
|--------|------|---------------------|
| `id` | UUID | PK |
| `occurred_at` | TIMESTAMPTZ | NOT NULL, default `NOW()` |
| `actor_user_id` | TEXT | NOT NULL |
| `action` | TEXT | NOT NULL — ex.: `seller_portfolio.transfer_customers` |
| `entity_type` | TEXT | NOT NULL — ex.: `seller_portfolio` |
| `entity_id` | TEXT | NOT NULL — UUID ou chave composta |
| `branch` | TEXT | NULL |
| `payload` | JSONB | NOT NULL, default `{}` — antes/depois resumido |
| `reason_code` | TEXT | NULL |
| `reason_note` | TEXT | NULL |
| `correlation_id` | TEXT | NULL |
| `ip` | TEXT | NULL — se disponível |

**Índices:** `(entity_type, entity_id, occurred_at DESC)`; `(actor_user_id, occurred_at DESC)`; `(occurred_at DESC)`.

**Proibido:** UPDATE/DELETE em runtime de aplicação.

---

## 4. Onda M2 — Worklist, atividades, visitas (F5)

### 4.1 `tasks`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `title` | TEXT NOT NULL | |
| `description` | TEXT | |
| `task_type` | TEXT NOT NULL | `follow_up` \| `call` \| `email` \| `visit` \| `internal` \| `other` |
| `status` | TEXT NOT NULL | `open` \| `done` \| `cancelled` \| `deferred` |
| `priority` | TEXT NOT NULL | `low` \| `normal` \| `high` \| `critical` · default `normal` |
| `due_at` | TIMESTAMPTZ | |
| `completed_at` | TIMESTAMPTZ | |
| `assignee_user_id` | TEXT NOT NULL | |
| `created_by_user_id` | TEXT NOT NULL | |
| `customer_code` / `customer_store` | TEXT | conta opcional |
| `opportunity_id` | UUID NULL | FK → `opportunities` (nullable até M3; criar FK na M3) |
| `prospect_id` | UUID NULL | FK → `prospects` (M2/M3) |
| `related_entity_type` / `related_entity_id` | TEXT | polimórfico leve |
| `sla_policy_id` | UUID NULL | FK → `sla_policies` |
| `sla_due_at` | TIMESTAMPTZ | |
| `defer_reason_code` / `defer_note` | TEXT | |
| `version` | INT NOT NULL DEFAULT 1 | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |
| `deleted_at` | TIMESTAMPTZ | |

**Índices:** `(assignee_user_id, status, due_at)`; `(customer_code, customer_store)`; `(due_at) WHERE status = 'open'`.

### 4.2 `task_dependencies`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `task_id` | UUID NOT NULL | FK → `tasks` ON DELETE CASCADE |
| `depends_on_task_id` | UUID NOT NULL | FK → `tasks` ON DELETE CASCADE |
| `created_at` | TIMESTAMPTZ NOT NULL | |

**Único:** `(task_id, depends_on_task_id)`.  
Check: `task_id <> depends_on_task_id`.

### 4.3 `activities`

Registro imutável de interação (timeline).

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `activity_type` | TEXT NOT NULL | `call` \| `email` \| `meeting` \| `visit` \| `note` \| `system` |
| `subject` | TEXT | |
| `body` | TEXT | |
| `occurred_at` | TIMESTAMPTZ NOT NULL | |
| `actor_user_id` | TEXT NOT NULL | |
| `customer_code` / `customer_store` | TEXT | |
| `prospect_id` | UUID NULL | |
| `opportunity_id` | UUID NULL | |
| `task_id` | UUID NULL | FK → `tasks` |
| `visit_id` | UUID NULL | FK → `visits` |
| `metadata` | JSONB NOT NULL DEFAULT `{}` | |
| `created_at` | TIMESTAMPTZ NOT NULL | |

**Índices:** `(customer_code, customer_store, occurred_at DESC)`; `(opportunity_id, occurred_at DESC)`; `(prospect_id, occurred_at DESC)`.

### 4.4 `prospects`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | identificador interno estável pré-TOTVS |
| `legal_name` | TEXT NOT NULL | |
| `trade_name` | TEXT | |
| `document_id` | TEXT | CNPJ/CPF normalizado (busca) |
| `origin_code` | TEXT | catálogo configurável |
| `status` | TEXT NOT NULL | `new` \| `in_contact` \| `qualified` \| `nurturing` \| `converted` \| `disqualified` \| `lost` |
| `owner_user_id` | TEXT NOT NULL | |
| `team_key` | TEXT | |
| `branch` | TEXT | filial comercial |
| `territory_code` | TEXT | |
| `segment_code` | TEXT | |
| `subsegment_code` | TEXT | |
| `potential_amount` | NUMERIC(18,2) | |
| `potential_qty` | NUMERIC(18,4) | |
| `next_action_at` | TIMESTAMPTZ | |
| `next_action_summary` | TEXT | |
| `converted_customer_code` / `converted_customer_store` | TEXT | preenchidos na conversão |
| `converted_at` | TIMESTAMPTZ | |
| `converted_by_user_id` | TEXT | |
| `disqualify_reason_code` | TEXT | |
| `tags` | TEXT[] | ou JSONB |
| `version` | INT NOT NULL DEFAULT 1 | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |
| `deleted_at` | TIMESTAMPTZ | |

**Índices:** `(owner_user_id, status)`; `(document_id)`; `(next_action_at) WHERE status NOT IN ('converted','disqualified','lost')`.

### 4.5 `prospect_contacts`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `prospect_id` | UUID NOT NULL | FK CASCADE |
| `full_name` | TEXT NOT NULL | |
| `role_title` | TEXT | |
| `email` | TEXT | |
| `phone` | TEXT | |
| `is_primary` | BOOLEAN NOT NULL DEFAULT FALSE | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

### 4.6 `visits`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `customer_code` / `customer_store` | TEXT | XOR com prospect |
| `prospect_id` | UUID NULL | |
| `scheduled_start_at` / `scheduled_end_at` | TIMESTAMPTZ | |
| `status` | TEXT NOT NULL | `planned` \| `done` \| `cancelled` \| `no_show` |
| `objective` | TEXT | |
| `agenda` | TEXT | |
| `outcome_summary` | TEXT | |
| `owner_user_id` | TEXT NOT NULL | |
| `participants` | JSONB NOT NULL DEFAULT `[]` | `[{user_id, name}]` |
| `version` | INT NOT NULL DEFAULT 1 | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |
| `deleted_at` | TIMESTAMPTZ | |

### 4.7 `integration_outbox`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `event_type` | TEXT NOT NULL | ex.: `commercial.task.overdue` |
| `aggregate_type` / `aggregate_id` | TEXT NOT NULL | |
| `payload` | JSONB NOT NULL | |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `available_at` | TIMESTAMPTZ NOT NULL DEFAULT `NOW()` | |
| `published_at` | TIMESTAMPTZ | NULL = pendente |
| `attempts` | INT NOT NULL DEFAULT 0 | |
| `last_error` | TEXT | |

**Índice:** `(available_at) WHERE published_at IS NULL`.

### 4.8 `integration_checkpoints`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `source_key` | TEXT NOT NULL UNIQUE | ex.: `api-delpi.open-orders` |
| `cursor_value` | TEXT | |
| `last_success_at` | TIMESTAMPTZ | |
| `metadata` | JSONB NOT NULL DEFAULT `{}` | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

---

## 5. Onda M3 — Oportunidades e forecast (F6)

### 5.1 `pipeline_definitions`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `code` | TEXT NOT NULL UNIQUE | |
| `name` | TEXT NOT NULL | label pt-BR pode ir em content/i18n; aqui nome operacional |
| `active` | BOOLEAN NOT NULL DEFAULT TRUE | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

### 5.2 `pipeline_stages`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `pipeline_id` | UUID NOT NULL | FK → `pipeline_definitions` |
| `code` | TEXT NOT NULL | |
| `name` | TEXT NOT NULL | |
| `sort_order` | INT NOT NULL | |
| `default_probability` | NUMERIC(5,2) | 0–100 |
| `is_won` / `is_lost` | BOOLEAN NOT NULL DEFAULT FALSE | |
| `active` | BOOLEAN NOT NULL DEFAULT TRUE | |

**Único:** `(pipeline_id, code)`.

### 5.3 `opportunities`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `title` | TEXT NOT NULL | |
| `pipeline_id` | UUID NOT NULL | FK |
| `stage_id` | UUID NOT NULL | FK → `pipeline_stages` |
| `status` | TEXT NOT NULL | `open` \| `won` \| `lost` \| `cancelled` \| `deferred` |
| `customer_code` / `customer_store` | TEXT | cliente convertido |
| `prospect_id` | UUID NULL | FK → `prospects` |
| `owner_user_id` | TEXT NOT NULL | |
| `branch` | TEXT | |
| `amount` | NUMERIC(18,2) | |
| `quantity` | NUMERIC(18,4) | |
| `probability` | NUMERIC(5,2) | override manual opcional |
| `expected_close_on` | DATE | |
| `next_action_at` | TIMESTAMPTZ | |
| `next_action_summary` | TEXT | |
| `won_at` / `lost_at` | TIMESTAMPTZ | |
| `close_reason_code` | TEXT | |
| `close_reason_note` | TEXT | |
| `external_proposal_key` | TEXT | `branch\|number\|revision` |
| `external_order_key` | TEXT | `branch\|order\|item` ou cabeçalho |
| `entered_stage_at` | TIMESTAMPTZ NOT NULL | para aging |
| `version` | INT NOT NULL DEFAULT 1 | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |
| `deleted_at` | TIMESTAMPTZ | |

**Índices:** `(owner_user_id, status)`; `(stage_id)`; `(expected_close_on)`; `(customer_code, customer_store)`.

### 5.4 `opportunity_stage_history`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `opportunity_id` | UUID NOT NULL | FK CASCADE |
| `from_stage_id` | UUID NULL | |
| `to_stage_id` | UUID NOT NULL | |
| `changed_at` | TIMESTAMPTZ NOT NULL | |
| `changed_by_user_id` | TEXT NOT NULL | |
| `reason_code` / `reason_note` | TEXT | |
| `duration_seconds` | INT | calculado na saída do estágio anterior |

### 5.5 `opportunity_products`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `opportunity_id` | UUID NOT NULL | FK CASCADE |
| `product_code` | TEXT | TOTVS |
| `family_code` | TEXT | |
| `description` | TEXT | |
| `quantity` | NUMERIC(18,4) | |
| `unit_amount` | NUMERIC(18,2) | |
| `line_amount` | NUMERIC(18,2) | |
| `created_at` | TIMESTAMPTZ NOT NULL | |

### 5.6 `forecast_cycles`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `code` | TEXT NOT NULL UNIQUE | ex.: `2026-08` |
| `period_start` / `period_end` | DATE NOT NULL | |
| `status` | TEXT NOT NULL | `draft` \| `open` \| `locked` \| `closed` |
| `opens_at` / `closes_at` | TIMESTAMPTZ | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

### 5.7 `forecast_submissions`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `cycle_id` | UUID NOT NULL | FK |
| `owner_user_id` | TEXT NOT NULL | |
| `scope` | TEXT NOT NULL | `own` \| `team` \| `branch` |
| `branch` | TEXT | |
| `status` | TEXT NOT NULL | `draft` \| `submitted` \| `approved` \| `rejected` |
| `submitted_at` | TIMESTAMPTZ | |
| `version` | INT NOT NULL DEFAULT 1 | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

**Único sugerido:** `(cycle_id, owner_user_id, scope)` para rascunho ativo (parcial único com `WHERE status IN (...)` se necessário).

### 5.8 `forecast_items`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `submission_id` | UUID NOT NULL | FK CASCADE |
| `category` | TEXT NOT NULL | `pipeline` \| `best_case` \| `commit` \| `closed` |
| `opportunity_id` | UUID NULL | |
| `external_order_key` | TEXT | |
| `amount` | NUMERIC(18,2) NOT NULL | |
| `quantity` | NUMERIC(18,4) | |
| `note` | TEXT | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

### 5.9 `forecast_adjustments`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `submission_id` | UUID NOT NULL | FK CASCADE |
| `category` | TEXT NOT NULL | mesma enum de items |
| `delta_amount` | NUMERIC(18,2) NOT NULL | |
| `justification` | TEXT NOT NULL | |
| `adjusted_by_user_id` | TEXT NOT NULL | |
| `created_at` | TIMESTAMPTZ NOT NULL | |

### 5.10 `forecast_approvals`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `submission_id` | UUID NOT NULL | FK CASCADE |
| `decision` | TEXT NOT NULL | `approved` \| `rejected` |
| `decided_by_user_id` | TEXT NOT NULL | |
| `decided_at` | TIMESTAMPTZ NOT NULL | |
| `comment` | TEXT | |

### 5.11 `forecast_snapshots`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `cycle_id` | UUID NOT NULL | FK |
| `captured_at` | TIMESTAMPTZ NOT NULL | |
| `scope_key` | TEXT NOT NULL | user/team/branch |
| `totals` | JSONB NOT NULL | pipeline/best_case/commit/closed/realized |
| `accuracy` | JSONB | preenchido pós-ciclo |

---

## 6. Onda M4 — Amostras, confirmação, exceções (F7)

### 6.1 `sample_developments`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `title` | TEXT NOT NULL | |
| `customer_code` / `customer_store` | TEXT | |
| `prospect_id` / `opportunity_id` | UUID NULL | |
| `product_code` | TEXT | |
| `status` | TEXT NOT NULL | `open` \| `paused` \| `done` \| `cancelled` \| `rejected` |
| `current_stage_code` | TEXT NOT NULL | |
| `owner_user_id` | TEXT NOT NULL | |
| `area_code` | TEXT | área atual |
| `started_at` / `due_at` / `completed_at` | TIMESTAMPTZ | |
| `pause_reason_code` | TEXT | |
| `version` | INT NOT NULL DEFAULT 1 | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

### 6.2 `sample_stage_history`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `sample_id` | UUID NOT NULL | FK CASCADE |
| `stage_code` | TEXT NOT NULL | |
| `entered_at` / `exited_at` | TIMESTAMPTZ | |
| `owner_user_id` | TEXT | |
| `area_code` | TEXT | |
| `note` | TEXT | |

### 6.3 `order_confirmation_cases`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `order_branch` | TEXT NOT NULL | |
| `order_number` | TEXT NOT NULL | |
| `line_item` | TEXT | NULL = cabeçalho |
| `customer_code` / `customer_store` | TEXT | |
| `status` | TEXT NOT NULL | `received` \| `in_review` \| `confirmed` \| `rejected` \| `cancelled` |
| `current_stage_code` | TEXT NOT NULL | |
| `requested_delivery_on` | DATE | |
| `confirmed_delivery_on` | DATE | |
| `owner_user_id` | TEXT | vendas |
| `current_area_code` | TEXT | |
| `sla_due_at` | TIMESTAMPTZ | |
| `version` | INT NOT NULL DEFAULT 1 | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

**Único:** `(order_branch, order_number, COALESCE(line_item,''))`.

### 6.4 `order_confirmation_stage_history`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `case_id` | UUID NOT NULL | FK CASCADE |
| `stage_code` | TEXT NOT NULL | |
| `area_code` | TEXT | |
| `entered_at` / `exited_at` | TIMESTAMPTZ | |
| `actor_user_id` | TEXT | |
| `note` | TEXT | |

### 6.5 `delivery_exceptions`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `order_branch` / `order_number` / `line_item` | TEXT | |
| `customer_code` / `customer_store` | TEXT | |
| `exception_type` | TEXT NOT NULL | `late` \| `partial` \| `invoiced_not_shipped` \| `other` |
| `status` | TEXT NOT NULL | `open` \| `in_progress` \| `resolved` \| `accepted` |
| `cause_code` | TEXT | internal/customer/material/capacity/transport |
| `detected_at` | TIMESTAMPTZ NOT NULL | |
| `resolved_at` | TIMESTAMPTZ | |
| `owner_user_id` | TEXT | |
| `summary` | TEXT | |
| `version` | INT NOT NULL DEFAULT 1 | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

### 6.6 `delivery_exception_actions`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `exception_id` | UUID NOT NULL | FK CASCADE |
| `action_type` | TEXT NOT NULL | `justification` \| `plan` \| `note` \| `resolve` |
| `body` | TEXT NOT NULL | |
| `due_at` | TIMESTAMPTZ | |
| `assignee_user_id` | TEXT | |
| `created_by_user_id` | TEXT NOT NULL | |
| `created_at` | TIMESTAMPTZ NOT NULL | |

### 6.7 `approvals`

Aprovação genérica (desconto, margem, exceção).

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `approval_type` | TEXT NOT NULL | `discount` \| `margin` \| `exception` \| `other` |
| `status` | TEXT NOT NULL | `pending` \| `approved` \| `rejected` \| `cancelled` |
| `subject_type` / `subject_id` | TEXT NOT NULL | |
| `requested_by_user_id` | TEXT NOT NULL | |
| `decided_by_user_id` | TEXT | |
| `payload` | JSONB NOT NULL DEFAULT `{}` | |
| `requested_at` / `decided_at` | TIMESTAMPTZ | |
| `comment` | TEXT | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

---

## 7. Onda M5 — Conta, referências, SLA, qualidade

### 7.1 `account_plans`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `customer_code` / `customer_store` | TEXT NOT NULL | |
| `version_number` | INT NOT NULL | |
| `status` | TEXT NOT NULL | `draft` \| `active` \| `archived` |
| `objectives` | TEXT | |
| `risks` | TEXT | |
| `strategy` | TEXT | |
| `owner_user_id` | TEXT NOT NULL | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

**Único:** `(customer_code, customer_store, version_number)`.

### 7.2 `account_plan_actions`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `account_plan_id` | UUID NOT NULL | FK CASCADE |
| `title` | TEXT NOT NULL | |
| `assignee_user_id` | TEXT | |
| `due_at` | TIMESTAMPTZ | |
| `status` | TEXT NOT NULL | `open` \| `done` \| `cancelled` |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

### 7.3 `account_contacts_extension`

Dados complementares **não** canônicos do contato TOTVS.

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `customer_code` / `customer_store` | TEXT NOT NULL | |
| `full_name` | TEXT NOT NULL | |
| `role_title` | TEXT | |
| `email` / `phone` | TEXT | |
| `influence_notes` | TEXT | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

### 7.4 `reference_reasons`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `domain` | TEXT NOT NULL | `opportunity_won` \| `opportunity_lost` \| `disqualify` \| `delay` \| `pause` \| `cancel` \| … |
| `code` | TEXT NOT NULL | |
| `label_pt` | TEXT NOT NULL | texto ao usuário (exceção: conteúdo PT na tabela de catálogo) |
| `active` | BOOLEAN NOT NULL DEFAULT TRUE | |
| `sort_order` | INT NOT NULL DEFAULT 0 | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

**Único:** `(domain, code)`.

### 7.5 `reference_segments` / `reference_customer_groups` / `reference_product_families`

Padrão comum:

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `code` | TEXT NOT NULL UNIQUE | |
| `name` | TEXT NOT NULL | |
| `parent_code` | TEXT | hierarquia opcional |
| `source` | TEXT NOT NULL | `totvs` \| `manual` \| `import` |
| `active` | BOOLEAN NOT NULL DEFAULT TRUE | |
| `valid_from` / `valid_to` | DATE | |
| `metadata` | JSONB NOT NULL DEFAULT `{}` | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |
| `updated_by_user_id` | TEXT | |

`reference_customer_groups`: incluir `group_kind` (`weg_subgroup` \| `economic_group` \| `other`).

### 7.6 `sla_policies`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `code` | TEXT NOT NULL UNIQUE | |
| `name` | TEXT NOT NULL | |
| `applies_to` | TEXT NOT NULL | `task` \| `sample` \| `order_confirmation` \| `offer_stage` |
| `duration_hours` | INT NOT NULL | |
| `calendar_code` | TEXT | útil vs corrido |
| `active` | BOOLEAN NOT NULL DEFAULT TRUE | |
| `created_at` / `updated_at` | TIMESTAMPTZ NOT NULL | |

### 7.7 `data_quality_issues`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `issue_type` | TEXT NOT NULL | |
| `severity` | TEXT NOT NULL | `info` \| `warning` \| `critical` |
| `entity_type` / `entity_id` | TEXT NOT NULL | |
| `message` | TEXT NOT NULL | |
| `status` | TEXT NOT NULL | `open` \| `resolved` \| `ignored` |
| `detected_at` | TIMESTAMPTZ NOT NULL | |
| `resolved_at` | TIMESTAMPTZ | |
| `resolved_by_user_id` | TEXT | |
| `payload` | JSONB NOT NULL DEFAULT `{}` | |

---

## 8. Anexos genéricos (opcional M2+)

### `attachments`

| Coluna | Tipo | Notas |
|--------|------|--------|
| `id` | UUID PK | |
| `owner_type` / `owner_id` | TEXT NOT NULL | prospect, opportunity, visit, … |
| `file_name` | TEXT NOT NULL | |
| `storage_key` | TEXT NOT NULL | volume persistente |
| `content_type` | TEXT NOT NULL | |
| `byte_size` | BIGINT | |
| `uploaded_by_user_id` | TEXT NOT NULL | |
| `created_at` | TIMESTAMPTZ NOT NULL | |

**Índice:** `(owner_type, owner_id)`.

---

## 9. Mapa legado → alvo (F2)

| Legado (`pedidos_venda_abertos`) | Alvo (`commercial`) |
|---------------------------------|---------------------|
| `sellers` | `seller_portfolios` |
| `sellers.user_id` | `seller_portfolios.user_id` |
| `seller_customers.seller_id` | `seller_customers.seller_portfolio_id` |
| `customer_avatars` | `customer_avatars` (+ `storage_key`, `byte_size`) |

Preservar UUIDs no cutover quando possível para não quebrar favoritos/logs.

---

## 10. O que **não** vira tabela Delpi

| Dado | Onde fica |
|------|-----------|
| Pedido / item / saldo / entrega | TOTVS via api-delpi |
| NF saída / billing series | api-delpi |
| Proposta OV / AD* | api-delpi |
| ROL / OTD / hit rate | api-delpi (+ SI metas) |
| Cadastro SA1 completo | TOTVS |

---

## 11. Checklist antes da primeira migration M1

1. [ ] Schema `commercial` no Postgres plugins (runner próprio da `commercial-api`, não misturar com `run_plugins_migrations` da api-delpi sem ADR).
2. [ ] Volume avatars nos dois composes.
3. [ ] Teste de backfill contagem `sellers` = `seller_portfolios`.
4. [ ] Dual-read até cutover MFE/Portal Comercial.
5. [ ] Nunca `reset` em produção.

---

## 12. Referências

- SQL legado: `api-delpi/migrations/plugins/pedidos-venda-abertos/V001__*.sql`, `V002__*.sql`
- Estilo documental: [delpi-reports/SCHEMA.md](../delpi-reports/SCHEMA.md)
- Wireframes: [WIREFRAMES.md](./WIREFRAMES.md)
