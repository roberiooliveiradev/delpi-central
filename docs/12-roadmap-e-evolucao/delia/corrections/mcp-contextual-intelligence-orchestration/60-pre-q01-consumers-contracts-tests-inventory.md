# 60 — Pré-Q01: inventário de consumidores, contratos e testes levantado pelo GPT

**Data:** 2026-10-19. **TIPO:** `PRE-Q01_DISCOVERY_DOCUMENTATION` (não habilita nem executa Q01). **Main reanchor:** `9dad78c53beb2a5e5de50695fbb590b40440baf6`. **Código analisado:** `delia-api/app/application/capability_provision/orchestration.py` (10.592 linhas; blob atual `bc13e07b31b6844e172c5d485d77f59a4b8c0a10`); `paginated_result_semantics.py`, consumer `handle_interactive_turn.py`, provider contracts/ports, adapters MCP+OpenAPI and tests. **Baseline decisions:** [56](./56-orchestration-audit-semantic-ownership-checkpoint.md), [57](./57-orchestration-complete-second-pass-static-audit.md), [58](./58-adr-llm-semantic-decision-ownership.md), [59](./59-orchestrator-refactoring-finite-execution-roadmap.md).

## 1. Conclusão do levantamento possível via GitHub connector

**PROVEN por leitura de fonte:** entrypoint `HandleInteractiveConversationTurn._execute_observed` em `app/application/interaction/handle_interactive_turn.py:301–432`: `self._capability_orchestration.attempt(...)` (317–329), mapeia `SUCCESS/outcome` (333–344) em `grounded_result` ou `prior_continuation_result` não fundamentado; `SOURCE_UNAVAILABLE/AUTHZ_DENIED` terminam (346–366); confirmação/escrita/clarificação terminam (368–389), e NOT_APPLICABLE pode cair no modelo geral (391–432). Preservar status contracts.

**PROVEN:** `CapabilityProviderPort.list_groups` + `invoke`, `ProviderCapability`/`CapabilityGroup`/`ProviderSurface` em `capability_provision/contracts.py` e `ports.py`; `McpCapabilityProvider` e `OpenApiCapabilityProvider` implementam boundaries distintos, invocados pelo orquestrador por adapter. Surface source/operation permissions jamais auto autorizam.

**PROVEN:** `InvokeModel` e `_propose` são mecanismos existentes; o arquivo invoca `InvokeModel.execute` diretamente nos pontos 8676 (dentro de `_propose`), 10262 (`_select_candidate`) e 10408 (`_propose_candidate_arguments`). Consolidar 2 duplicações, sem novo provider/model service.

**PROVEN:** existe interpretação por regex fora do arquivo em `paginated_result_semantics.py:49–110/203–232` (`classify_result_intent`, `classify_personal_ticket_scope`), consumida em `orchestration.py:2616–2617/8873–8874`, e `unique_structural_ticket_list_capability` faz bypass semântico por regex em `paginated_result_semantics.py:769–801`, consumido em `orchestration.py:9490/9558`. Não apagar cálculo, distinção page-vs-total nem personal-scope fail-closed.

**PROVEN:** segurança e estruturas reutilizáveis: `interaction/argument_validation.py`, `interaction/turn_budget.py`, `interaction/capability_attempt.py`, `interaction/pending_proposals.py`, `interaction/workspace_context.py`, `model_invocation/invoke_model.py`, `domain/planning/rules.py`, `domain/governed_write/rules.py`. Nenhuma nova abstraction requerida para a direção aprovada.

**LIMITAÇÃO:** a ferramenta de busca indexada do GitHub retornou `0 results` até para símbolos confirmadamente existentes; não prova ausência de outros importadores/testes em todo repo. O diretório/git working tree e execução SSH não estão expostos por esta integração. `REPO_WIDE_RIPGREP=TO_INVENTORY` e `GIT_STATUS=TO_REVALIDATE_CURSOR` (não substituir por conjectura). O Cursor deverá rodar **um único** residual search validatório contra SHA atualizado como pré-gate de diff, e reportar diferenças sem reiniciar levantamento.

## 2. Mapa estruturado dos 42 achados → estágio e chamadas

**Disposition:** `REMOVE` retira decisão semântica e seus testes de implementação; `REPLACE` reutiliza decisão LLM tipada; `RESTRICT` mantém função somente quando compatível com intenção/contrato; `REPLACE_FAIL_CLOSED` exige prova de provenance/autorização sem regressão; `CONTRACT_GATE` proíbe mudança sem owner/ADR; `MEASURE_FIRST` depende de perf real.

| ID | Pacote | Código atual (def/linha) | Callers confirmados na fonte | Disposição | Contrato/owner correto | Teste existente sujeito a revisão |
|---|---|---|---|---|---|---|
| S01 | Q02-A | `_is_information_coverage_inquiry` (1355) | _select_target:8467 | `REPLACE` | Typed applicability/discovery goal; no keyword regex | `test_r2_provider_neutral_capability_selection_quality.py` |
| S02 | Q02-A | `_GUIDANCE_*_CUE_RE` (2887–2911) | _guidance_intent_families:2914 | `REMOVE` | Typed requested guidance kind already from LLM | `test_i02_k2_k3_output_quality.py` |
| S03 | Q02-A | `_guidance_intent_families` (2914) | _deterministic_guidance_content:3083 | `REPLACE` | Selection by grounded goal/owner evidence; preserve limits | `test_stage03_discovery_guidance.py` |
| S04 | Q02-A | `_PRIOR_TRANSFORM_CUE_RE / _LIVE_FACT_CUE_RE` (2356–2375) | _prior_transform_probe_eligible:2378 | `REMOVE` | No keyword prior-versus-fresh decision | `test_stage05_multiturn_latency.py` |
| S05 | Q02-A | `_prior_transform_probe_eligible` (2378) | _attempt:4963 | `REPLACE` | Typed prior_sufficient + freshness/evidence checks | `test_stage05_multiturn_semantic_rework.py` |
| S06 | Q02-A | `_user_list_ordinal` (3231) | _resolve_missing_inputs:6215 | `REPLACE` | Typed ordinal/ref from LLM, validated owner candidate index | `test_generic_multistep_orchestration.py` |
| S07 | Q02-A | `_INDEX_INTENT_CLUSTERS` (3648) | _index_cluster_hits:3707 | `REMOVE` | Provider-neutral semantic index proposal, no hardcoded dashboard/playlist vocabulary | `test_adaptive_capability_routing_completion.py` |
| S08 | Q02-A | `_index_text_tokens/_index_cluster_hits/_tokens_stem_related` (3699–3722) | _index_option_relevance_score:3725 | `REMOVE` | Remove semantic lexical scoring only; retain format parsing | `test_adaptive_capability_routing_completion.py` |
| S09 | Q02-A | `_index_option_relevance_score` (3725) | _rank_index_options_by_overlap:3788;_bind_arguments_from_index:9676/9731 | `REMOVE` | Owner index membership and LLM selection replace manual relevance | `test_mcp_iterative_index_probe.py` |
| S10 | Q02-A | `_rank_index_options_by_overlap/_index_selection_is_relevant` (3773–3823) | _bind_arguments_from_index:9674/9704 | `REMOVE` | No lexical veto after typed owner-index selection; retain exact identifier membership | `test_r2_provider_neutral_capability_selection_quality.py` |
| S11 | Q02-A | `_EXTRACTION_FOLLOWUP_RE/_LIMITATION_FOLLOWUP_RE` (3827–3843) | _recover_prior_extraction_after_invalid_index:3938 | `REMOVE` | Typed request kind drives extraction/limitation selection | `test_i03_k2_k3_nonregression.py` |
| S12 | Q02-C | `_count_covered_extraction_units/_prior_extraction_incomplete` (3870–3917) | _prior_continuation_attempt:6971 | `REPLACE` | Outcome task semantics not word quantity or overlap | `test_i02_k2_k3_output_quality.py` |
| S13 | Q02-C | `_MIN_USEFUL_CONTINUITY_CHARS` (3826) | _prior_extraction_incomplete:3897 | `REMOVE` | No length-as-task-sufficiency | `test_stage05_multiturn_latency.py` |
| S14 | Q02-C | `_recover_prior_extraction_after_invalid_index/_extraction_list_from_prior_excerpts` (3919–3957) | _prior_continuation_attempt:6887 | `RESTRICT` | Permitted only for list/extraction, never compare/analyze; previous factual evidence not refreshed | `test_provider_neutral_semantic_provenance_and_continuity.py` |
| S15 | Q02-C | `_prior_listing_hint` (3242–3291) | _select_capability/_select_capability_with_goal:9505/9574 | `REPLACE` | Typed prior evidence/render metadata, not assistant string UUID/encontrei | `test_i03_k2_k3_nonregression.py` |
| S16 | Q02-C | `_prior_excerpt_records` (2311–2353) | _prior_continuation_attempt:6808 | `RESTRICT` | Text excerpts allowed as nonauthoritative continuity hints, not fact provenance | `test_stage05_multiturn_semantic_rework.py` |
| S17 | Q02-B | `_token_covered_by_user_tokens/_free_string_grounded_in_user_input` (888–945) | _build_arguments:5769 | `REPLACE_FAIL_CLOSED` | Exploratory READ proposal separate from exact sourced ID or business filter | `test_provider_neutral_semantic_provenance_and_continuity.py` |
| S18 | Q02-B | `_single_free_text_argument_from_input` (3573–3589) | _build_arguments:9863/9932 | `RESTRICT` | Raw full-request passthrough only if owner declares intended free-text semantics | `test_real_product_owner_read_and_budget_rework.py` |
| S19 | Q02-B | `_resolved_values_proven/_unproven_identifier_inputs` (3372–3473) | _build_arguments:5511/5689;_resolver:6182/6225/6271/6277;_foreign:7228 | `REPLACE_FAIL_CLOSED` | Typed source references and owner/domain verification, never word occurrence as authority | `test_generic_multistep_orchestration.py` |
| S20 | Q02-A | `_select_group singleton short circuit` (9381–9385) | _select_target:8411 | `RESTRICT` | Do not presume relevance solely because one eligible provider exists | `test_specialist_capability_orchestration.py` |
| S21 | Q02-A | `_admit_conversational_turn if prior_turns` (9283–9285) | _attempt:4896 | `REMOVE` | Allow topical change and conversational followup after owner result | `test_semantic_intelligence_orchestration_recovery.py` |
| S22 | Q02-A | `admission/group/capability/goal/native_assessment` (4893–5235;9267–9609) | _attempt/_select_target/_understand_goal/_assess_native_path | `CONSOLIDATE` | Reuse typed semantic decisions instead of repeated disconnected LLM calls | `test_i02r3b_typed_capability_goal_selection.py` |
| S23 | Q02-B | `_budget_allows_optional_index_probe/_propose_index_probe` (6735–6759;9609–9650) | _attempt:5414/5415 | `RESTRICT` | Optional probe impossible with ~66s headroom/30s turn; never assume empty READ is index | `test_i02r2_index_probe_headroom.py` |
| S24 | Q02-B | `experimental_arguments_budget_guard` (4778–4793;6761–6782) | _build_arguments:9858 | `REMOVE_IF_UNUSED` | Inventory flag consumers in composition/config; verify mode before removing | `test_execution_ceiling_turn_budget.py` |
| S25 | Q02-C | `_compare_records` (1589–1716) | _corroborate_attempt:7349 | `CONTRACT_GATE` | Instruction/context_fields empty vs runtime comparability; frozen authority first | `test_stage05_grounded_response.py` |
| F26 | ADR_GATE | `selection-only synthesis and deterministic render` (547–608;2159–2273;8984–9190) | _synthesize_content:6072 | `FROZEN_KEEP` | Do not authorize model factual prose by this roadmap | `test_intelligence_loop_evals.py` |
| F27 | Q02-A/C | `_GUIDANCE_SECTION_FAMILIES/_guidance_family_for_key/_deterministic_guidance_content` (2750–3108) | _business_lines:4391/4428;_synthesize_content:9036/9086/9133 | `RELOCATE_OR_REPLACE` | Check owner response meaning vs field-name lexical interpretation; preserve factual renderer | `test_stage03_discovery_guidance.py` |
| F28 | Q02-A | `classify_result_intent/classify_personal_ticket_scope (adjacent module)` (paginated_result_semantics.py:49–110,203–232) | orchestration:2616/2617/8873/8874 | `REPLACE_SEMANTIC_ENTRY` | Keep count scopes and all ticket authorization/total safeguards; move language meaning to typed intent | `test_conversational_intelligence_baseline.py` |
| F29 | Q02-B | `_eligible_self_index_probe optional schema assumptions` (1252–1278) | _attempt probe:5414;_bind_arguments_from_index:9652 | `CONTRACT_GATE` | {} schema-valid not equivalent to omit→index owner operation contract | `test_mcp_iterative_index_probe.py` |
| F30 | ADR_GATE | `_synthesize_content evidence selection-only` (8984–9190) | _attempt:6072 | `FROZEN_KEEP` | Owner-sourced scalar leaves only; meaningful comparison may need separate ADR | `test_stage05_grounded_response.py` |
| F31 | Q02-C | `_select_candidate/_propose_candidate_arguments duplicate InvokeModel.execute` (10208–10465) | _resolve_candidate:10199;_candidate_arguments:10363 | `CONSOLIDATE` | Use existing _propose/invoke model stage without exposing candidate tokens | `test_specialist_capability_orchestration.py` |
| F32 | Q02-A | `prior skip/singleton structural inference` (9283–9285;9381–9385) | _attempt/_select_target | `REMOVE` | Semantic applicability must remain explicit model proposal | `test_r1_r3_none_selection_and_projection.py` |
| F33 | Q02-C | `recover_empty_selection returns list` (4931–5025;6784–7027) | _attempt/_prior_continuation_attempt | `RESTRICT` | Compare/analyze cannot pass by copying lines; must signal true insufficiency | `test_provider_neutral_semantic_provenance_and_continuity.py` |
| F34 | Q02-B | `substring/stem provenance & untrusted workspace` (875–945;3425–3473) | _build_arguments/_resolve_missing_inputs | `REPLACE_FAIL_CLOSED` | Typed value provenance not model assertion or substring; live owner revalidation unchanged | `test_generic_multistep_orchestration.py` |
| F35 | Q02-A | `index rerank LLM then lexical veto` (3760–3823;9652–9744) | _bind_arguments_from_index | `REMOVE` | Exact declared identifier membership only; no post-LLM linguistic scoring | `test_i04_provider_neutral_generalization.py` |
| F36 | Q02-B | `full-input free string & dormant experimental budget guard` (3548–3590;4778–4795;9813–9955) | _build_arguments | `CONTRACT_CONSUMER_GATE` | Identify valid free-text consumer and all env/test defaults first | `test_real_product_owner_read_and_budget_rework.py` |
| F37 | Q02-A | `_groups provider.list_groups sequential each turn` (8312–8345) | _attempt/_select_target | `MEASURE_FIRST` | May be latency, but cannot cache authority or alter credentials without contract | `test_provider_neutral_orchestration.py` |
| F38 | Q02-A/B | `_propose model budget and index headroom` (6735–6782;8596–8772) | _attempt/index selection | `MEASURE_FIRST` | Use TurnDeadline shared; stage/turn config unaltered without runtime evidence | `test_execution_ceiling_turn_budget.py` |
| F39 | Q02-C | `_wording_leaks_technical and clarification fallback` (2121–2158;3325–3371) | _clarification_question:8773 | `RESTRICT` | Protect credential redaction while avoiding broad punctuation/field-name suppression | `test_stage06_generalization_safety.py` |
| F40 | Q02-A | `coverage detector overrides group select` (1320–1395;8374–8497) | _select_target:8467 | `REMOVE` | Typed coverage/discovery request, validate live surface | `test_r2_provider_neutral_capability_selection_quality.py` |
| F41 | ADR_GATE | `empty context_fields contract vs compare checker` (1589–1716) | _corroborate_attempt:7349 | `CONTRACT_GATE` | Cannot silently change comparability rules, owner evidence and units | `test_stage05_grounded_response.py` |
| F42 | ADR_GATE | `all shared fields treated as comparison context` (1559–1716) | _compare_records:1589 | `CONTRACT_GATE` | Separate scope from differences only if provenance-aware contract legitimizes it | `test_stage05_grounded_response.py` |

## 3. Reutilização e owners — decisões do levantamento

| Necessidade | Equivalente existente | `EXISTING_EQUIVALENT` | `REUSE_DECISION` | Binding |
|---|---|---|---|---|
| Interpretação, goal, seleção e arg proposal | `InvokeModel`, `_propose`, `_understand_goal`, `_select_capability_with_goal` | YES | EXTEND | Revisão de consumers tipados; evitar nova camada |
| Live provider discovery/invoke | `CapabilityProviderPort`, `ProviderCapability`, adapters MCP e OpenAPI | YES | REUSE | Provider protocol/details permanecem adapter-only |
| JSON Schema/protection | `argument_validation`, `_unproven_identifier_inputs` (gate preservado, mecanismo não) | YES | EXTEND | Identificadores reais exigem proveniência e Core/Domain owner |
| Deadline/invoke model | `TurnDeadline`, `InvokeModel.execute` | YES | REUSE | 30s global sem timeout bump genérico |
| Conversation input/status | `HandleInteractiveConversationTurn` + `GovernedCapabilityAttempt` | YES | REUSE/EXTEND | Lifecycle non-grounded vs grounded nunca confundir |
| Prior evidence typed beyond rendered text | `InteractionTurn` / `SpecialistOutcome` / `SourceRef` | YES for concepts, unknown durable replay contract | TO_INVENTORY | Não inventar nova memória nem considerar texto anterior fonte FACT |
| Literal verified user span/owner result provenance | `SourceRef`, model typed proposal, workspace context | PARTIAL — typed origin representation gap | TO_INVENTORY | STOP if new contract needed; never accept self-claimed model provenance |
| Owner index omit→index | `_contract_declares_omit_returns_index` + provider schema | YES for owner-declared cases | REUSE | Empty-read inferido só por schema é insuficiente |
| Comparison with factual authored prose | `SYNTHESIS_INSTRUCTION` `selection-only` frozen | YES with restrictive contract | PRESERVE | Qualquer evolução requer ADR separado |
| Write/confirm/idempotency/postcondition | `domain/governed_write`, PendingWrite, Domain API/Core | YES | REUSE | Preservar integralmente |

## 4. Testes existentes já localizados no GitHub (não executados)

Relevant suites and uncovered behavior flagged by static evidence:

| Suite | Evidência de testes no arquivo | Direção |
|---|---|---|
| `test_specialist_capability_orchestration.py` | 99 tests, model-invented capability/ACT/write/real provider | PRESERVE security, update semantic-only assertions |
| `test_generic_multistep_orchestration.py` | 25 tests, resolver, unknown IDs, PREPARE chain | PRESERVE fail-closed |
| `test_provider_neutral_orchestration.py` | 19 tests, renamed providers, contract & failure | PRESERVE |
| `test_intelligence_loop_evals.py` | 39 tests incl. selection-only hallucination/technical leak | PRESERVE frozen factual contract |
| `test_semantic_path_composition_evals.py` | 36 tests, native/foreign fanout & trusted goal | PRESERVE |
| `test_execution_ceiling_turn_budget.py` | 36 tests, timeout, no general hallucination, ACT denied | PRESERVE |
| `test_adaptive_capability_routing_completion.py` | 10 tests incl. lexical rank `test_rank_index_options_prefers_lexical_overlap` | **SUPERSEDED TEST**: replace with semantic selection + owner member check |
| `test_r2_provider_neutral_capability_selection_quality.py` | 20 tests incl. `test_coverage_inquiry_detector` | **SUPERSEDED TEST**: replace with typed coverage request holdouts |
| `test_semantic_intelligence_orchestration_recovery.py` | 6 tests incl. `test_sem_t20_admission_skips_when_prior_turns_present` | **SUPERSEDED TEST**: topic-change/greeting on prior history |
| `test_i03_k2_k3_nonregression.py` | 13 tests incl. invalid-index extraction recovery | DIFFERENTIATE extraction vs compare; don't simply delete |
| `test_i02_k2_k3_output_quality.py` | 16 tests incl. phrase coverage/continuity helpers | Behavior-based verification of task completeness |
| `test_stage05_multiturn_semantic_rework.py` | 14 tests, epistemic hints and referent continuity | PRESERVE negative/evidence controls |
| `test_stage05_multiturn_latency.py` | 7 tests, follow-ups and 30s budget | PRESERVE strict deadline |
| `test_i04_provider_neutral_generalization.py` | 17 tests, provider rename, ordering, live-like model | PRESERVE metamorphic tests |
| `test_mcp_iterative_index_probe.py` | 11 tests, owner contract omit-index | PRESERVE contract gate |
| `test_i02r2_index_probe_headroom.py` | 7 tests, optional index and budget | PRESERVE strict budget, adjust dead-path assertions if contract changes |
| `test_stage05_grounded_response.py` | 9 tests, comparison and evidence claims | PRESERVE |
| `test_provider_neutral_semantic_provenance_and_continuity.py` | 17 tests, lexical coverage, bullet recovery | REWORK negative cases, preserve rejection of invented qualifier |
| `test_real_product_owner_read_and_budget_rework.py` | 16 tests, product real READ and id guards | PRESERVE outcome/security |
| `test_openapi_capability_provider.py` | 16 tests, HTTP/auth/timeout | PRESERVE adapter |
| `test_interaction_continuity.py` | 30 tests, prior-turn untrusted/nonFACT | PRESERVE |
| `test_render_specialist_outcome_fidelity.py` | 10 tests, leaf/fidelity/redaction | PRESERVE |

**Caution:** test count here based on `def test_*` static extraction in individual fetched files, not pytest collection count or runtime `PASS`.

## 5. Reconciliation: ADR58 × finite roadmap59 × actual phase

- `I04_ACCEPTED=NO`; owner-read DAVI/OpenAPI reported live, TÉO personal blocked by real subject/owner, VISTA C02 = 504 reported. G0 is not PASS via docs.
- `Q01_AUTHORIZED=NO`; this dossier is **preparation by GPT**, not acceptance of Q01. If G0 is approved later, Q01 may use this inventory and request only SHA drift/consumer residual check plus baseline gates.
- Q02-A/B/C own respectively semantic code, arguments/index/provenance, continuity/outcome; each only diff after prerequisites. Security tests never loosened; obsolete tests replaced with behavior tests, not deleted without coverage.
- `SELECTION_ONLY_GROUNDED_SYNTHESIS=FROZEN` (ledger §6.145); no unsupported promise to generate model-authored business facts.

```text
DISCOVERY_STATUS=COMPLETED_WITH_CONNECTOR_LIMITATION
REVIEWED_SOURCE_BLOB=bc13e07b31b6844e172c5d485d77f59a4b8c0a10
AUDIT_FINDINGS_MAPPED=42/42
INTERNAL_CALL_SITE_MAP=PROVEN_FOR_KEY_BOUNDARIES
CROSS_FILE_ENTRYPOINT_AND_PROVIDER_CONTRACT=PROVEN
TEST_SUITES_OPENED=22
REPO_WIDE_FULL_CONSUMER_SEARCH=TO_INVENTORY
LIVE_G0_REEVAL=TEST_NOT_RUN
Q01_EXECUTED=NO
RUNTIME_DIFF=NONE
```
