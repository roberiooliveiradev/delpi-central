# 33 — I04 · Contextual Provider-Neutral Generalization · Implementation Evidence

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-I04-CONTEXTUAL-PROVIDER-NEUTRAL-GENERALIZATION-01`  
**BASE_HEAD:** `2b00c576b940c3dc13b1aeb3396a38e13fd343e5`  
**AUTHORITIES:** [32](./32-i03-independent-nonregression-review-and-acceptance.md), README I04, ledger §6.273  
**EXISTING_EQUIVALENT:** `YES` — `OperationalCapabilityOrchestrator` + `select_decision_path`  
**REUSE_DECISION:** `EXTEND` (one proven arguments-budget defect; no second planner)  
**I04_ACCEPTED:** `NO`  
**VERDICT:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Reuse gate

| Mechanism | Status |
|---|---|
| Orchestrator / typed goal / discovery / index / continuity | REUSE |
| Decision-path FAST/OPERATIONAL/REASONING | REUSE (telemetry) |
| Foreign evidence / corroboration | REUSE (existing LOOP-02 tests + I04 holdout) |
| Specialist-name branches | ABSENT (source hygiene test) |

## 2. Generalization matrix (synthetic)

Suite: `tests/test_i04_provider_neutral_generalization.py`

| Scenario | Result |
|---|---|
| Renamed / non-MCP methodology READ | PASS |
| Capability order independence | PASS |
| Equivalent descriptions without specialist tokens | PASS |
| Discovery search-miss vs absence (HTTP provider) | PASS |
| Index no-match clarification | PASS |
| Continuity invalid-index recovery | PASS |
| Forged history never ACT | PASS |
| Multi-owner comparison | PASS |
| Owner unavailable truthful | PASS |
| Missing inputs clarify | PASS |
| Ambiguous write clarify | PASS |
| FAST / OPERATIONAL / REASONING rules | PASS |
| Singleton opaque schema ≠ auto FAST | PASS |
| Arguments budget → query projection | PASS (new) |

Full `delia-api` pytest **PASS**.

## 3. Defect found in live characterization

**K4 sample (pre-fix):** DAVI `discover_delpi_information` selected; `arguments` hit `budget_too_small` (remaining_ms=52) → `turn_budget_exhausted` → `delpi_source_unverified` without owner invoke.

**ROOT_CAUSE:** `_StageDeadlineExceeded(turn_budget_exhausted)` on arguments propagated as SOURCE_UNAVAILABLE after correct selection.

**FIX:** `_single_free_text_argument_from_input` + catch only `turn_budget_exhausted` in `_build_arguments` → project sole free-string field from user text, else clarify. `model_timeout` remains terminal.

## 4. Live (MESSAGE-only)

| Field | Value |
|---|---|
| MODEL | `moonshotai/kimi-k3` / `openai_compatible` |
| BUDGET / STAGE | 30 / 30 |

### Pre-fix sample (characterization)

| Case | ms | Result |
|---|---|---|
| K1 | 12995 | PASS GROUNDED |
| K2 | 28857 | PASS continuity 5 bullets |
| K3 | 22388 | PASS clarification |
| K4 | 29959 | FAIL budget on arguments |

### Post-fix sample

_(filled after deploy)_

## 5. Direct MCP

`DIRECT_OWNER_TEST_NOT_RUN` from this executor for TÉO/VISTA/DAVI in I04 window; DAVI contract remains as doc 29 (0/95 miss vs catalog).

## 6. Rollback

```text
git revert <IMPLEMENTATION_SHA>
```

## 7. State

```text
I04_ACCEPTED=NO
ALGORITHM_COMPLETION=PARTIAL
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
