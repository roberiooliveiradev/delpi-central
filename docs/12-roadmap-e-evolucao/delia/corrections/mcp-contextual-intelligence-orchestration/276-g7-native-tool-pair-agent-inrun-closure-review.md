# 276 — DÉLIA · Review G7 tool-pair ID e in-run Agent

**DATA:** 2026-11-05  
**REVIEWED TASK:** `DELIA-C3-G7-NATIVE-TOOL-PAIR-ID-AND-INRUN-AGENT-CLOSURE-01`  
**REVIEWED SHA:** `d3bf57a14a0e0122a9328d410d2e11bb7da6b4d8`  
**BASE SHA:** `d9e49460f4ad6b96c7b0207f5bc3e0b22de4d42a`  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` for bounded technical remediation of tool-pair ID and typed in-run Agent overflow. `POSITIVE_OWNER_OUTCOME=INCONCLUSIVE`, RQ24/RQ28 remain PARTIAL. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## GitHub inspection

Single DÉLIA commit modifies orchestrator (+30/-14), tests (+134/-4), doc256 (+14); unrelated more recent Kaizometro HEAD may coexist. The review was on exact commit SHA, not on working tree/runtime. Executor reports full delia-api suite PASS, focused 40/40; reviewer did not execute pytest.

1. `_history_units`: explicit `tool_call_id` match required; mismatched explicit ID with same tool name no longer rescued by name. Duplicate explicit return IDs in a single return request rejected. For ID-less returns, unique matching tool name fallback. Tests verify same-name/different-ID rejection, duplicate and earlier valid multi-call scenario.
2. `GovernedCapabilityAttempt.limitations`: integrity branch is now tuple-shaped rather than string. The exception text is limited to generated typed message, not tool payload; do not include raw secrets in future message formats.
3. `test_agent_in_run_overflow_after_tool_result_no_second_call` uses actual Pydantic AI Agent/FunctionModel and ProcessHistory, with first model response containing a 40000-character `TextPart` plus `ToolCallPart`. The test asserts `len(calls)==1` and typed `investigation_context_overflow`. Thus it tests actual in-run ProcessHistory invocation rather than only helper. **Evidence nuance:** overflow is driven mainly by *synthetic large assistant text*, not a large owner tool return; test does not directly assert that the governed tool was called or that a large returned owner projection caused overflow. This is a residual coverage gap, not grounds to re-open the whole implementation.
4. The tests for explicit ID duplicates are within one return message; multi-message duplicate returns may need dedicated characterization if the actual SDK can produce them. Do not assume all native history variants have been proven.
5. Legacy `_prior_context_block`/`prior_turn_max_chars` remain removed; no new duplicate history engine in this commit. `context_budget.py` retained for legitimate `InvokeModel` consumers. Estimated context remains heuristic; no 4096-token provider success proven on this SHA.
6. Positive owner data from known-present authoritative record remains **INCONCLUSIVE**. Native test success does not prove business-grounded DÉLIA response. Do not declare E01–E10/RQ24/RQ28 fully accepted.

## Next bounded step

Do not repeat another indefinite micro-fix loop around the same helpers. Bundle remaining verification into one **evidence-focused gate**, and implement only upon demonstrated failure.

**TASK_ID:** `DELIA-C3-G7-NATIVE-CONTEXT-REAL-OWNER-OUTCOME-EVIDENCE-GATE-01`.

- Reanchor current HEAD/status, Project Instructions/.cursor, authorities 16→50→17→49→51→52→21→20→25, architecture/product/thematic spec, ledger/docs 256/273–276. Check actual Pydantic AI version and source-consumer inventory. Keep no production deployment.
- Verify native Agent context behavior with **bounded real tool outputs**, multiple model turns, explicit physical request counts, and 4096-window local model measurement if authorized. Assert actual governed tool invocation and its evidence retention, not just a synthetic fat model TextPart. Separate estimated token counts from observed provider tokens.
- Acquire **known-present** read-only business record directly from authorized owner (DAVI/TÉO/VISTA/Domain API) before asking corresponding DÉLIA question. Record canonical source, owner contract, redacted expected answer, result, SourceRefs and legitimate outcome. If unavailable, mark explicit `INCONCLUSIVE` and concrete unblock; do not invent seed data.
- If verifiable defect appears, do smallest patch with RED→GREEN, same-delivery physical legacy cleanup and consumer updates, full security/backend regressions; otherwise no code churn. Preserve native history, tool-pair ID, typed failures, authorized owner policy. Runtime code SHA/config/model must be independently recorded, reconcile stale baked `DELIA_RUNTIME_SHA` without claiming a production deploy.
- Reassess RQ24/RQ28 and business outcomes only on evidence, update docs and ledger, commit/push, report PASS/FAIL/INCONCLUSIVE appropriately.

**Acceptance boundary:** bounded technical fixes accepted with coverage residual, independent production/business acceptance still requires live, authoritative positive outcome.
