# DATA-MODEL — supplies-api (estado Minha DELPI)

Princípio: **não persistir cópia de TOTVS**. External keys = códigos Protheus (`branch`, `product_code`, `supplier_code` + `store`, `request_number`, `order_number`).

Schema Postgres proposto: `supplies` em `postgres-plugins`.  
Schema `purchase_requests` permanece com ownership atual até C2 ([ADR-002](./adr/ADR-002-purchase-requests-api.md)).

A autorização de leitura/escrita sobre entidades deste schema segue [ADR-007](./adr/ADR-007-permission-minimization.md): capability mínima + unidade + ownership/escopo de recurso + regra de negócio.

---

## 1. Hipóteses rejeitadas

| Entidade | Motivo |
|---|---|
| clone SC1 / snapshot diário de SC | regra e leitura canônica já existem na api-delpi |
| `savings_targets` | meta pertence ao Strategic Indicators |
| `supplier_scorecard_facts` P0 | calcular/compor antes de materializar |
| espelho SA2/SB1 | cadastro TOTVS |
| tabela de permissions local | RBAC é Core API |

---

## 2. Identidade de usuário (P-13 — FECHADO E2.S4)

| Campo | Valor |
|---|---|
| `canonical_user_id_source` | Core API `GET /me` → campo `id` (UUID do usuário Delpi) |
| column type | `UUID` |
| mapping strategy | JWT `sub` só em `keycloak_sub` (audit/trace); PK/FK de domínio = `user_id` Core |
| rollback/migration strategy | migration SQL versionada imutável; não reescrever V001; correção = V00N nova |

**Não** usar Keycloak `sub` como PK. **Não** misturar os dois identificadores na mesma coluna.

---

## 3. Entidades justificadas

### 3.1 `supply_user_preferences`

Preferências do **Portal Suprimentos** (tema, `default_branch`, …). UI canônica de edição = **WF-USER** (`/users/:userId`, self); API também exposta em `/me/preferences` (mesmo owner). Não confundir com perfil global Minha DELPI (`/profile` no Portal host).

- propósito: última filial, densidade e preferências próprias do Portal;
- owner: supplies-api;
- PK: `user_id` canônico;
- campos P0: `default_branch`, `table_density`, timestamps;
- `default_branch` deve pertencer a `allowedUnits` no momento da gravação;
- `home_layout_json` fica fora da P0 até existir caso de uso homologado;
- lifecycle: upsert do próprio usuário.

### 3.2 `supplier_notes`

**Escopo P0 decidido: nota de equipe/unidade, não privada e não global irrestrita.**

- propósito: contexto interno operacional no Fornecedor 360;
- external key: `branch`, `supplier_code`, `store`;
- leitura: usuário com `supplies.operations.access` e acesso à `branch`;
- criação: mesma capability + fornecedor/unidade autorizados;
- edição: autor da nota ou regra de equipe/admin explicitamente homologada;
- remoção: soft delete; nunca apagar trilha de auditoria;
- campos: `id UUID`, `branch`, `supplier_code`, `store`, `body`, `created_by_user_id`, `updated_by_user_id`, `created_at`, `updated_at`, `deleted_at`, `version`;
- índice: `(branch, supplier_code, store, created_at DESC)`;
- concorrência P0: **optimistic locking obrigatório** por `version` ou `updated_at` comparado no PATCH; conflito → 409.

Não criar permission `supplier-notes.write` por padrão. Se a homologação provar públicos distintos para leitura e escrita, revisar ADR-007.

### 3.3 `supply_tasks`

Unifica follow-up operacional e tarefas próprias do Portal.

Campos P0:

```text
id UUID
status: open|done|canceled
task_type: follow_up|alert_ack|note_action
due_on
assignee_user_id
created_by_user_id
title
body
ref_kind
ref_branch
ref_keys_json
created_at
updated_at
version
```

`ref_kind` permitido:

```text
supplier
product
purchase_request
purchase_order
safety_stock_item
```

`ref_keys_json` **não é JSON livre**. Cada `ref_kind` possui schema de validação:

| ref_kind | chaves mínimas |
|---|---|
| supplier | `supplier_code`, `store` |
| product | `product_code` |
| purchase_request | `request_number`, opcional `item` conforme contrato |
| purchase_order | `order_number`, opcional `item` |
| safety_stock_item | `product_code` |

`ref_branch` é obrigatório quando o recurso for filial-específico.

Autorização:

```text
portal.access
+ capability do recurso referenciado
+ unit scope
+ ownership/equipe
→ operação permitida
```

Não criar `tasks.view/write/create/complete` na P0 sem nova evidência de segregação.

Índices:

- `(assignee_user_id, status, due_on)`;
- `(ref_kind, ref_branch)`;
- índice para lookup do recurso referenciado conforme volume real.

### 3.4 Idempotência de `supply_tasks`

Não usar `UNIQUE(..., open)` se `open` não é coluna.

Preferência P0:

- gerar `ref_fingerprint` determinístico para tasks automáticas;
- índice unique parcial para tasks automáticas abertas, por exemplo conceitualmente:

```sql
UNIQUE (task_type, ref_kind, ref_fingerprint)
WHERE status = 'open' AND source = 'system'
```

Tasks manuais não devem ser deduplicadas pelo mesmo critério sem requisito funcional.

O SQL exato deve seguir a tecnologia de migration escolhida e testes de concorrência.

### 3.5 `supply_alert_events` — P1, condicional

Não criar preventivamente. Primeiro medir latência/carga do `/home/attention`.

Só materializar se houver evidência de:

- custo de recomposição alto;
- necessidade de ack/histórico;
- necessidade de distribuição assíncrona.

### 3.6 `portal_settings`

Não usar key/value irrestrito.

Criar **catálogo tipado de settings permitidos** no código da aplicação, com:

```text
key
schema/type
default
validation
owner
help text
```

Banco persiste apenas keys conhecidas. Keys desconhecidas → 422.

Administração exige `supplies.administration.manage` + unidade quando o setting for unit-scoped.

### 3.7 `audit_logs`

Audita CUD funcional da supplies-api; não substitui audit Core de RBAC.

Campos mínimos:

```text
id
actor_user_id
action
entity
entity_id
branch quando aplicável
request_id
payload_redacted
created_at
```

Não logar JWT, cookies, secrets ou body integral sensível.

### 3.8 `outbox_events`

Somente quando jobs/notificações de Solicitações migrarem na C2. Herdar padrão existente; não criar na fundação P0 sem necessidade.

---

## 4. Schema `purchase_requests`

O schema existente continua inalterado até C2:

- visibility scopes;
- user mappings;
- subscriptions;
- cursors/eventos de PO/receipt.

C2 muda o **process owner** para supplies-api sem renome obrigatório do schema. Migrations aplicadas permanecem imutáveis.

Sequência obrigatória:

```text
C1 composição
→ paridade inicial
→ C2 ownership + jobs + reconciliação
→ paridade final
→ C3 cutover
```

---

## 5. Migrations

Não usar expressão ambígua `Alembic/V001`.

Pela decisão de framework do [ADR-001](./adr/ADR-001-supplies-api.md), a proposta P0 é **Alembic** para o schema `supplies`, salvo revisão explícita antes da E2.

Regras:

- migration aplicada é imutável;
- expand-and-contract quando houver coexistência de versões;
- rollback deve considerar aplicação antiga + schema novo;
- C2 não reescreve migrations do `purchase-requests-api`.

---

## 6. Anexos

Fora da P0. Se tasks ganharem arquivos futuramente: storage persistente, MIME/tamanho validados e nenhuma gravação em filesystem efêmero do container.
