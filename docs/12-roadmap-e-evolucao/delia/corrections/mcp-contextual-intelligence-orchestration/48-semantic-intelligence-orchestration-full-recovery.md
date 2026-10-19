# 48 — Semantic intelligence orchestration full recovery

**DATE:** 2026-10-19  
**TASK_ID:** `DELIA-C3-SEMANTIC-INTELLIGENCE-ORCHESTRATION-FULL-RECOVERY-01`  
**BASE_HEAD:** `eca913e4f8d75cf12aef1f74c0bc2efb67fc3140`  
**REUSE:** `EXISTING_EQUIVALENT=YES` / `REUSE_DECISION=EXTEND`  
(`OperationalCapabilityOrchestrator` + `_propose` + handler conversational fallback — **no** new planner / intent regex engine)

## 1. Root causes (PROVEN)

| ID | Cause | Evidence |
|---|---|---|
| `COLD_START_ROOT_CAUSE` | Cold greetings ran `select_group` with `DELIA_MODEL_STAGE_TIMEOUT_SECONDS=30` equal to turn budget → ~29s propose → no room for conversational synthesis → HTTP 504 (doc 47) | live A01; prod env |
| `CONVERSATIONAL_ADMISSION_ROOT_CAUSE` | No cheap typed admission before MCP listing / group catalog; conversational turns paid full operational surface cost | `_attempt` order |
| `ARGUMENT_RESOLUTION_ROOT_CAUSE` | Model often returned `missing_inputs` despite subject/quantity already in the user message → generic clarification | ARGUMENTS path + live C01 class |
| `CLARIFICATION_ROOT_CAUSE` | Deterministic fallback “Quais itens…” when model missed stated fields | `_clarification_content` |
| `CONTEXT_CONTINUITY_ROOT_CAUSE` | Admission must **not** short-circuit when `prior_turns` present | SEM-T20 |
| `MODEL_OUTPUT_VALIDATION_ROOT_CAUSE` | (inherited doc 46) applicable=false without companion fields — already fixed | CONV |
| `ACTIVITY_PROJECTION_ROOT_CAUSE` | (inherited doc 46) page-slice `record_count` — already fixed | CONV |
| `ERROR_TAXONOMY_ROOT_CAUSE` | Preserve timeout vs owner unavailable — reserve must not abort mid-turn tight budgets | i02r3 synthetic |

## 2. Minimal correction

| Change | Behavior |
|---|---|
| `interaction_admission` propose (≤6s, no catalog) **before** `_groups` | `requires_owner_surface=false` + conversation/explanation/hypothetical → `NOT_APPLICABLE` without listing owners |
| Cold `select_group` reserve 8s when remaining is still large | Prevents env stage=30 from burning the whole turn on early miss |
| ARGUMENTS instruction: preserve stated subject/quantity | Model guidance only |
| `_recover_stated_arguments_from_input` | Schema-driven fill of search-like free strings + small integer limits from the user message when the model declared them missing — **not** intent keyword routing |
| Admission skipped when `prior_turns` non-empty | Continuity / clarification follow-ups reach selection |

## 3. Tests

| Suite | Result |
|---|---|
| `test_semantic_intelligence_orchestration_recovery.py` (SEM-T*) | **PASS** |
| CONV recovery + related orchestration suites | **PASS** |
| Full `delia-api` pytest | **PASS** |

## 4. Live (to be filled after deploy)

```text
HOST=operador@192.168.1.237
SERVICE=delpi-delia-api
DEPLOY=./infra/scripts/up-prod-sequential.sh --pull --build delia-api
MODEL_ID=moonshotai/kimi-k3
```

Live matrix A–F outcomes: see follow-up section after production verification.

## 5. Phase gates (unchanged)

```text
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
Q01_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
