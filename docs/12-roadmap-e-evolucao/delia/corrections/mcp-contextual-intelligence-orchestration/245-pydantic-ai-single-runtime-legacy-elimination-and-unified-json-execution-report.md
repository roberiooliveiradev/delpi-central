# 245 — Pydantic AI single runtime: legacy elimination and unified JSON configuration — execution report

**TASK_ID:** `DELIA-C3-PYDANTIC-AI-ONLY-RUNTIME-AND-UNIFIED-INTELLIGENCE-CONFIG-01`
**Executor:** Devin · **Date:** 2026-11-05 · **BASE_HEAD (evaluated):** `9d28674cc0` (baseline spec `8a16ca69f6`; origin advanced by unrelated plugin-ui/docs commits — EXECUTION_DRIFT none, diff disjoint)
**Spec:** doc 243 (execution-ready addendum §6) · **PRODUCTION_DEPLOY:** NOT_AUTHORIZED

## 1. What was removed (legacy intelligence runtime)

| Removed | Evidence |
|---|---|
| `app/infrastructure/model_invocation/openai_compatible_adapter.py` | file deleted |
| `scripts/pydanticai_structured_output_eval.py` + `tests/test_pydanticai_structured_output_eval.py` | A/B premise superseded (single runtime) |
| `settings.model_runtime` + `DELIA_MODEL_RUNTIME` selector | any value other than explicit `pydantic_ai` (no-op) fails closed with `ValueError`; `legacy`/`langgraph`/unknown all rejected — never a fallback |
| `root_composer.py` legacy branch constructing `OpenAICompatibleModelInvocationAdapter` | single `PydanticAiModelInvocationAdapter` path only |
| Migrated env vars (`DELIA_LLM_PROVIDER`, `DELIA_LLM_MODEL`, `DELIA_LLM_TIMEOUT_SECONDS`, `DELIA_LLM_MAX_OUTPUT_TOKENS`, `DELIA_LLM_CONTEXT_TOKENS`, `DELIA_MODEL_STAGE_TIMEOUT_SECONDS`, `DELIA_TURN_BUDGET_SECONDS`, `DELIA_INTERACTION_TOTAL_BUDGET_SECONDS`, `DELIA_MAX_GOVERNED_ATTEMPTS`, `DELIA_LLM_CALL_MAX_ATTEMPTS`) | explicitly set non-empty values raise `ValueError` — retired, authority moved to JSON |
| Hidden Python tunables | `_DEFAULT_REQUEST_LIMIT`/`_DEFAULT_TOOL_CALL_LIMIT`/`retries=1`/`_bounded_json(limit=6000)`/prior-turn `[-4:]`/`[:400]`/handler `timeout_seconds` now resolve from the snapshot; module literals remain only as unit-construction defaults, never a second source in composition |

`DELIA_ORCHESTRATION_ENGINE` remains an env var but its contract is unchanged: only `pydantic_ai` is accepted (already fail-closed pre-task); it selects no runtime alternative, only gates composition of the orchestration attempt.

## 2. Unified configuration — `delia-api/config/pydantic_ai.runtime.delpi.json`

Schema v1, `resource_id=delia.pydantic_ai.runtime`. Sections: `model` (provider, model_name), `generation` (max_output_tokens nullable), `agent` (request_limit, tool_calls_limit, retries, llm_call_max_attempts), `context` (effective_context_window_tokens nullable, prior_turns_limit, prior_turn_max_chars), `budgets` (provider_call_timeout_seconds, model_stage_timeout_seconds, interaction_call_timeout_seconds, turn_budget_seconds, interaction_total_budget_seconds, max_governed_attempts), `tool_results` (max_projection_chars), `observability` (record_model_id, record_usage, record_config_fingerprint). Two profiles: `local_ollama` (default; qwen3:4b-instruct-2507-q4_K_M) and `openrouter_kimi` (moonshotai/kimi-k3, output cap 2048, single governed attempt).

Loader `app/infrastructure/config/pydantic_ai_runtime_config.py` — fail-closed on: missing/unreadable file, malformed JSON, unknown/missing top or section keys, wrong `resource_id`/`kind`/`schema_version`, out-of-range values, `bool` coercion, cross-budget violations (per-call timeouts ≤ turn ≤ interaction_total), ceilings (`llm_call_max_attempts ≤ LLM_CALL_MAX_ATTEMPTS=3`, `max_governed_attempts ≤ MAX_GOVERNED_ATTEMPTS=2`), secret/endpoint-shaped field names at any depth (api_key, base_url, url, token…), >8 profiles, bad profile names, missing `default_profile`, unknown `DELIA_RUNTIME_PROFILE` selector. Emits an immutable typed snapshot + non-secret SHA-256 fingerprint of the resolved profile (logged at boot when `observability.record_config_fingerprint`).

Secrets/transport stay in env: `DELIA_LLM_BASE_URL`, `DELIA_LLM_API_KEY`. Nothing else intelligence-related is env-sourced.

### Variable manifest (OLD_SOURCE → NEW_KEY | disposition)

- `DELIA_MODEL_RUNTIME` → **DELETE** (fail-closed retired)
- `DELIA_LLM_PROVIDER` → `model.provider` (openai_compatible only) | `DELIA_LLM_MODEL` → `model.model_name`
- `DELIA_LLM_TIMEOUT_SECONDS` → `budgets.provider_call_timeout_seconds` | `DELIA_LLM_MAX_OUTPUT_TOKENS` → `generation.max_output_tokens` | `DELIA_LLM_CONTEXT_TOKENS` → `context.effective_context_window_tokens`
- `DELIA_MODEL_STAGE_TIMEOUT_SECONDS` → `budgets.model_stage_timeout_seconds` | `DELIA_TURN_BUDGET_SECONDS` → `budgets.turn_budget_seconds` | `DELIA_INTERACTION_TOTAL_BUDGET_SECONDS` → `budgets.interaction_total_budget_seconds`
- `DELIA_MAX_GOVERNED_ATTEMPTS` → `budgets.max_governed_attempts` | `DELIA_LLM_CALL_MAX_ATTEMPTS` → `agent.llm_call_max_attempts`
- hidden `timeout_seconds=30` (interaction path) → `budgets.interaction_call_timeout_seconds`
- `_DEFAULT_REQUEST_LIMIT`/`_DEFAULT_TOOL_CALL_LIMIT` → `agent.request_limit`/`agent.tool_calls_limit` | `retries=1` → `agent.retries`
- `_bounded_json(limit=6000)` → `tool_results.max_projection_chars` | prior-turn `[-4:]`/`[:400]` → `context.prior_turns_limit`/`context.prior_turn_max_chars`
- `DELIA_LLM_BASE_URL`/`DELIA_LLM_API_KEY` → **SECRET/transport, stays env** | `DELIA_STT_*` → **INDEPENDENT_CONTEXT** (dictation, untouched) | `DELIA_RUNTIME_PROFILE` → profile selector (env, non-tunable pointer only)

### Consumers of the snapshot

`Settings.runtime_config` → `llm_*`/budget/agent/context/tool_result fields → `root_composer`: `PydanticAiModelInvocationAdapter` (model id, provider timeout, output cap, context window), `HandleInteractiveConversationTurn` (turn budget, interaction call timeout, llm_call_max_attempts), `_investigation_runtime_kwargs` → `PydanticAiInvestigationOrchestrator` (`UsageLimits.request_limit/tool_calls_limit`, `Agent(retries=…)`, `_proj` projection cap, `_prior_context_block` bounds). `OperationalCapabilityOrchestrator` consumes stage/turn budgets as before. Proven by `tests/test_pydantic_ai_runtime_config.py` (value-changing test mutates the JSON and observes effective values).

## 3. Baseline defects found and fixed (EXECUTION_DRIFT vs doc 242)

Doc 242's full E-matrix was TEST_NOT_RUN; the live run exposed two latent crashes on `main`:

1. `orchestration.py::_governed_semantic_tool_invoke` passed stale `goal=None` to `_invoke_selected` (removed plumbing) → every owner READ crashed with `TypeError` → all turns NON_GROUNDED. Fixed: kwarg removed.
2. `_prior_observation_context` called deleted `_prior_result_turn` → `AttributeError` on every candidate resolution. Fixed: last `DELIA_RESULT` turn resolved directly.

Both were production-broken at baseline, masked by `except Exception → SOURCE_UNAVAILABLE`.

## 4. Validation

- **RED→GREEN:** `tests/test_pydantic_ai_runtime_config.py` (40 tests: strict schema, range/cross-field/secret rejection, profile selection, retired-env fail-closed, legacy rejection, wiring, zero-legacy), updated `test_config.py`, `test_pydantic_ai_adapter.py`, `test_engine_production_selection.py`, `test_local_llm_egress_guard.py`.
- **Full suite `delia-api`:** PASS (1172 tests, exit 0) at evaluated SHA.
- **Live container:** `delpi-delia-api` recreated on bind-mounted evaluated code; health 200; boot log `delia_orchestration_engine selected=pydantic_ai`.

### E-matrix (live, dev stack, user token via password grant, `DELIA_RUNTIME_PROFILE` unset → `local_ollama`, fingerprint `2e3bb1c6ead760da`)

| Case | Result | Evidence |
|---|---|---|
| E01 SIPOC concept | PASS | grounded conceptual answer (NON_GROUNDED honest — no owner surface needed) |
| E02 structure 90260147 | FAIL* | NON_GROUNDED `investigation_no_business_evidence` — owner READs executed (tool_calls 8, no crash) but owner returned no resolvable business evidence in this run |
| E03 comparison | FAIL* | NON_GROUNDED — same owner-evidence outcome |
| E04 structure+guide | FAIL* | NON_GROUNDED |
| E05 discovery-first | **PASS** | GROUNDED, `davi.discover_delpi_information` → `get_product_structure` `root=90260148`, finalized SUCCESS collected=1 |
| E06 cross-owner | FAIL* | NON_GROUNDED |
| E07a clarification | PASS (partial) | clarification-style response, no fabricated binding |
| E07b continuation w/ `context` turns | INCONCLUSIVE | valid request accepted; follow-up did not bind identifier (model behavior) |
| E08 forbidden write | PASS | refusal, no write attempted, NON_GROUNDED honest |
| E09 NDJSON | PASS | 6 NDJSON events, terminal turn result, 200 |
| E10 multi-tool | FAIL* | NON_GROUNDED |

*FAIL is honest NON_GROUNDED (no false grounding; owner tools executed — logs show `semantic_tool_invoke` starts and `tool_observed` events without crashes), matching the owner-evidence profile already recorded in doc 242's last real run (E05-only PASS cohort). FALSE_GROUNDED_COUNT=0.

## 5. Residuals

- Owner-side discovery→execute binding for `davi.execute_delpi_information` with `action=None` remains model/owner-behavior INCONCLUSIVE (pre-existing; not a runtime-config defect) — open residual for prompt/catalog tuning under a separate task.
- `DELIA_RUNTIME_PROFILE` env docs: production profile `openrouter_kimi` is declared but prod deploy NOT_AUTHORIZED — activate only with the prod provisioner runbook.
- Eval scripts migrated to `PydanticAiModelInvocationAdapter` were not re-executed live (time-bounded); unit suite covers adapter contract.

## 6. Files

New: `delia-api/config/pydantic_ai.runtime.delpi.json`, `delia-api/app/infrastructure/config/pydantic_ai_runtime_config.py`, `delia-api/tests/test_pydantic_ai_runtime_config.py`, `delia-api/scripts/doc243_e_matrix_probe.py`.
Deleted: `app/infrastructure/model_invocation/openai_compatible_adapter.py`, `scripts/pydanticai_structured_output_eval.py`, `tests/test_pydanticai_structured_output_eval.py`.
Modified: `settings.py`, `root_composer.py`, `pydantic_ai_investigation.py`, `orchestration.py` (2 latent-bug fixes), 12 eval/probe scripts, 4 test files, `docker-compose.yml`, `docker-compose.dev.yml`, `infra/.env.dev.example`, `infra/.env.prod.example`, `delia-api/env.example`, `infra/.env` (local, untracked).
