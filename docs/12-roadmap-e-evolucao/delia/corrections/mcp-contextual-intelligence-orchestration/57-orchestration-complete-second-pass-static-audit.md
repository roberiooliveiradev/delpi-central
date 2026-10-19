# 57 — Second-pass complete file sweep: orchestration code audit and safe-removal map

**Date:** 2026-10-19. **Repository:** `roberiooliveiradev/delpi-central`. **Source SHA examined:** `8fc45e2119f3cc7b1b34a0f79bca144e5f822516` (only documentation commits after this SHA during audit). **Scope:** `delia-api/app/application/capability_provision/orchestration.py`, **1–10,592 / 10,592 lines**, **179 declarations**. **First-pass checkpoint:** [56](./56-orchestration-audit-semantic-ownership-checkpoint.md), 25 candidate groups. **Second-pass:** full source line-range census, static def/call-site/cross-stage review, supplementary findings F26–F42. **Tests and live production:** `TEST_NOT_RUN` in this review. **No code edited.**

## Review authority and limitations

Reviewed at GitHub HEAD: 16 (phase authority), 50 (standalone boundary), 49 (design patterns), 51 (platform baseline), 52 (bootstrap), 21 (state), 20 (testing), 25 (traceability), contextual correction docs 52–55 and ledger §§6.294–6.298. **Canonical 17 and .cursor entrypoints not independently located/read in this review; a future code-changing task MUST perform full mandated reanchor.** Existing canon may freeze selection-only factual synthesis and comparable-context gates: `STOP → ARCHITECTURE_DECISION_REQUIRED`, never redesign silently. The review does **not** certify deletion safety or audit all external consumers.

Source truth hierarchy: code SHA for implementation; authorities for normative design; ledger for accepted execution; executor reports for reported live outcomes. No new runtime acceptance inferred.

## Coverage: every file region inspected and classified

| Inclusive lines | Responsibilities examined | Audit disposition |
|---|---|---|
| 1-220 | Imports, capability structures, bounds | RETAIN structural ports, operation classes; verify unused caps |
| 221-760 | LLM stage prompts and purpose contracts | CONSOLIDATE duplicated interpretation; preserve output schema/trust rules; syntax/synthesis policy ADR |
| 761-1320 | Candidate lineage, schema/index eligibility, free-text provenance | REMOVE lexical semantic gate; retain contract ids and typed validation; review inferred self-index |
| 1321-1755 | Discovery, coverage regex, owner evidence comparison | REMOVE coverage regex; FIX comparison contract contradiction; retain provenance gates |
| 1756-2148 | Evidence, missing inputs, schema defaults, clarification | KEEP schema/owner defaults; REWORK semantic ask-back; protect policy |
| 2149-2604 | Synthesis render, prior excerpts, comparison clauses | STOP list-as-compare; evidence must remain typed; UI projection relocation by reuse |
| 2605-3174 | Pagination, guidance classification, owner payload projection | KEEP pagination math; REPLACE language regex and schema-shape guesses |
| 3175-3641 | Resolver ambiguity, ordinal regex, id provenance, schema args | REPLACE ordinal and substring provenance; retain owner membership |
| 3642-3960 | Index intent clusters, extraction regex, scoring, list fallback | REMOVE semantic lexical ranking and response-size heuristics |
| 3961-4734 | Capability projection, redaction, formatting, activity | KEEP redaction/sanitization; inventory renderer owner; distinguish page count |
| 4735-5100 | Orchestrator init, admission, prior continuity, selection | REWORK repeated semantic decisions; preserve cancellation and confirmed path |
| 5101-5610 | Write-intent reconciliation, native/foreign assessment, discovery/index | KEEP fail-closed write gate; remove needless inference stages and ambiguous index semantics |
| 5611-6107 | Argument binding, optional probe-skip, invoke, final attempt | REPLACE lexical provenance; keep owner schemas and failure taxonomy |
| 6108-6783 | Resolver, continuation ANALYSIS->PREPARE, goal, budgets | KEEP governed cross-operation; remove lexical ordinal; avoid redundant model decisions |
| 6784-7404 | Prior transformation, native/foreign evaluation, evidence comparison | REPLACE list fallback for compare; preserve typed evidence and multi-owner constraints |
| 7405-8311 | PREPARE/ACT, confirmation, pending state, idempotency, audit | PRESERVE; audit semantics; never remove governance with refactor |
| 8312-8983 | Capability listing, target, plan, model propose, pagination aggregate | CONSOLIDATE model invocation & repeated semantic calls; keep live validation/count math |
| 8984-9608 | Synthesis, repair, interaction admission/group and capability selection | REWORK no-prose-only synthesis, prior skip and singleton shortcut; keep repair bound |
| 9609-10000 | Index probe/selection, arguments, selected invoke | REMOVE lexical relevance veto; fix unreachable optional probe; keep contract validation |
| 10001-10592 | Candidate discover->execute, raw model duplicate calls, provider invocation | UNIFY model invocation, preserve candidate token and owner delegated context |

Coverage is a **static source sweep**, not formal proof that every branch was executed. The 20 inclusive partitions above are contiguous and jointly cover every line 1–10592.

## Supplemental findings beyond first-pass 25

| ID | Source line(s) | New finding / failure mode | Disposition | Boundary-safe direction |
|---|---|---|---|---|
| F26 | 2409–2440; 2493–2604; 8984–9190 | Model synthesis is selection-only, user-facing prose prohibited; deterministic field labels and templates may not meet analysis/comparison outcome | `ARCHITECTURE_DECISION_REQUIRED` | Do not enable unconstrained model factual prose; consider evidence-cited claim/sentence contract only after governance approval |
| F27 | 2780–3067 | _GUIDANCE_SECTION_FAMILIES and shape/key prefix affinity plus guidance aliases embedded in generic orchestrator | `SEMANTIC_REWORK` | Move purely factual projection to legitimate typed owner/adapter if available; model chooses relevance |
| F28 | 2604–2657; 8853–8983 | Two rendering/aggregation paths call classify_personal_ticket_scope and classify_result_intent(input_text), outside-file linguistic classifiers | `CROSS_FILE_AUDIT` | Keep count/personal fail-closed, source semantic intent from existing typed goal; separately audit paginated_result_semantics.py |
| F29 | 1252–1278; 5402–5485; 5730–5790 | Self-index eligibility inferred from optional strings and empty args, but searchable READ need not expose index; optional probe always skipped at stage30/turn30 | `CONTRACT_REVIEW` | Require explicit owner contract for omit->index; distinguish exploratory free text from opaque identifiers |
| F30 | 2098–2107; 2159–2273; 8984–9190 | Fixed synthesis index/field selection + template renderer cannot express rich, traceable reasoning; recorded live L5 list masqueraded as comparison | `ARCHITECTURE_DECISION_REQUIRED` | Preserve evidence boundary and prior-only status; design typed grounded propositions if authorities allow |
| F31 | 10208–10324; 10380–10465 vs 8596–8772 | Candidate selection and candidate argument projection invoke model directly rather than shared _propose, duplicate stage timeout/lineage/output validation | `CONSOLIDATE` | Reuse approved InvokeModel/_propose path without widening what model sees |
| F32 | 9283–9285; 9381–9385; 9500+ | Prior-turns skip admission; singleton group auto-selected; semantic applicability can be inferred from structure | `SEMANTIC_REWORK` | Unified typed decision and conversation support for follow-ups; keep surface membership validation |
| F33 | 4931–5025; 6784–7027 | Prior continuation can return SUCCESS/limitation with replayed bullet list after empty model selection even for compare/analyze goal | `OUTCOME_REWORK` | Verify type of task and evidence field sufficiency; return explicit insufficiency if comparison impossible |
| F34 | 3410–3473; 875–946 | Substring/prefix rules are weak provenance for identifiers/free text; workspace prompt block is client-supplied and cannot authorize | `PROVENANCE_REWORK` | Keep reject-unproven gate and owner revalidation; user-spans/owner refs typed not lexical acceptance |
| F35 | 3760–3823; 9652–9744 | Owner index option is first semantically reranked by fixed clusters, then selected by LLM, then vetoed by same lexical score | `REMOVE_SEMANTIC_VETO` | Retain membership in owner-declared identifiers and exact field validation |
| F36 | 9813–9955; 4778–4795 | Single-free-text budget fallback can put entire request into owner field; experimental argument guard dead/default false may add complexity | `CONTRACT_AND_CONSUMER_INVENTORY` | Do not remove valid owner-declared single text passthrough; establish usage before deleting experiment |
| F37 | 8312–8345 | Every eligible provider group is queried serially each operational turn before choosing target; under load may constrain 30s budget | `PERFORMANCE_INVESTIGATION` | Do not cache authority silently or parallelize insecurely; measure per-owner surface list and contract freshness |
| F38 | 8600–8676; 6735–6782 | Numerous LLM stages share global 30s budget; independent stage cap30 and optional-probe headroom≈66s produce unreachable path | `MODEL_CALL_CONSOLIDATION` | Measure cold/warm per purpose, retain deadline and user outcome |
| F39 | 2121–2130; 3325–3371 | Static blacklists/generic clarifications can suppress ordinary natural-language output and lose missing-field semantics | `PRESENTATION_GATE_REVIEW` | Retain redaction/secret filtering; avoid user text/punctuation heuristics as substitute for safe grounded responses |
| F40 | 1320–1395; 8374–8497 | Fixed 'coverage' regex can override model selection into DISCOVERY despite alternative semantic intent | `REMOVE_LANGUAGE_OVERRIDE` | Typed LLM intent, validate provider discovery capability against live surface; no provider names |
| F41 | 1609–1716; 711–729 | Comparison instruction says context_fields may be empty; _compare_records insists nonempty and all other shared scalars equal | `CONTRACT_DRIFT` | Do not silently weaken business comparability; reconcile canonical policy + tests |
| F42 | 1559–1716 | Comparing two different product records with all shared fields treated as scope can spuriously yield INCONCLUSIVE | `CONTRACT_DRIFT` | Separate identifying/business context from fields intentionally compared under owner schema; no generic inferred equivalence |

## Architectural central observation

There are three different classes of code mixed into one large Application service:

1. **Language/intent policy embedded in Python:** regexp-based coverage, guidance intent, recent/live text cues, ordinal, index clusters, extraction completeness. These are strong candidates for removal or replacement with the existing typed LLM goal/selection outcome. `REMOVE` only after tests prove no uncovered contracted behavior.
2. **Safe deterministic runtime:** schema validation, owner-declared identifiers, cross-owner capability projection, generic adapter invocation, redaction, bounded deadlines, confirmation/pending store, idempotency, audit, Core/domain authority, verified outcome, count semantics. These are **not removal targets**.
3. **Presentation and task outcome:** raw-text excerpts, lexical intent-to-guidance projection, bullet recovery and selection-only synthesis; these can avoid 504 while failing user intent. Need review of existing Evidence/Outcome/presentation contracts and possible architecture decision before changing the frozen fact-grounding model.

## Subtle cross-cutting findings

- `interaction_admission`, `select_group`, `select_capability_with_goal`, `turn_goal`, and `native_assessment` can independently spend model calls on adjacent semantic decisions. The issue is *validity and continuity of a single typed interpretation*, not simply number of LLM requests; any consolidation must keep owner selection/gates.
- `_eligible_self_index_probe` assumes a schema-valid empty READ with optional free strings may be an index; owner explicit omit→index and model-suggested probe are not equivalent contractual guarantees.
- Owner-guidance normalization maps `displayformats`, `legibility`, `playbook`, etc. through generic prefixes and user regex. This is a field-vocabulary adapter/classifier embedded inside the generic orchestrator, susceptible to incidental matches.
- Three direct `InvokeModel.execute` calls in this file: line **8676** is shared `_propose`; lines **10262** and **10408** are candidate-specific duplicate orchestration of model stages. Reuse before new abstraction.
- **21** `re.compile` occurrences in the file; some legitimate (secrets/redaction and syntactic format), some language classifiers. Blanket regex removal would weaken privacy and is not authorized.
- No explicit `if provider == DAVI/TEO/VISTA` branch in the inspected file. The coupling is primarily to **language/topic shapes, presentation fields and generic provider response heuristics**, not hard-coded owner identity.
- The 30s stage+turn setup means optional index headroom = `2 * stage_timeout + 3 * MIN_VIABLE_MODEL_STAGE_SECONDS` (reported ≈66s), exceeding 30s turn; this path should be explicit contract-led or removed if genuinely unreachable. Do not increase global timeout.
- The prior-continuation "list recovery" must never pass task-outcome checks for requests to compare/analyze when it only repeats excerpts. A SUCCESS transport envelope can still contain business insufficiency.
- `classify_personal_ticket_scope` and `classify_result_intent` are imported from adjacent module; their internals are outside this file and require separate follow-up before changes. Personal ticket count, page_size/total safeguards remain essential.

## Exact definition inventory (179 declarations; preserves scope accountability)

Each declaration is listed with its line. Dispositions indicate **review category**, not implementation authorizations.

**Lines 1-220:** No function/class declarations; top-level contracts/configuration inspected.

**Lines 221-760:** No function/class declarations; top-level contracts/configuration inspected.

**Lines 761-1320:** `768:_lineage` (`CONTRACT_INVENTORY`), `810:_candidate_args_lineage` (`CONTRACT_INVENTORY`), `816:_candidate_selection_lineage` (`CONTRACT_INVENTORY`), `822:_is_candidate_bound` (`CONTRACT_INVENTORY`), `827:_is_proposal_bound` (`CONTRACT_INVENTORY`), `834:_requires_field` (`CONTRACT_INVENTORY`), `846:_is_open_vocabulary` (`CONTRACT_INVENTORY`), `875:_fold_alnum_text` (`CONTRACT_INVENTORY`), `884:_alnum_tokens` (`CONTRACT_INVENTORY`), `888:_token_covered_by_user_tokens` (`SEMANTIC_REWORK`), `915:_free_string_grounded_in_user_input` (`SEMANTIC_REWORK`), `948:_is_unconstrained_string` (`CONTRACT_INVENTORY`), `984:_requires_owner_vocabulary` (`CONTRACT_INVENTORY`), `1005:_contract_declares_omit_returns_index` (`CONTRACT_INVENTORY`), `1041:_optional_unconstrained_string_keys` (`CONTRACT_INVENTORY`), `1065:_index_catalog_entities` (`CONTRACT_INVENTORY`), `1078:_mappings` (`CONTRACT_INVENTORY`), `1104:_index_option_rows` (`CONTRACT_INVENTORY`), `1182:_index_declared_identifiers` (`CONTRACT_INVENTORY`), `1194:_post_self_index_argument_gaps` (`PRESERVE_GATE`), `1234:_project_selected_index_identifier` (`PRESERVE_GATE`), `1252:_eligible_self_index_probe` (`BOUNDARY_REVIEW`), `1297:_PlanCapabilityView` (`CONTRACT_INVENTORY`), `1305:_plan_views` (`CONTRACT_INVENTORY`), `1320:_discovery_capability` (`CONTRACT_INVENTORY`)

**Lines 1321-1755:** `1355:_is_information_coverage_inquiry` (`SEMANTIC_REWORK`), `1371:_owner_eligible_action_count` (`CONTRACT_INVENTORY`), `1391:_discovery_empty_result_class` (`CONTRACT_INVENTORY`), `1407:_live_interop_surface_lines` (`CONTRACT_INVENTORY`), `1438:_render_zero_candidate_discovery` (`CONTRACT_INVENTORY`), `1511:_find_capability` (`CONTRACT_INVENTORY`), `1529:_comparison_records` (`CONTRACT_INVENTORY`), `1543:_comparable_scalar` (`CONTRACT_INVENTORY`), `1589:_compare_records` (`BOUNDARY_REVIEW`), `1609:_side` (`CONTRACT_INVENTORY`), `1719:_bound_owner_evidence` (`CONTRACT_INVENTORY`), `1755:_compact_evidence` (`CONTRACT_INVENTORY`)

**Lines 1756-2148:** `1794:_evidence_rows` (`CONTRACT_INVENTORY`), `1823:_missing_inputs` (`CONTRACT_INVENTORY`), `1846:_extract_owner_entity_schemas` (`PRESERVE_GATE`), `1876:_entity_payload_slot` (`CONTRACT_INVENTORY`), `1893:_value_present` (`CONTRACT_INVENTORY`), `1903:_schema_required_gaps` (`PRESERVE_GATE`), `1966:_apply_owner_declared_defaults` (`CONTRACT_INVENTORY`), `1981:_owner_entity_completeness_gaps` (`CONTRACT_INVENTORY`), `2031:_apply_entity_defaults_to_arguments` (`CONTRACT_INVENTORY`), `2053:_argument_completeness_gaps` (`PRESERVE_GATE`), `2121:_wording_leaks_technical` (`CONTRACT_INVENTORY`), `2132:_clarification_content` (`BOUNDARY_REVIEW`)

**Lines 2149-2604:** `2159:_render_synthesis` (`BOUNDARY_REVIEW`), `2274:_proven_field_differences` (`CONTRACT_INVENTORY`), `2306:_insufficiency_content` (`CONTRACT_INVENTORY`), `2311:_prior_excerpt_records` (`BOUNDARY_REVIEW`), `2378:_prior_transform_probe_eligible` (`SEMANTIC_REWORK`), `2457:_record_identifier` (`CONTRACT_INVENTORY`), `2482:_clause_prefix` (`CONTRACT_INVENTORY`), `2493:_compose_answer` (`BOUNDARY_REVIEW`), `2539:_detail_header` (`CONTRACT_INVENTORY`), `2552:_detail_lines` (`CONTRACT_INVENTORY`), `2565:_records_are_prior_excerpts` (`CONTRACT_INVENTORY`), `2581:_list_header` (`CONTRACT_INVENTORY`), `2604:_project_paginated_personal_or_count` (`BOUNDARY_REVIEW`)

**Lines 2605-3174:** `2689:_unwrap_owner_payload` (`CONTRACT_INVENTORY`), `2704:_resolver_entities` (`CONTRACT_INVENTORY`), `2715:_mappings` (`CONTRACT_INVENTORY`), `2914:_guidance_intent_families` (`SEMANTIC_REWORK`), `2934:_guidance_family_for_key` (`BOUNDARY_REVIEW`), `2948:_render_guidance_value` (`CONTRACT_INVENTORY`), `2972:_mapping_items_excluding_control` (`CONTRACT_INVENTORY`), `2982:_guidance_hit_count` (`CONTRACT_INVENTORY`), `2990:_iter_guidance_doc_items` (`CONTRACT_INVENTORY`), `3030:_guidance_section_records` (`BOUNDARY_REVIEW`), `3067:_deterministic_guidance_content` (`BOUNDARY_REVIEW`), `3122:_synthesis_records` (`BOUNDARY_REVIEW`)

**Lines 3175-3641:** `3175:_entity_identifier` (`CONTRACT_INVENTORY`), `3202:_resolver_ambiguous` (`CONTRACT_INVENTORY`), `3231:_user_list_ordinal` (`SEMANTIC_REWORK`), `3242:_prior_listing_hint` (`SEMANTIC_REWORK`), `3294:_fill_missing_from_entity` (`CONTRACT_INVENTORY`), `3325:_candidate_clarification_content` (`BOUNDARY_REVIEW`), `3372:_resolved_values_proven` (`BOUNDARY_REVIEW`), `3393:_schema_declared_literals` (`PRESERVE_GATE`), `3400:_walk` (`CONTRACT_INVENTORY`), `3425:_unproven_identifier_inputs` (`BOUNDARY_REVIEW`), `3481:_effective_confirmation_policy` (`PRESERVE_GATE`), `3513:_schema_keys` (`PRESERVE_GATE`), `3536:_property_node` (`CONTRACT_INVENTORY`), `3548:_sole_unconstrained_string_field` (`CONTRACT_INVENTORY`), `3573:_single_free_text_argument_from_input` (`BOUNDARY_REVIEW`), `3592:_deterministic_arguments_from_schema` (`PRESERVE_GATE`)

**Lines 3642-3960:** `3699:_index_text_tokens` (`SEMANTIC_REWORK`), `3707:_index_cluster_hits` (`SEMANTIC_REWORK`), `3716:_tokens_stem_related` (`SEMANTIC_REWORK`), `3725:_index_option_relevance_score` (`SEMANTIC_REWORK`), `3773:_rank_index_options_by_overlap` (`SEMANTIC_REWORK`), `3786:_key` (`CONTRACT_INVENTORY`), `3795:_index_selection_is_relevant` (`SEMANTIC_REWORK`), `3846:_collect_extraction_units` (`CONTRACT_INVENTORY`), `3870:_count_covered_extraction_units` (`SEMANTIC_REWORK`), `3897:_prior_extraction_incomplete` (`SEMANTIC_REWORK`), `3919:_extraction_list_from_prior_excerpts` (`BOUNDARY_REVIEW`), `3938:_recover_prior_extraction_after_invalid_index` (`SEMANTIC_REWORK`), `3960:_project_surface` (`CONTRACT_INVENTORY`)

**Lines 3961-4734:** `3981:_group_summaries` (`CONTRACT_INVENTORY`), `4039:_capability_payload` (`CONTRACT_INVENTORY`), `4121:_canonical_key` (`CONTRACT_INVENTORY`), `4125:_is_sensitive_key` (`CONTRACT_INVENTORY`), `4181:_redact_text` (`PRESERVE_GATE`), `4192:_sanitize_renderable` (`PRESERVE_GATE`), `4234:_is_generic_status` (`CONTRACT_INVENTORY`), `4238:_format_structured` (`CONTRACT_INVENTORY`), `4277:_format_list` (`CONTRACT_INVENTORY`), `4302:_format_records` (`CONTRACT_INVENTORY`), `4318:_business_lines` (`CONTRACT_INVENTORY`), `4352:render_specialist_outcome` (`CONTRACT_INVENTORY`), `4524:_find_act_capability` (`CONTRACT_INVENTORY`), `4544:_act_arguments` (`CONTRACT_INVENTORY`), `4571:_preview_render` (`CONTRACT_INVENTORY`), `4665:_emit_activity` (`CONTRACT_INVENTORY`), `4677:_group_activity_refs` (`CONTRACT_INVENTORY`), `4697:_activity_outcome_summary` (`CONTRACT_INVENTORY`), `4734:_StageDeadlineExceeded` (`CONTRACT_INVENTORY`)

**Lines 4735-5100:** `4744:__init__` (`CONTRACT_INVENTORY`), `4750:OperationalCapabilityOrchestrator` (`CONTRACT_INVENTORY`), `4769:__init__` (`CONTRACT_INVENTORY`), `4796:attempt` (`CONTRACT_INVENTORY`), `4863:_attempt` (`CONTRACT_INVENTORY`)

**Lines 5101-5610:** No function/class declarations; top-level contracts/configuration inspected.

**Lines 5611-6107:** No function/class declarations; top-level contracts/configuration inspected.

**Lines 6108-6783:** `6108:_resolve_missing_inputs` (`CONTRACT_INVENTORY`), `6299:_select_resolver` (`CONTRACT_INVENTORY`), `6385:_analysis_continuation` (`CONTRACT_INVENTORY`), `6543:_turn_goal_from_proposal` (`CONTRACT_INVENTORY`), `6649:_understand_goal` (`CONTRACT_INVENTORY`), `6689:_prior_result_turn` (`CONTRACT_INVENTORY`), `6701:_prior_result_content` (`CONTRACT_INVENTORY`), `6717:_budget_allows_resolver` (`CONTRACT_INVENTORY`), `6735:_budget_allows_optional_index_probe` (`CONTRACT_INVENTORY`), `6761:_budget_allows_arguments_propose` (`CONTRACT_INVENTORY`)

**Lines 6784-7404:** `6784:_prior_continuation_attempt` (`BOUNDARY_REVIEW`), `7029:_assess_native_path` (`CONTRACT_INVENTORY`), `7107:_select_foreign_capability` (`CONTRACT_INVENTORY`), `7191:_invoke_foreign_evidence` (`PRESERVE_GATE`), `7280:_corroborate_attempt` (`CONTRACT_INVENTORY`)

**Lines 7405-8311:** `7405:_select_prepare_continuation` (`CONTRACT_INVENTORY`), `7479:_attempt_prepare` (`PRESERVE_GATE`), `7691:_attempt_direct_act` (`PRESERVE_GATE`), `7762:_attempt_confirmation` (`PRESERVE_GATE`), `7852:_confirm_proposal` (`PRESERVE_GATE`), `7975:_execute_prepared_act` (`PRESERVE_GATE`), `8083:_invoke_act` (`PRESERVE_GATE`), `8160:_provenance` (`PRESERVE_GATE`), `8194:_outcome_attempt` (`PRESERVE_GATE`), `8278:_audit` (`PRESERVE_GATE`)

**Lines 8312-8983:** `8312:_groups` (`PRESERVE_GATE`), `8347:_fresh_group` (`PRESERVE_GATE`), `8374:_select_target` (`BOUNDARY_REVIEW`), `8498:_build_plan` (`PRESERVE_GATE`), `8581:_log_plan` (`CONTRACT_INVENTORY`), `8596:_propose` (`CONTRACT_INVENTORY`), `8773:_clarification_question` (`CONTRACT_INVENTORY`), `8853:_maybe_aggregate_paginated_count` (`BOUNDARY_REVIEW`)

**Lines 8984-9608:** `8984:_synthesize_content` (`BOUNDARY_REVIEW`), `9191:_repair_once` (`CONTRACT_INVENTORY`), `9267:_admit_conversational_turn` (`BOUNDARY_REVIEW`), `9365:_select_group` (`BOUNDARY_REVIEW`), `9422:_capability_from_selection_proposal` (`CONTRACT_INVENTORY`), `9470:_select_capability` (`CONTRACT_INVENTORY`), `9530:_select_capability_with_goal` (`CONTRACT_INVENTORY`)

**Lines 9609-10000:** `9609:_propose_index_probe` (`CONTRACT_INVENTORY`), `9652:_bind_arguments_from_index` (`CONTRACT_INVENTORY`), `9746:_propose_index_identifier` (`CONTRACT_INVENTORY`), `9813:_build_arguments` (`CONTRACT_INVENTORY`), `9979:_invoke_selected` (`PRESERVE_GATE`)

**Lines 10001-10592:** `10128:_discover_candidate` (`CONTRACT_INVENTORY`), `10160:_candidates_present` (`CONTRACT_INVENTORY`), `10168:_resolve_candidate` (`CONTRACT_INVENTORY`), `10208:_select_candidate` (`BOUNDARY_REVIEW`), `10326:_candidate_arguments` (`PRESERVE_GATE`), `10380:_propose_candidate_arguments` (`BOUNDARY_REVIEW`), `10466:_invoke` (`PRESERVE_GATE`)

**Classification counts:** `CONTRACT_INVENTORY=112`; `SEMANTIC_REWORK=16`; `PRESERVE_GATE=27`; `BOUNDARY_REVIEW=24`; total=179.

## Dependency and acceptance gates BEFORE removing a single item

For each F/S candidate produce: `RESPONSIBILITY → OWNER → SOURCE CANONICAL → CONSUMERS → CONTRACT → IMPLEMENTATION → TEST → OUTCOME`; `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` and `REUSE_DECISION=REUSE|EXTEND|NEW`. Search usages in all repo (not just this file), tests, prompts, adapters and declared public fields; residual search zero results never proves absence. Compare stable schema outputs, provenance, live domain AuthZ, prior privacy, product/task generalization, timeout 30s, failure taxonomy and rollback at evaluated SHA/config.

**Preserve** Keycloak identity; Core AuthZ; Domain API final authority; owner-supplied schemas; model proposals as HYPOTHESIS, not FACT; PREPARE != ACT; confirmation, pending store, audit, idempotency, postcondition; contextual minimization; secrets redaction; no model-driven physical/safety commands.

**Proposal for bounded execution, not approval:** first remove/replace raw language classifiers and lexical vetoes behind the existing typed decision contract; next address typed prior Evidence/Outcome and grounded synthesis semantics (architecture decision required if frozen contract); then de-duplicate model proposal paths and review optional-index headroom, all with DAVI/TÉO/VISTA/OpenAPI/non-MCP/no-tool test matrix. No new planner/intent engine or provider special-case.

## Review verdict

```text
AUDITED_FILE_LINES=10592/10592_STATIC_SWEEP
DECLARATIONS_INDEXED=179
FIRST_PASS_CANDIDATE_GROUPS=25
SECOND_PASS_ADDITIONAL_FINDINGS=17
CODE_CHANGE=NONE
LIVE_PRODUCTION_TEST=TEST_NOT_RUN
INDEPENDENT_REGRESSION_TEST=TEST_NOT_RUN
CROSS_FILE_CONSUMER_VERIFICATION=TO_INVENTORY
COMPLETE_CANONICAL_REANCHOR_FOR_IMPLEMENTATION=NO
EXISTING_EQUIVALENT=TO_INVENTORY_PER_CHANGE
REUSE_DECISION=PENDING_PER_CHANGE
DELETION_AUTHORIZED=NO
ARCHITECTURE_DECISION_REQUIRED=YES_FOR_FROZEN_SYNTHESIS_OR_COMPARABILITY
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=COORDINATION_ARCHITECTURE_DECISION_ON_SEMANTIC_OWNERSHIP_AND_BOUNDED_REFACTOR
```
