# 195 — DÉLIA · LangGraph Engine B — Architectural Isolation Remediation (F1–F3)

**Date:** 2026-10-29. **Task:** `DELIA-C3-PLUGGABLE-ORCHESTRATION-ENGINE-B-ISOLATION-REMEDIATION-01`. **Base:** `a76c9e2a69` (doc 194). **Status:** DONE — PROVEN.

## 1. Scope executed

Independent-review findings F1–F3 remediated with the smallest legitimate changes: framework dependency moved to the Infrastructure layer, concrete Engine-A coupling inverted into a narrow application contract, dependency metadata reconciled. Behavior preserved — no sequencing, prompt, corpus or gate change.

## 2. F1 — framework inside Application → Infrastructure adapter

**Before:** `app/application/capability_provision/langgraph_engine.py` imported `langgraph.graph` — an external framework inside the Application layer.

**After:** `app/infrastructure/orchestration/langgraph_engine.py` (+ package `__init__.py`). Dependency direction now:

```
Application:  SupportsGovernedCapabilityAttempt (unchanged)
Application:  SupportsGovernedStageGates       (new narrow contract)
      ^                ^
      | implements     | consumes
Infrastructure:  langgraph_engine.py  →  langgraph SDK (infra-only)
```

No LangGraph type appears in any Application/Domain contract or signature. Enforced by `test_application_and_domain_contain_no_framework_imports` (AST scan of `app/application/**` + `app/domain/**` for `langgraph|langchain|langsmith|langgraph_sdk`).

## 3. F2 — concrete Engine-A coupling → injected gates contract

**Before:** the adapter constructed `OperationalCapabilityOrchestrator` internally (`self._gates = OperationalCapabilityOrchestrator(providers, **kwargs)`) — coupling to the concrete Engine A class and duplicating its wiring.

**After:** new application-owned contract `app/application/capability_provision/governed_stage_gates.py` — `SupportsGovernedStageGates(Protocol)` declaring exactly the six governed primitives Engine B consumes:

`_admit_conversational_turn` · `_attempt_confirmation` · `_groups` · `_surface_inquiry_attempt` · `_governed_owner_path` · `_run_governed_attempts`

The adapter's constructor is now `__init__(self, gates: SupportsGovernedStageGates)` — it never imports or constructs the Engine A class (AST-enforced). Composition moved to the legitimate wiring point: the test harness builds the gates provider instance and injects it.

**Coupling classification (T5):**

| Item | Status |
|---|---|
| `self._gates.<method>` calls | 6 — all declared in the protocol; `test_engine_b_consumes_only_declared_gate_methods` diffs used-vs-declared |
| `OperationalCapabilityOrchestrator` import/construct in adapter | NONE — AST test |
| Gates provider = Engine A's class | **RESIDUAL, accepted** — the sole runtime provider of the shared primitives is Engine A itself. Removing it would require migrating a large coupled method set (the doc-194 deferred mega-extraction) for zero behavior gain — explicitly outside this task per §4/F2 guidance |
| `_emit_activity` import | module-level application helper — shared primitive, not Engine-A strategy coupling; classified acceptable residual |

`test_engine_a_satisfies_the_gates_contract` guards protocol/implementation signature drift permanently.

## 4. F3 — dependency metadata reconciled (PyPI authoritative)

| Field | Verified |
|---|---|
| Version | `langgraph==1.2.16` (unchanged pin) |
| Release date | `upload_time 2026-10-16T22:11Z` — **doc 194 said "2025-10-16" (year typo); corrected** |
| Python | `requires_python >=3.10` — compatible with env 3.12.16 |
| License | MIT (`license_expression`) |
| Direct deps | `langchain-core<2,>=1.4.7`, `langgraph-checkpoint<5,>=4.3.0`, `langgraph-prebuilt<1.2,>=1.1.0`, `langgraph-sdk<0.5,>=0.4.6`, `pydantic>=2.7.4`, `xxhash>=3.5.0` |
| Advisories | PyPI `vulnerabilities: []` at pin |
| Isolation | `requirements-eval.txt` only; `requirements.txt`/Dockerfile untouched |

## 5. T1–T8 evidence (new `tests/test_engine_b_architecture_isolation.py`)

| Gate | Result |
|---|---|
| T1 framework isolation | AST scan — zero framework imports in Application/Domain |
| T2 contract conformance | adapter satisfies `SupportsGovernedCapabilityAttempt` — 43/43 contract tests |
| T3 independent sequencing | real-graph node trace + non-delegation spy (never calls `attempt`/`_attempt`) — both GREEN |
| T4 governed-control reuse | same gates provider methods; identical outcomes + identical model-call counts (A/B §6) |
| T5 coupling classification | declared-vs-used gate-method diff; residual documented §3 |
| T6 production isolation | `root_composer.py`: no framework/engine-B reference (AST + text) |
| T7 dependency absence | `builtins.__import__` blocker simulation — composer + Engine A import/construct fine; adapter import raises ImportError |
| T8 dependency presence | adapter builds + executes real compiled graph; `last_node_trace` proves nodes ran |

**RED recorded:** 5 failures before remediation (`application_and_domain framework imports`, adapter location, Engine-A construction, undeclared gates, no gates injection). **GREEN:** all 9 isolation tests + 43 conformance tests on both engines.

## 6. Conformance + A/B after remediation

- `test_governed_attempt_contract.py`: 43/43 on `delia` AND `langgraph` — unchanged assertions.
- `scripts/engine_ab_eval.py`: `OUTCOME_DIVERGENCES=0`; identical fake-model call counts (6/7/9/6/3/4); statuses byte-identical to the pre-remediation run.

## 7. Regression / audit / residuals

- Focused orchestration sweep (8 files): **309 passed**.
- Full `delia-api` suite: **2534 passed, 2 failed, 3 skipped** — same two pre-existing environment failures as the Task-02/03 baseline (`test_cri_instruction_variant_carries_requirements_clause`; `test_g4_integrated_homologation` missing `/plugins` fixture mount). Classification unchanged — unrelated to this diff.
- `audit_architecture_phase3.py`: PASS. `audit_backend_boundaries.py`: PASS (0 findings).
- Residual search: `langgraph` occurs only in `app/infrastructure/orchestration/langgraph_engine.py`, its tests, `requirements-eval.txt`; zero refs under `app/application`, `app/domain`, `app/composition`.

## 8. Files changed

- MOVED `app/application/capability_provision/langgraph_engine.py` → `app/infrastructure/orchestration/langgraph_engine.py` (+ `__init__.py`); docstring rewritten for layer position; constructor takes injected `gates`.
- NEW `app/application/capability_provision/governed_stage_gates.py` — `SupportsGovernedStageGates` protocol.
- NEW `tests/test_engine_b_architecture_isolation.py` — T1–T8 gates.
- `tests/test_governed_attempt_contract.py` — builder composes gates + injects; module path updates.
- `requirements-eval.txt` + doc 194 — release-date metadata corrected (2026-10-16).
- This document + ledger.

## 9. Remaining technical debt → Task 04 prerequisites

- **Residual coupling:** gates provider is still Engine A's class. If coordination wants a true owner split (`GovernedStageGates` collaborator the orchestrator delegates to), that is a bounded refactor — the protocol now makes the boundary explicit and tested, so the move is mechanical when authorized.
- Task 04 (sequencing-variation POC) may proceed: the adapter boundary is stable, contract-tested, and the A/B harness is unchanged. Prerequisites: none beyond the accepted residual note — no new config, no composition-root wiring required for local experiments.
