# CLARA-MCP-SEMANTIC-001 — Capability Matrix (G1)

Migration manifest da execução do plano `CLARA-MCP-SEMANTIC-001`
(documento 119, commit base `f0e889513f`). Cobre **100%** das tools do
`tools/list` legado (43) e **100%** das governed operations do catálogo
(48). Fonte: código vigente em
`controllership_finance_app/interface/mcp/{tool_bridge,semantic_bridge,server,constants}.py`
e `application/clara/governed_writes.py`.

Legenda de colunas (conforme doc 119 §4):

- `old_tool`: nome legado no `tools/list` pré-migração.
- `consumer`: consumidor conhecido (plugin ChatGPT via discovery
  dinâmico; sem consumers por nome no repo — `INCONCLUSIVE` se houver
  consumer externo não rastreado).
- `capability_id`: id no catálogo governado (`ClaraGovernedWrites`).
- `semantic_tool`: tool alvo entre as seis finais.
- `entity/action`: chave tipada do registry semântico.
- `backend handler`: função `tool_bridge.tool_*` ou capability
  `entity.action` — os mesmos handlers das rotas BFF (`_call_route`).
- `permission`: gate efetivo (`access`/`manage`/`dre`) idêntico ao
  Portal.
- `risk`: `READ` | `GOVERNED_HIGH` | `DESTRUCTIVE` — classificação
  conservadora do doc 119 §5 (nenhuma capability foi rebaixada: a
  matriz não comprova LOW/MEDIUM sem mudança de política no owner).
- `phase_policy`: política de fase vigente.
- `migration_status`: `MIGRATED` = despachável pela superfície
  semântica com paridade de comportamento.

## 1. Ferramentas legadas → superfície semântica (43)

| old_tool | semantic_tool | entity/action | backend handler | permission | risk | phase_policy | migration_status |
|---|---|---|---|---|---|---|---|
| get_my_context | get_context | topic=`actor` | `tool_get_my_context` | access | READ | imediata | MIGRATED |
| get_catalog | get_context | topic=`catalog` | `tool_get_catalog` + `_semantic_catalog` | access | READ | imediata | MIGRATED |
| get_competence_state | read | `competence.state` | `tool_get_competence_state` | access | READ | imediata | MIGRATED |
| get_checklist_items | read | `checklist.list` | `tool_get_checklist_items` | access | READ | imediata | MIGRATED |
| list_documents | read | `document.list` | `tool_list_documents` | access | READ | imediata | MIGRATED |
| get_p3_reconciliation | read | `p3.state` | `tool_get_p3_reconciliation` | access | READ | imediata | MIGRATED |
| list_pendencies | read | `pendency.list` | `tool_list_pendencies` | access | READ | imediata | MIGRATED |
| get_package_review | read | `package.review` | `tool_get_package_review` | access | READ | imediata | MIGRATED |
| analyze_closing_blockers | analyze | `closing.blockers` | `tool_analyze_closing_blockers` | access | READ | imediata | MIGRATED |
| search_closing_knowledge | knowledge | `knowledge.search` | `tool_search_closing_knowledge` | access | READ | imediata | MIGRATED |
| get_knowledge_item | knowledge | `knowledge.get` | `tool_get_knowledge_item` | access | READ | imediata | MIGRATED |
| list_knowledge_sources | knowledge | `knowledge.sources` | `tool_list_knowledge_sources` | access | READ | imediata | MIGRATED |
| list_competences | read | `competence.list` | `tool_list_competences` | access | READ | imediata | MIGRATED |
| get_competence | read | `competence.get` | `tool_get_competence` | access | READ | imediata | MIGRATED |
| get_checklist_item | read | `checklist.get` | `tool_get_checklist_item` | access | READ | imediata | MIGRATED |
| get_closing_cockpit | read | `competence.cockpit` | `tool_get_closing_cockpit` | access | READ | imediata | MIGRATED |
| list_my_tasks | read | `task.list` | `tool_list_my_tasks` | access | READ | imediata | MIGRATED |
| get_pendency | read | `pendency.get` | `tool_get_pendency` | access | READ | imediata | MIGRATED |
| list_p3_events | read | `p3.events` | `tool_list_p3_events` | access | READ | imediata | MIGRATED |
| get_package | read | `package.get` | `tool_get_package` | access | READ | imediata | MIGRATED |
| get_document | read | `document.get` | `tool_get_document` | access | READ | imediata | MIGRATED |
| get_item_validation | read | `validation.item` | `tool_get_item_validation` | access | READ | imediata | MIGRATED |
| lookup_participants | read | `document.participants` | `tool_lookup_participants` | access | READ | imediata | MIGRATED |
| get_financial_settlements | read | `report.settlements` | `tool_get_financial_settlements` | access | READ | imediata | MIGRATED |
| get_financial_settlements_summary | read | `report.settlements_summary` | `tool_get_financial_settlements_summary` | access | READ | imediata | MIGRATED |
| get_stock_inventory | read | `report.stock_inventory` | `tool_get_stock_inventory` | access | READ | imediata | MIGRATED |
| get_stock_movements | read | `report.stock_movements` | `tool_get_stock_movements` | access | READ | imediata | MIGRATED |
| get_work_in_process | read | `report.work_in_process` | `tool_get_work_in_process` | access | READ | imediata | MIGRATED |
| get_stock_reconciliation | read | `report.stock_reconciliation` | `tool_get_stock_reconciliation` | access | READ | imediata | MIGRATED |
| get_report_matrix | read | `report.matrix` | `tool_get_report_matrix` | access | READ | imediata | MIGRATED |
| list_closing_catalogs | read | `catalog.list` | `tool_list_closing_catalogs` | manage | READ | imediata | MIGRATED |
| list_catalog_entries | read | `catalog.entries` | `tool_list_catalog_entries` | manage | READ | imediata | MIGRATED |
| list_checklist_templates | read | `template.list` | `tool_list_checklist_templates` | manage | READ | imediata | MIGRATED |
| get_checklist_template_version | read | `template.version` | `tool_get_checklist_template_version` | manage | READ | imediata | MIGRATED |
| list_received_deliveries | read | `received.deliveries` | `tool_list_received_deliveries` | dre | READ | imediata | MIGRATED |
| get_received_delivery | read | `received.delivery` | `tool_get_received_delivery` | dre | READ | imediata | MIGRATED |
| get_received_document | read | `received.document` | `tool_get_received_document` | dre | READ | imediata | MIGRATED |
| prepare_governed_operation | execute/delete | `*.(*)` — `phase=prepare` | `ClaraGovernedWrites.prepare` | por capability | GOVERNED_HIGH | PREPARE selado | MIGRATED |
| commit_proposal | execute/delete | `phase=commit` + `proposal_handle` | `ClaraGovernedWrites.commit` | por capability | GOVERNED_HIGH | ACT após consentimento | MIGRATED |
| prepare_batch | execute | `batch.phase=prepare` | `ClaraBatchOrchestrator.prepare_batch` | por capability | GOVERNED_HIGH | PREPARE selado | MIGRATED |
| confirm_batch | execute | `batch.phase=confirm` | `ClaraBatchOrchestrator.confirm_batch` | por capability | GOVERNED_HIGH | verificação de consentimento | MIGRATED |
| execute_batch | execute | `batch.phase=execute` | `ClaraBatchOrchestrator.execute_batch` | por capability | GOVERNED_HIGH | ACT após consentimento | MIGRATED |
| get_batch_status | read | `batch.status` | `tool_get_batch_status` | access | READ | imediata | MIGRATED |

## 2. Governed operations → `execute`/`delete` (48)

**Atualização SEMANTIC-002 (doc 124):** a classificação por risco
real foi publicada — 11 capabilities viraram `DIRECT_ALLOWED` (executam
já com AuthZ+idempotência física V019+read-back, sem desafio de
consentimento; `phase=prepare` segue compatível), 37 permanecem
`CONFIRMATION_REQUIRED` (`PREPARE → consentimento verificável no Portal
→ ACT`, incluindo as 6 destrutivas da tool `delete`). A matriz completa
com justificativa por efeito está no
[Documento 124](./124-clara-write-execution-risk-policy.md).

| capability_id | semantic_tool | entity/action | permission | risk | phase_policy | migration_status |
|---|---|---|---|---|---|---|
| evidence.decide_version | execute | `evidence.decide_version` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| evidence.decide_item_set | execute | `evidence.decide_item_set` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| review.record_decision | execute | `review.record_decision` | access | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| clarification.open | execute | `clarification.open` | access | DIRECT_ALLOWED | direct (prepare→consent→commit compat) | MIGRATED |
| clarification.resolve | execute | `clarification.resolve` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| competence.open | execute | `competence.open` | access | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| pendency.create | execute | `pendency.create` | access | DIRECT_ALLOWED | direct (prepare→consent→commit compat) | MIGRATED |
| pendency.claim | execute | `pendency.claim` | access | DIRECT_ALLOWED | direct (prepare→consent→commit compat) | MIGRATED |
| pendency.reassign | execute | `pendency.reassign` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| pendency.transition | execute | `pendency.transition` | access | DIRECT_ALLOWED | direct (prepare→consent→commit compat) | MIGRATED |
| pendency.confirm_classification | execute | `pendency.confirm_classification` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| p3.confirm_cutoff | execute | `p3.confirm_cutoff` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| p3.upsert_reconciliation | execute | `p3.upsert_reconciliation` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| p3.revalidate | execute | `p3.revalidate` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| package.finalize | execute | `package.finalize` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| package.reopen | execute | `package.reopen` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| package.complement | execute | `package.complement` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| package.submit_review | execute | `package.submit_review` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| package.assignment_create | execute | `package.assignment_create` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| package.assignment_deactivate | execute | `package.assignment_deactivate` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| package.start_review | execute | `package.start_review` | access | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| package.confirm_terminal_rejection | delete | `package.confirm_terminal_rejection` | access | DESTRUCTIVE | prepare→consent→commit | MIGRATED |
| package.revert_terminal_rejection | execute | `package.revert_terminal_rejection` | access | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| item.reverse_decision | execute | `item.reverse_decision` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| item.mark_not_applicable | execute | `item.mark_not_applicable` | access | DIRECT_ALLOWED | direct (prepare→consent→commit compat) | MIGRATED |
| item.revert_not_applicable | execute | `item.revert_not_applicable` | access | DIRECT_ALLOWED | direct (prepare→consent→commit compat) | MIGRATED |
| item.cancel | delete | `item.cancel` | access | DESTRUCTIVE | prepare→consent→commit | MIGRATED |
| item.create_exceptional | execute | `item.create_exceptional` | access | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| item.request_correction | execute | `item.request_correction` | access | DIRECT_ALLOWED | direct (prepare→consent→commit compat) | MIGRATED |
| item.review_correction | execute | `item.review_correction` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| document.post_message | execute | `document.post_message` | access | DIRECT_ALLOWED | direct (prepare→consent→commit compat) | MIGRATED |
| document.cancel | delete | `document.cancel` | access | DESTRUCTIVE | prepare→consent→commit | MIGRATED |
| document.answer_adjustment | execute | `document.answer_adjustment` | access | DIRECT_ALLOWED | direct (prepare→consent→commit compat) | MIGRATED |
| received.post_message | execute | `received.post_message` | dre | DIRECT_ALLOWED | direct (prepare→consent→commit compat) | MIGRATED |
| received.create_adjustment | execute | `received.create_adjustment` | dre | DIRECT_ALLOWED | direct (prepare→consent→commit compat) | MIGRATED |
| received.confirm_adjustment | execute | `received.confirm_adjustment` | dre | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| catalog.entry_create | execute | `catalog.entry_create` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| catalog.entry_update | execute | `catalog.entry_update` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| catalog.entry_deactivate | delete | `catalog.entry_deactivate` | manage | DESTRUCTIVE | prepare→consent→commit | MIGRATED |
| catalog.entry_reactivate | execute | `catalog.entry_reactivate` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| checklist.draft_create | execute | `checklist.draft_create` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| checklist.draft_update | execute | `checklist.draft_update` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| checklist.version_submit | execute | `checklist.version_submit` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| checklist.version_return | execute | `checklist.version_return` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| checklist.version_discard | delete | `checklist.version_discard` | manage | DESTRUCTIVE | prepare→consent→commit | MIGRATED |
| checklist.version_publish | execute | `checklist.version_publish` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |
| checklist.version_inactivate | delete | `checklist.version_inactivate` | manage | DESTRUCTIVE | prepare→consent→commit | MIGRATED |
| checklist.doc_requirement | execute | `checklist.doc_requirement` | manage | GOVERNED_HIGH | prepare→consent→commit | MIGRATED |

## 3. Propriedades preservadas (não por linha, por mecanismo)

- **Backend handler**: as 32 read actions invocam as mesmas funções
  `tool_*` que chamam `_call_route` → função de rota BFF canônica —
  gate, bearer delegado ao api-delpi, envelope e erros tipados
  idênticos (sem SQL/cálculo duplicado).
- **Scopes**: `branch_scope`, `request_scope`, `ids`, `report_scope`,
  `warehouse`, `sort_*`, `page`/`page_size` preservados via `filters`
  com allowlist por action; `page_size` máximo = 200.
- **Error mapping**: `UNAUTHORIZED/FORBIDDEN/NOT_FOUND/
  VALIDATION_ERROR/CONSENT_REQUIRED/PROPOSAL_*/STALE/UNAVAILABLE/
  NOT_IMPLEMENTED/PARTIAL_OUTCOME/UNKNOWN` mapeados aos códigos
  existentes (`_ERROR_KIND_BY_CODE`), sem quebrar códigos canônicos.
- **Idempotência/OCC**: `idempotency_key` e `expected_revision`
  top-level de `execute`/`delete` são injetados no payload selado —
  mesmo mecanismo das capabilities.
- **Batch**: `depends_on`, `plan_hash`, `resume` preservados; execução
  ordenada, stop-on-failure dos dependentes, `PARTIAL` honesto.
- **Avatar/persona**: `get_context(topic="persona")` entrega
  `agent_directives` completo (character + `avatar_distribution`),
  `FICTION_IDENTITY_ONLY` preservado.
- **Consumers**: plugin ChatGPT (conector MCP com OAuth
  `mcp-controllership-finance`) — discovery dinâmico via `tools/list`;
  não há consumer por nome de tool no repositório (`search miss` ≠
  ausência — consumer externo não rastreado = `INCONCLUSIVE`, mitigado
  pelo cutover atômico do discovery).
- **Janela de compatibilidade**: os 43 nomes legados permanecem em
  `LEGACY_TOOL_NAMES`/`TOOL_CLASS` e os handlers continuam em
  `tool_bridge` (alvos do dispatcher). Não são registrados no
  `tools/list` — reexposição como alias exigiria nova decisão (doc 119
  §7.5: não mascarar dual surface como six-tools-final).

## 4. Lacunas declaradas

- Reports `R04, R06, R07, R09–R15`: sem handler BFF — `NOT_IMPLEMENTED`
  honesto via `not_implemented` (doc 120/122 = TARGET).
- Upload/download de binários e exports CSV/PDF: `PORTAL_ONLY` por
  natureza de payload (execução 016) — não são gap de autorização.
- Execução direta classe B: **RESOLVIDO em SEMANTIC-002** — decisão
  do owner publicada no doc 124 (11 DIRECT_ALLOWED / 37
  CONFIRMATION_REQUIRED; BLOCKED = erro tipado por pré-condição).
