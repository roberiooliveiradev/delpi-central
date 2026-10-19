# 50 — Semantic argument and task-outcome rework

**DATE:** 2026-10-19  
**TASK_ID:** `DELIA-C3-SEMANTIC-ARGUMENT-AND-TASK-OUTCOME-REWORK-01`  
**BASE_HEAD:** `13453414405e9eda7e7894ce5211e810da6e49e3`  
**REUSE:** `EXISTING_EQUIVALENT=YES` / `REUSE_DECISION=EXTEND`  
(no new planner; remove heuristic argument recovery)

## 1. User reproduction (pre-patch)

> Liste 2 exemplos de terminal pino.  
> → «Para continuar com «liste 2…», preciso de mais um detalhe (código, filtro ou escopo)»

That ask invents owner requirements the contract did not prove.

## 2. Root causes (PROVEN)

| ID | Cause |
|---|---|
| `ROOT_CAUSE_ARGUMENTS` | `_recover_stated_arguments_from_input` + `_STATED_QUANTITY_RE` / field-name hints — linguistic heuristic (doc 49 REWORK) |
| `ROOT_CAUSE_CLARIFICATION` | `_clarification_content` quoted the user request and invented «código, filtro ou escopo» |
| `ROOT_CAUSE_BUDGET` | `skip_budget_identifier_required` turned optional-index budget skip into a user clarification for invented mandatory fields |
| `ROOT_CAUSE_ADMISSION` | Admission treated many «liste N exemplos…» as ambiguous/operational → owner path under load |

## 3. Correction

| Change | Behavior |
|---|---|
| Remove stated-argument recovery helpers | LLM proposes args; schema validates |
| Clarification fallback | No quote + no invented código/filtro/escopo |
| Budget skip of optional identifiers | `SOURCE_UNAVAILABLE` / `turn_budget_exhausted` (honest), not fake ask |
| Admission instruction | Illustrative examples without cadastrados/reais/DELPI catalog → `hypothetical` / no owner surface |

## 4. Tests

| Suite | Result |
|---|---|
| SEMARG-T* | **PASS** |
| SEM/CONV/i02r2 headroom updates | **PASS** |
| Full `delia-api` pytest | see execution |

## 5. Live (post-deploy)

Filled after production verification.

## 6. Phase gates (unchanged)

```text
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
Q01_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
