# 275 — DÉLIA · Review ToolReturn match por ID, limitations tipadas e Agent in-run

**DATA:** 2026-11-05  
**TASK_ID REVIEWED:** `DELIA-C3-G7-NATIVE-HISTORY-ORPHAN-RESULT-AND-INRUN-OVERFLOW-REWORK-01`  
**REVIEWED_HEAD:** `65a9d787635c5c402d9c34935ef4798cfd2c87b6`  
**BASE_HEAD:** `a7af2161313945d212278a346fe07db7c405581d`  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` for guarding clear orphan/mismatch cases and helper overflow; `REWORK` for claim of complete tool-call-ID integrity and in-Agent overflow proof; positive owner outcome `INCONCLUSIVE`. **PRODUCTION_DEPLOY=NOT_AUTHORIZED**.

## GitHub evidence

- One DÉLIA commit changes `delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py` (+69/-19), `delia-api/tests/test_g1_native_structured_output.py` (+156/-10) and doc256 (+18). Origin/main was verified as `65a9d787...` on review.
- `_history_units` now inspects `ToolCallPart` and `ToolReturnPart` and raises `_InvestigationHistoryIntegrityError` on clear missing/mismatched calls. Prior orphan test inverted to expect failure. Positive multi-call/multi-return test exists.
- **ID correctness bug:** `r.tool_call_id in ids or r.tool_name in names` accepts a return with explicit mismatched ID when tool name matches (e.g. call name=search, id=A; return name=search, id=B). The negative test uses *both a different name and ID*, so it does not detect this bug. Also potential duplicate returns are not rejected by set-membership matching, and cardinality/ID pairing of two calls with same name is not validated.
- **Typed limitation shape bug:** the return branch constructs `limitations=(("investigation_history_invalid:" + str(exc)[:200]) if integrity else ("investigation_context_overflow:in-run",))`. On integrity branch this evaluates to **str**, not **tuple[str,...]**. Must use tuple for both branches, test consumer interpretation; preserve no secret/raw tool payload in limitations.
- **In-run integration unproven:** test `test_in_run_mandatory_suffix_overflow_raises_typed` calls module function `_select_surviving_messages` directly with large ToolReturn content. This proves helper raises, not that actual `PydanticAiInvestigationOrchestrator.attempt` using `ProcessHistory` calls it after a real tool event and returns typed `GovernedCapabilityAttempt` while avoiding next physical model call. Need focused Agent/FunctionModel integration test with initial pre-call gate passing, bounded tool result/cumulative multi-step growth, and counting actual model requests.
- Existing legacy `_prior_context_block`/`prior_turn_max_chars` remain retired; `context_budget.py` has legitimate non-Agent users. No new legacy engine introduced.
- Executor reports focused 37/37 and full backend suite PASS; **not independently run in this review**. Owner-read positive control still `INCONCLUSIVE`, RQ24/RQ28 PARTIAL. Do not treat native tests/HTTP200 as business outcome.

## Next bounded implementation

**TASK_ID:** `DELIA-C3-G7-NATIVE-TOOL-PAIR-ID-AND-INRUN-AGENT-CLOSURE-01`.

1. Reanchor HEAD/status, .cursor/Project Instructions → 16→50→17→49→51→52→21→20→25 → architecture/spec/ledger and docs256/272–275. Decide `EXISTING_EQUIVALENT`/`REUSE_DECISION` using Pydantic AI 2.50.0 message contracts before changing code.
2. RED tests: same tool_name but *different explicit tool_call_id* rejected; two identical-name calls with distinct IDs return correctly; duplicate return for same ID rejected; unmatched/missing/partial return handled according to actual SDK contract; legitimate ID-less match only when SDK supports it, no fabricated results. Prefer native framework rules rather than a parallel message validator.
3. Fix `_history_units` match logic with minimal change, preserve whole causal units and current user question. Inspect SDK return/call ID semantics before deciding exact fallback behavior.
4. Fix `limitations` to be consistently tuple-shaped for both integrity and context failures. RED->GREEN checks that downstream consumer sees correct typed errors.
5. **Integration RED->GREEN:** Agent+ProcessHistory+FunctionModel (or equivalent native SDK harness) first physical request succeeds and invokes a governed fake READ/tool; second step receives bounded evidence that causes cumulative mandatory suffix overflow; assert no second physical model request and typed `investigation_context_overflow`. Separately verify actual orphan/mismatch through native processor route typed `investigation_history_invalid` if SDK allows injecting such a malformed history without other validation stopping earlier.
6. After GREEN, remove any newly obsolete code/imports/tests/configs in same delivery. Do not restore retired prior-context char path or duplicate local token engine. Retain context_budget for legitimate InvokeModel consumers. Full backend/architecture/security/privacy suite, residual search and ledger/doc update; no production deploy.
7. Positive business control: only when existing authorized record independently verified at owner; otherwise `INCONCLUSIVE`. No live write/ACT.
8. Report exact SHA, native runtime/model/config, tests actually executed, `LEGACY_REMOVED/RETAINED`, `RESIDUAL_SEARCH`, RQ24/RQ28, blockers and evidence.

**Review decision:** The current patch corrects obvious orphan results but is not sufficient to certify pair-ID integrity or full in-run Agent outcome gating.
