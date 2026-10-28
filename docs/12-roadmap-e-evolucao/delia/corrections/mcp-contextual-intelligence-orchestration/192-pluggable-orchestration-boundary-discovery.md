# 192 — DÉLIA · Pluggable Orchestration — Boundary Discovery & Implementation-Ready Plan

**Date:** 2026-10-28. **Task:** `DELIA-C3-PLUGGABLE-ORCHESTRATION-BOUNDARY-DISCOVERY-01`. **SHA:** `fc30ea947c` (main; doc 191 landed at `994d0be168`, HEAD advanced). **Status:** INVESTIGATION_DONE — read-only; PROPOSED ADR pending coordination.

## 1. Entrypoint and verified call graph

```
POST /interaction/turns  (interfaces/http/interaction_routes.py)
  → HandleInteractiveConversationTurn.handle(request)          interaction/handle_interactive_turn.py
      → self._capability_orchestration.attempt(…)   L426        injected, typed SupportsGovernedCapabilityAttempt (Protocol)
          → OperationalCapabilityOrchestrator.attempt(…)        capability_provision/orchestration.py L4061
              → _attempt() L4228 → admission → turn_goal/with_goal → select_group →
                select_capability → native_assessment → foreign_selection → arguments →
                discover → resolve/select_candidate → candidate_arguments → invoke →
                relevance judgment → _recover_relevance → synthesis/render
      → GovernedCapabilityAttempt → presentation/response assembly
```

| Field | Evidence |
|---|---|
| ENTRYPOINT | `OperationalCapabilityOrchestrator.attempt` — `orchestration.py:4061` |
| INTERFACE | `SupportsGovernedCapabilityAttempt` (Protocol) — `interaction/capability_attempt.py:222` |
| CALLERS | exactly one: `handle_interactive_turn.py:426` (incl. confirmation turns via `confirmation` param) |
| INPUT | `input_text` + kwargs: correlation_id, actor_user_id, session_id, confirmation, workspace_context, prior_turns, max_execution_stage, turn_deadline, activity_sink, **cancel_check** |
| OUTPUT | `GovernedCapabilityAttempt` — status enum (8 values incl. CONFIRMATION_REQUIRED/PROCESSING_TIMEOUT), outcome, provenance, error_code, owner_hint, content, limitations, markdown_content, confirmation_context |
| DEPENDENCIES (injected at composer) | `providers` (CapabilityProvider port), `invoke_model` (ModelInvocationPort), `model_ref`, budgets (turn/stage/interaction/attempts/llm-call-attempts), CRI flags/vocab, field_labels, orchestration_instructions resource |
| SIDE_EFFECTS | owner invokes via `McpCapabilityProvider`/`SpecialistInterop`; activity events; `ModelCallLedger` records; resume checkpoints (contextvars) |
| SECURITY_GATES | fail-closed instruction resource (`root_composer.py:357-366`), admission gate, declared-goal write gate, candidate-token opacity, AuthZ via provider errors, PREPARE/ACT separation, confirmation resume |
| ERROR_CONTRACT | `CapabilityProviderError` typed codes → `GovernedCapabilityStatus` + `error_code` (frozen `_error_attempt`) |
| TIMEOUT_BUDGET | `TurnDeadline` monotonic shared budget + per-stage timeout + `MIN_VIABLE_MODEL_STAGE_SECONDS` |
| OBSERVABILITY | `ModelCallLedger` (stage/instruction, tokens, latency, error class, attempt) + structured stage logs |
| COMPOSITION | `root_composer.py:368-387` — unconditional `OperationalCapabilityOrchestrator` when `providers`+instructions valid; `None` otherwise |

**Contract drift found (minor):** the `SupportsGovernedCapabilityAttempt` Protocol signature omits `cancel_check`, which both the implementation (`attempt`, L4071) and the call site (L426-436) use. Protocol is a subset — runtime safe, but the boundary contract should be made exact in Step I.

## 2. EXISTING_EQUIVALENT / REUSE_DECISION

`EXISTING_EQUIVALENT=YES` — the replaceable boundary **already exists**: protocol + constructor injection + composer wiring + `None`-off semantics. No new port is required or justified.

`REUSE_DECISION=EXTEND` — extend the existing protocol to full signature parity (`cancel_check`) and add a fail-closed engine selector in the composer. No generic plugin registry.

## 3. Replaceable vs non-substitutable responsibilities

| Responsibility | Varies by implementation? | Owner (non-negotiable) |
|---|---|---|
| Stage sequencing/graph (admission→…→synthesis order, branches, loops) | **YES — engine strategy** | DÉLIA application |
| Semantic proposals (what the LLM is asked, stage instructions) | Same instructions v25 shared; node-level prompting may vary | governed instruction resource |
| Capability discovery/selection semantics | Stage outputs vary; **contract identical** | `CapabilityProvider` port |
| Model invocation | **Shared port — NOT replaceable per engine** | `ModelInvocationPort` |
| Argument validation, schema checks | **Shared — non-substitutable** | `_validate_instance`, typed contracts |
| Candidate token opacity, action_id membership | **Non-substitutable** | deterministic code |
| Evidence/relevance contracts | **Non-substitutable** | `EvidenceFacts`, `GoalEvidenceJudgment`, `parse_*` |
| Recovery semantics (bounded, dedup, no verbatim re-exec) | Sequencing may vary; **rules identical** | recovery contract |
| AuthZ/AuthN, error vocabulary | **Non-substitutable** | Core/provider errors |
| PREPARE/ACT, confirmations, idempotency | **Non-substitutable** | write-governance chain |
| Budgets/deadlines, ledger, activity sink, cancel | **Non-substitutable** | `TurnDeadline`, `ModelCallLedger` |
| Outcome rendering/`GovernedCapabilityAttempt` | **Non-substitutable** | `capability_attempt.py` |

The engine owns **only how stages are scheduled and sequenced** — never what is authorized, validated or rendered.

## 4. Doc-191 conflict resolution (explicit)

Doc 191 rejected agent frameworks **as orchestrator replacements** because a framework-owned tool-calling loop creates a second planner and parallel authority. That verdict stands. This plan does NOT contradict it: the alternative engine is an *alternative sequencing* over **the same governed primitives** — LangGraph nodes delegate to DÉLIA-owned stage functions and ports; no framework-native tool calling, AuthZ, memory or planner enters the boundary. If a future proposal uses LangGraph's own agent/tool mechanisms instead → that is exactly the doc-191 violation → `ARCHITECTURE_DECISION_REQUIRED`.

## 5. Boundary options

| Option | Callers | Impls | Contract change | Security | Verdict |
|---|---|---|---|---|---|
| **A — `SupportsGovernedCapabilityAttempt` (existing protocol)** | 1 | 2+ | protocol drift fix only | clean: attempt-level contract | **RECOMMENDED** |
| B — narrower "semantic strategy" port inside `_attempt` | — | — | new port splits semantics from gates | blurs gate ownership | REJECT — no evidence it exists/needed |
| C — provider/model ports underneath | many | n/a | already pluggable | n/a | NOT the orchestration boundary |
| D — plugin registry/platform | — | — | new abstraction | registry risk | REJECT — prohibited by task |

**Recommended boundary = A**, applied via a shared substrate (below). ABSTRACTION_GATE: PASS (reuse, no new abstraction).

## 6. The real constraint — and the Step-II answer

Today the governed gates are **instance methods of a single 11.5k-line orchestrator** (`_model_stage_proposal`, `_propose`, `_invoke`, `_build_arguments`, `_select_group/_select_capability`, `_candidate_arguments`, `_judge_goal_evidence`, `_recover_relevance`, `_synthesize_content`, `_unusable_candidate_terminal`, plus module-level helpers `_fit_json_block`, `_omit_tail_entries`, `_validate_instance`, `parse_*`, `_error_attempt`, `_contract_*`). A second engine cannot reuse them without (a) duplicating them (second source of truth — prohibited) or (b) extracting a shared runtime.

**Step II extracts `GovernedStageRuntime`** (`capability_provision/governed_stage_runtime.py`): a collaborator constructed with the same dependencies (providers, invoke_model, model_ref, budgets, instructions, labels, ledger) exposing the stage methods verbatim. `OperationalCapabilityOrchestrator` delegates to it — **behavior-preserving move refactor**, proven by running the full 2415-test suite unchanged. Engine B instantiates the same `GovernedStageRuntime` and supplies only its own graph/sequencing.

## 7. LangGraph feasibility (evaluation only — not installed)

| Question | Answer |
|---|---|
| Represent stages | YES — node per stage fn, `StateGraph` over a typed state (turn goal, evidence, attempts, budgets) |
| Call existing model port | YES — nodes are plain callables; delegate to `GovernedStageRuntime._model_stage_proposal` (same `ModelInvocationPort`) |
| Use capability contracts | YES — `_invoke`→`McpCapabilityProvider` unchanged |
| State propagation/recovery | YES — channels carry _TurnGoal/EvidenceFacts; conditional edges = gates; `recursion_limit` bounds loops; checkpointer **not needed** (in-memory `InMemorySaver` or none) |
| Sync/async | `graph.invoke()` sync-compatible; current adapter is sync `requests` — compatible |
| Budget/deadline | `TurnDeadline` object threaded through state — preserved |
| Telemetry | `ModelCallLedger` is already populated inside `_model_stage_proposal` — works regardless of sequencer |
| Security boundary | Holds **only** if nodes delegate to governed primitives — no LangGraph agents/tools/handoffs used |
| Dependencies | `langgraph` + `langgraph-checkpoint` (+langchain-core transitive) — new dep tree into a lean service; pin ≥7-day release |
| License | MIT |
| Feasibility verdict | **FEASIBLE as internal sequencer; MODERATE-HIGH effort** — the value is an alternative *ordering/recovery policy*, not new machinery |

Pydantic AI / mcp-agent could implement the same boundary later (graph/loop over `GovernedStageRuntime`) — same contract, no per-framework redesign. Assessment depth: lightweight (doc 191 details stand).

## 8. Engine selection & rollback

- New env `DELIA_ORCHESTRATION_ENGINE` ∈ {`delia` (default), `langgraph`}; composer reads it at `root_composer.py:368`; **invalid/missing → log + `delia`** (same pattern as `llm_call_max_attempts` fail-closed).
- Never request/model/user controlled; experimental engine cannot reach prod wiring without an env change + deploy (separate authorization).
- Rollback = env value back to `delia` — no data migration (stateless per-turn).
- During A/B, a test-harness selector injects each engine directly — no production flag needed for evaluation.

## 9. Test design (S1–S10, local fakes only)

Common conformance suite parametrized over engine fixture (`_engine(param) → SupportsGovernedCapabilityAttempt`); reuses `FakeProposalModel`, `FakePort`, `MULTI_CANDIDATE_RESULT`, `_davi_read` harness from `test_specialist_capability_orchestration.py`.

| ID | Scenario | Gates asserted |
|---|---|---|
| S1 | Simple authorized read | selection → invoke → SUCCESS; provenance fields |
| S2 | Two matching products w/ codes | records surface codes; min_items satisfied |
| S3 | Irrelevant→recovery | mismatch → single bounded recovery round; no verbatim re-exec |
| S4 | Knowledge ≠ records | knowledge candidate not accepted as substitute for registered-record goal |
| S5 | Multi-candidate | goal-aware candidate selection (v25); token opacity; invented id fails closed |
| S6 | Context continuity | _TurnGoal/evidence survive transitions; prior_turns honored |
| S7 | Owner unavailable | SOURCE_UNAVAILABLE; no invented evidence |
| S8 | Unauthorized capability | proposal can't bypass eligibility/AuthZ; AUTHZ_DENIED |
| S9 | Invalid structured output | retry within LLM_CALL_MAX_ATTEMPTS; deadline honored |
| S10 | Governed write | PREPARE→CONFIRMATION_REQUIRED→ACT separation; no autonomous material action |

**A/B metrics** (doc §11): BUSINESS_OUTCOME_SUCCESS, SEMANTIC_SELECTION_ACCURACY, GOAL_REQUIREMENT_COVERAGE, MODEL_CALL_COUNT, INPUT/OUTPUT_TOKENS (ledger-reported), LATENCY, RECOVERY_EFFECTIVENESS, EVIDENCE_PROVENANCE, AUTHORIZATION_COMPLIANCE, CONTRACT_CONFORMANCE, ERROR_HANDLING, MAINTENANCE_COMPLEXITY. Fake-model runs establish **contract/flow** equivalence only — semantic equivalence needs authorized-model eval (separate authorization).

## 10. Implementation-ready plan (Steps I–VI — NOT executed)

| Step | Goal | Files | Key tests | Stop condition |
|---|---|---|---|---|
| **I. Contract parity** | Fix protocol drift (`cancel_check`); document attempt contract | `interaction/capability_attempt.py` (Protocol sig) | existing suite green | any behavioral change needed → STOP |
| **II. Extract `GovernedStageRuntime`** | Move stage methods to shared collaborator; orchestrator delegates | `capability_provision/governed_stage_runtime.py` (new), `orchestration.py` (delegate), `root_composer.py` (wire shared deps) | full suite must pass **unchanged** (move refactor) | test expectation change required → STOP |
| **III. Conformance suite** | Parametrize candidate/governed tests over engine fixture | `tests/conftest_engine.py` + existing files | both engines on same corpus | Engine B can't satisfy contract w/o gate change → ESCALATE |
| **IV. Engine B (LangGraph)** | Graph over `GovernedStageRuntime`; env-gated, default delia | `capability_provision/langgraph_engine.py` (new), composer selector, `requirements.txt` (pinned dep) | S1–S10 on engine B | needs framework tool-calling/AuthZ → ARCHITECTURE_DECISION_REQUIRED |
| **V. Local A/B** | Same fixtures/model/config both engines; metrics per §9 | `scripts/orchestration_engine_eval.py` (new) | report | — |
| **VI. Decision** | Retain/reject/extend eval | doc + ledger | — | — |

Steps I+II are the combinable next implementation task (behavior-preserving, test-proven). III–IV require dependency approval + security review. V–VI gated on IV.

## 11. Proposed ADR — status `PROPOSED — PENDING_COORDINATION_APPROVAL`

**Problem:** PO direction — replaceable orchestration implementations to avoid bespoke lock-in (LangGraph first candidate). **Constraints:** ADR 58 (LLM owns semantics; code owns gates); doc 191 (no framework planner authority); DAVI-only boundary; lean dep posture. **Existing equivalent:** `SupportsGovernedCapabilityAttempt` protocol + DI — proven above. **Boundary:** Option A + shared `GovernedStageRuntime`. **Conflict:** none residual — resolved per §4. **Risks:** dep tree growth; Engine B drifting from gate semantics (mitigated by shared primitives + conformance suite); over-pluggability (mitigated by 2-way env selector, no registry). **Costs:** Step II is the only non-trivial refactor (mechanical, suite-proven). **Benefits:** measurable A/B of sequencing policies; option value without architecture rewrite. **Open questions:** (a) does Engine B's ordering actually differ enough to justify cost — baseline vs LangGraph should first be sketched in POC; (b) dependency approval for `langgraph`; (c) authorized-model eval budget for semantic A/B.

## 12. UNRESOLVED

- Whether LangGraph's sequencing would *materially differ* (different recovery policy, parallel native+foreign probe) vs merely re-expressing the same DAG — to be answered in Step IV/V, not assumed.
- `cancel_check` protocol drift — trivial fix queued in Step I.
- Dep size/transitives of `langgraph` not yet enumerated (no install per restriction).

NEXT_BOUNDED_IMPLEMENTATION_TASK: Steps I+II combined — "protocol parity + `GovernedStageRuntime` extraction, zero behavior change, suite must pass untouched."
