# 263 — DÉLIA: Review G4 rework + G5 interoperabilidade handoff

**DATE:** 2026-11-05  
**TASK_ID REVIEWED:** `DELIA-C3-G4-TELEMETRY-RETRY-EVIDENCE-AND-DEAD-STATE-REWORK-01`  
**REVIEWED_SHA:** `a51c0c322ff314add0b1323e5da673fa6bc2e441`  
**BASE_SHA:** `67db08c0b91469455f6d3ab895e406c0c04e8790`  
**VERDICT:** **ACCEPT_WITH_RESIDUAL** for bounded G4 rework (not total G4/G7 acceptance); Pydantic AI full investigation integration and token-usage coverage remain G7 checks.  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED; **E01–E10:** TEST_NOT_RUN.

## Verified GitHub evidence

- One commit, 3 changed paths: `infrastructure/orchestration/pydantic_ai_investigation.py` -9 lines, `tests/test_g1_native_structured_output.py` +81 lines, doc256 +16 lines. Zero `last_agent_usage` references or assignment in inspected investigation source; orphan `started` removed. No secondary collector added in this diff.
- Native investigation still calls `agent.run_sync` once syntactically and has `UsageLimits(request_limit,tool_calls_limit)`; separate non-Agent retries are governed by `call_retry_eligible` in interaction/orchestration. Presence of separate paths not permission to retry ACT.
- Three new tests use independent `Agent(FunctionModel(...),output_type=str)` constructed **inside the test functions**: normal one model request; native `ModelRetry` produces second; `UsageLimits(request_limit=1)` raises before second. This is **behavioral evidence for Pydantic AI's native retry/usage-limit semantics**, but does **not** run `PydanticAiInvestigationEngine.attempt` with its real `InvestigationDeps`, toolset, model_factory, owner gates, deadline, or structured `InvestigationAnswer`. Claim that physical retry multiplication is excluded for the complete DÉLIA callgraph remains **INCONCLUSIVE pending full path test/G7**. This is not a blocker for removing a truly unused field.
- `infrastructure/model_invocation/pydantic_ai_adapter.py::_map_usage` maps SDK-reported `input_tokens/request_tokens` and `output_tokens/response_tokens` to `UsageMetadata` for `InvokeModel`. The removed `last_agent_usage` field had no consumers according to executor search; independently, current investigation source no longer exports that field. **Agent investigation token telemetry is not thereby proven exposed to `turn_observability`; do not imply universal measured token coverage.** Model-specific runtime E01–E10 remains not run.
- No local tests run by this reviewer. Executor states 21/21 G1 tests and full backend suite exit 0; source of three new tests verified.

## Review decision and metrics

- **G4 bounded technical cleanup:** ACCEPT_WITH_RESIDUAL. Dynamic state removed coherently; no evidence of a new engine; correct KEEP of pre-call budget and independent C3-T4 `InvokeModel`.
- **M1:** native Pydantic AI retries proven only for isolated Agent fixtures; complete DÉLIA tool loop retry and deadline semantics **TO_VERIFY**.
- **M2:** correct per-InvokeModel measured usage mapping, but full investigation usage pipeline **TO_VERIFY**. No false assertion of zero new behavior errors.
- **M3:** dead `last_agent_usage` and `_recovery_reuse_enabled` removed. Effective JSON config retained.
- **RQ-11–RQ-15:** do not claim new IMPLEMENTED from these test-only/code-delete changes. Current executor statuses PARTIAL/PARTIAL/PARTIAL/NOT_IMPLEMENTED/NOT_IMPLEMENTED are a reporting snapshot; reconcile exact stage-specific RQ mapping from doc256 at independent G7 acceptance. Partial has 0 credit.
- **G5 can proceed** because remaining G4 caveats are G7 integration/observability checks, with fail-closed safety boundaries preserved. No phase advance or production deployment.

## G5 next executable task

**TASK_ID:** `DELIA-C3-G5-MCP-OPENAPI-SNAPSHOT-BOUNDARY-CLEANUP-01`.

1. Reanchor current git HEAD/status/origin, Project Instructions/.cursor, authorities 16→50→17→49→51→52→21→20→25, technical/product/thematic specs, ledger, docs 216/248/255/256/263. Treat frozen decisions as binding. `EXISTING_EQUIVALENT` and `REUSE_DECISION` recorded per slice. Preserve concurrent WIP.
2. **MCP live:** check `SpecialistInterop`, `SpecialistInteropPort`, existing MCP adapter/transport, Keycloak delegation and root composition. KEEP live discovery/invocation and revalidate tool/operation class and Core/domain security. Only shrink provably unused/doubled code; do not replace live MCP boundary with raw Pydantic AI tool execution bypassing gates. Discovery != approval; metadata != permission; provider result != FACT.
3. **Snapshot:** resolve source decision (doc216/ledger/authorities). `application/specialist_interop/snapshot_interop.py` directly imports `infrastructure/interoperability/mcp/catalog_store.py`, a layering violation. If experiment is explicitly retired, REMOVE full experiment atomically with root wiring/config/sync script and targeted tests while proving active MCP behavior unchanged. If still approved, STOP that deletion and request architecture decision on the legitimate boundary correction. No speculative port.
4. **OpenAPI C3-T5:** preserve canonical approved OpenAPI Action Catalog/Capability Projection (16/20/25); separate foundation/fixture/contract from unwired direct DELPI transport. Remove any truly dead direct adapter only if existing legitimate equivalent preserves approved C3-T5 or superior authority explicitly supersedes it. Else STOP affected slice with `ARCHITECTURE_DECISION_REQUIRED`, not silent deletion. No parallel authority.
5. RED→GREEN targeted tests: unknown MCP tool, live operation-class changes, invalid metadata, AuthZ denial, timeout, delegation scope, result not FACT, partial provenance, snapshot fail-closed (if kept), C3-T5 contract/fixture and real-owner safety negatives. No material ACT retry. Verify true owner business outcome not only HTTP200.
6. Full backend/architecture/security suite, residual search (dynamic consumers included), changed/deleted physical files and LOC, evidence SHA/model/config/owner outcomes. Local real-model spot tests if authorized, otherwise `TEST_NOT_RUN`; E01–E10 formally G7.
7. Commit/push bounded source diffs and fact-based docs/ledger. If no safe deletion is authorized in one branch, report KEEP/BLOCKED and continue independent approved branches. No production deploy.

**G7 carryover:** A real PydanticAiInvestigationEngine integration test should instrument provider requests, including its native toolset, owner gate and usage/latency through response observability; ensure read-only and no multiplying model/tool calls under ModelRetry or deadline. G5 must not mislabel that as tested.

**STATUS:** code review/doc only. No source mutation or test execution from reviewer.
