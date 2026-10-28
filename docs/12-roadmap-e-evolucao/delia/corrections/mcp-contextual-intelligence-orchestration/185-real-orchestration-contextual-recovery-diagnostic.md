# 185 — DÉLIA · Real-Orchestration Contextual Recovery Diagnostic

**Date:** 2026-10-28. **Task:** `DELIA-C3-REAL-ORCHESTRATION-CONTEXTUAL-RECOVERY-DIAGNOSTIC-01`. **References:** docs 175–184; ledger. **Status:** DIAGNOSTIC_EXECUTED; FAILURES_REPRODUCED; ROOT_STAGES_IDENTIFIED; NO_CODE_CHANGES.

## 1. Environment

- DELIA_RUNTIME=local dev stack (`docker-compose.dev.yml`+`minimal`), `delpi-delia-api` rebuilt at EVALUATED_SHA=`f55e966f8a` (main HEAD; boundary code identical to deployed `48afe2ba86`).
- MODEL_PROVIDER=`openai_compatible` (Ollama `http://ollama:11434/v1`); MODEL_ID=`delia-json:latest` (~1.9 GB). **Not the production model** (`moonshotai/kimi-k3`) — external LLM egress is deliberately refused outside production (`llm_egress_blocked_reason`, `settings.py`) per the approved Ollama local-testing policy.
- MCP_DAVI_ENDPOINT=`http://api-delpi:8000/mcp` (local container, healthy); auth via delegated subject bearer (dev portal user, password grant — env-provided, no reset).
- Identity: real auth middleware → Core `/me`; all turns HTTP 200 through `/interaction/turns`.
- Config note: local container recreated with shell-env overrides for `DELIA_LLM_*` (no `.env` edit, no commit, production untouched). Local `infra/.env` still carries 4 dead `DELIA_OPENAPI_*` vars — unreadable by current code (settings attrs removed); cosmetic residue only.

## 2. Result matrix (2 runs per scenario max)

| Test | Run 1 | Run 2 | Capability reached | Outcome |
|---|---|---|---|---|
| T1 terminal bala | `capability_surface_listing` | `owner_path_unbound` | none | FAIL (variable stage) |
| T2 terminal ilhós | `owner_path_unbound` | `delpi_source_unverified` | `teo.get_product_guide` (wrong surface, `mcp_protocol_error`) | FAIL |
| T3 terminais do tipo bala | `owner_path_unbound` | `delpi_source_unverified` | `davi.discover_delpi_information` ok → `no_result` | FAIL |
| T4.1 pesquise terminais bala | `delpi_source_unverified` (discover ok → `no_result`) | `owner_path_unbound` | `davi.discover_delpi_information` | FAIL |
| T4.2 selecione dois exemplos | `capability_surface_listing` | `capability_surface_listing` | none (no new owner call) | FAIL |

All results `NON_GROUNDED`, honest limitations, zero fabricated records, zero unauthorized actions. `governed_attempts=1` each; model_calls 1–8; duration ~0.9–34 s; tokens reported by observability projection.

## 3. Stage-level root causes (from `orchestration stage=*` logs)

**RC1 — Semantic target selection binds the wrong surface (deterministic).** In every `owner_surface` admission run, `target_selection` selected `group=mcp:vista capability=search_data_routes` for DELPI product queries — VISTA's route-search capability, never a DELPI owner path. Evidence: stage log lines at 15:07:52/15:08:07/15:09:20/15:09:32/15:09:50 correlation_ids `3302a3b6`, `a07ecc6b`, `ed26d55a`, `f85ccc19`, `fc34e22f`. Owner: DÉLIA `capability_provision/orchestration` model stages (`select_capability` projection + contract). Plausible attractor: capability name `search_data_routes` reads product-search-like to a small model.

**RC2 — foreign_selection emits invalid output (intermittent).** `foreign_selection decision=invalid` → `semantic_path=foreign_required_invalid` → `owner_path_unbound` (T1-run2, T2-run1, T3-run1, T4.1-run2). Model produced `decision=ok` HTTP-level responses whose content failed the selection contract parse.

**RC3 — interaction_admission misclassification (intermittent).** `decision=surface_inquiry` for operational product queries → `capability_surface_listing` (T1-run1, T4.2 ×2). Follow-up turn T4.2 also did NOT reuse/continue investigation — it listed surfaces deterministically (2/2).

**RC4 — candidate argument generation for execute fails (when DAVI is reached).** `provider_invoke ok davi.discover_delpi_information` (arg_keys=query[,top_k], ~180 ms) → `model_propose candidate_arguments ok` → `foreign_invocation decision=no_result` (T3-run2, T4.1-run1). Discovery returned; the model's candidate-arguments output could not be merged (`_candidate_arguments` → `merged=None` → `_unusable_candidate_terminal` → `invoked=None`).

**RC5 — wrong-specialist enrichment selection.** `foreign_selection selected teo.get_product_guide` for DELPI product data → `mcp_protocol_error` (T2-run2).

**Explicitly NOT root causes:** DAVI MCP transport (200/202, ~180 ms), api-delpi health, AuthN/AuthZ (token minted, `/me` resolved, unauth→401), evidence projection/synthesis (never reached; all failures fail-closed NON_GROUNDED). No direct DELPI path existed — `DIRECT_DELPI_*=0` verified in the runtime image.

## 4. Consolidated diagnosis

All failures sit in the **LLM-responsibility stages** (admission, target/foreign selection, candidate-argument generation) — none in DAVI/API DELPI/transport/governance. Failure signatures are **variable** (same question flips between surface_listing / owner_path_unbound / delpi_source_unverified), consistent with a small local model producing semantically-unstable structured output against the selection contracts.

**Model-scope caveat:** evidence is `delia-json` (local, ~1.9 GB). Production runs `moonshotai/kimi-k3`, a much larger model. This diagnostic cannot claim the production model fails identically — it proves the failure *stages* and their mechanics, and that the previous class of problems (capability selection + continuation) still reproduces end-to-end with a real LLM under the real DAVI-only boundary.

## 5. Recommended minimal correction (not executed — out of scope)

Bounded A/B: run the identical T1–T4 suite against the production-model configuration in an authorized environment (e.g., a permitted test env or the prod container with a legitimately provisioned identity). If `kimi-k3` selects `davi` correctly → model-capacity issue, no orchestration change needed. If it also binds `mcp:vista.search_data_routes` → minimal fix at the capability-projection/contract level (e.g., surface naming/descriptions fed to `select_capability`) — owner: `capability_provision`.

## 6. Compliance

CODE_CHANGED=NO; PROMPTS_CHANGED=NO; DAVI_CHANGED=NO; API_DELPI_CHANGED=NO; DEPLOY_EXECUTED=NO; no secrets/tokens/CoT persisted; phase C3 not advanced.
