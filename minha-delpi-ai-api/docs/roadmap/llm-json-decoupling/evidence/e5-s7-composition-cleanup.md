# E5.S7 — Cleanup composition/enrichment maps

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** E (plano 05)  
**Escopo:** DELETE de maps mortos pós-cutover S5/S6; preservar policies de budget.

## Veredito

```text
DEAD_MAPS_REMOVED = PASS
BUDGET_CAPS_PRESERVED = PASS
GOAL_AUTHORITY_ONLY = PASS
NO_USER_FACING_HELP_DELTA = PASS (mudança interna de routing)
PLANO_05_ACEITE = PASS
```

## Removido

| Artifact | Removido |
|----------|----------|
| `entity_capability_catalog.json` | `scopeToRouteId`, `enrichInsightScopes`, `artifactToEnrichKey`, `domains.*.capabilities`, flags `cutoverEnabled`/`enrichMapsDeprecated` |
| `department_meta_composition.json` | `byDepartment` (`primaryRouteId`/`composeRouteIds`), flags `cutoverEnabled`/`routeMapsDeprecated` |
| `ChatEntityCapabilityCatalogService` | `route_id_for_scope`, `enrich_insight_scopes`, `artifact_enrich_key`, `available` (dependia de domains/routeId), cutover flags |
| `ChatDepartmentMetaCompositionPlanningService` | `route_ids_for_department`, cutover/deprecation observers |

## Preservado (policy legítima)

- `limits.maxExtraRoutesPerTurn` / `maxFanOutKeys`
- `enrichInsightLimitsByMode` (fast/normal/thinker)
- `semanticGoals` (entity + department)
- Taxonomia `department_idd`
- E5.S3/S4 goal coverage + retry
- Multi-scope `_SCOPE_TO_ROUTE` (irmão explícito na mensagem — fora deste DELETE)
- `product_enrichment_composition.composeRouteIds` (planner `.plan` ainda DEAD; anomaly plans LIVE — não misturar)

## Aceite do plano 05

```text
GOAL_COVERAGE = PASS
NO_FIXED_ROUTE_MAP_REQUIRED = PASS
BUDGET_ENFORCEMENT = PASS
UNKNOWN_API_ENRICHMENT = PASS (default goals)
PARTIAL_FAILURE = invariante mantida
```

## Próximo

Onda E **ATENDIDA** no plano 05 → **Onda F** (`planos/06-recommendations-composer-contextual.md`).
