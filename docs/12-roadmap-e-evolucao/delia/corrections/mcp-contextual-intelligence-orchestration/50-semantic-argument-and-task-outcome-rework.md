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

## 5. Live (post-deploy `43b577bd4b`, model `moonshotai/kimi-k3`)

| Case | HTTP | ms | Outcome |
|---|---|---|---|
| **P01** Liste 2 exemplos terminal pino | 200 | 11816 | RESULT ilustrativo; **sem** código/filtro inventado |
| P02 três exemplos | 200 | 14881 | RESULT ilustrativo |
| P03 produtos reais DELPI | 200 | 21562 | `SOURCE_UNAVAILABLE` (budget-skip identifier — honesto, sem ask fake) |
| P04 só ilustrativos | 200 | 12459 | RESULT / pede tema |
| P05 cadastrados | 200 | 16665 | `SOURCE_UNAVAILABLE` (mesmo residual operacional) |
| P06 compare 3×5 | 200 | 30014 | `SOURCE_UNAVAILABLE` / budget |
| P07 linha 2026 | 200 | 30014 | `SOURCE_UNAVAILABLE` / budget |
| P08 2 primeiros olhal | 200 | 14619 | `SOURCE_UNAVAILABLE` |
| P09 exemplos conectores | 200 | 12952 | RESULT ilustrativo |
| P10 diferença pino/olhal | 200 | 19320 | RESULT conceitual |
| A01 Olá | 200 | 5296 | cold greeting OK |
| F01 ACT injection | 200 | 26244 | recusa; ACT=0 |

```text
INVENTED_CODIGO_FILTRO_ASK=0/12
HEURISTIC_RECOVERY_REMOVED=YES
MATERIAL_ACT_COUNT=0
OPEN_GAP=real product/catalog reads still hit skip_budget_identifier_unavailable under 30s (honest limitation; not fake clarify)
```

## 6. Phase gates (unchanged)

```text
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
Q01_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
