# 242 — Capability Provision Legacy Removal + Pydantic AI Consolidation — Execution Report

TASK_ID=DELIA-C3-CAPABILITY-PROVISION-FULL-LEGACY-REMOVAL-AND-PYDANTIC-AI-CONSOLIDATION-01
EXECUTOR=Devin
DATE=2026-11-05
BASE_HEAD=c311e75e14
PLAN=doc 241 (§10 full-folder audit)
PRODUCTION_DEPLOY=NOT_AUTHORIZED

## 1. Objective

Retire DÉLIA's bespoke semantic orchestration architecture — the
Application-sequencer engine (`OperationalCapabilityOrchestrator.attempt`
→ `_governed_owner_path`) and the second LLM controller inside the
native invoke chain (`_select_candidate` /
`_propose_candidate_arguments` / selection+arggen model stages) — so
Pydantic AI is the sole semantic investigation runtime, while the
legitimate Application controls (admission, discovery/binding, AuthZ,
evidence, outcome, pagination, PREPARE/ACT, confirmation, audit,
presentation, JSON/NDJSON) remain owner-governed and verifiable.

## 2. What was removed (real deletion, not redistribution)

### orchestration.py — 16,287 → 6,476 lines (−60.2 %)

| Component removed | Status |
|---|---|
| `attempt` / `_attempt` / `_run_governed_attempts` legacy driver entry | REMOVED (native adapter owns the boundary) |
| `_governed_owner_path` (~1,565 lines) | REMOVED |
| Subobjective engine (`_decompose_objective`, `_investigate_subobjectives`, `_decomposed_investigation`, `_subobjectives_*`, `SubObjectiveTracker` wiring) | REMOVED |
| Selection planner (`_select_target`, `_select_group`, `_select_capability`, `_select_capability_with_goal`, `_capability_from_selection_proposal`, `_filter_groups_for_selection`, `_build_plan`, `_log_plan`) | REMOVED |
| Argument generator (`_build_arguments`) + index machinery (`_propose_index_probe`, `_bind_arguments_from_index`, `_propose_index_identifier`) | REMOVED |
| Second LLM controller in native path (`_select_candidate`, `_propose_candidate_arguments`, `_unusable_candidate_terminal`) | REMOVED |
| Recovery/synthesis (`_recover_relevance`, `_apply_semantic_relevance`, `_synthesize_content`, `_repair_once`, `_recover_owner_contract`, `_judge_goal_evidence`) | REMOVED |
| Continuation/foreign machinery (`_analysis_continuation`, `_select_prepare_continuation`, `_prior_continuation_attempt`, `_prior_result_*`, `_select_resolver`, `_resolve_missing_inputs`, `_select_foreign_capability`, `_invoke_foreign_evidence`, `_corroborate_attempt`, `_assess_native_path`, `_turn_goal_from_proposal`, `_understand_goal`, `_budget_allows_*`) | REMOVED |
| Pagination aggregation (`_maybe_aggregate_paginated_count`, `_requirements_need_more_pages`, `_page_cursor`), outcome bridge (`_apply_outcome_assessment`, `_compose_cri_response`), clarification (`_clarification_question`) | REMOVED |
| 17 specialized instruction IDs + 20→2 instruction JSON entries | REMOVED (kept: `interaction_admission`, `evidence_composition`) |
| ~60 dead top-level helpers/constants (selection payload builders, bond/identifier/resolver/comparison/instruction-payload machinery, native-assessment ledger, retry contextvars) | REMOVED |

### Files deleted

- `capability_retrieval.py` (BM25 ranking, eval-only modes) — 83 lines
- `subobjective_tracker.py` (`SubObjectiveTracker`) — 365 lines
- `app/infrastructure/arggen/` (`pydantic_arggen.py`, eval-only arggen engine) — deleted

### Tests deleted (implementation-coupled suites)

77 test files removed — they scripted the retired engine's stage
vocabulary (instruction IDs, `.attempt()` owner path, selection
proposals) and cannot execute against a runtime that no longer exists,
per the task's "no dead code preserved because of historical tests"
directive. Shared fixtures needed by the surviving native-path suites
were extracted to `tests/support/capability_fixtures.py`
(FakeProvider/FakeProposalModel/_cap/_group/_outcome/_providers/...).

### Wiring/config

- `_SUPPORTED_ORCHESTRATION_ENGINES` = `{"pydantic_ai"}`; `delia`
  rollback retired and fails closed.
- `DELIA_ARGGEN_ENGINE`, `DELIA_TOOL_SELECTION_MODE`,
  `DELIA_SUBOBJECTIVE_INVESTIGATION` settings + env vars removed.
- `for_testing()` no longer forces `orchestration_engine="delia"`;
  composition falls back to `build_test_investigation_model()`
  (infrastructure, `pydantic_ai.models.test.TestModel`) so SDK stays
  out of composition/Application.
- `_NATIVE_ASSESSMENT_LEDGER` + `recovery_reuse_enabled` usage removed
  from the adapter (the native-assessment reuse stage is gone).
- `governed_stage_gates` Protocol: `_decompose_objective` +
  `_governed_owner_path` removed; the remaining protocol is the real
  gate surface the adapter consumes.
- `ORCHESTRATION_INSTRUCTION_KEYS` = {admission, evidence_composition}.

## 3. Native-path semantic deduplication (doc 241 §10.1)

Before: `_governed_semantic_tool_invoke` → `_invoke_selected` →
`_discover_candidate`/`_resolve_candidate` → `_select_candidate` /
`_propose_candidate_arguments` → `_model_stage_proposal` — a second
selection+arggen controller behind the agent's own tool call.

Now:

- `_resolve_candidate` is deterministic only: exactly one live-token,
  non-dead-end candidate chains; zero/ambiguous sets resolve to None.
- Multi-candidate discovery outcomes are returned to the Agent through
  the bounded tool projection — the semantic pick is the agent's next
  native tool call carrying the owner-issued `candidate_token`, never
  a second LLM selector.
- `candidate_token` passthrough added to `_invoke_selected`: an
  agent-supplied owner-issued token is treated as opaque untrusted data
  and passed to the owner verbatim — never synthesized, never
  authorization.
- `_candidate_arguments` is deterministic schema validation +
  utterance-identifier binding only; the LLM second proposal is gone.
- `_discover_candidate` keeps the deterministic context-folded retry
  only; the `_build_arguments` reformulation leg and the empty-result
  `_propose_candidate_arguments` retry leg are gone — reformulation is
  the agent's tool-loop decision.
- `goal` plumbing removed from the native invoke chain (typed plan is
  accepted via `declare_investigation_goal` / `SemanticInvestigationPlan`,
  reusing `_TurnGoal`/`_GOAL_CLASSES`).

## 4. What was preserved (legitimate Application controls)

- Typed conversational admission: ONE `self._propose` call
  (`_admit_conversational_turn` → `_model_stage_proposal`) — the
  retained semantic gate that both engines shared (doc 241 §3.3).
- Evidence composition: `compose_verified_observations` →
  `_compose_multi_evidence` keeps its single bounded proposal +
  deterministic verifier (agent-requested, never a planner).
- Write governance chain intact (dormant while the tool surface is
  READ-only): `PendingWriteStore`, `_attempt_prepare`,
  `_attempt_direct_act`, `_attempt_confirmation`, `_confirm_proposal`,
  `_execute_prepared_act`, `_invoke_act`, `_provenance`, `_audit`,
  `_outcome_attempt`, `_effective_confirmation_policy`,
  `_preview_render`. Pending proposals can only be produced by these
  gates — a confirmation for a nonexistent digest fails closed.
- Discovery-first deterministic chaining (single usable candidate →
  single candidate-bound READ), context-folded retry, zero-candidate
  honest terminals (guidance/zero-candidate projection).
- `SemanticInvestigationPlan` + `_accept_semantic_investigation_plan`
  (`_TurnGoal`/`_GOAL_CLASSES` reused — no parallel goal model).
- `conversational_response.py`, `outcome_assessment.py`,
  `generic_evidence_renderer.py`, `paginated_result_semantics.py`,
  `contracts.py`, `ports.py`, `mcp_provider.py`, `openapi_provider.py`
  kept — providers stay at the infrastructure/application boundary;
  Application/Domain carry no SDK imports (`test_v14_architecture_isolation`
  PASS).
- Live Core AuthZ (`_groups` request-scoped), schema validation,
  cancellation/deadline/budget gates, resume/checkpoint contextvars,
  activity observability — all retained.

## 5. Metrics

| Metric | Before | After |
|---|---|---|
| Package total lines | 21,844 | 11,550 (−47%) |
| `orchestration.py` lines | 16,287 | 6,476 (−60%) |
| Top-level functions | 131 | 69 |
| `OperationalCapabilityOrchestrator` methods | 84 | 31 |
| Module constants | 101 | 58 |
| Model-stage call sites (own LLM) | ~15 stages | 2 (admission, evidence_composition) |
| Instruction IDs | 20 | 2 |
| Files in package | 13 | 10 |
| Test files | ~155 | 78 (77 implementation-coupled removed) |
| Executable orchestration paths | 2 (delia + pydantic_ai) | 1 (pydantic_ai only) |
| Semantic selectors | group/capability/candidate/resolver/foreign/index | 0 (agent tools) |
| Planners | `_build_plan` + subobjective decomposition | 0 (native tool loop) |
| Registries/retrieval | BM25 `rank_capabilities` | 0 |
| Flags | `delia` engine, arggen, tool-selection, subobjective | `pydantic_ai` only |

## 6. Verification

- `delia-api` full suite (tests/, non-live): **GREEN** at the final
  diff — ~1,150 tests, exit 0.
- 74 native-path contract tests (semantic_rework, investigation_runtime,
  real_owner_tool_loop_rework, engine_production_selection, native_first
  _consolidation) PASS, including: unknown capability rejected,
  write class rejected on tool surface, invalid args rejected,
  candidate_token binding, prompt-injection does not bind identity,
  provenance/grounding gates, multi-source verified composition,
  clarification contracts, catalog omits writes.
- `test_v14_architecture_isolation` PASS — no `pydantic_ai` import
  outside `app/infrastructure/` (TestModel moved into the adapter).
- Engine resolver: `delia`/`langgraph`/unknown fail closed;
  `pydantic_ai` requires a composed model; retired fanout/checkpoint
  flags still fail closed.
- E01–E10 real-owner runs: TEST_NOT_RUN — the local dev container
  carries the previous image; a real E-run at this SHA requires a
  rebuild+restart of the shared local stack which was not executed in
  this session. The contract suite at the evaluated SHA is the
  regression evidence. E-runs remain the next gate.
- FALSE_GROUNDED=0 in the executed suite (no fabricated evidence path:
  identity/provenance/injection negatives all PASS).
- Residual search: no live references to removed files, instruction
  IDs, `tool_selection_mode`, `arggen_engine`,
  `subobjective_investigation_enabled`, `_NATIVE_ASSESSMENT_LEDGER`,
  `attempt(` on the orchestrator, or `DELIA_ORCHESTRATION_ENGINE=delia`
  outside the fail-closed validation.

## 7. Decisions and notes

- `_admit_conversational_turn` keeps ONE `_propose` call — this is the
  typed admission gate doc 241 §3.3 keeps (proportional conversational
  path), not a second controller: it emits a typed class + flag, the
  semantic content still comes from the agent.
- `_compose_multi_evidence` keeps its single bounded proposal because
  the agent explicitly requests composition and the deterministic
  verifier computes every fact — the proposal is never authority.
- The write gates are dormant (no tool exposes writes); the
  confirmation chain remains executable for pending proposals and is
  deliberately preserved per task §9 rather than deleted as
  unreachable-by-tool.
- `unique_structural_ticket_list_capability` re-export restored —
  pinned by an existing contract test.
- EXECUTION_DRIFT=NONE: no removal conflicted with a higher authority;
  `AGENTS.md` deploy guidance is superseded by the explicit
  PRODUCTION_DEPLOY=NOT_AUTHORIZED for this task.

## 8. Remaining

- Real E01–E10 at a rebuilt local runtime is the residual gate before
  any phase advance; FUNCTIONAL_ACCEPTANCE_CANDIDATE stays NO.
- Doc 239 feature matrix updated with the adopted/removal state.
