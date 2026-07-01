# PAC Qualidade — Planos de Ação (`/quality/action-plans`)

CRUD e leitura consolidada de **planos de ação central de qualidade** (PAC), persistidos no PostgreSQL de plugins (`schema quality`).

**Plugin consumidor:** `plugins/quality-action-plans`  
**Agente GPT (escrita alternativa):** `api-pac-quality` em `pac-api.minhadelpi.com.br` — mesma base Postgres, autenticação por API key.  
**Migrations:** `api-delpi/migrations/plugins/quality-action-plans/` (V001–V019)

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
| GET | `/quality/action-plans/my-queue` | `list_quality_action_plan_my_queue` | Fila pessoal — ações em que o usuário autenticado é responsável (`quality_action_responsibles`) |
| GET | `/quality/action-plans/assignable-users` | `list_quality_action_plan_assignable_users` | Busca usuários Delpi elegíveis para responsável / equipe 8D (proxy Core API) |
| GET | `/quality/action-plans/evidences/search` | `search_quality_action_plan_evidences` | Busca textual em evidências (nome, descrição, trecho) |
| GET | `/quality/solution-patterns` | `list_quality_solution_patterns` | Padrões de solução testados |
| GET | `/quality/action-plans/{plan_id}` | `get_quality_action_plan_detail` | Detalhe completo |

### GET `/quality/action-plans/{plan_id}` — `data`

| Chave | Conteúdo |
|-------|----------|
| `plan` | Cabeçalho do plano (incl. `customer_template`, `client_nc_registry`, `template_payload`, `was_ever_completed`) |
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

### GET `/quality/action-plans/my-queue`

**Query:** `branch_code`, `overdue_only` (bool), `page`, `page_size` — usuário via JWT (`responsible_user_id` da ação)

**`data`:** `user_id`, `summary` (`open_actions`, `overdue_actions`), `items[]` (ação + contexto do plano), `pagination`

### GET `/quality/action-plans/assignable-users`

**Query:** `q` (mín. 2 caracteres), `limit` (1–20, padrão `10`)

**`data`:** `{ "items": [{ "id": "uuid", "name": "...", "email": "a***@dominio.com" }] }` — `meta.entity` = `directory_user`, `meta.shape` = `paged_list`

**Origem:** proxy S2S para `GET /core-api/integrations/directory/users?app=quality-action-plans`. Requer `CORE_API_BASE_URL` e `CORE_API_INTEGRATIONS_SERVICE_TOKEN` na api-delpi; sem configuração retorna lista vazia.

**Uso:** vincular `responsible_user_id` em ações e `member_user_id` em `team_members` do relatório 8D (Minha fila e notificações).

---

## Delegação S2S (api-pac-quality)

Com `PAC_DELEGATE_TRANSACTIONAL_TO_API_DELPI=true`, a **api-pac-quality** repassa CRUD transacional para esta API usando `API_DELPI_INTERNAL_SERVICE_TOKEN` (JWT `internal-service`).

**Middleware `pac_service_actor_middleware`:** em rotas `/quality/action-plans/*`, quando o JWT é de serviço interno e há `X-Delpi-Actor-Id`, o ator efetivo passa a ser o analista GPT:

```http
X-Delpi-Actor-Id: <uuid ou pac-gpt-agent>
X-Delpi-Actor-Name: Nome do analista (opcional)
X-Delpi-Actor-Email: email@empresa.com (opcional)
```

Histórico, audit log e evidências gravam `created_by_*` / `actor_*` / `uploaded_by_*` (migration V017).

---

## Endpoints — escrita

| Método | Rota | `operationId` | Descrição |
|--------|------|---------------|-----------|
| POST | `/quality/action-plans` | `create_quality_action_plan` | Criar plano |
| PATCH | `/quality/action-plans/{plan_id}` | `update_quality_action_plan` | Atualizar identificação do plano |
| PATCH | `/quality/action-plans/{plan_id}/status` | `update_quality_action_plan_status` | Atualizar status |
| DELETE | `/quality/action-plans/{plan_id}` | `delete_quality_action_plan` | Marcar plano como excluído (soft delete) |
| POST | `/quality/action-plans/{plan_id}/reopen` | `reopen_quality_action_plan` | Reabrir plano `completed`/`cancelled` |
| PUT | `/quality/action-plans/{plan_id}/ishikawa` | `upsert_quality_action_plan_ishikawa` | Ishikawa (upsert) |
| PUT | `/quality/action-plans/{plan_id}/five-whys` | `upsert_quality_action_plan_five_whys` | 5 Porquês duplo (upsert) |
| POST | `/quality/action-plans/{plan_id}/actions` | `create_quality_action_plan_actions` | Criar ações |
| PATCH | `/quality/action-plans/{plan_id}/actions/{action_id}` | `update_quality_action_plan_action` | Atualizar ação |
| DELETE | `/quality/action-plans/{plan_id}/actions/{action_id}` | `delete_quality_action_plan_action` | Remover ação |
| POST | `/quality/action-plans/{plan_id}/effectiveness-review` | `record_quality_action_plan_effectiveness` | Registrar eficácia (coordenador — direto) |
| POST | `/quality/action-plans/{plan_id}/effectiveness-review/submit` | `submit_quality_action_plan_effectiveness_review` | Submeter eficácia para aprovação (analista) |
| POST | `/quality/action-plans/{plan_id}/effectiveness-review/approve` | `approve_quality_action_plan_effectiveness_review` | Aprovar submissão de eficácia |
| POST | `/quality/action-plans/{plan_id}/effectiveness-review/reject` | `reject_quality_action_plan_effectiveness_review` | Rejeitar submissão de eficácia |
| GET | `/quality/action-plans/effectiveness-review/pending` | `list_quality_action_plan_pending_effectiveness_reviews` | Fila de eficácia pendente |
| GET | `/quality/action-plans/{plan_id}/audit-log` | `list_quality_action_plan_audit_log` | Trilha de auditoria do plano |
| PUT | `/quality/action-plans/{plan_id}/rnc-8d` | `upsert_quality_action_plan_rnc_8d` | Salvar relatório 8D |
| GET | `/quality/action-plans/{plan_id}/export/rnc-8d` | `export_quality_action_plan_rnc_8d` | Exportar planilha Excel |
| GET | `/quality/action-plans/{plan_id}/export/pdf` | `export_quality_action_plan_pdf` | Exportar resumo do plano em PDF |
| GET | `/quality/action-plans/{plan_id}/export/rnc-8d/pdf` | `export_quality_action_plan_rnc_8d_pdf` | Exportar relatório 8D em PDF |
| GET | `/quality/action-plans/{plan_id}/evidences` | `list_quality_action_plan_evidences` | Listar evidências (`q` opcional filtra no plano) |
| POST | `/quality/action-plans/{plan_id}/evidences` | `attach_quality_action_plan_evidence` | Anexar arquivo (multipart) |
| GET | `/quality/action-plans/{plan_id}/evidences/{evidence_id}/file` | — | Download do arquivo |
| DELETE | `/quality/action-plans/{plan_id}/evidences/{evidence_id}` | `delete_quality_action_plan_evidence` | Remover evidência |
| PATCH | `/quality/action-plans/{plan_id}/evidences/{evidence_id}` | `update_quality_action_plan_evidence` | Atualizar metadados da evidência |
| GET | `/quality/action-plans/{plan_id}/similar-cases` | `get_quality_action_plan_similar_cases` | Casos similares + log de decisão (Onda 5.5) |

**Inteligência — `similar_cases_decision_log` (Onda 5.5):** cada resposta de casos similares traz `influence_factors` por plano e `similar_cases_decision_log.entries` com ranking explicável (`product_match`, `text_overlap`, `semantic_similarity`, etc.).

**Busca semântica (Onda 6.2):** com `PAC_SIMILARITY_EMBEDDINGS_ENABLED=true` e Ollama (`OLLAMA_BASE_URL`, `EMBEDDING_MODEL=bge-m3`), o índice grava `search_embedding` no sync e a busca combina pgvector + filtros textuais. Sem embeddings, permanece o ranking lexical (trgm/ILIKE).

**Recorrência na abertura (Onda 6.4):** `POST /quality/action-plans/intelligence/recurrence-opening-assessment` (`assess_quality_action_plan_recurrence_on_opening` / `pac_assess_recurrence_on_opening`) retorna `recurrence_score`, `alert_level`, `should_warn_before_opening` e preview de casos similares — chamar **antes** de `create_quality_action_plan`.

**Tags de evidência (Onda 6.3):** `POST .../intelligence/suggest-evidence-tags` com `ocr_text`/`file_name`/`description`; variante `.../from-image` (multipart) com OCR opcional (`PAC_EVIDENCE_OCR_ENABLED`).

**Grafo de conhecimento (Onda 6.5):** `GET /quality/action-plans/intelligence/knowledge-graph` (`get_quality_action_plan_knowledge_graph` / `pac_get_quality_knowledge_graph`) com filtros opcionais `branch_code`, `product_code`, `limit`. Retorna `nodes` (tipos `product`, `failure_mode`, `root_cause`, `effective_action`), `edges` com `plan_count`/`effective_plan_count`, `summary` e `filters`.

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

Campos opcionais (envie só o que mudou): `title`, `customer_name`, `customer_contact`, `customer_contact_email`, `customer_contact_phone`, `delpi_contact_name`, `delpi_contact_area`, `delpi_sales_rep`, `delpi_quality_contact`, `product_code`, `product_description`, `batch_number`, `reported_problem`, `severity`, `branch_code`, `nonconformity_scope`, `department`, `failure_mode`, `customer_template` (`generic` \| `rnc_8d`), `client_nc_registry`, `export_template_key`, etc.

No detalhe (`GET /{plan_id}`), o payload inclui `contact_roles` — visão resolvida dos papéis de contato (cliente vs DELPI) para leitura e export 8D.

**Cabeçalho material/NF (8D):** chaves em `template_payload` — quantidades **numéricas** com unidade separada (`defective_quantity` + `defective_quantity_unit`, `batch_quantity` + `batch_quantity_unit`, `rejected_quantity` + `rejected_quantity_unit`), além de `purchase_order`, `invoice_number`, `client_batch`, `disposition`, `return_by`, `contact_phone`. Gravação via `PUT /{plan_id}/rnc-8d` (`pac_upsert_rnc_8d`), não no PATCH de identificação.

**Status:** altere apenas via `PATCH /{plan_id}/status` — não envie `status` neste PATCH de identificação.

Vínculos com Kaizen ou Auditoria 5S não usam mais colunas em `quality_action_plans` (removidas na migration V016); amarrações futuras devem usar tabelas auxiliares dedicadas.

### POST evidências (multipart)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `file` | arquivo | Obrigatório (máx. 25 MB) |
| `evidence_type` | string | `email`, `pdf`, `image`, … |
| `section` | string | `general`, `containment`, `root_cause`, `attachments`, … |
| `action_id` | UUID | Opcional — vincula a uma ação do plano (V007) |
| `description` | string | Opcional |
| `knowledge_visible` | bool | Default `true` |

**Storage:** variável `PAC_EVIDENCE_UPLOAD_DIR` (default `/app/data/pac-evidences`).

**Deploy:** montar volume persistente no host — ver `infra/docker-compose.yml` (`${DELPI_DATA_HOST_DIR}/pac-evidences`). Sem volume, anexos são perdidos em `docker compose up --force-recreate api-delpi` (metadado permanece no Postgres).

### Relatório 8D (V006+)

- `customer_template`: `generic` ou `rnc_8d`
- `template_payload`: JSON com seções do formulário (contenção, NC, eficácia, preventiva, documentação). Campo legado `attention_to` sincroniza com `customer_contact` quando aplicável.
- **Contatos (V025):** `customer_contact*` = pessoa no cliente (WEG: G21/J21); `delpi_contact_*` = interlocutores DELPI (WEG: J5/J6 via `delpi_contact_name` + `template_payload.contact_phone`)
- `team_members[]`: `member_name` (obrigatório), `member_user_id` (opcional — UUID Delpi via `assignable-users`), `is_leader`, `department`, `sort_order` (V019)
- Ações do plano podem herdar `responsible_user_id` do membro da equipe vinculado no plugin MFE
- Export Excel 8D: `GET .../export/rnc-8d?template_key=weg_wfr20997` (ou `delpi_8d`) — preenchimento por cópia do template (preserva desenhos/setas WEG)
- Catálogo de templates: `GET /quality/action-plans/export-templates`
- Export inclui imagens de evidência na aba `Anexos(Evidencias)` (tipos `image` ou `mime` `image/*`)

### DELETE `/quality/action-plans/{plan_id}`

Soft delete: grava `deleted_at`, remove o plano das listagens e do índice de casos similares, marca evidências com `knowledge_visible = false` e registra `plan_deleted` no histórico e na auditoria. **Arquivos anexados permanecem no volume** (`PAC_EVIDENCE_UPLOAD_DIR`), mas deixam de ser acessíveis pela API e não entram em buscas de conhecimento.

**Bloqueios:** plano com status `completed`, plano que já foi concluído (mesmo reaberto), eficácia `pending_review` ou `approved`. O detalhe expõe `was_ever_completed` para o plugin desabilitar o botão de exclusão.

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
| V001 | Tabelas core PAC (`quality_action_plans`, ações, Ishikawa, 5 Porquês, histórico) |
| V002 | Sequência `PAC-YYYY-####` + submodule |
| V003 | Knowledge layer (`similarity_index`, `solution_patterns`) |
| V004 | `branch_code` |
| V005 | `nonconformity_scope` |
| V006 | `customer_template`, `rnc_8d`, evidências com arquivo, equipe, trilha detecção |
| V007 | `action_id` em evidências (vínculo com ação do plano) |
| V008 | `quality_audit_log` (append-only) |
| V009 | `quality_notification_dispatches` (dedup alertas) |
| V010 | Workflow aprovação de eficácia (submit / approve / reject) |
| V011 | `search_embedding` pgvector (busca semântica) |
| V012 | `linked_kaizen_id` (experimental — revertido na V016) |
| V013 | `linked_audit_5s_nc_id` (experimental — revertido na V016) |
| V014 | Ishikawa 6M — causas por categoria em JSONB |
| V015 | 5 Porquês — trilhas `occurrence_whys` / `detection_whys` em JSONB |
| V016 | Remove colunas de vínculo Kaizen/5S; integrações futuras via tabelas auxiliares |
| V017 | Nome/e-mail do ator em histórico, audit log e evidências |
| V018 | `customer_code` e `customer_store` (cliente Protheus SA1) no plano |
| V019 | `member_user_id` na equipe de análise 8D (`quality_analysis_team_members`) |
| V024 | `export_template_key` no plano (modelo Excel 8D preferido) |
| V025 | Papéis de contato: `customer_contact_*`, `delpi_contact_*` + `contact_roles` no detalhe |

### Variáveis — diretório e delegação PAC

| Variável | Uso |
|----------|-----|
| `CORE_API_BASE_URL` | Base da Core API (ex.: `http://delpi-core-api:8000`) |
| `CORE_API_INTEGRATIONS_SERVICE_TOKEN` | Token S2S para `GET /integrations/directory/users` |

---

## Testes e smoke

```bash
cd delpi-central
.venv/bin/python -m pytest api-delpi/tests/test_quality_action_plans_dashboard.py \
  api-delpi/tests/test_quality_action_plans_write_use_cases.py -q

TOKEN="<jwt>" bash scripts/homologacao/check-quality-action-plans.sh
```
