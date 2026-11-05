# 274 — DÉLIA · Review independente: turno atual corrigido; ToolReturn órfão e integração do processor pendentes

**DATA:** 2026-11-05  
**TASK_ID:** `DELIA-C3-G7-NATIVE-HISTORY-CURRENT-TURN-AND-TOOL-PAIR-SAFETY-REWORK-01`  
**REVIEWED_SHA:** `b7ebe235ee82fb23820e5234cf7c9e6f7403b5cf`  
**BASE_SHA:** `d0cfca3eae0f7fd5c6fd2b4a2999cbfbf8556bb3` (contains prior concurrent work; GitHub commit b7ebe is only DÉLIA code change).  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` for fixing old-anchor/current-turn deletion; **`REWORK` for claiming complete ToolCall/ToolReturn causal integrity**; live owner positive outcome `INCONCLUSIVE`; `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## Direct source evidence

- Commit b7ebe adds module helper `_select_surviving_messages(messages,window)` and replaces the inline `ProcessHistory` trimming loop with a call to it. It locates the last unit whose first `ModelRequest` contains `UserPromptPart`, preserves the suffix from that unit, and drops units preceding it oldest-first; overflow in mandatory suffix throws `_InvestigationContextOverflow`. This correctly addresses the previously found old-anchor deletion scenario for valid grouping.
- Test `test_current_turn_survives_compaction_prior_turn_dropped` calls the production helper with old prior, current user, tool call, tool result and interim response, checks old text removed, current text/evidence retained and adjacent call/return preserved. Good bounded behavioral evidence for this case. `test_prior_and_current_arrive_natively_under_window` uses actual `PydanticAiInvestigationOrchestrator`/`FunctionModel` but **under** window, without exercising native processor compaction during an actual multi-tool run.
- **Critical integrity gap:** current `_history_units` (carried from earlier SHA) appends **any** `ModelRequest` containing `ToolReturnPart` to the preceding unit, irrespective of whether the preceding response actually issued a matching `ToolCallPart`. The newly added `test_orphan_tool_return_groups_with_previous_unit` constructs a user prompt followed by a ToolReturn for `orphan_tool` with no ToolCall and **asserts it is attached to the user unit**. This is *not* evidence of valid causal pairing or that the history becomes provider-valid. It can preserve an orphan result into subsequent model requests. Never treat owner evidence as originating from a call that did not occur.
- `test_mandatory_overflow_returns_typed_outcome_no_model_calls` uses `context_window_tokens=10`: it exercises the **pre-call context gate**, rather than raising `_InvestigationContextOverflow` *within the native ProcessHistory processor* after tool result growth. The report’s claim of in-run mandatory overflow protection remains **INCONCLUSIVE**. Add a real Agent+FunctionModel test where pre-call passes, tool result inflates mandatory suffix, next processor call fails typed with no next physical model request.
- `_estimate_history_tokens` is heuristic and cannot independently prove actual provider window fit; retain ESTIMATED label. Question/current-turn preservation is implementation evidence, not independently verified with real provider 4096 on this SHA.
- Previously removed `_prior_context_block` and `prior_turn_max_chars` remain absent in inspected changed file/config from prior reviewed commit. `context_budget.py` legitimately remains for `InvokeModel`; no new legacy fallback added. No reason to restart a global cleanup.
- Executor reports focused 33/33 and full backend suite PASS; reviewer inspected GitHub source/diff only, did not run tests. Positive owner outcome remains INCONCLUSIVE.

## Required bounded follow-up

**TASK_ID:** `DELIA-C3-G7-NATIVE-HISTORY-ORPHAN-RESULT-AND-INRUN-OVERFLOW-REWORK-01`.

1. Reanchor actual git HEAD/status, Project Instructions/.cursor, authorities 16→50→17→49→51→52→21→20→25, technical/product/ledger, docs 256/272–274. Verify installed Pydantic AI 2.50.0 contracts and current session/tool boundaries. Record `EXISTING_EQUIVALENT`/`REUSE_DECISION`.
2. Create RED→GREEN tests for orphan `ToolReturnPart`: zero preceding call, mismatched name/ID, multiple calls/results in same request, interleaved text and tool parts. An orphan must fail closed or be rejected at the appropriate native boundary; **never attach to an unrelated user prompt, synthesize a business result, or silently relabel it valid**. Preserve actual matching pairs and SourceRef provenance; use Pydantic AI native message validity rules when possible, no second history framework.
3. Integrate `ProcessHistory` into actual Agent/FunctionModel multi-step scenarios with forced compaction (previous conversations + current question + tool call+return), assert **effective messages received by provider** contain current request and causally matched tool results. Explicit in-run growth test: initial pre-call fits, returned tool evidence exceeds remaining mandatory window, processor must return typed `investigation_context_overflow` before next model request (count requests physically). Do not present pre-call rejection as proof of in-run behavior.
4. Shrink/retire obsolete branches/tests/configs in the same delivery once replacement passes. Keep native `message_history`; do not restore `_prior_context_block`, char-only limits, redundant estimator or direct legacy transports. Preserve `context_budget.py` for legitimate non-Agent consumers.
5. Full backend, security/architecture, Pydantic native history and privacy regression; inspect actual 4096 model where authorized, with measured-vs-estimated counts; no live ACT. Positive owner control requires previously known owner record; otherwise keep INCONCLUSIVE.
6. Update docs256, ledger, review trail only after factual results. Commit/push preserving others' work. Report legacy removal, in-run behavior, RQ24/28 status and explicit no production deploy.

**OVERALL:** Current-turn loss regression fixed for tested input. Complete history/tool-result safety and live positive outcome **not yet accepted**.
