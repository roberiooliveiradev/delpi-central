# PAC Qualidade — Planos de Ação (`/quality/action-plans`)

CRUD e leitura consolidada de **planos de ação central de qualidade** (PAC), persistidos no PostgreSQL de plugins (`schema quality`).

**Plugin consumidor:** `plugins/quality-action-plans`  
**Agente GPT (escrita alternativa):** `api-pac-quality` em `pac-api.minhadelpi.com.br` — mesma base Postgres, autenticação por API key.  
**Migrations:** `api-delpi/migrations/plugins/quality-action-plans/` (V001–V006)

**Formato:** envelope `{ success, message, data, meta }` (Playbook 10).

**Headers obrigatórios (plugin):**

```http
Authorization: Bearer <access_token>
X-Delpi-Caller-App: quality-action-plans
```

---

## Permissões

| Operação | Permissões aceitas (qualquer uma) |
|----------|-----------------------------------|
| Leitura | `api-delpi.access`, `api-delpi.quality.access`, `api-delpi.quality.action-plans.read`, `dashboard-quality.view`, `quality-action-plans.access`, `quality-action-plans.read`, `quality-action-plans.manage` |
| Escrita | `api-delpi.access`, `api-delpi.quality.access`, `quality-action-plans.access`, `quality-action-plans.write`, `quality-action-plans.manage` |

Registrar manifesto: `plugins/quality-action-plans/scripts/register-manifest.sh`

---

## Endpoints — leitura

| Método | Rota | `operationId` | Descrição |
|--------|------|---------------|-----------|
| GET | `/quality/action-plans/dashboard` | `get_quality_action_plans_dashboard` | Cards executivos |
| GET | `/quality/action-plans` | `list_quality_action_plans` | Listagem paginada |
| GET | `/quality/action-plans/overdue` | `list_quality_action_plans_overdue` | Planos com ações vencidas |
| GET | `/quality/action-plans/recurrence` | `list_quality_action_plans_recurrence` | Agrupamento por `recurrence_key` (reincidência) |
| GET | `/quality/action-plans/evidences/search` | `search_quality_action_plan_evidences` | Busca textual em evidências (nome, descrição, trecho) |
| GET | `/quality/solution-patterns` | `list_quality_solution_patterns` | Padrões de solução testados |
| GET | `/quality/action-plans/{plan_id}` | `get_quality_action_plan_detail` | Detalhe completo |

### GET `/quality/action-plans/{plan_id}` — `data`

| Chave | Conteúdo |
|-------|----------|
| `plan` | Cabeçalho do plano (incl. `customer_template`, `client_nc_registry`, `template_payload`) |
| `ishikawa` | Análise Ishikawa ou `null` |
| `five_whys` | 5 Porquês (ocorrência + `detection_why_*`) ou `null` |
| `team_members` | Equipe de análise (relatório 8D) |
| `evidences` | Evidências anexadas |
| `actions` | Ações (`cause_track` quando aplicável) |
| `history` | Histórico de eventos |

### GET `/quality/action-plans/dashboard`

**Query:** `branch_code` (`01` \| `02`, opcional), `nonconformity_scope` (`internal` \| `external`, opcional), `months` (1–36, padrão `12` — janela dos KPIs de tempo)

**`data` (consolidado):** `open_plans`, `critical_open`, `waiting_validation`, `completed_this_month`, `overdue_actions`, `overdue_plans`, `by_branch`, `by_scope`, `open_internal`, `open_external`, `timing`

**`data.timing`:** `window_months`, `avg_closure_days` (dias, `created_at`/`detected_at` → `closed_at`), `closure_sample_size`, `avg_time_to_effectiveness_days`, `effectiveness_sample_size`

**`data.breakdowns`:** `window_months`, `by_root_cause[]`, `by_failure_mode[]`, `by_action_type[]` — cada item `{ label, total }` (top 8 no período)

**`data.rankings`:** `window_months`, `by_customer[]`, `by_product[]`, `by_owner[]` — cada item `{ label, total, open_plans }` (top 8 no período)

**`data.recurrence_alert`:** `window_months`, `groups_detected`, `plans_in_window`, `open_plans_in_recurrence`, `top_groups[]` — cada grupo `{ recurrence_key, product_code, failure_mode, branch_code, plans_in_window, total_plans, open_plans }` (≥ 2 aberturas no período; top 5)

**`data.effectiveness_by_action_type`:** `window_months`, `overall`, `by_action_type[]` — cada bucket `{ reviewed_plans, effective_plans, partially_effective_plans, ineffective_plans, effectiveness_rate }` (% `effective` / `reviewed`; planos com `effectiveness_verified_at` no período); itens por tipo incluem `action_type`

### GET `/quality/action-plans` e `/overdue`

**Query:** `status`, `severity`, `product_code`, `customer_name`, `owner_user_id`, `branch_code`, `nonconformity_scope`, `department`, `root_cause_category`, `overdue_only` (bool), `page`, `page_size`

---

## Endpoints — escrita

| Método | Rota | `operationId` | Descrição |
|--------|------|---------------|-----------|
| POST | `/quality/action-plans` | `create_quality_action_plan` | Criar plano |
| PATCH | `/quality/action-plans/{plan_id}` | `update_quality_action_plan` | Atualizar identificação do plano |
| PATCH | `/quality/action-plans/{plan_id}/status` | `update_quality_action_plan_status` | Atualizar status |
| PUT | `/quality/action-plans/{plan_id}/ishikawa` | `upsert_quality_action_plan_ishikawa` | Ishikawa (upsert) |
| PUT | `/quality/action-plans/{plan_id}/five-whys` | `upsert_quality_action_plan_five_whys` | 5 Porquês duplo (upsert) |
| POST | `/quality/action-plans/{plan_id}/actions` | `create_quality_action_plan_actions` | Criar ações |
| PATCH | `/quality/action-plans/{plan_id}/actions/{action_id}` | `update_quality_action_plan_action` | Atualizar ação |
| POST | `/quality/action-plans/{plan_id}/effectiveness-review` | `record_quality_action_plan_effectiveness` | Registrar eficácia |
| PUT | `/quality/action-plans/{plan_id}/rnc-8d` | `upsert_quality_action_plan_rnc_8d` | Salvar relatório 8D |
| GET | `/quality/action-plans/{plan_id}/export/rnc-8d` | `export_quality_action_plan_rnc_8d` | Exportar planilha Excel |
| GET | `/quality/action-plans/{plan_id}/evidences` | `list_quality_action_plan_evidences` | Listar evidências (`q` opcional filtra no plano) |
| POST | `/quality/action-plans/{plan_id}/evidences` | `attach_quality_action_plan_evidence` | Anexar arquivo (multipart) |
| GET | `/quality/action-plans/{plan_id}/evidences/{evidence_id}/file` | — | Download do arquivo |
| DELETE | `/quality/action-plans/{plan_id}/evidences/{evidence_id}` | `delete_quality_action_plan_evidence` | Remover evidência |

### POST `/quality/action-plans` — corpo mínimo

```json
{
  "title": "Reclamação cliente — cabo X",
  "branch_code": "01",
  "nonconformity_scope": "external",
  "severity": "high",
  "status": "triage",
  "customer_name": "Cliente ABC",
  "reported_problem": "Descrição do problema"
}
```

- `branch_code`: `01` ou `02` (obrigatório)
- `nonconformity_scope`: `internal` ou `external` (obrigatório; default `external`)
- Código gerado: `PAC-YYYY-####`

### PATCH `/quality/action-plans/{plan_id}`

Campos opcionais (envie só o que mudou): `title`, `customer_name`, `customer_contact`, `product_code`, `product_description`, `batch_number`, `reported_problem`, `severity`, `branch_code`, `nonconformity_scope`, `department`, `failure_mode`, `customer_template` (`generic` \| `rnc_8d`), `client_nc_registry`, etc.

### POST evidências (multipart)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `file` | arquivo | Obrigatório (máx. 25 MB) |
| `evidence_type` | string | `email`, `pdf`, `image`, … |
| `section` | string | `general`, `containment`, `root_cause`, `attachments`, … |
| `action_id` | UUID | Opcional — vincula a uma ação do plano (V007) |
| `description` | string | Opcional |
| `knowledge_visible` | bool | Default `true` |

**Storage:** variável `PAC_EVIDENCE_UPLOAD_DIR` (default `/app/data/pac-quality-evidences`).

### Relatório 8D (V006)

- `customer_template`: `generic` ou `rnc_8d`
- `template_payload`: JSON com seções do formulário (contenção, NC, eficácia, preventiva, documentação)
- Template Excel: `api-delpi/app/content/templates/quality/rnc_8d_template.xlsx` (copiar no deploy)
- Export inclui imagens de evidência na aba `Anexos(Evidencias)` (tipos `image` ou `mime` `image/*`)

### Status do plano

`draft` → `triage` → `containment` → `root_cause_analysis` → `action_plan_defined` → `in_progress` → `waiting_validation` → `completed` | `cancelled`

### Tipos de ação

`containment`, `corrective`, `preventive`, `verification`, `standardization`, `training` — com `cause_track`: `occurrence` | `detection` quando NC 8D.

---

## Inteligência (api-pac-quality)

Casos similares, padrões de solução e sugestão de ações: `POST /quality/action-plans/intelligence/*` na **api-pac-quality** (agente GPT). Paridade de escrita com api-delpi inclui `pac_upsert_rnc_8d`, `pac_attach_plan_evidence`, `pac_update_action_plan`.

---

## Migrations

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin quality-action-plans
```

| Versão | Conteúdo |
|--------|----------|
| V006 | `customer_template`, `rnc_8d`, evidências com arquivo, equipe, trilha detecção |

---

## Testes e smoke

```bash
cd delpi-central
.venv/bin/python -m pytest api-delpi/tests/test_quality_action_plans_dashboard.py \
  api-delpi/tests/test_quality_action_plans_write_use_cases.py -q

TOKEN="<jwt>" bash scripts/homologacao/check-quality-action-plans.sh
```
