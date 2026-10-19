# 46 — Conversational intelligence and orchestration recovery

**DATE:** 2026-10-19  
**TASK_ID:** `DELIA-C3-CONVERSATIONAL-INTELLIGENCE-AND-ORCHESTRATION-RECOVERY-01`  
**BASE_HEAD:** `b69d2359f7dd552226b150e6d1f46d1647d1583c`  
**REUSE:** `EXISTING_EQUIVALENT=YES` / `REUSE_DECISION=EXTEND` (`OperationalCapabilityOrchestrator` + `HandleInteractiveConversationTurn` + activity projection + interaction instruction v5)

## 1. Live baseline (before)

| Case | Outcome |
|---|---|
| A01 Olá | `select_group=none` → R1 `CLARIFICATION_REQUIRED` (“capability…”) ~3.4s |
| A05 O que você faz? | DAVI discovery miss ~18s |
| B01 SIPOC | TÉO methodology dump |
| C04 hipotético | same capability clarification as A01 |
| Activity | `record_count=N` → UI “N registro(s) localizado(s)” even for `has_more=True` pages |

## 2. Root causes (PROVEN)

1. **Conversational degradation:** R1 mapped every model-backed `select_target=None` to `CLARIFICATION_REQUIRED`, including group/capability `applicable=false` (greetings, hypothetics). That blocked the handler’s legitimate conversational fallback.
2. **InvokeModel:** `expected_fields` rejected `{"applicable": false}` without `remote_name`, turning honest not-applicable into proposal `None` → inconclusive clarify.
3. **Activity “10 registros”:** `_activity_outcome_summary` set `record_count=len(records)` for incomplete page slices (`has_more=True`); frontend rendered that as “localizado(s)”.

## 3. Minimal correction

| Change | Behavior |
|---|---|
| Tagged selection (`not_applicable` / `inconclusive` / `selected`) | `applicable=false` → `NOT_APPLICABLE` → conversational model; invented/invalid remote → clarify |
| Group selection instruction | Explicit: greetings / role / general concept / hypothetical → applicable false |
| InvokeModel + `_propose` | Accept applicable=false without companion ids |
| Clarification copy | No “capability” jargon |
| `_activity_outcome_summary` | Omit `record_count` when `has_more is True` |
| Interaction instruction v5 | Natural greetings; label hypotheticals |

Coverage inquiry + sole DISCOVERY recovery (R2) still runs before conversational not_applicable.

## 4. Tests

| Suite | Result |
|---|---|
| CONV recovery suite | **PASS** |
| R1/R2/R4/R5 / full `delia-api` pytest | **PASS** |

## 5. Phase gates (unchanged)

```text
I03_ACCEPTED=YES_WITH_RESIDUAL
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
Q01_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
