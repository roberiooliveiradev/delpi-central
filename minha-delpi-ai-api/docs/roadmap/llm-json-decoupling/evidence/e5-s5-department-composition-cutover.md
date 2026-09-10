# E5.S5 — Department composition cutover

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** E (plano 05)  
**Owner:** `ChatDepartmentMetaCompositionPlanningService.plan_goal_driven`  
**Wiring:** `ChatExternalActionOrchestrationService._enrich_openapi_plan_with_department_meta`  
**Harness:** `tests/unit/domain/services/test_e5_s5_department_composition_cutover.py`

## Veredito

```text
NO_FIXED_ROUTE_MAP_REQUIRED = PASS
SEMANTIC_GOALS = PASS
RETRIEVAL_AMONG_ALLOWED = PASS
FINANCIAL_COMMERCIAL_QUALITY_PRODUCTION = PASS
PROVIDER_PATH_RENAME = PASS
TAXONOMY_DEPARTMENT_IDD = PASS (mantida)
ROUTE_MAPS_DEPRECATED = PASS (DELETE → E5.S7)
```

## Antes → depois

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Authority | `primaryRouteId` / `composeRouteIds` (DEAD `.plan`) | `semanticGoals` + Action Catalog (`whenToUse`/hints) |
| Runtime | tool_count freeze 0 (E5.S2) | LIVE via orchestration enrich/fallback |
| Path rename | quebraria routeId/registry | seleciona por semântica (`acme.dept.meta_panel` + path `/v2/...`) |
| Taxonomia dept | `department_idd` | inalterada |

## Famílias cobertas

`financial` / `commercial` / `quality` / `production` — compose ≥2 actions (indicators + IDD + flagship KPI hint), sem `routeId` nos arguments.

## Não feito (proposital)

- DELETE de `byDepartment.*.primaryRouteId/composeRouteIds` → **E5.S7**
- Cutover de entity `scopeToRouteId` / enrich maps → **E5.S6**

## Próximo

**E5.S6** — entity enrichment cutover (retirar scope→route maps quando goal coverage cobrir).
