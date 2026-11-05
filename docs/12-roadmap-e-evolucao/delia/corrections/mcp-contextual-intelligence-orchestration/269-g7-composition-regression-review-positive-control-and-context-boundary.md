# 269 — DÉLIA · Review da proteção de composição e próximo gate de outcome/contexto

**DATA:** 2026-11-05  
**TASK_ID REVIEWED:** `DELIA-C3-G7-COMPOSITION-SURFACE-AND-LIVE-OUTCOME-REWORK-01`  
**REVIEWED_HEAD:** `4315244c8354eeb12b9f9d4a083c08876a5bdc1c`  
**BASE:** `a1f9c5587fae0b5f49b626f8d3115742b6881cd1`  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` for composition regression guard; whole G7 live owner business outcome `INCONCLUSIVE`.  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED.

## GitHub findings

- Single commit adds 126-line `delia-api/tests/test_composition_surface_regression.py`, updates doc256. No production code changed in this commit.
- Test 1 invokes real composition `root_composer._compose_turn_handler` with specialist enabled, FakeInterop and valid shipped instructions; asserts `handler._capability_orchestration is not None`. This is a genuine behavioral guard against the prior loader-deletion bug, though it does not discover/invoke a live MCP provider.
- Test 2 monkeypatches `root_composer.load_orchestration_instructions` to raise, composes the handler, asserts handler exists and its capability orchestration is None. **The test does not assert the warning log**, despite its docstring/report calling the configuration failure “observável.” Add `caplog` assertion for `delia_orchestration_instructions decision=fail_closed reason=resource_invalid` and confirm the existing logger is appropriately configured; no new logging framework.
- Test 3 opens the shipped JSON instructions resource and validates `ORCHESTRATION_INSTRUCTION_KEYS` subset. Proves required-key coverage at current test checkout; consider stable absolute app config path when existing fixtures already provide it; do not redesign.
- The code contains unused imports and auxiliary test classes, which are minor test hygiene only; no mass cleanup needed.
- Executor reports 3/3 and complete backend suite PASS; independent reviewer inspected GitHub source and diff, not tests run.
- `DELIA_RUNTIME_SHA` remains reported stale; runtime identity cannot be proven solely by baked environment string. No new runtime verification evidence in this task.
- Post-fix original E01–E10 remain 0/10 business grounded in reported live run. The owner data availability and one model context overflow are not resolved by these three tests.

## Next bounded implementation and verification task

**TASK_ID:** `DELIA-C3-G7-POSITIVE-OWNER-OUTCOME-AND-AGENT-CONTEXT-BOUNDARY-01`

1. Reanchor HEAD/status/origin and mandatory authority order + doc256, reviews268/269, ledger. Preserve other work. No production deploy.
2. First close only the small test gap: assert the existing warning with caplog when required instruction load fails, while retaining fail-closed and configured behaviors.
3. **Positive control with real owner:** select from authorized Domain API/MCP one READ-only business record whose existence is verified by the owner independent of the model; document redacted identity, expected fields/projection, exact owner contract. Ask corresponding natural-language question to real DÉLIA on authenticated dev stack. Compare authoritative record to returned answer, SourceRefs, grounding, logs and outcome. Do not invent fixture data or treat discovery/HTTP200/SourceRef alone as outcome. If absent permissions/data, mark `INCONCLUSIVE` with precise unblock.
4. **Agent context limit:** reproduce `4211 tokens > 4096 ctx` using effective runtime configuration, actual Ollama context window, specific investigation Agent prompt/mandatory instructions/tools/prior turns and token accounting; distinguish model/provider measured input from heuristic estimator. Determine whether existing `InvokeModel/context_budget` policy actually governs native investigation `Agent`. Prefer extending current legitimate budget boundary only where parity and owners proven; no second token engine or provider branches in planner. Tests for below/at/above context threshold, required instruction preservation, truncation/fail-closed and deadline.
5. Repeat affected E-cases and ultimately E01–E10 with per-case oracle, identity of mounted code/config/model, owner result, ToolCalls, grounding, claims matched to evidence, tokens measured/estimated, duration. Distinguish healthy honest NON_GROUNDED from successful business answers and actual owner contract failure.
6. Full backend+security+architecture regression, residual search, doc256/ledger updates only on factual outcomes, commit/push. No ACT/write. No production deploy.

**Acceptance gate:** at least one demonstrated read-only business question against **known existing owner data** with authoritative answer in DÉLIA plus precise context boundary outcome. If no known data, do not claim full functional acceptance. RQ24 and RQ28 remain PARTIAL pending independent review. `E01–E10` historical run is not `TEST_NOT_RUN` anymore, but 0 grounded means the benchmark's business outcomes remain unproven.
