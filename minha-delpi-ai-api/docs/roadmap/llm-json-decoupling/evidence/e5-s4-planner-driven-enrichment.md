# E5.S4 — Planner-driven enrichment

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** E (plano 05)  
**Owner:** `ChatGoalCoverageRetryService.plan_follow_ups`  
**Wiring:** `ChatToolContextService._maybe_apply_goal_coverage_retry`  
**Harness:** `tests/unit/domain/services/test_e5_s4_planner_driven_enrichment.py` (+ regressão retry)

## Veredito

```text
EXTRA_NECESSARY = PASS (mismatch → allowed action)
EXTRA_UNNECESSARY = PASS (fulfilled / partial → [])
MAX_BUDGET = PASS (remaining_slots ∩ maxRetryActionsPerTurn)
DUPLICATE_ACTION_SUPPRESSION = PASS
ALLOWED_ONLY = PASS (não amplia permissions)
NO_ENTITY_LIST_FANOUT = PASS (sem maps neste path)
```

## Comportamento

| Caso | Resultado |
|------|-----------|
| Goal `mismatch`/`pending` + allowed restante | propõe follow-up com `enrichmentReason=goal_coverage_gap` + `uncoveredGoalIds/Statuses` |
| Goal `fulfilled` | sem extra |
| Goal `partial` (paginação) | sem auto-enrich (dados já cobrem o goal; truncamento ≠ gap) |
| `remaining_slots=0` ou fora de allowlist | sem extra |
| actionId já tentado | excluído |

Maps `enrichInsightScopes` / critic `followUpRouteIds` **permanecem** (cutover = E5.S5–S6). Este path é o enrichment planner-driven canônico pós-wave1.

## Content

`openapi_tool_routing.goalCoverage.maxRetryActionsPerTurn` = `2`

## Próximo

**E5.S5** — department composition cutover (primary/compose → goals + retrieval).
