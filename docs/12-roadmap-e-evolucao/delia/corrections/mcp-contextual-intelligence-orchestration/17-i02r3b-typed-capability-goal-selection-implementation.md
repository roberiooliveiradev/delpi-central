# 17 — I02-R3B · Typed Capability+Goal Selection Implementation

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-MCP-I02-R3B-ADAPTIVE-CAPABILITY-ROUTING-IMPLEMENTATION-01`  
**BASE_HEAD (coordination ref):** `72aa0aa5f8dccac701b218c5a9434ac1d68e92fe`  
**IMPLEMENTATION_HEAD:** `cda4963e52ae5cadc66392a5f4fcf37fb3c5aa17`  
**AUTHORITIES:** [14](./14-i02r3-independent-diagnostic-review-and-architecture-decision.md), [15](./15-i02r3a-controlled-budget-and-critical-path-experiments.md), [16](./16-i02r3a-independent-experiment-review.md) — **not redefined**  
**I02_ACCEPTED:** `NO`  
**VERDICT:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Contract / safety gate (pre-patch)

### Dependency map

| Stage | Inputs | Outputs | Consumers | Independent? |
|---|---|---|---|---|
| `select_group` | multi-group summaries | `group_key` | capability selection | YES |
| `select_capability` | group surface, prior_listing | `remote_name` → `ProviderCapability` | write demotion, plan, args | YES (surface revalidation) |
| `turn_goal` | user text, prior turns | `_TurnGoal` | write gate, native, continuity, comparison | YES (semantic) |
| `native_assessment` | target group + goal | foreign/corroboration status | foreign selection | Depends on goal |
| `arguments` | schema + DISCOVERY | validated args | owner READ | Depends on capability |

### Gate answers

1. **Independent:** group pick, capability surface match, and goal/write semantics remain separately validated after merge.  
2. **Write gate fields:** `declared`, `goal_class`, `execution_bound` (unchanged consumers).  
3. **Deterministic validations kept:** remote_name ∈ invocable live surface; goal_class ∈ `_GOAL_CLASSES`; prior_evidence_sufficient requires prior turns; write demotion/clarify unchanged.  
4. **Typed proposal can preserve semantics:** YES for cold-start when `goal_class` is present and valid; incomplete payloads fall back to dedicated `turn_goal`.  
5. **Foreign/corroboration:** native assessment still runs when `len(groups)>1`; `comparison_requested` still from validated goal.  
6. **Fallback:** missing `goal_class` → separate `_understand_goal`; invalid class → undeclared `_TurnGoal()`; unknown remote → `NOT_APPLICABLE`.  
7. **Minimal diff:** extend cold-start capability propose with optional goal fields (same purpose id); no new planner/registry.  
8. **RED/GREEN:** `tests/test_i02r3b_typed_capability_goal_selection.py`.

```text
CONTRACT_GATE=PASS (internal propose shape; no public OpenAPI change)
SECURITY_GATE=PASS (synthetic holdouts; MESSAGE≠ACT)
ABSTRACTION_GATE=PASS (REUSE _propose + _TurnGoal validations)
ARCHITECTURE_DECISION_REQUIRED=NO for this scoped merge
```

Native short-circuit and production stage-cap/headroom defaults were **not** changed (single optimization measured first; doc 14/16).

## 2. Selected optimization

```text
SELECTED_OPTIMIZATION=TYPED_CAPABILITY_AND_GOAL_COLD_START
WHY_SELECTED=
  Doc 16 prioritized typed merge; eliminates one sequential pre-owner
  model call without removing write/foreign/discovery gates.
ALTERNATIVES_REJECTED_NOW=
  stage_cap_10 production (doc 14/15)
  arguments_headroom default ON (doc 15/16)
  native multi-group skip (not proven)
  TEO-specific planner branches
```

### Behavior

- Cold start (`goal is None`): `_select_capability_with_goal` uses `CAPABILITY_AND_GOAL_INSTRUCTION` under purpose `select_capability`.  
- If proposal includes valid `goal_class` → skip dedicated `turn_goal`.  
- If `goal_class` absent → fallback to `_understand_goal` (legacy fixtures).  
- Multiturn with `prior_turns`: early `_understand_goal` unchanged; capability selection remains capability-only.  
- Demotion / repair: capability-only `_select_capability` unchanged.  
- `experimental_arguments_budget_guard` remains default `False`.  
- `GLOBAL_TURN_BUDGET_SECONDS=30` unchanged.

## 3. Files changed

| File | Change |
|---|---|
| `delia-api/app/application/capability_provision/orchestration.py` | `CAPABILITY_AND_GOAL_INSTRUCTION`, `_turn_goal_from_proposal`, `_select_capability_with_goal`, wire cold-start |
| `delia-api/tests/test_i02r3b_typed_capability_goal_selection.py` | RED/GREEN holdouts |
| `delia-api/tests/test_i02r3a_budget_and_critical_path_experiments.py` | E3 note points to R3B |
| This doc + README + Execution Ledger | evidence |

## 4. Metrics (SYNTHETIC)

| Metric | Legacy (separate goal) | Typed (goal in capability) |
|---|---:|---:|
| MODEL_CALL_COUNT (TEO multi-group success path) | N | N−1 |
| GOAL_INSTRUCTION invoked | YES | NO |
| METHODOLOGY_READ | YES | YES |
| MATERIAL_ACT | 0 | 0 |

```text
BASELINE_MODEL_CALLS=legacy fixture path (includes turn_goal)
OPTIMIZED_MODEL_CALLS=typed path (−1 when goal_class present)
MODEL_CALL_REDUCTION=1 (eligible cold-start)
PRE_OWNER_LATENCY=SYNTHETIC only — live p95 INCONCLUSIVE
TASK_SUCCESS_SYNTHETIC=PASS (methodology READ)
LIVE_AUTHENTICATED_K1=TEST_NOT_RUN
```

P50/P95: **INCONCLUSIVE** (synthetic n small; no live A/B at this SHA).

## 5. Evals

| Case | Result |
|---|---|
| K1 TEO synthetic typed | PASS (catalog + methodology READ, grounded path) |
| K2 continuity early goal | PASS (dedicated turn_goal; no typed merge) |
| K3 VISTA-like single-group typed | PASS (INDEX/topic shape; no native) |
| Renamed provider | PASS |
| Write demotion / clarify | PASS |
| Foreign/comparison native retained | PASS |
| Injection / forged history | PASS (ACT=0) |
| Full `delia-api` pytest | PASS |
| Live K1/K2/K3 authenticated | **TEST_NOT_RUN** |

## 6. Acceptance vs AC

| AC | Status |
|---|---|
| AC-01 call reduction eligible path | PASS (synthetic) |
| AC-02 capability selection | PASS |
| AC-03 write intent | PASS |
| AC-04 foreign/corroboration | PASS (native still called) |
| AC-05 DISCOVERY/READ | PASS synthetic |
| AC-06 provider neutral | PASS |
| AC-07 K2/K3 | PASS synthetic |
| AC-08 no ACT | PASS |
| AC-09 budget 30s | PASS |
| AC-10 live latency/completion | **INCONCLUSIVE** (no live) |
| AC-11 full backend | PASS |
| AC-12 docs/ledger | PASS (this delivery) |
| AC-13 commit/push | PASS (after publish) |

## 7. Rollback

```text
Revert orchestration cold-start wiring to always call _understand_goal
after _select_capability (capability-only instruction).
Tests in test_i02r3b_* document expected behavior for residual review.
```

## 8. Open gaps

- Live authenticated K1 under same model/config as fail class `561bb788` not re-run at this SHA.  
- Real LLM may omit `goal_class` → falls back to two calls (no worse than baseline).  
- Native multi-group short-circuit still not authorized.  
- Independent coordination review required before I02 accept.

```text
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
