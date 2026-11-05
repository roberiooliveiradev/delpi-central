# 241 — DÉLIA — Auditoria integral de capability_provision e plano de eliminação do legado

**TASK_ID:** DELIA-C3-CAPABILITY-PROVISION-FULL-FOLDER-NATIVE-FIRST-CLEANUP-01
**DATA:** 2026-11-04
**STATUS:** AUDIT / PLANNED; implementação NÃO EXECUTADA
**HEAD AUDITADO:** 6a7fdc65c16132726749c1ebfccd3415a0ecdd63
**REPOSITÓRIO:** roberiooliveiradev/delpi-central
**ESCOPO:** delia-api/app/application/capability_provision/ — TODOS os 13 arquivos diretos
**EXECUTOR:** Cursor, uma tarefa de implementação integral e bounded
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED
**LOCAL ISOLATED TEST:** AUTHORIZED

## 1. Decisão orientadora

O usuário determinou uma revisão **arquivo por arquivo**, remoção da infraestrutura agentiva construída localmente e utilização máxima das funcionalidades nativas do Pydantic AI. A missão não é reorganizar 16 mil linhas em novos módulos, mas efetivamente **excluir código, seletores, prompts, planners, sequenciadores, branches e dependências redundantes**. O Pydantic AI é runtime semântico único. Domain/Application não importam SDK. Core é AuthZ, Domain API é autoridade, DÉLIA verifica Evidence/Policy/Decision/Outcome; provider/MCP são interoperabilidade não confiável; writes mantêm PREPARE/ACT, audit, confirmação/idempotência e segurança.

O diretório de fato mistura decisões semânticas antigas, adapters, contracts, renderizadores, paginação, Evidence, writes e gates. **Nem todo código grande é descartável**: não substituir autorização, validação factual, paginação correta nem escaping por saídas livres do LLM.

Reancorar obrigatoriamente antes do diff: git status/HEAD/origin → Project Instructions/.cursor → docs 16→50→17→49→51→52→21→20→25 → arquitetura técnica → product spec → specs temáticas → execution ledger → docs 220, 226, 228–240. Em conflito, EXECUTION_DRIFT ou ARCHITECTURE_DECISION_REQUIRED, não reinterpretar silenciosamente.

## 2. Inventário COMPLETO de arquivos diretos — GitHub HEAD auditado

| Arquivo | Bytes | Linhas | Responsabilidade observada | Decisão de execução |
|---|---:|---:|---|---|
| __init__.py | 0 | 1 | Marcador de pacote | KEEP enquanto o pacote existir |
| capability_retrieval.py | 2.494 | 84 | BM25 custom: tokens, RankedCapability, ranking por descrição/nome/owner | REMOVE CANDIDATE; selector paralelo ao Agent; benchmark apenas fora de runtime se necessário |
| contracts.py | 4.684 | 134 | CapabilityProviderError, ProviderCapability, CapabilityGroup, ProviderSurface | KEEP/CONSOLIDATE contratos canônicos, sem duplicar Domain |
| conversational_response.py | 48.576 | 1.331 | CRI E3: síntese, textos, Markdown, registros, comparações e apresentação | SHRINK/MERGE; output tipado do agente para proposta semântica, manter apresentação factual e labels necessários |
| generic_evidence_renderer.py | 13.373 | 352 | Markdown genérico, árvore de evidência, orçamento/escaping | KEEP um renderer determinístico; remover duplicação de formatação onde comprovada |
| governed_stage_gates.py | 7.996 | 227 | Protocol de catálogo, invoke, finalize, admission, confirmação e path legado | SHRINK para consumers efetivos do adapter e governança; não criar novo protocolo paralelo |
| mcp_provider.py | 6.184 | 164 | McpCapabilityProvider: SpecialistInterop/live tools/list e execução via adapter | KEEP responsabilidade, REHOME em Infra se houver mechanics; consolidar com SpecialistInterop já existente |
| openapi_provider.py | 8.882 | 248 | Projeção OpenAPI, classes, conversão schema e execução | KEEP responsabilidade, REHOME em Infra se aplicável; não duplicar adapter/OpenAPI owner |
| orchestration.py | 645.094 | 16.174 | ~90 métodos de classe e muitas funções: engine legado + gates Pydantic AI, seleção, args, writes, Evidence, provider e renderização | MAJOR DELETE: aposentar engine semântico legado, separar gates/contratos legítimos, eliminar código substituído |
| outcome_assessment.py | 61.583 | 1.806 | CRI E2: requisitos, EvidenceFacts, OutcomeVerdict, comparadores, redaction, extração e avaliação | KEEP validação factual; REMOVE parsing heurístico de intenção e redundâncias; não validar FACT só com Pydantic |
| paginated_result_semantics.py | 26.363 | 802 | PaginationEnvelope, CountResolution, total autoritativo, agregação, ticket intent e scope | KEEP contagem/escopo válidos; REMOVE seleção de tool/ticket por keyword depois de paridade; Domain owner valida regra |
| ports.py | 1.665 | 54 | CapabilityProviderPort | KEEP/REUSE port real; consolidar duplicatas se comprovadas |
| subobjective_tracker.py | 14.680 | 366 | SubObjective/Tracker, estados, dependências, attempts, gaps e regras de transição | REMOVE CANDIDATE do planner/scheduler; manter somente obrigações/evidências autoritativas que não tenham owner equivalente |

**Total observado:** 13 arquivos e aproximadamente 841 KB. Fonte: listagem GitHub contents + leitura de cada arquivo no SHA auditado. Listagem de símbolos em §3/§4. **TO_INVENTORY:** consumidores transitivos e dispatch dinâmico: a ferramenta de busca de código retornou zero para símbolos conhecidos, o que NÃO prova ausência. Cursor deve usar AST, rg, callgraph e testes no checkout real antes de excluir.

## 3. Arquivo orchestration.py — mapa de TODAS as famílias funcionais

### 3.1 REMOVE CANDIDATE — arquitetura semântica legada (prioridade máxima)

Métodos declarados de seleção: _select_group; _capability_from_selection_proposal; _select_capability; _select_capability_with_goal; _select_target; _select_foreign_capability; _filter_groups_for_selection.

Métodos de raciocínio paralelo: _model_stage_proposal; _propose; _understand_goal; _turn_goal_from_proposal; _decompose_objective; _subobjectives_from_proposal; _decomposed_investigation; _investigate_subobjectives; _subobjective_attempt_result; _record_subobjective_outcome; _analytical_evidence_covered_by_acquisitions; _acquisition_subobjectives; _subobjectives_from_session_refs; _build_plan; _log_plan; _select_resolver; _analysis_continuation; _select_prepare_continuation.

Proposta/argumentos/retries locais: _propose_index_probe; _propose_index_identifier; _bind_arguments_from_index; _build_arguments; _candidate_arguments; _propose_candidate_arguments; _repair_once; _recover_owner_contract; _judge_goal_evidence; _recover_relevance; _apply_semantic_relevance; _clarification_question; _synthesize_content; _select_candidate; _assess_native_path.

IDs próprios: GROUP_SELECTION_INSTRUCTION_ID, CAPABILITY_SELECTION_INSTRUCTION_ID, INDEX_PROBE_INSTRUCTION_ID, INDEX_SELECT_INSTRUCTION_ID, ARGUMENTS_INSTRUCTION_ID, RESOLVER_SELECTION_INSTRUCTION_ID, CONTINUATION_INSTRUCTION_ID, CLARIFICATION_INSTRUCTION_ID, SYNTHESIS_INSTRUCTION_ID, GOAL_INSTRUCTION_ID, SUBOBJECTIVES_INSTRUCTION_ID; os outros IDs de prompt só permanecem se forem contratos legítimos e consumidos pela nova execução.

**Solução nativa:** Agent com tool loop, FunctionToolset tools dinâmicas, schemas Pydantic/validação, RunContext, native retries/UsageLimits, message history e output_type tipado quando supported pelo SDK installed (reportado 2.50.0). Não instalar segundo framework, construir registry, planner ou engine.

**Condition for deletion:** consumidores reais demonstrados, remoção de config DELIA_ORCHESTRATION_ENGINE=delia quando rollback não for mais autorizado/necessário; substituir apenas legitimate owner steps em interface já existente. Nenhum legacy semantic selector no caminho nativo.

### 3.2 REMOVE/REDUCE CANDIDATE — heurísticas, index selection e scaffolding

Top-level functions identificadas:
_group_unbound_feedback, _empty_result_feedback_with_args, _synthesis_rejection_feedback, _is_open_vocabulary, _is_unconstrained_string, _requires_owner_vocabulary, _contract_declares_omit_returns_index, _optional_unconstrained_string_keys, _index_catalog_entities, _index_option_rows, _index_declared_identifiers, _post_self_index_argument_gaps, _project_selected_index_identifier, _eligible_self_index_probe, _PlanCapabilityView, _plan_views, _discovery_capability, _owner_eligible_action_count, _discovery_empty_result_class, _live_interop_surface_lines, _render_zero_candidate_discovery, _bond_token, _bond_forms, _subject_bond_tokens, _identity_tokens_bond, _capability_identity_text, _candidate_identity_text, _iter_bond_candidates, _contract_subject_bond, _render_unusable_candidate_discovery, _surface_inquiry_content.

Ainda: _prior_observation_context, _context_folded_discovery_query, _fill_missing_from_entity, _candidate_clarification_content, _missing_inputs_bound, _resolved_values_proven, _declared_requirements_projection, _schema_declared_literals, _unproven_identifier_inputs, _schema_keys, _property_node, _sole_unconstrained_string_field, _single_free_text_argument_from_input, _free_text_is_verbatim_request, _workspace_identifier_literals, _resolvable_identifier_literals, _candidate_needs_missing_identifier, _capability_needs_missing_identifier, _capability_requires_orchestrated_input, _capability_dead_end, _named_provider_tokens, _vocative_provider_tokens, _group_short_ids, _edit_distance_leq, _nearest_capability_name, _elide_unproven_optional_args, _drop_orchestration_field_args, _drop_null_literal_args, _deterministic_arguments_from_schema, _index_selection_is_member.

Projeções de prompts legados: _project_surface, _resolve_live_group_key, _group_scope_text, _group_summaries, _capability_payload, _projected_capability_names, _projected_capability_ids, _json_block, _truncate_text_field, _truncate_entry_field, _drop_block_fields, _omit_tail_entries, _fit_json_block, _select_guidance_records, _md_guidance_content.

**Critério:** scaffolding que só serve a selector/prompt legado deve ser excluído em cascata. Regras de schema/identificadores comprovadamente necessárias para owner/candidate/Audit permanecem em implementações existentes, não em seletor semântico alternativo. Evitar nearest-name/keyword routing e manipulação de intenção via regex. Recentes _bind_missing_required_query e _bind_identifier_args_from_utterance exigem análise adversarial para não inventar ou reinterpretar pedido.

### 3.3 KEEP RESPONSIBILITY — owner invocation, catálogo e write governance

Funções/métodos a preservar por contrato, diminuindo e posicionando corretamente:
_project_semantic_tool_catalog; _governed_semantic_tool_invoke; _groups; _fresh_group; _invoke_selected; _invoke; _find_capability; _is_candidate_bound; _is_proposal_bound; _requires_field; _discover_candidate; _resolve_candidate; _candidates_present; _unusable_candidate_terminal; _accept_semantic_investigation_plan; _finalize_semantic_investigation; _compose_observation_pair.

Governança de writes: _effective_confirmation_policy, _find_act_capability, _act_arguments, _preview_render, _attempt_prepare, _attempt_direct_act, _attempt_confirmation, _confirm_proposal, _execute_prepared_act, _invoke_act, _provenance, _audit. Não remover Core live AuthZ, Domain rule validation, confirmation, idempotency, audit, PREPARE/ACT nem OT Safety.

**Atenção:** _invoke_selected no native path também pode chamar seleção/argumentação legada. Extrair somente protocolo determinístico de candidate binding e owner invocation; apagar semantic arggen. A função _governed_owner_path é legado candidato a remoção; _attempt, _run_governed_attempts, attempt, __init__ misturam paths e devem ser classificados por consumidor. Não manter helper legado porque seus testes o referenciam: substituir testes de implementação por testes contratuais legítimos.

### 3.4 KEEP/CONSOLIDATE — Evidence, apresentação, paginação e telemetria

Evidence/functions: _flatten_evidence_records, _evidence_rows_by_code, _verify_evidence_composition, _render_evidence_comparison, _compare_records, _compare_insufficiency_attempt, SemanticInvestigationPlan, _is_business_evidence_attempt, _authoritative_structure_root, _bind_attempt_to_target, _normalize_identity_tuple, _attempt_satisfies_obligation, _evaluate_material_obligations, _finalize_agent_collected_attempts, _compose_multi_evidence, _synthesis_records.

Guidance: _guidance_family_for_key, _render_guidance_value, _guidance_hit_count, _iter_guidance_doc_items, _guidance_section_records, _omitted_sections_line, _pack_guidance_sections, _deterministic_guidance_content.

Presentation/interaction: _project_paginated_personal_or_count, RenderedSpecialistOutcome, render_specialist_outcome, render_specialist_outcome_rich, _compose_cri_response, _outcome_attempt, _apply_outcome_assessment, _prior_result_turn, _prior_result_content, _prior_continuation_attempt, _maybe_aggregate_paginated_count, _requirements_need_more_pages, _page_cursor, _surface_inquiry_attempt, _admit_conversational_turn.

Control/telemetry: _lineage, _emit_activity, _AttemptCheckpoint, _TurnCancelled, _cancel_observed, _goal_fingerprint, _native_assessment_premise_fp, _record_native_assessment, _reusable_native_assessment, _native_assessment_reuse_verdict, _resume_stage_key, _resume_invoke_key, _group_activity_refs, _activity_outcome_summary, _StageDeadlineExceeded, _budget_allows_resolver, _budget_allows_optional_index_probe, _record_subobjective_outcome.

**KEEP is conditional on real consumer and legitimate authority.** Remove duplicate synthesis, text/intent judgement and root-specific mandatory finalization when contradicting heterogeneous evidence; retain fact verification independent of the model. Consolidate into existing Application/Evidence/Interaction boundaries, no invented second engine or second Evidence verifier.

## 4. Other 12 files — symbol inventory and action

### __init__.py
Empty marker. KEEP until package removed.

### capability_retrieval.py
_tokens; RankedCapability; _doc_text; rank_capabilities. REMOVE CANDIDATE, including retrieval selection mode, after proving no needed eval consumer. Agent native tool choice is already implemented.

### contracts.py
CapabilityProviderError; ProviderCapability; CapabilityGroup; ProviderSurface. KEEP one authoritative provider-neutral contract, compare against specialist_interop/domain duplicates.

### conversational_response.py
_shortage_key; PresentedRecord; CriComposition; _format; _subject; compose_cri_response; records_are_prior_excerpts; cri_scalar_text; presented_record; ordering_presentation; _render_synthesis; _proven_field_differences; _selected_proven_differences; _insufficiency_content; _compose_answer; _detail_header; _detail_lines; _list_header; _format_structured; _format_list; _format_records; _business_lines; _md_leaf; _md_format_structured; _md_format_list; _md_format_records; _md_business_lines.
SHRINK/MERGE: preserve factual, source-safe presentation, remove duplicate formatters and semantic composition. Compare generic_evidence_renderer, structured output and existing UI. Model narrative cannot replace authoritative Evidence.

### generic_evidence_renderer.py
_md_escape; field_label_parts; unmapped_field_label; field_display_label; field_clause_label; _render_label; _value_lines; EvidenceRender; _Budget; _render_node; render_business_evidence.
KEEP minimal deterministic renderer; merge duplicate Markdown/label/tree formatters after visual/semantic parity.

### governed_stage_gates.py
SupportsGovernedStageGates Protocol with catalog, invoke, finalize, admission, confirmation and legacy owner path. SHRINK signatures to real native-agent and write boundaries, no Pydantic AI import.

### mcp_provider.py
McpCapabilityProvider. KEEP only nonduplicated adapter function, consolidate with SpecialistInterop and move provider mechanics to Infra if currently in Application. Native MCPToolset must not bypass authorization.

### openapi_provider.py
_operation_class; _input_schema_from_inputs; _capability_from_projection; OpenApiCapabilitySource; OpenApiCapabilityProvider. KEEP actual integration/contract; consolidate with existing OpenAPI owner; move provider mechanics to Infra, no duplicate mapping.

### outcome_assessment.py
OrderingSemantic; AnswerRequirements; parse_answer_requirements; _parse_ordering_semantic; verified_ordering_event; EvidenceFacts; OutcomeVerdict; _parse_temporal; _temporal_proofs; _temporal_orders; ordering_proof_fields; parse_temporal_value; _distinct_delivered; distinct_delivered_count; _unproven_requirements; assess_outcome; _comparison_records; _comparable_scalar; _bound_owner_evidence; _is_capability_descriptor; _without_control_plane; _contract_fact_rows; _candidate_contract_rows; _compact_evidence; _evidence_rows; _missing_inputs; _extract_owner_entity_schemas; _entity_payload_slot; _value_present; _wording_leaks_technical; _synthesis_selections; _record_identifier; _unwrap_owner_payload; _resolver_entities; _mapping_items_excluding_control; _explicit_empty_business_collection; _prior_supports_typed_attribute_compare; _canonical_key; _is_sensitive_key; _redact_text; _sanitize_renderable_counted; _sanitize_renderable; _is_generic_status; _bounded_subject_node; _result_contract_context; outcome_facts; apply_verdict_limitation; GoalEvidenceJudgment; parse_goal_evidence_judgment.
KEEP fact sufficiency, temporal/count proof, provenance, redaction and sanitized output; REMOVE CANDIDATE regex/heuristic intent parsing, semantic judgment duplicated by model, duplicate projection. Pydantic output validators validate shape, not business facts.

### paginated_result_semantics.py
PersonalTicketScope; ResultIntent; CountResolutionKind; PaginationEnvelope; PageAggregationResult; CountResolution; classify_result_intent; classify_personal_ticket_scope; _as_bool; _as_int; _read_total; extract_pagination_envelope; item_stable_id; _is_first_page; aggregate_paginated_pages; resolve_count_semantics; personal_scope_response; list_header_for_envelope; count_message_for_visible_query; arguments_include_personal_assignee; arguments_include_requester_filter; is_ticket_domain_inquiry; schema_supports_ticket_list_action; unique_structural_ticket_list_capability.
KEEP authoritative totals, incomplete-page honesty, requester scope; REMOVE keyword-intent and ticket-specific preselection if Pydantic AI tool choice covers it. Owner's Domain API remains authority for counts/identity.

### ports.py
CapabilityProviderPort Protocol. KEEP/CONSOLIDATE with existing port owner; not framework logic.

### subobjective_tracker.py
SubObjective; subobjective_outcome_transition; SubObjectiveTracker (also inspect all internal methods via AST). REMOVE CANDIDATE as semantic scheduler/planner, KEEP only proven task-evidence bookkeeping if not already in Outcome/Evidence contract.

## 5. Decision matrix / framework replacement

| Local responsibility | Native or rightful owner | Outcome |
|---|---|---|
| Group/capability selection, lexical ranking | Pydantic AI Agent + FunctionToolset and native search if compatible | DELETE legacy selector |
| Semantic subgoal planning, decomposition, sequencer | Agent tool loop, deps, history and typed output | DELETE legacy scheduler |
| Argument-generation prompting, retries | tool schemas, Pydantic validation/native retries | DELETE duplicate logic; KEEP owner schema enforcement |
| Clarification/continuation | Agent, message history + existing session | DELETE duplicated prompts |
| LLM synthesis | structured output only for proposed claims; existing Evidence validation | REMOVE only overlapping semantic rendering |
| MCP/OpenAPI transport and live tools | existing provider adapters/Domain APIs | KEEP/CONSOLIDATE legitimate mechanics |
| Live AuthZ, candidate/proposal handles | Core/Domain + governed ports | KEEP |
| Fact correctness, provenance and outcome | DÉLIA Evidence/Policy/Outcome, Domain API | KEEP |
| Pagination and personal count truth | Domain rules + existing factual aggregation | KEEP |
| Writes and OT safety | existing Policy/Decision/Automation Hub | KEEP |

Status for replacement: EXISTING_EQUIVALENT=YES for agent/select/planner/retry roles; REUSE_DECISION=REUSE/EXTEND native Pydantic AI; REMOVE redundant local semantics. EXISTING_EQUIVALENT=YES for existing contracts/gates: REUSE/EXTEND, not recreation. Some adapter/renderer overlap remains TO_INVENTORY for exact consumers. Validate SDK pinned version (previously pydantic-ai[openai]==2.50.0), installed APIs, and model tool support.

## 6. Required exhaustive code-level verification BEFORE deletion

The audit covered ALL files and enumerated module-level declarations, plus **90 indented methods** of orchestration.py. Because remote GitHub code search returned no results for known functions, it is NOT authoritative evidence of no consumers. Executor MUST use local ripgrep, Python AST, import graph and runtime characterization for:
- every symbol of all 13 files, including class methods and nested closures;
- direct/indirect imports from root_composer, PydanticAiInvestigationOrchestrator, Interaction, tests, config and external adapters;
- dynamic getattr, monkeypatch, dependency injection, test-only consumers and exposed public contracts;
- exact active production path versus DELIA_ORCHESTRATION_ENGINE=delia rollback; _invoke_selected subcalls and legacy LLM stages in the native path;
- consumer→owner→source→contract→implementation→test→business outcome.

Produce a **machine-readable deletion manifest**: file, symbol, line range, actual consumers, NATIVE|LEGACY|BOTH|OUTSIDE, business owner, equivalent API, EXISTING_EQUIVALENT, REUSE_DECISION, action REMOVE|KEEP|MOVE|MERGE|SHRINK, tests and outcome. No deletion is accepted with TO_INVENTORY consumer. 0 rg results alone != unused.

## 7. One-task implementation plan

**E0 REANCHOR / baseline:** canonical sources, HEAD and WIP, file/symbol manifest, import graph, runtime traces, E01–E10 baseline and security/NDJSON, actual metrics. No new architecture study, proceed with implementation.

**E1 Lock contracts:** port and live AuthZ, Domain schemas/identity, Evidence/Outcome, candidate binding, prepare/act, confirmation, token budgets, interaction. No SDK in Domain/Application, no new authority.

**E2 DELETE semantic duplicate:** decommission legacy DELIA_ORCHESTRATION_ENGINE=delia and _governed_owner_path semantic engine after confirming frozen decisions, consumers and parity; eliminate selectors, prompts, subobjective scheduler, arggen, duplicate retries, ranking/flags and dead helpers. Preserve only governable owner mechanics. Do not re-create legacy elsewhere.

**E3 Reuse/relocate legitimate functions:** keep minimal Application catalog and governed execution ports, MCP/OpenAPI adapters at correct Infra boundary, evidence + write gates at owners; only MOVE if coupling is reduced and no duplicate. Reduce governed_stage_gates to actual consumers.

**E4 Consolidate presentation/evidence:** preserve SourceRef, authoritative identity, typed outcomes, safety, pagination counts and Markdown contract; remove duplicate prose/formatting and intent heuristics; consider Pydantic AI typed output only for claims and use deterministic validation for facts.

**E5 Tests / real runtime:** RED/GREEN; complete pytest AFTER FINAL diff; imports and architecture; READ E02/E03; honest multi-obligation E04/E06/E10; E07 clarification; E08 revoked/write negative; E09 NDJSON/cancel; pagination personal scope; no false grounded; local isolated EVALUATED_SHA==LOCAL_RUNTIME_SHA. Do not run production scripts or material writes.

**E6 Delivery:** next available numbered execution report after 241 + update doc 239, documentation/ADR if needed and ledger **after factual outcomes**, before/after lines and files, removed prompt IDs/LLM stages, commit/rebase/push main verified preserving foreign WIP. If frozen decision prevents a specific removal, mark EXECUTION_DRIFT and finish independent authorized work rather than silently ignoring it.

## 8. Acceptance criteria

AC01 13/13 files; all symbols covered and consumers verified.
AC02 demonstrable LOC and semantic-call-site reduction, not file splitting.
AC03 no alternate planner/selector and no LangGraph active; Pydantic AI sole semantic runtime.
AC04 no loss of Core/Domain authorization, Policy, Decision, Outcome, confirmation, idempotency or OT safety.
AC05 owner READ/discovery, identity, SourceRef, fact verification, catalog live still correct.
AC06 no duplicate MCP/OpenAPI mechanics or second registry.
AC07 factual pagination/count and deterministic presentation remain correct.
AC08 no false GROUNDED in security/evidence tests.
AC09 full backend suite and affected consumer tests GREEN on final SHA.
AC10 E01–E10 E2E local with honest statuses and no regression; separate partial vs full business outcome.
AC11 delete/retain manifest, docs/ledger, push verified, no prod deploy.

**Reject outcomes:** replacing 16k-line file with same functions distributed across new modules; removing Domain validation merely to use LLM; claim of zero consumers without callgraph; E2E on stale runtime; new custom planner or query-specific routes.

## 9. Required delivery report

DÉLIA EXECUTION REPORT — CAPABILITY PROVISION CLEANUP

TASK_ID, BASE_HEAD, FINAL_SHA, ORIGIN_MAIN, PUSH_VERIFIED, AUTHORITIES_READ, PHASE_CP_RQ, INVENTORY=13/13, SYMBOL_MANIFEST_PATH, BEFORE/AFTER_LINES, REMOVED_FILES, MOVED_FILES, MERGED_FILES, SHRUNK_FILES, KEPT_FILES, SEMANTIC_PROMPTS_REMOVED, SELECTORS_REMOVED, LEGACY_ENGINE_STATUS, PYDANTIC_AI_NATIVE_USAGE, OWNER_BOUNDARIES, AUTHZ_WRITE_SAFETY, EVIDENCE_OUTCOME, PAGINATION_COUNTS, JSON_NDJSON, RED_GREEN, FULL_BACKEND_SUITE, EVALUATED_SHA, LOCAL_RUNTIME_SHA, E01_E10, FALSE_GROUNDED, GENERALIZATION, RESIDUAL_SEARCH, DOCS_LEDGER, EXECUTION_DRIFT, UNRESOLVED, VERDICT, PRODUCTION_DEPLOY=NOT_AUTHORIZED.

**THIS DOCUMENT IS ONLY AN AUDIT AND IMPLEMENTATION PLAN. No source code was modified by this GitHub documentation commit.**


---

## 10. SEGUNDA AUDITORIA OBRIGATÓRIA — LEITURA CONTÍNUA DA LINHA 1 À LINHA FINAL

**Data:** 2026-11-04. **SHA de código revalidado:** \`3b6a73f1129a3ecfa08288509a66ada46482e80a\`. **Arquivo:** \`delia-api/app/application/capability_provision/orchestration.py\`. **Extensão:** 16.173 linhas de conteúdo retornado por API (inventário anterior 16.174 considerando newline); aprox. 645 KB. O arquivo inteiro foi lido em 17 faixas sequenciais [1–1000] ... [16001–fim], no mesmo SHA, com enumeração de declarações top-level e métodos indentados por bloco. Nenhuma faixa foi intencionalmente ignorada. A revisão aqui é **análise estática integral + inspeção dos trechos de ligação**, não prova de inexistência de consumidores dinâmicos.

### 10.1 Diagnóstico crítico comprovado por inspeção de chamadas

**O runtime nativo Pydantic AI AINDA ATRAVESSA O MOTOR DE ORQUESTRAÇÃO ANTIGO, não apenas gates determinísticos:**

\`\`\`text
pydantic_ai_investigation.py
  → _governed_semantic_tool_invoke [orchestration.py:13471]
    → _invoke_selected [13573, implementation starts 14982]
      → _discover_candidate [15012]
      → _resolve_candidate [15097, 15125, implementation 15560]
      → _candidate_arguments [15042, 15236, implementation 15745]
         → _propose_candidate_arguments [15810, implementation 15879]
            → Pydantic-specific arggen conditional [15918]
            → OTHERWISE _model_stage_proposal [15952]
      → _build_arguments [15176] for a recovery leg
      → _propose_candidate_arguments [15287] on chained read recovery
      → _invoke [15074, 15090, 15256, 15333, implementation 15980]
\`\`\`

**Detalhe:** \`_resolve_candidate\` [15560] can call \`_select_candidate\` [15616]; \`_select_candidate\` [15626–15744] calls \`_model_stage_proposal\` [15708] using \`CANDIDATE_SELECTION_INSTRUCTION_ID\`. \`_propose_candidate_arguments\` [15879–15978] has both an arggen-Pydantic-specific branch and a second call to \`_model_stage_proposal\` [15952]. Native agent selected the capability, but Application still contains a **second semantic selection/generation loop** in the owner discovery/candidate/execute path. This is a concrete native-path overlap, not merely dead rollback code. It must be removed in favor of typed owner tool schemas + owner-issued candidate handles and explicitly bounded, deterministic binding; if candidate choice remains ambiguous, agent chooses via native tool call or clarification, never a second independent LLM controller. Preserve candidate_token trust boundary. \`_invoke\` [15980–16173] is real provider execution and **cannot simply be deleted**.

**Classification:** NATIVE-path overlap = PROVEN for these call edges, **whether a particular branch is triggered at runtime** depends on input/schema/owner response and is TO_VERIFY via trace. No fabricated claim that every turn executes model-stage proposal.

### 10.2 Exact continuous line-range disposition (no unreviewed tail)

| Lines at audited SHA | Observed family | Decision |
|---|---|---|
| 1–443 | module description, imports, constants for multi-stage model selection, schema fields, budget, intent, prompts | REMOVE legacy prompt/config stage IDs and unused imports/constants; KEEP only contract/security/evidence limits consumed by native agent |
| 444–1000 | feedback/lineage, schema checks, self-index, view plan structures | DELETE index/selector prompt scaffolding; KEEP minimal schema, candidate/proposal authority and audit if consumed |
| 1001–1501 | plan views, discovery assistance, candidate identity and status, surface inquiry | DELETE pseudo-planner and lexical candidate scoring; KEEP factual owner discovery errors/identity with actual consumers |
| 1502–1926 | record flattening, verified composition, comparison rendering | KEEP legitimate proof; REMOVE duplicate handcrafted comparison control-flow after contractual parity |
| 1927–2300 | clarification, prior excerpts, personal/page count projection | REMOVE legacy semantic clarification and prior-message reinterpretation; KEEP correct pagination, privacy and presentation contracts |
| 2301–2976 | guidance family/section packing, synthesis/subject/entity/resolver hints and required schema binding | REDUCE duplication, old guidance budgets and resolver/planner heuristics; KEEP truthful guidance/source protection only |
| 2977–3557 | confirmation policy, schema shape, identifier resolution, fuzzy capability matching, deterministic argument projection, compare insufficiency | KEEP confirmation/auth constraints; DELETE fuzzy tool selection/old arggen; scrutinize recent identifier binder for overreach; no query-word authorization |
| 3558–4168 | business evidence, authoritative root, material obligations, native collected-attempt finalization | KEEP evidence/outcome; simplify no special compare engine if generic verified evidence works; guard partial/false GROUNDED |
| 4169–4772 | legacy surface summary, group/capability selection-prompt JSON shrinking, guidance Markdown | DELETE selection-prompt scaffolding no longer consumed by native tool projection; KEEP only actual projection for authorized tools |
| 4773–5607 | outcome renderer, write preview, activity, checkpoint, cancellation and recovery keys | KEEP write lifecycle/audit/turn protection, consolidate duplicate rendering/state |
| 5608–6050 | orchestration constructor, attempt, multi-attempt runner, conversational admission | SPLIT true native admission/confirmation from legacy main entry; remove second semantic runtime and redundant retries |
| 6051–7632 | _governed_owner_path ~1,582 lines: old group/capability selection, index, resolver, candidate, ARG/propose and prepare recovery | **DELETE as semantic runtime** once consumer/rollback and write parity cleared; extract only legitimate governed owner calls and write gates rather than moving block |
| 7633–8442 | custom subobjective planner, decomposition, fan-out, dependencies, pair compose | **DELETE semantic planning/scheduler**; keep verified evidence aggregation only when no legitimate equivalent |
| 8443–10035 | missing-input resolution, resolver, analysis continuation, goal proposal, assess native path, foreign selection/corroboration, prepare continuation | **DELETE second model-driven reasoner/selector/recovery**; preserve legitimate owner contract and write Policy gates |
| 10036–11011 | PREPARE/ACT confirmation, fresh revalidation, audit, outcome assessment and CRI composition | **KEEP genuine business/write protections**; remove duplicate semantic orchestration or renderer work after ownership verification |
| 11012–11766 | group filtering and live groups; old target selection/planning, model-stage proposals | **KEEP _groups/_fresh_group live; DELETE _select_target/_build_plan/_model_stage_proposal/_propose if no retained non-agent consumer** |
| 11767–13386 | clarification wording, pagination, synthesis/repair, contract and relevance recovery, conversational/surface inquiry | **KEEP pagination factual and allowed conversational admission, DELETE independent model repair/synthesis/relevance planner** with native result contract parity |
| 13387–13801 | **live** native Pydantic tool catalog, invocation, plan acceptance, compose, finalization | KEEP Application-owned authoritative gates; reduce coupling to old class; no Pydantic AI SDK imported here |
| 13802–14981 | **old** group/capability selector, candidate+goal proposal, index probing and argument construction | **DELETE obsolete semantic selector and arggen**; only retain exact owner schema checking that remains necessary to native path |
| 14982–15414 | _invoke_selected: owner discovery/execute intertwined with candidate LLM selection/argument generation, retry/reformulation, guidance | **REWRITE minimal governed protocol**: typed tool args, owner candidate token, live revalidation, provider invoke, provenance; remove independent model calls; do not blindly remove _invoke_selected while native tool uses it |
| 15415–15979 | _discover_candidate, _resolve_candidate, _select_candidate, _candidate_arguments, _propose_candidate_arguments | KEEP deterministic discovery/candidate ownership; **DELETE second LLM selection + arggen stages**; ambiguous candidate → agent tool interaction/clarification |
| 15980–16173 | _invoke — provider lookup, deadline/cancel, resume handling, invocation, ledger and outcome | **KEEP/MINIMIZE** provider-independent invocation logic / move mechanics to existing adapter; preserve errors and authoritative outcome; **last line 16173 reviewed** |

### 10.3 Path segregation for safe elimination

**PATH A — current native agent:** live catalog → native FunctionToolset → \`_governed_semantic_tool_invoke\` → Application/Core/domain validated READ → provider/owner → Evidence → output. Preserve path and *eliminate embedded second LLM selectors*. Native prompt/history, validation, retries, output structures are exclusively Infrastructure/Pydantic.

**PATH B — legacy:** \`OperationalCapabilityOrchestrator.attempt\` → \`_attempt\` → \`_governed_owner_path\` → \`_select_group\`/\`_select_capability\`/\`_propose\`/plan/repair, plus subobjective scheduling and retrieval. **TARGET REMOVE** after reanchor/frozen decision and production configuration consumers are proven. Do not retain an alternate engine as precaution without explicit authoritative justification. A legacy rollback may require explicit architecture decision to retire; do not silently delete it.

**PATH C — business control:** confirmation PREPARE/ACT, live Core/Domain revalidation, idempotency/audit, budget/deadline/cancel, owner provenance, genuine source identity and obligation coverage, paging, safe rendering. **KEEP** irrespective of framework; consolidate into existing legitimate Application/Domain/Infrastructure boundaries. Pydantic output validation cannot grant permission or prove FACT.

### 10.4 Explicit deletion order and anti-pattern tests

1. Capture initial grep/callgraph for all 90 methods and top-level symbols **including dynamic calls**; produce manifest by symbol (see §6). Add baseline tests for current native tool calls, multi-owner/candidate and protected writes; verify product/source identity, partial/non-grounded and NDJSON. Identify legacy engine users/config before deletion.
2. First eliminate **native-path legacy model stages** in [14982–15979]. Use native tools + typed schemas and owner candidate handle. Ensure no \`_model_stage_proposal\`, \`_propose_candidate_arguments\`, \`_select_candidate\` reached inside a native READ. If deterministic entity binding cannot be proved, return clarification/inconclusive instead of arbitrary pick.
3. Remove legacy \`_governed_owner_path\` [6051–7632] and all dependent selector/plan/subobjective/recovery functions after legitimate write/admission consumers are separated and rollback retirement is authorized. Then remove corresponding constants, instructions, config and \`capability_retrieval.py\` / \`subobjective_tracker.py\` if zero legitimate consumers.
4. Consolidate duplicate response/rendering/evidence/pagination helpers with an authoritative contract map; delete unnecessary code rather than copy functions into other files.
5. Run import graph and all tests after final diff. On executed SHA measure actual deleted LOC, deleted semantic proposal stages, owner reads, token/latency, security, JSON/NDJSON, E01–E10 and no false grounded. No production deployment.

**Hard regression assertions:** native tool READ never calls a second custom LLM semantic controller; multiple owner candidates are not silently picked by regex or nearest-name; old mode cannot run unless explicitly preserved by authority; Pydantic tool-result metadata remains untrusted; owner evidence only authoritative; PREPARE/ACT untouched; no green-only deleted tests.

### 10.5 Updated verdict

**Source audit:** \`PROVEN\` full file 1–16173 read at SHA, exact mixed native/legacy paths identified; **TO_INVENTORY** every transitive/dynamic caller and contract-specific owner; **PLANNED** physical deletion/refactor. This addition is NOT an implementation or a claim that all listed functions are currently invoked. **The strongest concrete finding is the call edge [13573]→[14982]→[15745]/[15879]/[15626]**. Executor must use this as the primary removal target instead of running another open-ended inventory.

**Do not replace Pydantic AI with another framework or build a third orchestrator.**
