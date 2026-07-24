# Lançamento de Notas Fiscais — `/lancamento-notas-fiscais`

Fila operacional de **solicitações de lançamento de NF de entrada** no Protheus: cadastro após recebimento físico, atendimento (iniciar / bloquear / retomar), comentários, conciliação automática com `SF1` e confirmação manual (**Já lançada**) quando o match não fecha.

**Permissões do plugin** (não usar só `api-delpi.access`):

| Código | Uso |
|--------|-----|
| `lancamento-notas-fiscais.access` | Abrir o MFE / refresh de fila |
| `lancamento-notas-fiscais.create` | Criar, corrigir próprias, comentar, cancelar própria `pending` |
| `lancamento-notas-fiscais.view` | Consultar todas as solicitações |
| `lancamento-notas-fiscais.process` | Atender, bloquear, retomar, **Já lançada**, editar |
| `lancamento-notas-fiscais.manage` | Admin + cancelar não terminais + `reconciliation/run` |

**Formato:** envelope `{ success, message, data, meta }` (Playbook 10).

**Caller header (MFE):** `X-Delpi-Caller-App: lancamento-notas-fiscais`

Plugin: `plugins/lancamento-notas-fiscais` · Roadmap: [docs/12-roadmap-e-evolucao/lancamento-notas-fiscais/](../../../docs/12-roadmap-e-evolucao/lancamento-notas-fiscais/) · Playbook: [PLAYBOOK.md](../../../docs/12-roadmap-e-evolucao/lancamento-notas-fiscais/PLAYBOOK.md).

**Persistência:** schema Postgres `lancamento_notas_fiscais` (migrations em `api-delpi/migrations/plugins/lancamento-notas-fiscais/`).  
**ERP (leitura):** fornecedores `SA2`; matching `SF1` (+ confirmação opcional `SD1`).

**Filiais v1:** `01` (SC), `02` (ES) — **sem** gate `.view.filial-*`.

---

## Endpoints

| Método | Rota | `operationId` | Permissão |
|--------|------|---------------|-----------|
| GET | `/lancamento-notas-fiscais/suppliers` | `search_lancamento_notas_fiscais_suppliers` | `create` |
| POST | `/lancamento-notas-fiscais/requests` | `create_lancamento_notas_fiscais_request` | `create` |
| GET | `/lancamento-notas-fiscais/requests` | `list_lancamento_notas_fiscais_requests` | qualquer read* |
| GET | `/lancamento-notas-fiscais/requests/{id}` | `get_lancamento_notas_fiscais_request` | qualquer read* |
| PATCH | `/lancamento-notas-fiscais/requests/{id}` | `update_lancamento_notas_fiscais_request` | create / process / manage |
| POST | `/lancamento-notas-fiscais/requests/{id}/start` | `start_lancamento_notas_fiscais_request` | process / manage |
| POST | `/lancamento-notas-fiscais/requests/{id}/block` | `block_lancamento_notas_fiscais_request` | process / manage |
| POST | `/lancamento-notas-fiscais/requests/{id}/resume` | `resume_lancamento_notas_fiscais_request` | process / manage |
| POST | `/lancamento-notas-fiscais/requests/{id}/comments` | `add_lancamento_notas_fiscais_comment` | create / process / manage |
| POST | `/lancamento-notas-fiscais/requests/{id}/cancel` | `cancel_lancamento_notas_fiscais_request` | create† / manage |
| POST | `/lancamento-notas-fiscais/requests/{id}/post-manual` | `post_manual_lancamento_notas_fiscais_request` | process / manage |
| POST | `/lancamento-notas-fiscais/reconciliation/refresh` | `refresh_lancamento_notas_fiscais_reconciliation` | qualquer read* |
| POST | `/lancamento-notas-fiscais/reconciliation/run` | `run_lancamento_notas_fiscais_reconciliation` | `manage` |

\* read = `access` \| `create` \| `view` \| `process` \| `manage`  
† cancel com `create`: somente **própria** em `pending` (+ justificativa). `manage`: qualquer não terminal.

Contratos em `route_contract_registry.py` (entity `invoice_posting_request` / `invoice_posting_supplier`).

---

## Status e ações

| Status | Significado |
|--------|-------------|
| `pending` | Aguardando atendimento |
| `in_progress` | Em atendimento |
| `blocked` | Impedimento (`block_reason` + `block_description`) |
| `posted` | Lançada (auto ou manual) — terminal |
| `cancelled` | Cancelada — terminal |

**Motivos de bloqueio:** `purchase_order` \| `supplier_registration` \| `information_correction` \| `other`.

`GET .../requests/{id}` devolve `allowed_actions` (ex.: `view`, `edit`, `start`, `block`, `resume`, `post_manual`, `cancel`, `comment`) conforme papel e estado — o MFE **não** reinventa a matriz.

---

## Normalizações fiscais

| Campo | Regra |
|-------|--------|
| Documento | só dígitos; apresentação / match com **9** zeros à esquerda (`document_match_key`) |
| Série | trim + uppercase; máx. 3; `''` ≠ `'0'` |
| Valor | `amount` ≥ 0; API aceita número ou string com **vírgula** PT-BR |
| Chave de duplicidade | filial + fornecedor + loja + `document_match_key` + série (valor **não** entra) |

Duplicidade em solicitação **não cancelada** → **409** com `existing_request_id` no meta quando aplicável.

---

## GET `/suppliers`

**Query:** `query` (mín. 2 chars), `limit` (1–50, default 20)

**`data`:** `{ items: [{ code, store, name, short_name?, … }] }` — SA2 ativos (não bloqueados na busca padrão).

---

## POST `/requests`

**Body (aliases aceitos):**

| Campo | Alias | Obrigatório |
|-------|-------|-------------|
| `branch_code` | `branch` | sim (`01`\|`02`) |
| `document_number` | `document` | sim |
| `series` | — | não |
| `supplier_code` / `supplier_store` | — | sim |
| `issue_date` | — | sim (ISO date) |
| `amount` | — | sim |
| `received_at` | — | sim (ISO datetime) |
| `observation` | — | não |

Cria em `pending` com snapshot do fornecedor.

---

## GET `/requests`

**Query:** `branch`, `status`, `supplier`, `document`, `issued_from`/`issued_to`, `received_from`/`received_to`, `page`, `page_size` (máx. 100).

**Escopo:** quem só tem `create` (sem view/process/manage) vê **somente as próprias**.  
Ordenação padrão da fila: `received_at ASC` (FIFO).

**`data`:** lista paginada (`items`, `total`, …).

---

## GET `/requests/{id}`

**`data`:** solicitação + timeline (histórico/comentários) + `allowed_actions`.

---

## PATCH `/requests/{id}`

Corrige dados fiscais/operacionais em `pending` ou `blocked` (donos com `create`, ou process/manage). Não permite `PATCH` livre de `status`.

---

## Ações de atendimento

### POST `.../start`

`pending` → `in_progress` (define assignee).

### POST `.../block`

Body: `{ "block_reason": "...", "block_description": "..." }`  
`pending` \| `in_progress` → `blocked`.

### POST `.../resume`

`blocked` → `in_progress` (preserva assignee).

### POST `.../comments`

Body: `{ "body": "..." }`

### POST `.../cancel`

Body: `{ "justification": "..." }` (obrigatória).

### POST `.../post-manual` (**Já lançada**)

Body opcional: `{ "justification": "..." }` — **não obrigatória** na UI/API atual.  
`completion_source = manual`, evento `manual_posted`. Idempotente se já `posted`.

---

## Conciliação

### POST `/reconciliation/refresh`

Usado ao abrir a fila no MFE. Se cooldown ativo (**45 s**), responde sem reexecutar o lote pesado (não bloqueia a listagem). Quem pode: qualquer permissão de leitura do plugin.

### POST `/reconciliation/run`

Lote administrativo (`manage`). Body opcional: `{ "limit": N }`.  
Busy → erro de domínio recuperável (ex. 409). Match em `SF1` (`D_E_L_E_T_ = ''`); confirmação opcional `SD1`. Persistência: `sf1_recno`, `erp_entry_date`, `reconciled_at`, `completion_source = auto` quando aplicável.

**Divergência pós-`posted`:** se o cabeçalho sumir do ERP, **não** reabre — seta alerta (`divergence_*`).

---

## Exemplos curl

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
BASE=http://localhost/apps/api-delpi/lancamento-notas-fiscais

# Fila
curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: lancamento-notas-fiscais" \
     "$BASE/requests?page=1&page_size=20" | jq '.success, .meta.operationId, .data.total'

# Já lançada
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: lancamento-notas-fiscais" \
     -H "Content-Type: application/json" \
     -d '{}' \
     "$BASE/requests/<uuid>/post-manual" | jq '.success, .message'
```

---

## Migrations

| Arquivo | Conteúdo |
|---------|----------|
| `V001__create_invoice_posting_core.sql` | Tabelas requests / history / comments |
| `V002__reconciliation_refresh_control.sql` | Controle de cooldown do refresh |
| `V003__document_number_pad_9.sql` | Backfill de documento com 9 dígitos |

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin lancamento-notas-fiscais
```

---

## Referências de código

| Peça | Caminho |
|------|---------|
| Router | `app/interface/http/routes/lancamento_notas_fiscais/` |
| Use cases | `app/application/use_cases/lancamento_notas_fiscais/` |
| Normalização / cooldown | `app/domain/services/lancamento_notas_fiscais/fiscal_normalization.py` |
| Matching | `…/reconciliation_matching.py` |
| Repo Postgres | `app/infrastructure/persistence/plugins/repositories/lancamento_notas_fiscais/` |
| Composer | `app/composition/lancamento_notas_fiscais_composer.py` |
