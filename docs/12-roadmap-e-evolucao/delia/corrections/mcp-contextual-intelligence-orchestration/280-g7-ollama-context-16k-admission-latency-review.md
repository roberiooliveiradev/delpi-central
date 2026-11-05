# 280 — DÉLIA · Review G7: contexto local Ollama 4096→16384 e novo bloqueio na admissão

**DATA:** 2026-11-05  
**TASK_ID REVIEWED:** `DELIA-C3-G7-OLLAMA-MCP-CATALOG-SELECTION-AND-READ-OUTCOME-DIAGNOSTIC-01`  
**BASE_HEAD REPORTED:** `c852b386dd74c2a2f5c08785f6d82910d39656ef`  
**REVIEWED_SHA:** `9f0b008ded64b98008de11f6b05caef8b1f74d6d`  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` local context-window configuration and causal distinction; semantic selection/business outcome `INCONCLUSIVE`; admitted local model latency `FAIL` for observed case; `PRODUCTION_DEPLOY=BLOCKED`.

## GitHub source and report classification

- Direct commit touches only `delia-api/config/pydantic_ai.runtime.delpi.json` (effective context window **4096→16384** for `local_ollama`) and documentation (doc256 +17). Other frontend/CI files in base-to-final compare originate from concurrent commits and are unrelated.
- Executor reports catalog 10 capabilities / 3 owners, dynamically registered and `surface=configured`, with admission `owner_surface`. Before config change, 3/3 observed pre-call gates rejected with `context_budget_fail` estimates 7643/7712/7642 greater than window 4096, meaning the LLM **was never invoked**. Prior “model chose no tool” inference is invalid for these cases; do not present the new state as proof of correct model selection either.
- Docker `OLLAMA_CONTEXT_LENGTH=16384`, mounted SHA `9f0b008...` and fingerprint `646e19a0` are executor-reported runtime observations, not independently inspected by reviewer. The stale baked `DELIA_RUNTIME_SHA` remains documented EXECUTION_DRIFT.
- After context change, reported `model_propose timeout 60s` followed by `budget_exhausted`; no positive model selection or MCP invocation. This shows the next observed boundary, **not** isolated cause. Could be model cold load, prompt prefill/tool schemas, generation tokens, CPU/GPU RAM spill, queue contention, timeout layering, or stage budget. Need measurements before concluding “4B model is slow” or changing timeout/model size.
- `effective_context_window_tokens=16384` is verified in repository; no measured provider input-token count, no VRAM/RAM usage timeseries or successful 16k admission recorded. The 7.6–7.7k prompt estimates are heuristic. The reported model native maximum of 262144 is not proof that the local 6GB GPU can economically run this window or that 16384 is optimal.
- Existing profile has `provider_call_timeout_seconds=60`, `model_stage_timeout_seconds=60`, `interaction_call_timeout_seconds=30`, `turn_budget_seconds=300`, `interaction_total_budget_seconds=300`; identify which actually governs `model_propose` before any change.
- No production code refactor in this commit, no legacy introduced. Full backend regression PASS executor-reported, not independently run. Owner positive oracle still absent; RQ24/RQ28 PARTIAL; release gate blocked.

## Next bounded work: performance characterisation then evidence-driven configuration

**TASK_ID:** `DELIA-C3-G7-OLLAMA-ADMISSION-LATENCY-PROFILE-AND-MCP-SELECTION-01`.

1. Reanchor current git HEAD/status, .cursor/Project Instructions → canonical 16→50→17→49→51→52→21→20→25 → architecture/product/thematic specs/ledger/docs 256/278–280. Verify actual local container/model/provider/SHA and configured/stale runtime identity. Avoid production deploy.
2. Instrument **existing** model-admission boundary to report measured monotonic timing: connection/start, cold vs warm Ollama load, prompt processing/prefill, output generation, provider wait/queue where measurable, interaction timeout source and available Ollama metrics (`prompt_eval_count`, `eval_count`, durations if exposed by allowed interface), GPU/CPU/RAM/VRAM. No secrets/raw token logging. Separate actual tokens, estimates and unavailable measures.
3. Run identical reproducible **READ-only** prompt with real current catalog and tool schemas at baseline 16384; first cold and warm attempts, number of model requests, admission latency, and actual model output/tool choice. Compare with at most one smaller window **only if estimated mandatory context and actual request can fit**; do not reduce below legitimate context or increase to 262144 merely because model metadata advertises it. Account for reserve, tool projection and structured output.
4. Inspect `model_propose` invocation path and deadline source (`provider_call_timeout_seconds`, `model_stage_timeout_seconds`, `interaction_call_timeout_seconds`, total budget). Do not increase timeout to hide a performance failure. If tuning justified, change one parameter at a time and compare success, latency, memory, quality and fail-closed; use existing config/profile, no provider-specific branches in planner.
5. When admission completes: determine whether the model selects a real compatible capability; capture catalog presence, actual native tool choice/arguments, governed MCP invocation, result and outcome. If not, characterize semantic selection separately from latency. Confirm one READ owner record independently before claiming business positive success.
6. If a real code defect found: RED→GREEN smallest diff, remove replaced legacy same task, fix consumers, full regression/residual search. Otherwise configuration/measurement only; do not reopen history/Agent framework redesign.
7. No production deploy unless release authority and all gates explicit. Record local SHA, model/hardware config, measured vs estimated usage, cold/warm latency, deadline, capability selection, owner evidence, statuses `PASS|FAIL|INCONCLUSIVE`, RQ24/RQ28, docs/ledger and commit/push.

**Review close:** The zero-selection symptom at 4096 was pre-call rejection; the new 16384 admission timeout needs performance diagnostics, not a new architecture loop.
