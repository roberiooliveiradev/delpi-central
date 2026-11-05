# 272 — DÉLIA · Review independente ProcessHistory nativo: integridade de pares e aposentadoria do legado

**DATA:** 2026-11-05  
**TASK:** `DELIA-C3-G7-PYDANTIC-AI-NATIVE-CONTEXT-HISTORY-AND-OWNER-POSITIVE-EVIDENCE-01`  
**BASE:** `7c8440a4e711f0cf3e943eab24b181b0746bc85e`  
**REVIEWED SHA:** `d3938116add28791fcf4e2977d87705e9316436f`  
**VERDICT:** **REWORK** for native history processor and no-legacy-retirement obligation; Pydantic AI 2.50.0 `ProcessHistory` usage is legitimate, but current trimming is unsafe for evidence continuity. **POSITIVE_CONTROL=INCONCLUSIVE; PRODUCTION_DEPLOY=NOT_AUTHORIZED**.

## Direct GitHub evidence

- The DÉLIA commit adds 29 lines to `infrastructure/orchestration/pydantic_ai_investigation.py`, adds `capabilities=[ProcessHistory(processor=_trim_overflow)]`, modifies three existing test/config expectation files and appends doc256. No dedicated history/compaction test was added.
- Processor computes `sum(estimate_text_tokens(str(m)) for m in messages)` and, while over `window - window//5`, `trimmed.pop(1)` if `len(trimmed)>2`. It sees native Pydantic AI messages, but **estimates their Python repr** rather than actual model serialization/provider usage. The policy is heuristic, not measured native token usage.
- Single-message deletion **can separate ToolCallPart and ToolReturnPart**, or remove a tool response while retaining the call. Pydantic AI documentation warns that provider-valid history repair can omit orphan returns or insert synthetic interrupted returns; these are different business evidence and cannot be treated as original owner outcomes. Must retain meaningful call/return pairs and current investigation frontier. Source: https://pydantic.dev/docs/ai/core-concepts/message-history/.
- Loop can stop with 2 messages still over window; there is no explicit typed failure if compulsory context remains larger than the budget. Existing pre-call estimate is separate and only covers initial request.
- Pydantic AI docs state `ProcessHistory` runs before each model request and replaces the effective history. Use native `message_history`, `RunContext.context_window_used` when meaningful, and complete-turn grouping; do not add another history manager. Source: https://pydantic.dev/docs/ai/capabilities/process-history/ and message-history link above.
- The code still uses `_prior_context_block` serialization of `ConversationContextTurn` into the prompt and prior turn char limits; no migration to `run_sync(message_history=...)`. This must be an explicit active residual, not claim a finished migration. Existing `context_budget.py` may still have legitimate non-Agent `InvokeModel` consumers; do not delete it globally without bounded consumer proof.
- Executor reports full backend PASS and Pydantic AI version 2.50.0; reviewer inspected source/diff and current official framework docs, **did not independently run suite**. The positive owner record was not preconfirmed; `INCONCLUSIVE`.

## Required bounded rework and legacy removal in same delivery

**TASK_ID:** `DELIA-C3-G7-PYDANTIC-AI-HISTORY-PAIR-INTEGRITY-AND-LEGACY-RETIREMENT-01`.

1. Reanchor current HEAD/status, .cursor, authority 16→50→17→49→51→52→21→20→25, technical/product specs, ledger, docs 256/268–272. Identify active Agent consumers, `InvokeModel` non-Agent consumers and frozen contracts. `EXISTING_EQUIVALENT`/`REUSE_DECISION` per responsibility.
2. RED tests in actual `PydanticAiInvestigationOrchestrator` using `FunctionModel`: multi-step tool call + verified ToolReturnPart and SourceRefs; low context trigger; ensure message pairs, the actual owner-derived evidence, immutable metadata, latest user turn and mandatory instructions survive; no invented interrupted tool outcome; don't use mocks as owner acceptance. Test a mandatory context that cannot fit, requiring typed fail-closed and zero additional model calls. Test normal multi-turn continuation, session isolation.
3. Implement proper native history processor using Pydantic AI's documented complete-turn boundaries and context-aware usage/window metrics where available. Avoid `str(ModelMessage)` as claim of exact tokens; where predictive estimate is necessary label ESTIMATED and validate against provider model at 4096. Tool projections and repeated calls remain governed; no local new token manager.
4. Convert supported previous ConversationContextTurn exchanges to native `message_history` using the legitimate existing session contract. Reject/skip unsupported synthetic or mismatched histories explicitly, rather than silently altering authorized/verified evidence. If legitimate schema blocker exists, leave clearly documented minimal bounded bridge, but do not leave both fully active pathways or call that migration completed.
5. **Remove legacy after GREEN in same diff**: retire `_prior_context_block` and its obsolete char-only limits/wiring/fixtures/config where truly no longer consumed; remove redundant pre-call envelope proxies, `InvestigationAnswer.__dict__`, catalog serialization approximations and stale comments/branches once native mechanism covers them. Retain `context_budget.py` for proven `InvokeModel` consumers. Update imports, callsites, snapshots, tests and docs. Report `LEGACY_IDENTIFIED|LEGACY_REMOVED|LEGACY_RETAINED_WITH_JUSTIFICATION|CONSUMERS_MIGRATED|DEAD_IMPORTS_REMOVED|CONFIG_TOGGLES_REMOVED|TESTS_REPLACED|RESIDUAL_SEARCH`.
6. Full backend/security/architecture regressions and a real local model reproduction at effective configured window when authorized; capture exact code SHA/config/model, provider usage measured vs estimates. Do not claim native processor can ensure all tool-call windows fit if that remains untested.
7. Separately obtain one independently known existing READ-only owner record, then ask DÉLIA and compare actual response/SourceRefs; if missing data/access, positive outcome remains INCONCLUSIVE. No synthetic owner proof or ACT.
8. Commit/push docs/ledger after factual results; preserve unrelated work. No production deploy. Final acceptance requires pair integrity and no silent survival of retired code; RQ24/RQ28 partial pending positive real owner outcome.

**REVIEW:** The new native boundary is a useful first step, but the code is not safe to certify for preserving causal evidence in a multi-step investigation and has not completed retirement of legacy history.
