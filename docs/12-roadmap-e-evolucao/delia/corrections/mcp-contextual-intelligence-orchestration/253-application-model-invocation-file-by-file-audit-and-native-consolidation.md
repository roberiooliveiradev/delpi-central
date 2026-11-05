# 253 — DÉLIA · Auditoria integral de application/model_invocation

**TASK_ID:** DELIA-C3-APPLICATION-MODEL-INVOCATION-FILE-BY-FILE-NATIVE-CLEANUP-01  
**DATE:** 2026-11-05  
**HEAD AUDITED:** `1b7c866e13d5f08fe0bedf822d82dd472b4bd7b0`  
**SCOPE:** `delia-api/app/application/model_invocation/`; **6/6 arquivos lidos integralmente**, consumidores selecionados inspecionados  
**STATUS:** AUDIT/PLANNED; SOURCE CODE UNCHANGED; TEST_NOT_RUN; PRODUCTION_DEPLOY=NOT_AUTHORIZED  
**RELATED:** docs 239–252, especialmente 243/245/246/249/250/252, autoridades e ledger.

## 1. Diagnóstico principal

Esta pasta **não implementa provider SDK** nem outro agent runtime: contém a fronteira Application `InvokeModel`, DTOs independentes do SDK, limites de contexto, tratamento de erros e política de retry por chamada. Há consumidores **reais** tanto em `handle_interactive_turn.py` (interação geral) quanto em `capability_provision/orchestration.py` (propostas semânticas). `root_composer.py` conecta `InvokeModel(PydanticAiModelInvocationAdapter(...))`. Isso obriga preservar a fronteira até a migração comprovada dos consumidores para o Agent nativo com output tipado (doc245); não renomear arquivos ou mover lógica inalterada para declarar redução.

**EXISTING_EQUIVALENT:** YES para Agent/Pydantic AI native structured output, UsageLimits e retries por Agent, contratos model invocation existentes, SourceRef/Eval/InstructionLineage, `TurnDeadline`, `ModelInvocationPort`; TO_INVENTORY para equivalência exata do SDK com histórico, strict schema, app exposure guard e context budget.  
**REUSE_DECISION:** REUSE boundaries e modelos tipados existentes, SHRINK old stage-call logic only when reachability proven, NEVER NEW semantic engine. Deterministic security controls remain independent from model.

**Pre-implementation authority:** local git status/HEAD/origin → Project Instructions/.cursor → docs 16→50→17→49→51→52→21→20→25 → architecture / product / applicable spec → ledger → docs 239–253. Only GitHub HEAD/file reads were performed; full authorities/ledger, local status/tests and dynamic consumers were NOT verified in this audit. Contradiction = EXECUTION_DRIFT / ARCHITECTURE_DECISION_REQUIRED, not silent redesign.

## 2. Matriz completa dos 6 arquivos

| Arquivo | Linhas extraídas | Responsabilidades / funções | Consumidores comprovados | Decisão |
|---|---:|---|---|---|
| `__init__.py` | 26 | re-export `InvokeModel`, requests/results/errors, safe observability | package imports | KEEP/SHRINK after consumer inventory |
| `context_budget.py` | 189 | `estimate_text_tokens`, `apply_context_budget`, `_estimated_input_tokens`, `_drop_oldest_pair`; estimate structural char weights and prune prior pairs | `InvokeModel._enforce_context_budget`; `turn_observability.py` reads observation | **REVIEW/SHRINK**: conserve budget+honest estimate label; remove obsolete adapter-overhead assumptions when native Agent end-to-end |
| `contracts.py` | 148 | `ConversationContextTurn`, `EvalBindRequest`, `ModelInvocationRequest`, `ContextBudgetObservation`, `ProviderInvocationPayload`, `ModelInvocationResult` | PydanticAI adapter, test adapter, InvokeModel, Interaction Handler, Orchestration, observability | **KEEP**, reduce only unconsumed fields after migration |
| `errors.py` | 42 | `ModelInvocationError`, semantic failure codes and optional context budget | Invocation/Handler/Orchestration/infra adapter | **KEEP**; no meaningful savings |
| `governed_retries.py` | 52 | `LLM_CALL_MAX_ATTEMPTS=3`, `RECOVERABLE_CALL_ERROR_CODES`, `call_retry_eligible` | `orchestration.py` and `handle_interactive_turn.py`; infra JSON loader imports ceiling | **REVIEW/CONSOLIDATE** with Pydantic AI retry behavior, preserving logical-call budget and non-retry of material actions |
| `invoke_model.py` | 343 | `InvokeModel.execute`, exposure/structured/request validation, context budget, lineage/eval binding, safe observability | Root composer, Orchestration, Interaction Handler, tests | **PRIORITY SHRINK**; not deletable until real callers absorbed with safety parity |

**TOTAL: 800 lines extracted**, counting final newline line where present. Final `wc -l` from worktree required for formal baseline.

## 3. Detailed per-file observations

### 3.1 invoke_model.py — 343 lines

`InvokeModel.execute` performs request validation, explicit exposure policy (TEST_ONLY or approved OPENAI_COMPATIBLE), context reduction, untrusted metadata guard, port invoke, structured-output guard, epistemic classification (model cannot assert FACT), configuration lineage and optional eval identity. These are **application governance**, not all duplicative of Pydantic AI. The safety controls may be reused by native output boundary without maintaining a separate per-stage generation engine.

**Legacy/native overlaps to remove after consumers migrated:**
- `_validate_structured_output` checks only `Mapping`, sensitive/COT/tool fields and *key presence*, including special `applicable=false` early return. It does **not** validate types of stage-specific fields; native Pydantic schema should be typed and strict, with independent acceptance of source/Evidence. Do not leave two contradictory schema pathways.
- `ModelInvocationRequest.expected_fields` and `output_schema_id/version` drive stage-schema generation via `pydantic_ai_adapter._proposal_model` (`Any|None` + `extra=allow`). Replace by existing strongly typed native models per genuine stage where possible; preserve exactly legal abstention and no fake FACT.
- `_enforce_context_budget`: uses adapter's declared effective context window. If unknown, does not guess. Keep this safety/continuity contract in correct owner while replacing old adapter overhead assumptions.
- `_enforce_exposure_policy`: literal adapter-kind string matching is a separate admission gate. SDK cannot decide policy; preserve explicit exposure allowlist but remove redundant implementation if authorized composition + existing gate already establishes it.
- `configuration_identity` and `_bind_eval_identity`: legitimate provenance SHA/model/instruction/config lineage, not eval PASS; KEEP until equivalent real contract proven.
- `safe_observability`: accepts only metadata (never secret/content) and may overlap with `interaction/turn_observability.py`; compare consumers and collapse duplication only if verified.
- `model_result_authorizes_act` always false; could be replaced by existing domain rule if no consumers (TO_INVENTORY). Do not drop invariant that model output never authorizes ACT.

**Risk to verify:** `MAX_TIMEOUT_SECONDS=60.0` approved per logical model call; separate config JSON has `provider_call_timeout_seconds` within 1–300 and turn budget up to 900. Confirm effective min gate without accidentally allowing >60 or rejecting explicitly approved higher post-decision calls. No silent policy relaxation.

### 3.2 context_budget.py — 189 lines

`estimate_text_tokens` estimates by weighted chars (Latin, digits, dense codes, non-ASCII), safety margin 1.12; `ADAPTER_OVERHEAD_TOKENS=260`, generation reserve default 512. Historical local-model calibration 21 samples (doc151). `apply_context_budget` removes the oldest complete USER_INPUT/DELIA_RESULT pairs, preserves mandatory prompt/instructions/current turn, rejects oversized mandatory input. Estimates are **not token consumption**. 
- Native Pydantic AI may expose usage/cost and model token estimators but this DOES NOT establish pre-call reliable token count for local Ollama. Do not replace bounded pruning with fabricated token accuracy.
- `ADAPTER_OVERHEAD_TOKENS=260` explicitly assumes older structured-output directive; after doc249 removes manual directive, calibrate against actual native Agent prompt and schema usage or label uncertain. No hidden hardcoded token model in another module.
- If unknown model context window (`None`), enforcement is disabled by design, not proof that input fits. Preserve truthful unknown.
- Test basis `tests/test_context_budget.py` (~542 lines) covers pruning, measured-corpus bound, monotonic estimates and no dispatch if overflow. Do not delete test coverage casually.

**Decision:** KEEP/SHRINK unless equivalent native pre-call budget proven; revisit calibration and consumer scope after Agent consolidation.

### 3.3 governed_retries.py — 52 lines

`call_retry_eligible` chooses only TIMEOUT/PROVIDER_UNAVAILABLE/INVALID_STRUCTURED_OUTPUT, max 3 real calls, per logical invocation and within interaction budget; consumers are `orchestration.py` and `handle_interactive_turn.py`. `pydantic_ai_runtime_config.py` imports `LLM_CALL_MAX_ATTEMPTS` ceiling, causing Infrastructure config to depend on implementation policy. 
- Native `Agent(retries=...)` controls validation/retry, but is NOT necessarily the same semantics as transport retry for provider availability/timeouts. Prove class-by-class parity and avoid multiplying native retries by outer retry loops.
- Never retry MCP/Domain material writes or broader turn because a model call failed. Preserve deadline/cancellation.
- If outer loop retired, replace with native mechanisms and a single governed max-call accounting contract; avoid double retry budget.

**Decision:** consolidate only after proof, otherwise KEEP.

### 3.4 contracts.py — 148 lines

Neutral DTOs: `ConversationContextTurn` (untrusted, entity refs only candidates), `EvalBindRequest` (identity, never PASS), `ModelInvocationRequest` (typed request + instruction/evidence refs), `ContextBudgetObservation` (estimated, not measured), `ProviderInvocationPayload` (infra result), `ModelInvocationResult` (lineage, usage, epistemic) with `is_fact=False`, `authorizes_act=False`. Preserving these boundaries matters even if Pydantic AI Agent produces typed output. 
**Decision:** KEEP; remove fields only if all consumers are gone and domain invariants preserved.

### 3.5 errors.py — 42 lines

`ModelInvocationError` with bounded semantic error codes, transport/SDK detail filtered by Infrastructure. **KEEP**.

### 3.6 __init__.py — 26 lines

Reexports stable package public API. **KEEP/SHRINK** if removed symbols are genuinely unconsumed. No SDK or behavior.

## 4. Confirmed consumer map

```text
root_composer
 └─ PydanticAiModelInvocationAdapter → InvokeModel (ModelInvocationPort)
      ├─ handle_interactive_turn._invoke [conversational/continuation]
      └─ capability_provision/orchestration._model_stage_proposal [legacy-shaped proposals]
          ├─ governed_retries.call_retry_eligible
          └─ context_budget.apply_context_budget
                ↳ ModelInvocationResult.context_budget → turn_observability
pydantic_ai_investigation (separate native Agent tool loop) → governed stage gates
```

This is real dual *Agent-invocation paths*, but it does not prove duplicate semantic authority: check callgraph, consumers and phase before deleting `InvokeModel`. `pydantic_ai_adapter` is PydanticAI-based, not old SDK runtime. Changing schema/validation must preserve fail-closed on malformed output, no fake FACT, forbidden COT/tool-call fields and secrets.

**Tests inspected:** `test_model_invocation_foundation.py` (~371 lines), `test_pydantic_ai_adapter.py` (~380), `test_context_budget.py` (~542), along with existing architecture/runtime tests. These are test sources, not PASS evidence.

## 5. Sequence for implementation

1. Reanchor, check doc245–252 actual execution state and source SHA, authoritative phase, status and frozen decisions.
2. AST + `rg` across repo for all public symbols, dynamic imports and stage-call use. Classify each caller `PROVEN ACTIVE | TEST_ONLY | OBSOLETE | TO_INVENTORY`. Determine whether native Agent output_type can absorb stage calls without losing typed contracts.
3. Write RED tests for missing/wrong field types, `applicable=false`, forbidden COT/secrets, attempted tool calls, source/evidence refs false grounded, lineage/eval identity, context pruning, actual/estimated token separation, timeout/cancel, retry budgets and effect-free failures.
4. Migrate semantic stage generation to native Pydantic AI structured output with typed models; preserve authority/evidence and domain validation. Remove obsolete `expected_fields` schema generation path/duplicated `_validate_structured_output` only after real caller migration.
5. Consolidate retries carefully: Pydantic native retries vs logical provider retry must be counted together and bounded; no nested multiplication.
6. Recalibrate context budget estimates and overhead against actual native prompt/schema or retain them explicitly as conservative heuristic, never call them measured tokens.
7. Remove unreachable code, adjust imports/tests and public exports; keep `ModelInvocationPort` if legitimate consumers remain; don't create another port/agent/controller.
8. Full backend, SDK TestModel and local real model E01–E10, negative security and task outcome on rebuilt SHA/config; ensure NDJSON/context usage and no false-grounded. If not run, TEST_NOT_RUN.
9. Residual search, LOC before/after by file/symbol, docs 243/245/246/249/250/252/253 and ledger/report update after factual result; commit/push main preserving WIP, no production deploy.

## 6. Status

**PROVEN:** all six files read from HEAD, direct consumers in handler, orchestration, root, adapter, tests; structural validation only checks presence and sensitive fields; heuristic context model exists; retry max3 and native Agent retry coexist as distinct possible layers.  
**TO_INVENTORY:** full dynamic callgraph, canon/ledger decisions, type schema parity with SDK, precise retry accounting, runtime calls, measured prompt overhead.  
**TEST_NOT_RUN:** no implementation and no local tests on this audit.

**REVIEW:** KEEP core DTOs/policy; prioritize `invoke_model.py`, `context_budget.py` and `governed_retries.py` as coordinated native-first shrink targets. Do NOT delete entire folder.
