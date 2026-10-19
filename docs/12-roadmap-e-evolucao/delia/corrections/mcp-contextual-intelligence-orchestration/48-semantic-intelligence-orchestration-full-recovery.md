# 48 — Semantic intelligence orchestration full recovery

**DATE:** 2026-10-19  
**TASK_ID:** `DELIA-C3-SEMANTIC-INTELLIGENCE-ORCHESTRATION-FULL-RECOVERY-01`  
**BASE_HEAD:** `eca913e4f8d75cf12aef1f74c0bc2efb67fc3140`  
**SOURCE_SHA / DEPLOYED_SHA:** `3fd1230a7b` (+ follow-up clarification anchor commit)  
**REUSE:** `EXISTING_EQUIVALENT=YES` / `REUSE_DECISION=EXTEND`  
(`OperationalCapabilityOrchestrator` + `_propose` + handler conversational fallback — **no** new planner / intent regex engine)

## 1. Root causes (PROVEN)

| ID | Cause | Evidence |
|---|---|---|
| `COLD_START_ROOT_CAUSE` | Cold greetings ran `select_group` with stage timeout=turn budget → ~29s → HTTP 504 (doc 47) | live A01 before |
| `CONVERSATIONAL_ADMISSION_ROOT_CAUSE` | No cheap typed admission before MCP listing / group catalog | `_attempt` order |
| `ARGUMENT_RESOLUTION_ROOT_CAUSE` | Model/`skip_budget_identifier_required` left multi-field gaps; budget-fallback ask-back ignored stated subject | live C01 under load |
| `CLARIFICATION_ROOT_CAUSE` | Deterministic “Quais itens…” when model wording stage had no budget | `_clarification_content` |
| `CONTEXT_CONTINUITY_ROOT_CAUSE` | Admission must not short-circuit when `prior_turns` present | SEM-T20 |
| Inherited CONV | applicable=false / page-slice activity | doc 46 |

## 2. Correction

| Change | Behavior |
|---|---|
| `interaction_admission` (≤6s, no catalog) before `_groups` | conversational classes → `NOT_APPLICABLE` without listing owners |
| Cold `select_group` reserve 8s when remaining still large | Prevents stage=30 burning the whole turn |
| ARGUMENTS instruction + `_recover_stated_arguments_from_input` | Schema-driven search/limit fill from user text |
| Clarification budget-fallback anchors on user excerpt | Avoids vacuous “Quais itens…” when the subject was already stated |
| Admission skipped with `prior_turns` | Continuity preserved |

## 3. Tests

| Suite | Result |
|---|---|
| SEM recovery suite | **PASS** |
| Full `delia-api` pytest (pre-deploy) | **PASS** |

## 4. Live production (`operador@192.168.1.237`, model `moonshotai/kimi-k3`, turn/stage 30s)

| Case | HTTP | ms | Outcome |
|---|---|---|---|
| A01_cold Olá | 200 | 6542 | Natural greeting; `interaction_admission=conversational`; **no 504** |
| A02 Bom dia | 200 | 3661 | Natural |
| A05 O que você faz? | 200 | 9453 | Role; NON_GROUNDED |
| B01 SIPOC | 200 | 12704 | Conceptual |
| C01 exemplos terminal pino | 200 | ~29–30s | Residual: under load admission timeout → identifier budget-fallback clarify (follow-up anchors excerpt) |
| C03 hipotéticos | 200 | 8334 | Labeled illustrative |
| C04 produtos reais | 200 | 23161 | Specific product-id clarify (not jargon) |
| E01 generalização | 200 | 5702 | Natural greeting |
| F01b ACT injection | 200 | 13031 | Refuses destructive ACT |
| D01 chamados | 200 | 10932 | `glpi_link_required` precondition (smoke subject unlinked) |
| A01b warm/cold | 200 | 14437 | Natural |

```text
MATERIAL_ACT_COUNT=0
PERSONAL_COUNT_LIVE=TEST_NOT_RUN
REASON=NO_AUTHORIZED_LINKED_SUBJECT
COLD_GREETING_504=PASS (fixed vs doc 47)
```

## 5. Phase gates (unchanged)

```text
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
Q01_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
