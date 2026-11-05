# 278 — DÉLIA · Review causal tool-result e próximo gate local Ollama/produção governada

**DATA:** 2026-11-05  
**REVIEWED TASK:** `DELIA-C3-G7-TOOL-RESULT-PROVENANCE-ASSERTIONS-AND-OWNER-READ-DIAGNOSTIC-01`  
**BASE_SHA:** `0352099e4bef79b60baf0cc652a7370f3d18cb00`  
**REVIEWED_SHA:** `69ce243978b7e19beeb48ae46c543a54e6c1cb6f`  
**REVIEW:** `ACCEPT_WITH_RESIDUAL` technical test hardening, `INCONCLUSIVE` real owner business outcome, `PRODUCTION_DEPLOY=NOT_YET_AUTHORIZED_BY_GATES`.

## GitHub evidence

- Commit `69ce2439...` modifies **only** `delia-api/tests/test_g1_native_structured_output.py` (+51/-22) and doc256 (+12); runtime code unchanged.
- Strengthened `test_governed_tool_invocation_real_and_request_counted` imports `_final_answer` rather than allowing NameError/agent_error; spies the actual `gates._governed_semantic_tool_invoke`, checks exactly one capability invocation, exactly two FunctionModel requests, matching explicit `tool_call_id` call and return in second request, non-empty return content, exact `status=SUCCESS` and `error_code=None`. This is meaningful deterministic multi-step causal-chain evidence.
- **Bounded claim limitation:** no assertion matches the ToolReturn content against exact spy-returned owner data or projection-limit length. Existing separate tests may address projection. Do not call this exact-test proof of text/size equivalence.
- Test uses a deterministic stub owner through real governance boundary, **not a live authority business oracle**. No runtime code changes, G7 native Agent correction accepted with evidence residuals. Executor reports focused 41/41, full suite exit 0, not independently run by reviewer.
- Financial `/financial/rol*` probe: unauthenticated HTTP401; JWT user request timed out after 5s. Could be dependency latency/timeout, not proof of absent data or broad owner failure. Positive control still `INCONCLUSIVE`, RQ24/RQ28 `PARTIAL`. Stale `DELIA_RUNTIME_SHA` metadata not reconciled by this test commit.
- No legacy reintroduction in this commit; prior removal `_prior_context_block`/`prior_turn_max_chars` preserved; `context_budget.py` legitimately retained for non-Agent `InvokeModel`.

## Coordinated next bounded task

**TASK_ID:** `DELIA-C3-G7-LOCAL-OLLAMA-MCP-REAL-EVAL-AND-PRODUCTION-RELEASE-GATE-01`

The user gave **conditional** direction to update the local container, validate LLM with real MCPs, tune effective context/config and consider production deployment only after tests and release gates. Treat this as conditional intent, **not blanket permission** to push an unverified production deployment.

1. Reanchor live git HEAD/status, Project Instructions/.cursor → canonical authorities 16→50→17→49→51→52→21→20→25 → specs/ledger/docs 256/272–278 and release/deploy runbooks. Confirm phase/CP/RQ, current production topology and authorization owner.
2. Update **local/dev** DÉLIA container using existing approved compose/scripts. Verify mounted-code SHA, package version Pydantic AI, effective model/provider profile, config fingerprint, live Core/AuthZ/MCP endpoints; distinguish stale baked `DELIA_RUNTIME_SHA` from actual process SHA, no claim of production parity without evidence. Rollback local if needed.
3. Run progressive authenticated **READ-only** questions against Ollama `qwen3:4b-instruct-2507-q4_K_M` and DAVI/TÉO/VISTA (or current authorized real MCP owners), with case oracle: simple catalog, identifier lookup, question requiring clarification, multi-step two tools, continuing conversation, no-data and explicit invalid capability. Instrument selected tool(s), actual invocation+ToolReturn, provenance, model calls, provider usage tokens vs estimated budget, 4096 window, latency, deadlines, and answer quality/honest uncertainty. Do not infer correct selection from HTTP200 or an inferred owner.
4. Settings tuning only with measured baseline and one bounded parameter change per comparison: context window (verify provider actual `num_ctx`), tool projection limit, prior-turns limit, output reserve/limits, requests/tool calls, retry/deadline. Compare outcome/quality/latency and memory demands. Do not simply increase 4096 or bake local_ollama into production.
5. Verify **known-present** record directly via authorized owner before using it as positive business oracle; prefer low-cost read. If none accessible, record exact owner/access unblock and `INCONCLUSIVE`. The owner financial timeout stays owner-side until evidence otherwise; do not patch DÉLIA to hide it.
6. Full backend regression, security architecture, production build, plugin/portal integration, AuthZ negative controls, read-only smoke and rollback/runbook validation. Apply same-delivery legacy removal for any proven replacement, including consumers/tests/config; no gratuitous refactor.
7. **Production gate:** authorize production deployment only if (a) exact SHA/config accepted by independent review, (b) release/rollback plan and actual deploy target confirmed, (c) tests and smoke passes, (d) security/permission and provider contract checks pass, (e) no unresolved blocker affecting safety or material behavior, (f) appropriate human deployment approval under project phase/authority. If real business positive oracle remains unavailable, record business acceptance INCONCLUSIVE, **do not silently interpret technical green as fulfilled gate**. If any mandatory gate fails, STOP prior to production, report `PRODUCTION_DEPLOY=BLOCKED` with causes, and offer bounded unblock. Do not modify prod data or perform ACT.
8. If authorized and all gates pass, deploy via approved sequential production scripts, verify runtime SHA, health/rollback, then run authenticated read-only production smoke with no secrets logged; rollback on postcondition failure. Report explicit separate `LOCAL_EVAL`, `BUSINESS_OUTCOME`, `PRODUCTION_RELEASE_GATE`, `PRODUCTION_DEPLOY`.
9. Publish factual evidence/docs/ledger after execution, commit/push; do not mark RQ24/RQ28 accepted without authoritative business outcome.

**STATUS:** documentation review only; no local/live tests independently executed by reviewer.
