# 38 — Orchestration none-selection and projection remediation (R1 + R3)

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-ORCHESTRATION-NONE-SELECTION-AND-PROJECTION-REMEDIATION-01`  
**AUTHORITIES:** Document 35 (authorized direction); docs 33–34 evidence; docs 21–32 track; ledger §§6.274–6.277  
**MODE:** REUSE `OperationalCapabilityOrchestrator` + interaction handler (`EXTEND`)  
**I03_ACCEPTED:** `YES_WITH_RESIDUAL` (unchanged)  
**C3_EXECUTED:** `NO`  
**C4_AUTHORIZED:** `NO`  
**Q01_AUTHORIZED:** `NO`

## 1. Reanchor

```text
BASE_HEAD_AT_TASK_START≈cb6ae480… (brief) / concurrent I04 landed as 37f4e21229
ORCH_R1_R3_LANDED_IN=37f4e21229 (I04 commit also carried doc-35 R1/R3 orch EXTEND)
THIS_DOC=38 (37 reserved by I04 independent review / §6.278)
LEDGER=§6.279
REUSE_DECISION=EXTEND
EXISTING_EQUIVALENT=YES
```

Document 35 direction preserved: no second planner, no DAVI/TÉO/VISTA hardcode, no auto-select singleton, no new timeout infra, no fake totals.

## 2. Root cause (proven)

### R1 — L02 / L06 → HTTP 504

```text
USER
 → select_group / select_capability_with_goal
 → _select_target returns None
 → GovernedCapabilityAttempt(NOT_APPLICABLE)   # pre-fix
 → HandleInteractiveConversationTurn fallthrough
 → general _invoke (free-form model)
 → TurnDeadline 30s exhausted
 → HTTP 504
```

Caller responsible for the avoidable budget burn: **interaction handler fallthrough** after bare `NOT_APPLICABLE`.  
Owning fix: **orchestrator** returns `CLARIFICATION_REQUIRED` + bounded ask-back when a selection model was present and selection is inconclusive — so the existing write-lifecycle/clarification terminal in the handler ends the turn without a second free-form call.

Bare `NOT_APPLICABLE` (empty surface / no governed path) **keeps** the ordinary conversational fallback when budget remains (doc 35: do not convert every `None` into immediate clarification).

### R3 — L04 “Encontrei N registros”

`_list_header(count)` always said “registros”. Prior-excerpt / methodological continuity lists are not operational records. Fix: `_records_are_prior_excerpts` + outcome-aware `_list_header(..., records=)`.

## 3. Implementation (minimal EXTEND)

| Surface | Change |
|---|---|
| `orchestration.py` | `_SELECTION_INCONCLUSIVE_CONTENT`; on `_select_target is None` + model present → `CLARIFICATION_REQUIRED`; R3 `_records_are_prior_excerpts` / `_list_header` / `_render_synthesis` |
| `handle_interactive_turn.py` | Comment lock: clarification terminal covers R1; bare NOT_APPLICABLE may fall through |
| Tests | `test_r1_r3_none_selection_and_projection.py` T01–T17; expectation updates where model-backed none/invalid now clarifies |

Not created: second planner, registry, DAVI-only branch, new public DTO, new timeout stack.

## 4. Tests

| Gate | Result |
|---|---|
| RED→GREEN R1/R3 T01–T17 | PASS |
| I01 / I02 K2·K3 / I02-R2 / R3A / R3B / I03 / I03 nonreg / Adaptive | PASS |
| Specialist + provider-neutral + I04 matrix | PASS |
| Full `delia-api` pytest | **PASS** |

## 5. Live (authenticated, MESSAGE-only)

**DEPLOYED_SHA / HOST_HEAD:** `ddc3c6f7e4e7b841e6526abb027de5940def54c1` (orch R1/R3 symbols present in running image; landed with I04 EXTEND on `37f4e21229`).  
**MODEL:** `openai_compatible` / `moonshotai/kimi-k3` (same stack as docs 33/36).  
**TURN_BUDGET / STAGE:** 30s / 30s.  
**AUTH:** Keycloak password-grant smoke subject (MESSAGE-only).  
**ACT material:** 0.

| Case | HTTP | ms | Outcome |
|---|---|---|---|
| **L02** terminal bandeira | **200** | 9053 | Clarification ask-back; logs `select_group=none` → `target_selection=none` corr `2f40f7b6-…`. **No 504** (was 30014ms/504 on `9a8775018f`) |
| **L06** DAVI discovery | **200** | 10174 | Clarification; logs `select_capability=none` on `mcp:davi` corr `3243dd19-…`. **No 504** (was 30011ms/504). Task semantic discovery still residual (R2) |
| **L04** K2 checklist | **200** | 27048 | `Recuperei 6 itens da orientação anterior:` — **not** “registros”; `prior_turn_evidence_only` |
| **L03** TÉO K1 | 200 | 15709 | GROUNDED `teo.get_methodology_guide` corr `25f19817-…` |
| **L05** VISTA | 200 | 29083 | Safe clarification (no ACT) |
| **L01** Helpdesk | 200 | 16978 | `helpdesk_read` → `glpi_link_required` / source unverified (precondition; no bypass) |
## 6. Security / governance

- Zero unauthorized ACT in evals.
- No metadata→authorization inference.
- Provider neutrality preserved (no specialist-name branches).
- Global 30s budget preserved; technical timeouts remain `SOURCE_UNAVAILABLE`.

## 7. Residuals

| Residual | State |
|---|---|
| R2 DAVI semantic selection quality | OPEN (not this task) |
| Helpdesk personal count / GLPI link | SEPARATE (§6.271) |
| I04 independent review | PENDING (doc 36) |
| Algorithm completion | PARTIAL |

## 8. Rollback

Revert this task’s commit(s) touching orch selection→clarification, `_list_header` R3, and R1/R3 tests. I04 args-budget projection (doc 36) is independent.

## 9. Next

```text
NEXT=COORDINATION_INDEPENDENT_REVIEW
I03_ACCEPTED=YES_WITH_RESIDUAL
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
Q01_AUTHORIZED=NO
```
