# 15 — I02-R3A · Controlled Budget and Critical-Path Experiments

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-MCP-I02-R3A-BUDGET-AND-CRITICAL-PATH-EXPERIMENTS-01`  
**BASE_HEAD:** `1b2d6a6662b7d0557231b15211bf9c9fa4ee553a`  
**DECISION AUTHORITY:** [14 — independent diagnostic + architecture direction](./14-i02r3-independent-diagnostic-review-and-architecture-decision.md) (**not redefined**)  
**MODE:** synthetic controlled experiments + characterization; **no** production default change; **no** deploy of experimental stage-cap/guard  
**I02_ACCEPTED:** `NO`  
**PERFORMANCE_FIX_PRODUCTION:** `NO`

## 1. Method

| Layer | What was measured |
|---|---|
| **SYNTHETIC** | Fake clock + fake model + synthetic multi-group TEO-like surface (`test_i02r3a_budget_and_critical_path_experiments.py`) |
| **LIVE_MODEL / LIVE_AUTH** | Experimental variants **not** deployed; baseline fail class reused from docs 13/14 (`561bb788-…`) |
| **HISTORICAL** | K1 success `daccc948-…` (doc 07) — STALE for re-log |

Variants compared **individually** (no combination scoring):

| ID | Variant | Production default? |
|---|---|---|
| E0 | Baseline: stage_timeout override 30 (live-like) / guard OFF | guard OFF = production |
| E1 | Stage cap 10 experimental | code default 10; **runtime env may be 30** — experiment does not change env |
| E2 | `experimental_arguments_budget_guard=True` (opt-in) | **OFF** in composer |
| E3 | Typed selection candidate | characterization only |
| E4 | Native short-circuit candidate | characterization only |
| E5 | Deterministic arguments classes | characterization only |

Headroom formula (E2, derived from existing caps only):

```text
required = model_stage_timeout_seconds + MIN_VIABLE_MODEL_STAGE_SECONDS * 3
# e.g. 10 + 6 = 16s
```

Opt-in constructor flag (default `False`):

```text
OperationalCapabilityOrchestrator(..., experimental_arguments_budget_guard=False)
```

Composer **does not** pass the flag → production path unchanged.

## 2. Baseline (E0)

### Synthetic success (stages fit under 30s)

```text
MODEL_CALL_COUNT≥5 (group, capability, goal, native, arguments [+synthesis])
OWNER: get_catalog → get_methodology_guide
TASK_SUCCESS=YES
```

### Synthetic fail class (remaining≈3s after early spend, arguments timeout)

```text
OWNER: get_catalog only
ARGUMENTS_MODEL_STARTED=YES
METHODOLOGY_READ=NO
error_code ∈ {model_timeout, turn_budget_exhausted}
TASK_SUCCESS=NO
```

### Historical live fail (doc 13/14) — not re-run as experiment

| Stage | ms |
|---|---:|
| select_group | 2284 |
| select_capability | 14778 |
| turn_goal | 7021 |
| native_assessment | 2398 |
| get_catalog | 151 |
| arguments | 3015 → timeout |
| **TOTAL** | **~30016** |

```text
K1_TIMEOUT_EXACT_STAGE=arguments (PROVEN prior)
METHODOLOGY_READ_REACHED=NO
```

## 3. Results by experiment

### E1 — Stage timeout 10 vs 30

| Scenario | Result | Classification |
|---|---|---|
| Cap=10, capability stage times out at stage bound | Fail **before** DISCOVERY; methodology never reached | **Earlier failure**, not task improvement |
| Cap=10, all stages finish under 10s | SUCCESS (same as healthy E0) | Cap does not block healthy path |
| Cap=30, arguments doomed at ~3s remaining | TIMEOUT on arguments (baseline fail) | Unchanged class |

**Answer to coordination Q1:** A blanket stage cap of 10s **does not** improve K1 task completion for the proven fail class (budget already consumed by sum of stages). It **anticipates** failure when a single stage (e.g. select_capability ~15s live) exceeds the cap — converting a late arguments timeout into an earlier capability timeout. Per doc 14: **not** a proven production remedy. `STAGE_CAP_10S_PRODUCTION_APPROVAL` remains **NO**.

P50/P95: **INCONCLUSIVE** (synthetic n=1 per cell; live experimental n=0).

### E2 — Pre-arguments headroom (opt-in)

| Scenario | Guard | Arguments model | Methodology READ | Outcome class |
|---|---|---|---|---|
| remaining≈3s | OFF | started → timeout | NO | opaque model_timeout |
| remaining≈3s | ON | **not started** | NO | clarify / source_unavailable (**honest limitation**) |
| remaining ample | ON | started | YES | SUCCESS |

**Answer Q2:** Justified headroom under stage_timeout=10: **≥ 16s** (`10 + MIN_VIABLE*3`). With runtime stage_timeout=30, the same formula yields 36s (> global 30) ⇒ guard would skip **all** arguments model calls — **REJECT** enabling under stage_timeout=30 without first aligning stage cap. Skip ≠ grounded success.

### E3 — Typed selection (capability + goal)

| Item | Finding |
|---|---|
| Current | Separate `_select_capability` + `_understand_goal` proposals |
| Candidate fields | goal_class, remote_name, subject, comparison_requested, prior_evidence_sufficient |
| Estimated Δ calls | −1 **if** approved |
| Write-gate | Must stay independent — **ARCHITECTURE_DECISION_REQUIRED** before merge |
| Implemented? | **NO** |

### E4 — Native assessment

| Item | Finding |
|---|---|
| Already skipped | `len(groups)==1` (PROVEN) |
| Live multi-MCP | Always runs (~1.8–5s) |
| Safe skip candidate | READ ∧ ¬comparison ∧ ¬foreign — **not proven**; foreign_required/corroboration holdouts required |
| Implemented bypass? | **NO** |

### E5 — Deterministic arguments

| Scenario | Class |
|---|---|
| Empty schema / no non-orchestrated keys | `DETERMINISTIC_SAFE` (existing `{}` path) |
| Opaque `context: object` (TÉO methodology) | `MODEL_REQUIRED` |
| Free-string / invented id | `CLARIFICATION_REQUIRED` |
| Ambiguous multi-enum without evidence | `CLARIFICATION_REQUIRED` / `OWNER_CONTRACT_GAP` |

No local vocabulary registry created.

## 4. Comparative matrix (synthetic)

| Variant | MODEL_CALLS (typ.) | METHODOLOGY_READ | TASK_SUCCESS | Notes |
|---|---:|---|---|---|
| E0 success | ≥5 | YES | YES | Control healthy |
| E0 fail | ≥5 (args fails) | NO | NO | Baseline problem |
| E1 long-cap kill | ≤2 | NO | NO | Earlier fail |
| E1 fit | ≥5 | YES | YES | Cap ok if stages short |
| E2 skip | 4 (no args) | NO | NO | Honest skip |
| E2 sufficient | ≥5 | YES | YES | Guard non-blocking |
| E3–E5 | n/a merge | — | — | Analysis only |

```text
MODEL_CALL_COUNT_BASELINE (success path) = 5 pre-READ model purposes (+ synthesis)
MODEL_CALL_COUNT_BEST_CANDIDATE_FOR_FAIL_CLASS = 4 (E2 skip; still TASK_SUCCESS=NO)
PRE_OWNER_LATENCY: synthetic wall-clock under fake advances — not live p95
TASK_SUCCESS_RATE: n too small for rate statistics → report per-scenario only
```

**Decisive metric (doc 14):** task completion with authority — **no variant yet yields K1 methodology READ under the live fail budget profile**. E2 only improves **honesty** of failure.

## 5. Holdouts

| Holdout | Result |
|---|---|
| MESSAGE≠ACT on E2 skip | PASS |
| Renamed non-MCP provider + guard ON sufficient | PASS |
| Catalog prompt injection | PASS (ACT=0) |
| K2 continuity default path | PASS (no ACT; continuity semantics preserved) |
| VISTA R2 index→topic→guidance | PASS |
| Foreign-required still invokes native | PASS (characterization) |
| Full `delia-api` pytest | PASS |
| I01/I02/R2/R3 characterization regression | PASS |

```text
MATERIAL_ACT_COUNT=0
SECURITY_RESULT=PASS (synthetic holdouts)
GENERALIZATION_RESULT=PASS (renamed provider)
K4_DAVI=TEST_NOT_RUN (out of R3A implementation scope; characterization deferred)
LIVE_EXPERIMENTAL_VARIANTS=TEST_NOT_RUN (no unauthorized production policy deploy)
```

## 6. Answers to coordination (§16)

1. **Stage cap 10:** anticipates failures on long stages; does **not** raise K1 completion under the proven sequential-sum fail class.  
2. **Headroom:** `stage + MIN_VIABLE*3` (16s @ stage=10). Do not enable under stage=30 without cap alignment.  
3. **Eliminable safely today:** none of group/capability/goal/native/arguments on multi-MCP TEO path without R3-B gate. Empty-schema args already eliminated (E5). Single-group native already eliminated.  
4. **Next investigation (R3-B):** typed goal+capability **or** narrow native skip — each with full safety matrix — **after** budget policy choice.  
5. **Harms:** E1 as sole fix → earlier NOT_APPLICABLE/timeout; E2 under stage=30 → over-skip; E3/E4 without proofs → write/foreign regressions.  
6. **Measured latency reduction:** synthetic only; live fail-class still ~30s without deployable fix that completes READ. E2 saves a doomed ~3s model call but does not complete the user goal.  
7. **Minimal diff recommended for R3-B design gate:** keep opt-in guard code; **do not** flip production default until coordination chooses (a) stage-cap policy + (b) whether honest skip is acceptable UX vs requiring call consolidation. Preferred functional path remains **reducing call count (E3/E4)** not only failing earlier.  
8. **Rollback:** remove/disable `experimental_arguments_budget_guard`; composer never enabled it.  
9. **Gaps:** live A/B of guard+cap on authenticated runtime; token telemetry; p95; K4; independent rerun.

## 7. Recommendation for R3-B (not approval)

```text
RECOMMENDED_R3B_DESIGN=
  1) Decide production stage_timeout vs global 30 (experiment showed 10 alone ≠ completion)
  2) If enabling arguments headroom: only with stage_timeout consistent with formula
  3) Prioritize R3-B call elimination (typed selection and/or native eligibility) with
     dependency maps + foreign/write/injection holdouts before expecting K1 PASS under load

RECOMMENDED_MINIMAL_DIFF_NOW=
  keep experimental_arguments_budget_guard default False (landed for harness only)
  no composer/env change

ROLLBACK_PLAN=
  revert orchestration opt-in flag / leave False forever
```

```text
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=COORDINATION_REVIEW_OF_R3A_EVIDENCE
```
