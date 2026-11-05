# 273 — DÉLIA · Review independente da migração de histórico nativo: remoção de legado aceita, compactação REWORK

**DATA:** 2026-11-05  
**TASK_ID:** `DELIA-C3-G7-PYDANTIC-AI-HISTORY-PAIR-INTEGRITY-AND-LEGACY-RETIREMENT-01`  
**BASE_SHA:** `d0cfca3eae0f7fd5c6fd2b4a2999cbfbf8556bb3`  
**REVIEWED_SHA:** `fed2ec9c5f5b42e36213d75f9d58c8d70ad2f673`  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` for native message-history migration and confirmed physical legacy retirement; **`REWORK` for ProcessHistory compaction correctness**; `INCONCLUSIVE` for live business-owner positive outcome. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## Confirmed by GitHub

- The actual DÉLIA commit removes `_prior_context_block`, `_DEFAULT_PRIOR_TURN_MAX_CHARS`, `prior_turn_max_chars` parameter/wiring/typed JSON settings/profile, and updates source tests. Historical `context_budget.py` still has legitimate non-Agent `InvokeModel` consumers, so KEEP is correct. Diff from BASE to FINAL also includes concurrent non-DÉLIA commits; do not attribute unrelated changes to this task.
- `_prior_message_history` maps `ConversationContextTurn(kind=USER_INPUT)` into `ModelRequest(UserPromptPart)`, and `DELIA_RESULT` into `ModelResponse(TextPart)`. `run_sync(prompt=input_text, message_history=message_history or None)` uses native Pydantic AI.
- `_history_units` groups a `ModelRequest` containing any `ToolReturnPart` with the immediately preceding unit, without confirming matched tool call ID/name or the immediately previous message's `ToolCallPart`. It may append orphan returns to an unrelated unit and is not a general valid-history validator.
- `ProcessHistory` processor `_trim_overflow` keeps the **first** and **last** units and drops complete intermediate units `units.pop(1)`. **Critical case**: message_history may start with a previous user's question; the current user question is appended later by `run_sync` and can be an intermediate unit before new tool call/return. Under context pressure it may be deleted, even though first (old) prior turn and last (tool reply) remain. This violates current objective preservation.
- The test `test_history_processor_preserves_tool_call_return_pairs` calls `_history_units` and only checks `len(units)==4` and grouping of a ToolCall + ToolReturn. It does **not exercise `_trim_overflow` under pressure** nor the actual FunctionModel input after native ProcessHistory processing. The `message_history` test proves mapping, not safe compaction.
- `_estimate_history_tokens` uses text parts and truncated repr for non-content parts, so it is an ESTIMATE, not exact native token count. `_InvestigationContextOverflow` maps to typed GovernedCapabilityAttempt when raised. Retain fail-closed design, but guard against silent loss of current request, evidence and call/return integrity.
- Executor reports suite PASS; reviewer inspected GitHub source only, no independent pytest. No owner record confirmed and business positive control still INCONCLUSIVE. RQ24/RQ28 PARTIAL.

## Bounded rework (implementation task)

**TASK_ID:** `DELIA-C3-G7-NATIVE-HISTORY-CURRENT-TURN-AND-TOOL-PAIR-SAFETY-REWORK-01`.

1. Canonical reanchor HEAD/status → Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → technical/product/ledger → docs256/271/272/273; don't branch on memory. Determine exact installed Pydantic AI 2.50.0 message/protocol behavior and owners/consumers.
2. RED integration test with actual Agent/FunctionModel/`ProcessHistory`: native prior history (user+assistant), current request, multi-step tool call/return, forced overflow. Assert **current user prompt/intent and required investigation evidence remain in the effective model requests**; obsolete earlier conversation can be pruned in complete turns, paired call/return never orphaned and action gates preserved. Test 2+ tool calls, completion, malformed/orphan tool returns, and mandated context > window → typed fail-closed without further model requests.
3. Correct native compaction by identifying **actual current request boundary** rather than assuming `messages[0]` is current turn. Use existing native Pydantic AI message metadata, documented boundary behavior and pre-existing session contract; no parallel history engine. Preserve complete causal cycles and current request, not only first+last units. Preserve owner evidence provenance; do not synthesize tool results.
4. Test with 4096-window local provider when authorized: measured provider usage vs estimate, tool growth during multi-step investigations and correct final outcome when evidence exists. Mock/FunctionModel tests cannot stand in for real owner success.
5. **Legacy retirement in same delivery**: check `_prior_context_block`, `prior_turn_max_chars`, dead imports/configs/tests/snapshots/old envelope proxies, remove any newly obsolete helpers after safe native replacement; `context_budget.py` KEEP for live non-Agent consumers; no fallback. Record `LEGACY_IDENTIFIED`, `LEGACY_REMOVED`, `LEGACY_RETAINED_WITH_JUSTIFICATION`, `CONSUMERS_MIGRATED`, `RESIDUAL_SEARCH`.
6. Focused tests RED→GREEN + full backend, architecture, security, privacy, outcome/provenance; docs/ledger after facts, commit/push while preserving parallel work. No production deploy, no ACT, never claim positive owner outcome without independently known record.

**Overall:** Do not accept native compaction as safe solely on grouping test or green suite. Real user current turn and authoritative tool results must survive compaction or the system must fail closed with typed limitation.
