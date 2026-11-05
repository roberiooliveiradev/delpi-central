# 282 — DÉLIA · Review de answer delivery: MCP READ positivo, saída estruturada não concluída

**DATA:** 2026-11-05  
**REVIEWED_TASK:** `DELIA-C3-G7-LOCAL-OLLAMA-ANSWER-DELIVERY-AND-RESOURCE-PROFILING-01`  
**BASE_REPORTED:** `a828b051424f3c4b87845bea05f350fab04d6b7d`  
**REVIEWED_SHA:** `0e10e29559231ea0a64278043a3489d49873ed36`  
**REVIEW VERDICT:** `ACCEPT_WITH_RESIDUAL` measurement and reported governed MCP owner reads; `FAIL` final structured answer delivered; `INCONCLUSIVE` business outcome end-to-end; `PRODUCTION_DEPLOY=BLOCKED`.

## GitHub inspection

- Exact commit only modifies `delia-api/config/pydantic_ai.runtime.delpi.json` by changing `local_ollama.agent.retries: 1→2`; appends documentation to doc256 and doc281. There is **no DÉLIA source-code remediation**, nor committed Ollama Compose memory/keep_alive change in this commit. Other context/profile settings remain at local 16384 and `max_output_tokens: null`.
- `delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py` uses Pydantic AI `Agent(..., retries=self._agent_retries, output_type=InvestigationAnswer, ...)`; a shape-only validator exists; native `run_sync` is used. Thus `UnexpectedModelBehavior: Exceeded maximum output retries` is **not sufficient by itself** to prove hardware throughput as the exclusive cause. Could arise from truncated/incomplete output, output schema mismatch, invalid final response or repeated failed validation. Examine actual redacted model output/validator class, retry causes and termination before proposing a change.
- Executor reports Ollama CPU-only, 5.1GB model, cold load 70.7s, warm prompt 3016 tokens + 48 generated over 23.1s, ~6 tokens/s generation; 6.8GB Docker memory cap around 72% and KEEP_ALIVE=30m after live changes. These metrics are observations from report, not reviewer-independent reproductions, and do **not** measure full DÉLIA final-answer token count/latency.
- Executor reports two governed READ chains through `davi.discover_delpi_information` followed by `davi.execute_delpi_information(action=search_products)` with `uncovered=50220013`. This is encouraging live owner-evidence availability, but reviewer did not inspect provider payload, actual SourceRefs or received final answer; **do not classify business outcome as grounded complete**.
- Final user response in both reported attempts failed; `ANSWER_DELIVERED=NO`, so G7 still has a material output-delivery residual. Increasing `retries` from 1 to 2 did not demonstrate success; avoid further retry or timeout increases without objective proof.
- Host RAM ~9.9GB with ~1.3GB free (executor reported); ensure 6.8GB container cap with keep-alive does not starve other services. GPU present but container not configured for GPU; GPU availability/capability is `TO_INVENTORY` and should not be assumed. `DELIA_RUNTIME_SHA` baked env remains stale, `EXECUTION_DRIFT`.
- Tests passed per executor, independently not run. No legacy history reintroduced; `context_budget.py` retains legitimate non-Agent consumers. RQ24/RQ28 PARTIAL. Production release remains blocked.

## Next bounded work — diagnose final output error before tuning or changing model

**TASK_ID:** `DELIA-C3-G7-STRUCTURED-OUTPUT-FAILURE-CAUSE-AND-LOCAL-DELIVERY-01`.

1. Reanchor current HEAD/status → Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → architecture/product/contract/thematic specs/ledger/docs256/279–282. Confirm actual deployed local code SHA, Pydantic AI 2.50.0/version, qwen model, profile fingerprint, Ollama memory cap/keep-alive, and deadlines. No production deployment.
2. Reproduce one previously confirmed authorized owner READ on product 50220013, with bounded/redacted evidence. Instrument existing native Pydantic AI/Ollama diagnostics at output stage: number of physical model calls, exact provider stop/finish reason, retries count and reason, native structured output validation error *class and path only*, whether text is truncated/incomplete/malformed, generated token count and eval duration, effective max_output_tokens, total request and gateway deadline. Do not log full sensitive outputs or secrets.
3. Distinguish `SCHEMA_INVALID`, `OUTPUT_TRUNCATED`, `RETRY_EXHAUSTED`, `MODEL_TOO_SLOW`, `PROVIDER_TIMEOUT`, `CLIENT_DELIVERY_TIMEOUT` with evidence. One cause may coexist with another; don't conflate native validation retry with pure CPU latency.
4. First preserve native `Agent(output_type=InvestigationAnswer)` and built-in retries. If structured schema overly complex or output settings are malformed, prove against canonical contract and fix smallest allowed configuration/schema mapping with RED→GREEN; do **not** bypass validation, replace output with raw text, weaken evidence/Policy, or introduce a second response engine. Any schema change requires owner/consumer contract compatibility.
5. Compare at most two **authorized** inference configurations on same prompt/model/hardware if safe: one baseline (CPU 16k) and one justified option (bounded output tokens or verified GPU-backed Ollama integration, if host/driver/compose existing support and memory safety confirmed). Measure actual request-level token counts/durations/outcome. Avoid throwing more memory, window, timeouts or retries without evidence. If GPU unavailable, clearly mark blocker and use safe fallback. Avoid new provider-specific planner branches.
6. Demonstrate a complete client-delivered user answer with explicit, independently confirmed owner record, SourceRefs and grounding or declare `INCONCLUSIVE/FAIL` with exact stage. Keep no-authorization/no-data controls. Do not treat owner result alone as success.
7. Any proven replacement: minimal diff, same-delivery removal of retired legacy, fix consumers/imports/config/tests, full regressions and residual search. If not proven, no code churn. Record model measured vs estimated metrics separately, SHA, config fingerprint, release gates, RQ statuses in docs/ledger, push preserving concurrent work.
8. Production stays blocked without end-to-end answer, approved production model/profile, safety/release/rollback gates and authorization.

**Technical review:** READ owner invocation now reported positive; final structured response still defective in this environment. Focus on precise native output validation failure and client delivery, not generalized architecture rebuild.
