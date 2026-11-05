# 245 — Remoção integral outcome_assessment.py + Pydantic AI structured output

**TASK_ID:** DELIA-C3-OUTCOME-ASSESSMENT-FULL-REMOVAL-AND-NATIVE-STRUCTURED-OUTPUT-01  
**DATE:** 2026-11-05  
**BASE_CODE_HEAD_INSPECTED:** 9d28674cc0d867f804af3648840e88b107fb1bd4  
**STATUS:** PLANNED, NOT IMPLEMENTED  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED

## 1. Pedido e objetivos congelados

Usuário determinou **DELETE físico total** de `delia-api/app/application/capability_provision/outcome_assessment.py` (~1.806 linhas), correção de TODOS os consumidores reais e adoção do **Pydantic AI** para produzir **respostas estruturadas nativas**. Sem mover 1.806 linhas de código para outro arquivo, sem segundo motor de avaliação semântica ou scanner de linguagem para construir Outcome, e sem converter opinião do modelo em FACT/permission.

Antes do diff, reancorar local git status/HEAD/origin + Project Instructions/.cursor → docs 16→50→17→49→51→52→21→20→25 → arquitetura/product spec → specs temáticas → ledger → docs 239–244. Resolver divergência com autoridade superior como EXECUTION_DRIFT/ARCHITECTURE_DECISION_REQUIRED.

**EXISTING_EQUIVALENT:** YES: Pydantic AI `Agent(..., output_type=...)`/native output validators for structured answer, Evidence/SourceRef/Outcome bounded contracts existing; TO_INVENTORY for location of current independent owner-evidence sanitizer/projection equivalents. **REUSE_DECISION:** REUSE native agent + proven Evidence owners; EXTEND minimum verified deterministic postconditions, DELETE module. Ninguém cria registry/Outcome engine ou framework próprio.

## 2. Confirmed consumer inventory at inspected HEAD (NOT exhaustive repository-wide)

`orchestration.py` imports `AnswerRequirements`, numeric limits, `_CAPABILITY_VOCABULARY_KEYS`, `_CONTROL_PLANE_KEYS`, `_RESOLVER_ENVELOPE_KEYS`, `_canonical_key`, `_comparison_records`, `_contract_fact_rows`, `_is_generic_status`, `_mapping_items_excluding_control`, `_redact_text`, `_resolver_entities`, `_sanitize_renderable`, `_unwrap_owner_payload`, `parse_temporal_value`; uses `_compose_multi_evidence` and `_TurnGoal.answer_requirements: AnswerRequirements`.

`conversational_response.py` imports `MAX_RENDER_LIST_ITEMS`, `MAX_SYNTHESIS_FIELDS`, Outcome status constants, `AnswerRequirements`, `OutcomeVerdict`, control keys, UUID regex, `_canonical_key`, `_record_identifier`, `_sanitize_renderable`, `_sanitize_renderable_counted`, `_synthesis_selections`, `ordering_proof_fields`, `parse_temporal_value`, `verified_ordering_event`.

`interaction/handle_interactive_turn.py` imports `_comparison_records`.

`pydantic_ai_investigation.py` did NOT import module directly at examined HEAD; indirectly invokes gates/renderers. Whole-repository imports and string/dynamic references require local `rg`, AST, test imports + contract search. ZERO search results != proof of absence.

Module includes direct `assess_outcome` / `outcome_facts`, structs `EvidenceFacts` / `OutcomeVerdict` / `AnswerRequirements`, sanitization/redaction/projection and comparison helpers, temporal evidence logic, contract metadata filter. Some are legitimate **trust-boundary controls** and must remain independently deterministic through existing owner/contracts (not copied whole).

**DEPENDENCY:** doc244 separately requests deleting `paginated_result_semantics.py`; `outcome_assessment.py::outcome_facts` imports its envelope extraction. Reanchor whether doc244 was executed. Execute changes in correct order or coordinate atomic diff; do not leave stale references in any replaced code.

## 3. Required Pydantic AI native replacement

In `app/infrastructure/orchestration/pydantic_ai_investigation.py` or its existing native Agent owner, define Pydantic v2 models for one terminal **structured investigation answer**, minimally:

`status: COMPLETE|PARTIAL|INSUFFICIENT|PROVEN_EMPTY`; `answer: str`; `evidence_refs: list[str]`; `missing_requirements: list[str]`; optionally `limit_reasons`/ `verified_record_ids` when justified by actual consumer contracts.

Check SDK 2.50.0 at installed version: use `Agent(..., output_type=StructuredInvestigationAnswer)` or correct equivalent API, and `@agent.output_validator` for non-authoritative proposal verification. **Output validation is not an evidence oracle.** Independently verify reference membership to actual authorized tool outcomes, required identity, authoritative page totals, missing obligations, owner scope, completeness; downgrade or reject unsupported COMPLETE as appropriate and preserve available real evidence. Avoid endless retries; honor UsageLimits/deadline/cancel; preserve JSON/NDJSON and terminal `turn_result`. No secret material or raw metadata in model context.

Critical: structured output only determines *format and candidate semantic assertion*. The deterministic Evidence/Policy/Domain boundary performs validation, provenance, redaction, security and factual acceptance. Use existing Evidence models/contracts; do not reconstitute a bespoke `outcome_assessment_v2.py`.

If native output_type conflicts with `FunctionToolset` tool loop or existing completion behavior, investigate exact SDK integration and implement with native feature; do not create alternate agent controller. Test with Pydantic AI TestModel and one real local model.

## 4. Physical deletion + consumers

1. Baseline inventory and RED tests (Outcome facts, content redaction, control-plane excluded from FACT, source lineage, owner identity, compare, timestamp sorting, pagination completeness, personal-ticket scoping, null/partial/guidance behavior, write governance, NDJSON; each must survive in valid owners).
2. Introduce typed terminal response in Infrastructure Agent; map to existing `GovernedCapabilityAttempt` / interaction result without duplicating status taxonomy.
3. Remove lexical/semantic requirement inference from Application; use typed native output semantics validated against authoritative observations.
4. Consolidate factual sanitation/projection only into EXISTING proper Evidence/security boundary, with minimal diff. If no equivalent, reuse explicit typed contract rather than copying 1000 lines of helpers; hold architectural decision for genuinely absent owner.
5. Rewrite `orchestration.py`, `conversational_response.py`, `handle_interactive_turn.py` and all other consumers; remove imports, class aliases and functions. Do not leave `from ...outcome_assessment import` anywhere.
6. Delete `outcome_assessment.py` physically. Remove obsolete tests or replace with equivalent native behavior contract tests; no dropped security/Outcome assertions.
7. Explicitly verify doc244 dependency (pagination) and doc243 (runtime JSON) sequencing; no hardcoded new agent budget limits. Do not reintroduce legacy or generic formatter engine.
8. RED/GREEN, full backend suite after final code diff, isolation (SDK only infrastructure), test evidence refs/multisource/false-grounded, live local E01–E10 on rebuilt SHA if available; no production deploy.

## 5. Acceptance criteria

AC01 file absent from `git ls-files` and imports/calls zero across repo; no renamed copy.
AC02 native Pydantic AI structured output actually executed, with Pydantic schema and output validator, no second LLM controller or bespoke Outcome planner.
AC03 no self-certification: owner evidence, AuthZ, Scope, SourceRef, redaction, control-plane filtering, temporal/count/pagination correctness and PREPARE/ACT remain independent.
AC04 PARTIAL/INSUFFICIENT for unproven obligations even if individual source is GROUNDED; E03 two product roots without verified compare != COMPLETE, E04 missing guide != COMPLETE, E10 unknown third != COMPLETE.
AC05 compare, multi-source, single source, result empty, owner-unavailable, error, clarification and cancellation reliable; TestModel plus real local E01–E10 validated where possible.
AC06 no brittle hardcoded owner/product/wording heuristics.
AC07 full regression, security, NDJSON, import graph after final diff, evaluated SHA == local runtime SHA for live E-runs. If not run -> TEST_NOT_RUN, no functional acceptance.
AC08 docs 239/243/244, ledger, next execution report and push main verified; no prod deploy.

**Mandatory report:** BASE_HEAD, IMPLEMENTATION_SHA, FINAL_SHA, ORIGIN_MAIN, PUSH_VERIFIED, OWNER_CONTRACTS, EXISTING_EQUIVALENT, REUSE_DECISION, SOURCE_FILE_DELETED, CONSUMERS_FIXED, LOC_BEFORE_AFTER, PYDANTIC_VERSION, OUTPUT_TYPE_SCHEMA, OUTPUT_VALIDATOR_BOUNDARY, EVIDENCE_PROTECTION, SECURITY_TESTS, OUTCOME_TESTS, FULL_SUITE, E01_E10, FALSE_GROUNDED, EVALUATED_SHA, LOCAL_RUNTIME_SHA, RESIDUAL_SEARCH, DOCS_LEDGER, EXECUTION_DRIFT, VERDICT, PRODUCTION_DEPLOY=NOT_AUTHORIZED.

**This is a documented implementation task. NO source code was changed or tested by this documentation-only commit.**
