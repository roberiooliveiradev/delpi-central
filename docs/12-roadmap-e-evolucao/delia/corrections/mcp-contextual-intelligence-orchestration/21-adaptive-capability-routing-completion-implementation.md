# 21 — Adaptive Capability Routing Completion · Implementation Evidence

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-ADAPTIVE-CAPABILITY-ROUTING-COMPLETION-01`  
**BASE_HEAD:** `37c908cf1d60db8c8486f8d33ad8cf3f7fbb9082`  
**AUTHORITIES:** [14](./14-i02r3-independent-diagnostic-review-and-architecture-decision.md)–[20](./20-i02r3b-independent-live-outcome-review.md); docs 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25  
**EXISTING_EQUIVALENT:** `YES` — `OperationalCapabilityOrchestrator` + `select_decision_path` + R3-B typed merge  
**REUSE_DECISION:** `EXTEND` (no second planner/engine/registry)  
**I02_ACCEPTED:** `NO` (not auto-advanced)  
**VERDICT:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Scope delivered (bounded A–D)

| Slice | Change | Safety gate |
|---|---|---|
| **A FAST** | Telemetry via existing `select_decision_path` when surface is singleton + native + no discovery + closed schema; **no** singleton auto-select of applicability (model validation preserved) | Unsafe FAST force-select reverted after metamorphic/NOT_APPLICABLE regressions |
| **B OPERATIONAL + native** | R3-B typed capability+goal preserved; native assessment skipped **only** when non-write + `comparison_requested` already declared (forces corroborate). Write targets still assess (enrichment may apply). **Prohibited** `READ ⇒ SKIP_NATIVE_ASSESSMENT` | Foreign / corroboration / multi-owner gates kept |
| **C Arguments** | `_deterministic_arguments_from_schema` before model when const/single-enum/optional-default cover material keys; opaque TEO schemas remain `MODEL_REQUIRED` | No invented ids; no parallel MCP vocabulary |
| **D K2/K3 quality** | Thin prior-continuation expands extraction lists from prior excerpts (≥3, cue match, not limitation ask); index options ranked by lexical overlap before model select; log `topic=` | Grounding preserved; limitations follow-up not expanded |

## 2. Invariants preserved

```text
MODEL_OUTPUT != FACT
MCP_METADATA != AUTHORIZATION
DISCOVERY != APPROVAL
READ != WRITE
PREPARE != ACT
MESSAGE != ACT
GLOBAL_TURN_BUDGET_SECONDS=30
STAGE_CAP_10S_PRODUCTION=OFF
ARGUMENTS_HEADROOM_PRODUCTION_DEFAULT=OFF
```

## 3. Synthetic / regression evidence

| Suite | Result |
|---|---|
| `tests/test_adaptive_capability_routing_completion.py` | PASS |
| I01 / I02 / R2 / R3 / R3A / R3B regressions | PASS |
| Full `delia-api` pytest | PASS |
| Provider rename / non-MCP / multi-owner / WRITE ambiguous / foreign / injection / missing inputs / budget 30 / ACT=0 | Covered by existing + completion suites (PASS) |

## 4. Live evaluation

Live authenticated K1/K2/K3 against the **deployed** SHA containing this completion is recorded after push/deploy. Until that SHA is proven in `delpi-delia-api`:

```text
LIVE_EVAL_AT_IMPLEMENTATION_CUT=PENDING_DEPLOY
HISTORICAL_R3B_LIVE_BASELINE=doc19 (K1 21469ms; K2 48 chars; K3 topic PARTIAL)
```

Post-deploy results (fill after eval):

| Case | Result | Notes |
|---|---|---|
| K1 TÉO | _pending_ | Preserve typed merge + grounded methodology |
| K2 continuity | _pending_ | Expect content_len ≫ 48 when extraction expand fires |
| K3 VISTA | _pending_ | Expect ranked index + logged topic |

## 5. Contract impact

```text
PUBLIC_OPENAPI=NONE
HTTP_DTO=NONE
NEW_PLANNER=NO
NEW_ENGINE=NO
NEW_REGISTRY=NO
EXPERIMENTAL_FLAGS_DEFAULT=UNCHANGED
```

## 6. Rollback

```text
git revert <IMPLEMENTATION_SHA>
# restores orchestration.py + completion tests + R3B comparison expectation
```

## 7. Decision state

```text
ALGORITHM_COMPLETION=PARTIAL_UNTIL_LIVE_OUTCOMES
FAST_PATH=TELEMETRY_SAFE_NO_AUTO_SELECT
OPERATIONAL_PATH=R3B_PRESERVED
REASONING_PATH=PRESERVED_ESCALATION
NATIVE_ASSESSMENT=CONDITIONED_COMPARISON_ONLY
DETERMINISTIC_ARGUMENTS=ELIGIBLE_SCHEMAS
CONTINUITY_QUALITY=SYNTHETIC_PASS_LIVE_PENDING
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=DEPLOY_THEN_AUTHENTICATED_LIVE_K1_K2_K3
```
