# E9.S5 — Canary / default cutover (inventário + rollback)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** H (plano 09)  
**Inventário:** `tests/fixtures/intelligence_baseline/e9_s5_canary_cutover_inventory.json`  
**Harness:** `tests/unit/domain/services/test_e9_s5_canary_cutover_inventory.py`

## Veredito

```text
COHORT_AGENT_CANARY = ABSENT (confirmado)
GLOBAL_CUTOVER_DIALS_INVENTORIED = PASS (11)
FLAG_REVERSIBLE_CONTROLS_EXIST = PASS
NON_REVERSIBLE_EXPLICIT = PASS
NO_FAKE_COHORT_SURFACE = PASS
NO_NEW_DUAL_RUN_SYSTEM = PASS
LIVE_L1_L4 = DEFERRED (aplicável a dials reversíveis; não bloqueia inventário)
```

## Decisão

O plano pedia liberar candidate **quando existir mecanismo canônico** de cohort/agente. Evidência: **não existe** filtro por cohort/userId/agentId; `OpenApiPlannerModeService` ignora `agent_id`.

E9.S5 entrega:

1. inventário dos dials globais (content JSON + env);
2. classificação `flagReversible` vs legado removido / permanente;
3. rollback observável documentado por cutover;
4. gate pytest que impede inventar cohort allowlist.

Não cria canary por cohort ad hoc (seria segunda fonte de verdade sem owner).

## Dials reversíveis (rollback simples)

| id | Dial | Observabilidade |
|----|------|-----------------|
| registrySelectionShadow / productSelectionShadow | `openapi_tool_routing.json` → `cutoverEnabled` | admin registry-selection-shadow |
| followUpRoutingAuthorityShadow | `operational_follow_up_routing.json` → `authorityShadow.cutoverEnabled` | metadata shadow |
| turnUnderstandingShadow | JSON + `CHAT_TURN_UNDERSTANDING_SHADOW` | shadowTurnUnderstanding |
| taskPlannerEnabled | JSON + `CHAT_TASK_PLANNER_ENABLED` (default off) | shadowTaskPlan |
| presentationComposerCanary | `PRESENTATION_COMPOSER_CANARY` / `_SHADOW` | presentationComposer* |

## Sem rollback por flag

parameterStrategy (dispatch permanente), department/entity (legado DELETE E5.S7), recommendation dual-run (sem dial), openapiPlannerMode (sempre on).

## Próximo

**E9.S6** — cleanup gates — **ATENDIDO_PARCIAL** (`e9-s6-cleanup-gates.md`). Próximo: **E9.S7** architecture audit.
