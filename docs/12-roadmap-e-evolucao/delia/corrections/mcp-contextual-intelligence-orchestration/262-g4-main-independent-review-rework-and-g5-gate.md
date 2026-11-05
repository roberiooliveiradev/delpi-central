# 262 — DÉLIA: G4 main independent review, targeted rework and G5 gate

**DATE:** 2026-11-05  
**TASK_ID:** `DELIA-C3-G4-RETRY-CONTEXT-CONFIG-OBSERVABILITY-IMPLEMENTATION-01`  
**REVIEWED_HEAD:** `3d7c1cd5f509abf97d3f9a9bdc1929f94f349d5a`  
**BASE_HEAD:** `abcdcc63f66b0c39779e00cdace9ab2679610a50`  
**REVIEW_VERDICT:** `REWORK` for bounded M3 cleanup/telemetry proof, `INCONCLUSIVE` for M1 physical retry-count claim, `ACCEPT_WITH_RESIDUAL` for keep decisions on legitimate context budget/ports. **G4 overall not yet accepted.**  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED; **E01–E10:** TEST_NOT_RUN.

## Actual GitHub diff and verified code

One DÉLIA commit, only five changed paths: `app/composition/root_composer.py` (-1), `app/infrastructure/orchestration/pydantic_ai_investigation.py` (-15), `tests/test_g1_native_structured_output.py` (+41), doc256 (+23), execution ledger (+12). No source modifications to `context_budget.py`, `governed_retries.py`, `pydantic_ai_runtime_config.py`, `turn_observability.py`, or JSON config in this task. This may be correct KEEP, not falsely counted as code cleanup.

**Concrete residual:** In `pydantic_ai_investigation.py` the diff removed `self.last_agent_usage: Mapping[str,Any]|None=None` and the `if usage is not None` branch that collected input/output/request tokens. It **did not remove** the corresponding `else: self.last_agent_usage={duration_ms,tool_calls}`; this `else` now syntactically attaches to the enclosing `try/except` and executes on a successful `agent.run_sync`. Python permits dynamic attribute assignment, so absence of the initializer does not make the attribute absent. It invalidates the reported `zero refs to last_agent_usage` and `removed` assertions. It may also prevent access to prior measured metrics through this field. Actual telemetry consumers MUST be checked before deleting or restoring the field; lack of direct consumers should not be assumed from a report.

**M1 separation (partially PROVEN):** `governed_retries.call_retry_eligible` is called in `handle_interactive_turn.py` and `capability_provision/orchestration.py`; `pydantic_ai_investigation.py` has `Agent(... retries=...)`, `UsageLimits`, and one syntactic `run_sync` callsite. This is evidence of separate paths and no obvious direct wrapper loop in Agent module, **not physical provider request measurement**. The new tests test source text `src.count('.run_sync(')==1` and that `call_retry_eligible` string is absent, plus policy return values. They do not execute a real or fake instrumented Agent and count model requests across native ModelRetry/internal retries. The report's “FÍSICO” assertion remains INCONCLUSIVE.

**M2:** `InvokeModel` has a pre-call `apply_context_budget`, distinct from SDK usage measurement; KEEP justified unless overlap proven. Actual usage mapping to `ModelCallObservation` requires an end-to-end or instrumented test proving input/output measured vs estimation, including investigation Agent path. Do not attribute removed `last_agent_usage` to completion of usage reconciliation.

**M3:** `_recovery_reuse_enabled` constructor arg+state removed and composition caller changed (appropriate dead code removal). `last_agent_usage` removal **incomplete**. `last_node_trace` remains and may be live. JSON config and C3-T4 invocation port remain legitimate.

## Required targeted G4 closure (not a new inventory)

**TASK_ID:** `DELIA-C3-G4-TELEMETRY-RETRY-EVIDENCE-AND-DEAD-STATE-REWORK-01`

1. Reanchor HEAD/status/origin and canonical authority order (Project Instructions/.cursor, 16→50→17→49→51→52→21→20→25, technical/product/thematic specs, ledger, doc256/261/262). Preserve concurrent changes and no deploy.
2. Fix the orphan `else: self.last_agent_usage` block. Determine authoritative consumers/usage path first. If truly unused, remove the entire dynamic field consistently and prove SDK-measured tokens are reported through an alternative existing legitimate ledger; if not, retain the complete field/typed initialization and accurate mapping. **No fake usage**, no second collector. Add negative test that targets the runtime behavior, not only token-string search.
3. Add behavior-based retry tests instrumenting actual path with a fake provider/Agent: number of physical model requests and tool invocations under success, one recoverable timeout, invalid structured output/ModelRetry, UsageLimitExceeded, cancellation, and total deadline. Distinguish `Agent.run_sync` invocations from internal provider requests; do not assert equality. Verify no retries of material writes and no attempt proliferation.
4. Prove estimated context budget vs actual SDK tokens are distinguished in the interactive observable output; verify protected model id, secret/COT/prompt exclusion, true latency and no telemetry loss. If no valid consumer reports Agent tokens, mark telemetry `PENDING` and restore canonical observable path minimally.
5. Execute focused RED→GREEN, full backend suite, architecture/security checks; real local model spot check as authorized, else `TEST_NOT_RUN`. Report exact SHA/config/model, tests, physical request counts, code LOC/removed symbols and source refs/outcomes, residual search. Correct RQ-11–15 in agreement with **doc256 stage definitions**, not invented mapping. Complete G4 or report residual factual blocker and continue independent authorized work.

## G5 preparation (not authorization to delete C3-T5)

After targeted G4 closeout, G5 addresses active MCP specialist boundary, snapshot Application→Infrastructure import violation, and C3-T5 OpenAPI foundation. Must read docs 16 C3-T5, 21 C3-T4, 248, 255, 256, 216 snapshot spec and ledger. KEEP active MCP/Keycloak and owner authorization; `MCP result != FACT`, discovery != approval. Direct DELPI OpenAPI adapters may be retired only if approved C3-T5 contract preserved or superior decision given. Snapshot experiment retirement requires frozen-decision evidence; otherwise `ARCHITECTURE_DECISION_REQUIRED`. No speculative ports or SDK swaps bypassing gates.

**NO RUNTIME CODE EDIT** in this review. Report statuses source-observed vs executor-reported tests; no automated production deploy.
