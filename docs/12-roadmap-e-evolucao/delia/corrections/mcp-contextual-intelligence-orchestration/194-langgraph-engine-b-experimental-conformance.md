# 194 — DÉLIA · LangGraph Engine B — Experimental Second Orchestration Mechanism, Conformance + Local A/B

**Date:** 2026-10-29. **Task:** `DELIA-C3-PLUGGABLE-ORCHESTRATION-LANGGRAPH-ENGINE-B-01`. **Base:** `5efaf41092` (doc 193 at `f02707409a`, plus coordination commits to `892e7b2049`). **Status:** DONE — PROVEN (local POC; Engine A remains the sole production-composed engine).

## 1. Scope executed

Two independent implementations of `SupportsGovernedCapabilityAttempt` now exist and pass the same conformance suite:

```
SupportsGovernedCapabilityAttempt
        |
   +----+----+
   |         |
Engine A   Engine B
Operational LangGraphCapabilityOrchestrator
Capability  (StateGraph — sequencing only)
Orchestrator
   |         |
   +----+----+
        |
  SAME governed primitives (one OperationalCapabilityOrchestrator
  instance's stage methods), providers, model port, budgets,
  instructions, write governance, provenance
```

Engine B is **not** a wrapper: `OperationalCapabilityOrchestrator.attempt()`/`._attempt()` are never invoked — enforced by `test_langgraph_attempt_does_not_delegate_to_engine_a` (spy on both entrypoints) and by `test_langgraph_attempt_executes_real_graph_nodes` (per-attempt `last_node_trace` asserts `preflight` + `admission` + `owner_path` executed).

## 2. Reanchor

HEAD `5efaf41092` (fast-forwarded to `892e7b2049` before work began); branch `main`; concurrent portal/plugin edits preserved untouched. Doc-192 Step II–VI plan followed; doc-193 boundary used as the contract.

## 3. Dependency Gate — LangGraph (APPROVED, eval-only)

| Check | Result |
|---|---|
| Python | 3.12.16 (dev container `delpi-delia-api`) |
| Version | `langgraph==1.2.16` — released 2025-10-16 (13 days at adoption; 1.2.17/1.2.18 < 7 days, rejected) |
| License | MIT (`License-Expression: MIT`) |
| Transitives | `langchain-core 1.7.1`, `langgraph-checkpoint 4.3.1`, `langgraph-prebuilt 1.1.1`, `langgraph-sdk 0.4.10`, `langsmith 0.14.14`, `pydantic 2.14.1`, `httpx 0.28.1`, `tenacity 9.2.1`, `orjson 3.13.0`, `ormsgpack 1.13.0`, `xxhash 4.0.2`, `langchain-protocol 0.0.20` |
| Conflicts | none observed — full suite 2525 passed post-install |
| Sync execution | `CompiledStateGraph.invoke` — synchronous, in-process |
| External services | none required; no checkpointer used |
| Isolation | new `delia-api/requirements-eval.txt` (opt-in `pip install -r`); `requirements.txt` and Dockerfile untouched; `pytest.importorskip("langgraph")` keeps absence green; residual grep: `langgraph` occurs only in `langgraph_engine.py` + its tests |

## 4. Shared-primitive extraction (doc-192 Step IV, bounded)

Only TWO boundaries were extracted — the minimum Engine B provably needed. Both are verbatim moves; Engine A delegates into them.

| Extraction | RESPONSIBILITY | OWNER | CONSUMERS | GATE |
|---|---|---|---|---|
| `_run_governed_attempts(attempt_once, …)` | contextvar binding (activity sink, resume checkpoint, cancel probe, relevance flag), monotonic interaction-budget anchoring, bounded attempt/resume loop, terminal status mapping | `OperationalCapabilityOrchestrator` | A: `attempt()` → `attempt_once → _attempt`. B: `attempt()` → `attempt_once → graph.invoke` | PASS — one runner, two callables; no retry/budget policy duplicated |
| `_governed_owner_path(…)` | post-admission owner path tail: surface listing → selection → invoke → judgment → recovery → synthesis | same | A: called from `_attempt` after admission dispatch. B: `owner_path` graph node | PASS — verbatim move; admission dispatch stays caller-owned |

Everything else Engine B consumes **pre-existed** as methods on the shared instance: `_admit_conversational_turn`, `_attempt_confirmation`, `_groups`, `_surface_inquiry_attempt`, `_emit_activity`, plus `EARLY_CONVERSATIONAL_ADMISSION`/`OWNER_PATH_UNBOUND` markers. No `GovernedStageRuntime` mega-extraction — the two boundaries above were the entire real need. Diff: `orchestration.py +90/-11` (signature/docstrings + delegation shims only).

**What Engine B does NOT share:** nothing new. Zero duplicated authorization, validation, evidence, retry or budget logic — the engine's `self._gates` IS an `OperationalCapabilityOrchestrator` instance (constructed with the same forwarded kwargs), used only for its stage methods.

## 5. Engine B — real graph

`delia-api/app/application/capability_provision/langgraph_engine.py` (325 lines):

- **State:** `_GovernedTurnState(TypedDict)` — bounded; contract inputs, admission decision, terminal `GovernedCapabilityAttempt`, node `trace`. No free-form state, no checkpointing, no chain-of-thought persistence.
- **Nodes (6):** `preflight` (deadline guard + activity emit), `admission`, `confirmation`, `surface_inquiry`, `conversational`, `owner_path`.
- **Edges:** `START→preflight`; conditional `preflight→{confirmation|admission}` (typed confirmation? — deterministic state routing, not model-owned); conditional `admission→{surface_inquiry|conversational|owner_path}`; all leaves `→END`.
- **Sequencing variable:** node routing only. Every gate runs the identical primitive Engine A runs — AuthZ, candidate-token opacity, schema bounds, PREPARE/ACT, budgets, cancellation, provenance are untouched.
- **v1 order** mirrors the governed pipeline deliberately — A/B comparability; legitimate re-ordering is a later bounded experiment.

## 6. Conformance — both engines

`test_governed_attempt_contract.py` parametrized `ENGINE_IDS = ("delia", "langgraph")`; signature parity now compares **each** engine to the Protocol, not only to Engine A.

**RED (true, recorded):** 17 `langgraph` params failed `ModuleNotFoundError`/`ImportError` before the engine existed; 3 Engine-B tests errored. Never simulated.

**GREEN:** 43 tests pass on both engines:

- 14 boundary tests × 2 engines (incl. per-engine signature parity)
- 5 S-scenario tests × 2 engines (S2, S3, S4, S6, S7 — see §7)
- Engine-B-only: real-graph node trace, non-delegation spy, isolation from `requirements.txt`, unregistered-id rejection, graph-vs-wrapper proof

**S1–S10 matrix (doc 192):**

| Scenario | Evidence (both engines) |
|---|---|
| S1 READ simples | `test_read_selected_invoked_and_projected` + A/B row — SUCCESS, provenance `teo/analyze/MCP` |
| S2 dois produtos | `test_s2_two_matching_records_with_codes` — `10080092`/`10081004` verbatim |
| S3 recovery | `test_s3_irrelevant_result_bounded_recovery` — exactly 2 invokes, no loop |
| S4 knowledge≠records | `test_s4_no_records_never_fabricates` — SUCCESS+insufficiency or non-success; zero fabricated codes |
| S5 multi-candidate | `test_multi_candidate_requires_selection` + `test_candidate_token_model_supplied_rejected` |
| S6 continuidade | `test_s6_prior_context_continuation_no_reinvoke` — SUCCESS, `port.calls == []` |
| S7 owner indisponível | `test_s7_owner_unavailable_truthful_failure` — SOURCE_UNAVAILABLE, no invented data |
| S8 capability não autorizada | `test_invented_capability_fails_closed` — truthful refusal, no owner call |
| S9 invalid output | existing `_FlakyStageModel`-style stage-timeout/invalid tests run on both engines via parametrization (`test_model_timeout_is_processing_timeout`) |
| S10 PREPARE/ACT | `test_prepare_act_governance_and_confirmation` + `test_act_never_invocable_without_pending_proposal` — CONFIRMATION_REQUIRED→single ACT; cold ACT→WRITE_REJECTED |

## 7. Local A/B — `scripts/engine_ab_eval.py`

Deterministic fake-model corpus (S1/S2/S3/S7/S8/S10), identical fixtures, identical limits. Measured: `FAKE_MODEL_CALLS` (scripted; no provider tokens exist in this harness), owner calls, local wall latency.

| scenario | A status | B status | A model calls | B model calls | owner calls | divergent |
|---|---|---|---|---|---|---|
| S1_read | SUCCESS | SUCCESS | 6 | 6 | 1 | no |
| S2_two_records | SUCCESS | SUCCESS | 7 | 7 | 1 | no |
| S3_recovery | SUCCESS | SUCCESS | 9 | 9 | 2 | no |
| S7_owner_unavailable | SOURCE_UNAVAILABLE | SOURCE_UNAVAILABLE | 6 | 6 | 1 | no |
| S8_unauthorized | CLARIFICATION_REQUIRED | CLARIFICATION_REQUIRED | 3 | 3 | 0 | no |
| S10_cold_act | WRITE_REJECTED | WRITE_REJECTED | 4 | 4 | 0 | no |

`OUTCOME_DIVERGENCES=0`. **Identical model-call counts per scenario** — Engine B consumes the same governed stages, confirming the primitives (not reimplemented gates) drive the work. Latency delta (+2–30ms on fakes) is graph-invocation overhead; meaningless on fake models, recorded for completeness. `SEMANTIC_EVAL=INCONCLUSIVE` — deterministic fakes prove conformance, not semantic superiority; no Ollama real-model run was performed this task.

## 8. Regression, audit, residuals

- Focused orchestration sweep (7 files): **300 passed**.
- Full `delia-api` suite: **2525 passed, 2 failed, 3 skipped** — the two failures are the SAME pre-existing environment issues as the Task-02 baseline (`test_cri_instruction_variant_carries_requirements_clause` fixture drift; `test_g4_integrated_homologation` missing `/plugins/delia/.../__fixtures__` mount). Classification unchanged; not caused by this diff (extraction is verbatim; engine is unreferenced by production wiring).
- `audit_architecture_phase3.py`: PASS, no new phase-3 regressions.
- Residual search: no `langgraph` references outside the engine file, its tests, and `requirements-eval.txt`; no composition-root wiring; no `DELIA_ORCHESTRATION_ENGINE` config (intentionally — one real alternative exists but is not yet production-authorized; selector design recorded for the acceptance task).
- `requirements.txt` unchanged; Engine B unreachable absent the eval env.

## 9. Files changed

- `delia-api/app/application/capability_provision/orchestration.py` — two verbatim extractions (+90/-11)
- `delia-api/app/application/capability_provision/langgraph_engine.py` — NEW (Engine B)
- `delia-api/tests/test_governed_attempt_contract.py` — parametrized to both engines + S-scenarios + Engine-B proofs (+427)
- `delia-api/scripts/engine_ab_eval.py` — NEW local A/B harness
- `delia-api/requirements-eval.txt` — NEW opt-in eval dependency pin

## 10. Residuals / next bounded step

- Engine B v1 mirrors Engine A's ordering — the POC proves substitutability + contract preservation, not a sequencing improvement. Any re-ordering experiment (e.g., parallel surface listing vs. admission) is a bounded follow-up.
- `SEMANTIC_EVAL` open: a real-model (Ollama `delia-json`) A/B on the R1 corpus would measure semantic parity/cost — next bounded evaluation, no new authorization needed for local runs.
- Engine selection config remains uncreated by design; when coordination accepts Engine B (or another), selector rules from doc 192 §composition apply (default `delia`, invalid → config error, never user/LLM-chosen, no masking fallback).
- Rollback: delete `langgraph_engine.py` + revert the two extractions' call sites (or keep them — they are also Engine A's own internals); requirements-eval.txt removal restores pre-POC state. Zero production surface to roll back.
