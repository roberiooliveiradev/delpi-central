# 277 — DÉLIA · Review do teste multi-step nativo e timeout owner

**DATA:** 2026-11-05  
**REVIEWED_TASK:** `DELIA-C3-G7-NATIVE-CONTEXT-REAL-OWNER-OUTCOME-EVIDENCE-GATE-01`  
**BASE_SHA:** `098bafd3519fdef38f0c2a464c2041b0595c1eb2`  
**REVIEWED_SHA:** `e7de0db750af7de901849a59b56177a52d944aee`  
**REVIEW_VERDICT:** `ACCEPT_WITH_RESIDUAL` for two-request native Agent continuity; `INCONCLUSIVE` for tool-result/grounded answer and positive owner outcome; `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## Source inspection

- Commit `e7de0db...` adds only a 60-line test `test_governed_tool_invocation_real_and_request_counted` and doc256 update. Comparison from base includes an unrelated production-control CSS commit. No DÉLIA runtime source modification.
- FunctionModel first response creates `ToolCallPart("invoke_read_capability", ...)`, then next response is `_final_answer("done", status="insufficient")`; the test asserts `len(model_requests)==2` and `attempt.error_code in (None, investigation_agent_error, investigation_no_business_evidence, investigation_clarification_required)`.
- **Unproved assertion in description:** despite claiming “spy proves owner invocation” and tool output enters native history, the new test has **no spy, no governed invocation counter and no assertion about `ToolReturnPart` contents in second `messages`**. Another older test may prove distinct gates, but this one does not prove the end-to-end causal chain.
- Accepting `investigation_agent_error` lets a post-tool structural/parse error pass; accepting `None` without checking authoritative content or returned status cannot prove no hallucinations. Narrow test assertions only after characterizing expected fixed FunctionModel result. No need to rewrite Agent logic absent failing evidence.
- Executor reports full delia-api suite exit0, focused 41/41. Reviewer inspected exact GitHub diff; did not independently run pytest. Legacy `_prior_context_block` and `prior_turn_max_chars` not reintroduced in this commit, `context_budget.py` remains used by non-Agent InvokeModel.
- Reported owner probe `api-delpi /financial/rol*` with no token HTTP401 confirms anonymous request rejected; not a comprehensive Core/Domain AuthZ check. JWT-authenticated request timed out after 5 seconds; **a timeout does not prove record missing, forbidden or owner data absent**. No verified known-present owner record, no positive oracle; `POSITIVE_OWNER_OUTCOME=INCONCLUSIVE`. Do not over-generalize financial timeout to all DAVI/TÉO/VISTA owners.
- `RUNTIME_SHA` mounted SHA reported `e7de0db`, but baked `DELIA_RUNTIME_SHA` stale; identity drift still unresolved. No production deploy.

## Bounded follow-up: evidence closure, not another framework refactor

**TASK_ID:** `DELIA-C3-G7-TOOL-RESULT-PROVENANCE-ASSERTIONS-AND-OWNER-READ-DIAGNOSTIC-01`.

1. Reanchor real git HEAD/status, Project Instructions/.cursor and authorities 16→50→17→49→51→52→21→20→25, technical/product specs, ledger/docs 256, 272–277. `EXISTING_EQUIVALENT=YES` for native Agent/gates; `REUSE_DECISION=EXTEND` existing tests/diagnostics, no new engines or authorization proxies. Verify actual SHA/config/identity without relying on stale env metadata.
2. **Strengthen existing test only**: spy on `_governed_semantic_tool_invoke` or actual governing boundary for exact one call; assert second FunctionModel request contains expected `ToolCallPart` and matching `ToolReturnPart` with legitimate bounded content; assert exact expected fixed outcome and typed fields (not a broad error-code allowlist). Treat mocked fixtures as technical proof, not business outcome. Capture physical request count. If malformed expectation, RED and minimal fix; otherwise no production source churn.
3. Diagnose owner read path independently via existing owner contracts and authorized dev environment: choose low-cost known-present read from DAVI/TÉO/VISTA or Domain API, if possible; independently confirm owner data exists *before* questioning DÉLIA. For `/financial/rol*` timeout, inspect route's real timeout/dependency and owner logs/latency (no secrets), avoid assuming records absent or increasing arbitrary timeouts; owner issue stays with owner.
4. If known-present record exists, send matching READ-only DÉLIA question and compare owner answer ↔ tool return ↔ SourceRefs ↔ user answer; classify business outcome. If blocked, `INCONCLUSIVE` with exact owner-side evidence and next necessary action; no invented seeds, no ACT/write.
5. Full focused/backend/security/architecture regression as applicable; physical removal of any newly obsolete mechanism in same diff, consumers/config/docs updated; residual search. Do not reintroduce retired history/token paths. Commit/push/docs/ledger factually, RQ24/RQ28 stay PARTIAL without positive oracle, no production deploy.

**Review classification:** Technical context mechanics increasingly evidenced; business outcome not established. Do not create more scaffolding or refactor framework internals without a concrete defect.
