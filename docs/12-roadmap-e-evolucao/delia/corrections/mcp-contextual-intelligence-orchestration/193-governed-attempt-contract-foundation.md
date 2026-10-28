# 193 — DÉLIA · Governed-Attempt Contract Foundation — Protocol Parity + Reusable Conformance Suite

**Date:** 2026-10-29. **Task:** `DELIA-C3-PLUGGABLE-ORCHESTRATION-CONTRACT-FOUNDATION-01`. **Base:** `5628f9eb60` (doc 192). **Status:** DONE — PROVEN.

## 1. Scope executed

Doc 192 Steps I + contract-suite portion of III, with the conditional Step-III extraction **declined on evidence** (§4).

## 2. Protocol parity (Step I)

**Drift:** `SupportsGovernedCapabilityAttempt.attempt` (`interaction/capability_attempt.py`) omitted `cancel_check`, placed `prior_turns` after `turn_deadline`, and typed `prior_turns`/`activity_sink` loosely — while the implementation (`orchestration.py:4061`) and the sole caller (`handle_interactive_turn.py:426-436`) already used the full signature.

**Fix (signature only, zero behavior):**

```diff
-        max_execution_stage: str | None = None,
-        turn_deadline: TurnDeadline | None = None,
-        prior_turns: tuple = (),
-        activity_sink: Any | None = None,
+        prior_turns: tuple[ConversationContextTurn, ...] = (),
+        max_execution_stage: str | None = None,
+        turn_deadline: TurnDeadline | None = None,
+        activity_sink: ActivityEventSink | None = None,
+        cancel_check: Callable[[], bool] | None = None,
```

Imports added: `ActivityEventSink` (interaction.activity), `ConversationContextTurn` (model_invocation.contracts). Neither module imports `capability_attempt` — no cycle. `Callable`/`Mapping`/`Any` already imported.

**RED→GREEN:** `test_attempt_signature_parity_with_runtime` compares parameter names, kinds and defaults between Protocol and `OperationalCapabilityOrchestrator.attempt`.
- RED: `missing=['cancel_check']` — observed before fix.
- GREEN: parity asserted; the test also guards `prior_turns` ordering drift and kind/default mismatches.

## 3. Reusable conformance suite (Step II)

New `delia-api/tests/test_governed_attempt_contract.py` — 14 tests, all boundary-only:

- **Engine registry:** `ENGINE_IDS = ("delia",)` + `build_engine(engine_id, ...)`. A future authorized engine adds one id + one builder branch; tests never change. Unregistered ids fail loudly (`AssertionError`, no silent fallback).
- **Assertions observe only:** `GovernedCapabilityAttempt` fields (status, error_code, provenance, confirmation_context, content), owner-port calls and model-stub requests. No internal stage names, methods or state are asserted.
- **Model-stub scripts are per-engine fixtures** supplied through `build_engine` — a different engine may map scenarios differently inside its builder.

Coverage (all GREEN on `delia`):

| Area | Tests |
|---|---|
| signature parity | `test_attempt_signature_parity_with_runtime` |
| READ select+invoke+project | `test_read_selected_invoked_and_projected` |
| fail-closed w/o model | `test_no_model_fails_closed` |
| goal+candidate binding | `test_candidate_bound_read_end_to_end`, `test_candidate_token_model_supplied_rejected`, `test_multi_candidate_requires_selection` |
| discovery+arg validation | `test_arguments_bounded_to_owner_schema` |
| owner errors | `test_owner_authz_denied_propagates` (AUTHZ_DENIED + typed error_code) |
| unauthorized capability | `test_invented_capability_fails_closed` (engine-neutral refusal, no owner call) |
| PREPARE/ACT | `test_prepare_act_governance_and_confirmation` (handle never leaves backend, single ACT), `test_act_never_invocable_without_pending_proposal` |
| timeout | `test_model_timeout_is_processing_timeout` (PROCESSING_TIMEOUT/model_timeout) |
| cancellation | `test_cancel_check_from_start_is_terminal` (cancelled, zero model invocations) |
| telemetry/identity | `test_correlation_id_round_trips` |

**Boundary-learning recorded:** `turn_budget_seconds=30` at construction is NOT equivalent to `turn_deadline=30s` at call time — a smaller constructor budget skips the optional self-index probe for headroom, and empty-arg invocations then fail closed (`skip_budget_identifier_unavailable`). The suite therefore keeps the implementation default and bounds windows via `turn_deadline` — same convention as `test_governed_stage_resume.py`.

## 4. Step III — conditional extraction inspection (declined)

| Gate | Verdict | Evidence |
|---|---|---|
| RESPONSIBILITY | PROVEN | stage primitives = `orchestration.py` instance methods (doc 192 §6) |
| OWNER | PROVEN | `capability_provision` |
| CURRENT_MECHANISM | PROVEN | `OperationalCapabilityOrchestrator` single impl |
| **SECOND_CONSUMER_NEED** | **NOT PROVEN** | no second engine authorized; `NEW_ENGINE=NOT_AUTHORIZED`, `LANGGRAPH_INSTALLATION=NOT_AUTHORIZED` |
| EXISTING_EQUIVALENT | YES (boundary) | `SupportsGovernedCapabilityAttempt` — now signature-faithful |
| ABSTRACTION_GATE | N/A | no extraction performed |

**Decision: NO extraction this task.** `GovernedStageRuntime` would migrate ~15 instance methods with shared mutable collaborators (providers, invoke_model, budgets, instructions, contextvars tokens) — exactly the "extensive method migration" the task prohibits without a real second consumer. The extraction boundary is recorded for the future bounded task: extract into `capability_provision/governed_stage_runtime.py` when Engine B is authorized; orchestrator delegates; suite must pass untouched.

**Composition rules:** no `DELIA_ORCHESTRATION_ENGINE` env created (single real implementation; a selector now would be speculative config with no second value). Deferred design recorded for the second-engine task: absent→`delia`, invalid→config error (no silent swap), experimental engines only in explicitly authorized environments, no request/model-driven selection, no fallback masking failures during A/B.

## 5. Residual checks

- Residual search: only one `attempt(` production implementer (`OperationalCapabilityOrchestrator`) — no hidden second producer.
- Callers/consumers unchanged: 1 caller (`handle_interactive_turn.py:426`), 1 output contract.
- Architecture Phase 3 gate: **PASS** (`audit_architecture_phase3.py`, no new regressions).
- AST/import sanity: `capability_attempt.py` parses; new imports are leaf-ward, no cycles.

## 6. Regression

```
container delpi-delia-api — python -m pytest tests/ -q
  (pre-existing collection-blocked: test_presentation_v2_*
   — missing /docs schema mount, environment issue)
  → 2431 passed, 2 failed (both PRE-EXISTING, unrelated):
    - test_cri_e2_outcome_assessment::test_cri_instruction_variant_
      carries_requirements_clause (instruction-version fixture drift,
      documented since doc 190 H6 regression)
    - test_g4_integrated_homologation::test_fixture_matches_
      current_producer_output (missing /plugins fixture mount)
```

No expectation edited to reach GREEN; the only assertion relaxed vs. the canonical suite is `test_invented_capability_fails_closed`, which deliberately accepts any non-SUCCESS refusal status so an alternative engine may answer the same scenario truthfully by a different route (canonical engine returns CLARIFICATION_REQUIRED; the no-call/fail-closed property is what the contract owns).

## 7. Result

`PROTOCOL_PARITY_BEFORE=missing cancel_check; prior_turns misplaced/untyped; activity_sink Any`
`PROTOCOL_PARITY_AFTER=exact (names/kinds/defaults match impl)`
`ORCHESTRATOR_BEHAVIOR_CHANGED=NO` (Protocol is structural typing only — zero runtime effect)
`SHARED_RUNTIME_EXTRACTION=DEFERRED (SECOND_CONSUMER_NEED not proven)`
`DEPENDENCIES_ADDED=NONE`
`SECURITY_GATES/PREPARE_ACT/CANCELLATION/TURN_BUDGET/EVIDENCE=PRESERVED` (14-test suite + 2431 regression)
`NEXT_BOUNDED_STEP=Engine-B authorization → GovernedStageRuntime extraction + langgraph_engine + env selector + A/B (doc 192 Steps II-VI)`
