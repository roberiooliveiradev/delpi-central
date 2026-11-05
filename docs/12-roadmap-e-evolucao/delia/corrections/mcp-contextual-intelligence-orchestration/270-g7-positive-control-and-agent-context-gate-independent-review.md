# 270 — DÉLIA · Review G7 positive control + contexto do Agent

**DATA:** 2026-11-05  
**TASK_ID:** `DELIA-C3-G7-POSITIVE-OWNER-OUTCOME-AND-AGENT-CONTEXT-BOUNDARY-01`  
**BASE_SHA:** `d55b0c76f353a3f196cbd3cf90a9dbb7ad54aede`  
**REVIEWED_SHA:** `1f529a6593a439895cbb1ae7fed8eda7636df408`  
**REVIEW:** `ACCEPT_WITH_RESIDUAL` composition caplog; `REWORK` context-boundary sufficiency; `INCONCLUSIVE` live positive owner outcome.  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED.

## Evidence from GitHub

- Commit changes `root_composer.py` (+3), `pydantic_ai_investigation.py` (+34), JSON profile local_ollama `effective_context_window_tokens: null -> 4096`, `test_composition_surface_regression.py` (+12/-2), `test_g1_native_structured_output.py` (+80), doc256 (+24). Unrelated concurrent plugin-ui CSS change in compare is from another commit.
- `test_composition_missing_instructions_fails_closed_observably` now asserts warning via `caplog`, verifying the actual resource-invalid fail-closed log.
- `context_window_tokens` propagates from `settings.llm_context_tokens` through composition into `PydanticAiInvestigationOrchestrator`. The investigation Agent rejects before `run_sync` when `estimate_text_tokens(instructions)+estimate_text_tokens(prompt) >= window`, with typed `investigation_context_overflow`.
- This checks only the current text estimate: it does NOT account for known existing `context_budget.py` `ADAPTER_OVERHEAD_TOKENS=260` and `DEFAULT_GENERATION_RESERVE_TOKENS=512`, nor the Agent's tool schemas, native output schema/protocol framing, and generated tool responses during the run. The constants are calibrated for a different invocation adapter and **cannot be transplanted as exact native Agent overhead** without measurement/contract evidence. Need bounded native-Agent envelope with measured failure reproduction and safe headroom.
- The new tests use windows of `1`, `1_000_000` and `None`; they do not test edge cases near the effective 4096 window or reproduce original `4211 > 4096` against local provider. PASS for them proves wiring, not sufficiency.
- No bounded pruning of prior context is implemented in the new Agent gate, unlike the existing `apply_context_budget` path. Avoid assuming it is equivalent. Preserve mandatory instructions and user input; only permitted optional history/tool-result projections may be reduced, with truthful omission markers.
- Reported live query for `90260147` reached davi discovery + execute and returned honest no-business-evidence. The report does **not establish a known-present owner record independently prior to execution**; thus it is a negative/unavailable-data experiment, not the requested positive control. “Record absent” requires authoritative owner evidence and cannot be inferred solely from non-grounded finalization.
- The runtime SHA is still based on mounted code whereas baked `DELIA_RUNTIME_SHA` is stale; exact running config fingerprint `ecc145fd` is reported but not independently verified here. Runtime identity remains `EXECUTION_DRIFT` until reconciled.
- Executor reports 29/29 targeted tests and full backend suite exit0; reviewer did not independently execute tests.

## Required bounded rework

**TASK_ID PROPOSED:** `DELIA-C3-G7-AGENT-CONTEXT-ENVELOPE-AND-AUTHORITATIVE-POSITIVE-CONTROL-REWORK-01`.

1. Reanchor git HEAD/status, Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → technical/product/thematic specs → ledger/docs 256/268–270. Preserve concurrent work, no production deploy.
2. Characterize **actual native Agent** assembled prompt envelope at window 4096 (instructions, user/prior turns, FunctionToolset tool definitions and input schemas, output_type schema, overhead, expected output/generation reserve, tool results on subsequent turns), with the existing authorized Ollama profile. Distinguish SDK observed input tokens from heuristic estimate and avoid leaking raw prompts.
3. RED test at below/near/over bound and reproduce the 4211>4096 failure as applicable, with physical model calls measured. Reuse only legitimate `context_budget` helpers or extend them to serve actual native-Agent boundary where proven, not a second token engine; do not reapply constants without validation. Fail-closed with typed limitation and 0 calls when known over budget; reduce optional prior turns in order where permitted, never mandatory owner evidence/instructions/IDs. Enforce growth limits during tool call cycles (projected results/usage limits) and characterize context pressure after tool results; do not claim a pre-call gate can cap subsequent turns by itself.
4. **Real owner positive control**: find/read one existing authorized record independently at Domain API/owner first, prove its availability and canonical fields, then run one natural-language question through authenticated DÉLIA. Capture authoritative answer/provenance/grounding and redacted outcome. If nothing accessible in dev, classify `INCONCLUSIVE` with actual owner-side evidence and precise environment unblock; never fabricate fixtures for live outcome.
5. Resolve `DELIA_RUNTIME_SHA` stale metadata through authorized deployment/config build workflow (not production deploy). Record both code SHA and active process version, JSON fingerprint/model, security identity, actual owner endpoints and no secrets. Do not silently claim the env SHA matches mounted code.
6. Full focused+backend+architecture/security regressions, replay affected E-cases with true oracle; docs/ledger append only after factual results, commit/push bounded changes. RQ24/RQ28 remain PARTIAL pending positive business outcome and independent approval.

**VERDICT:** caplog fix accepted; context guard is a partial safety improvement, not verified fix for actual model context overflow; no positive business outcome, final functional acceptance withheld.
