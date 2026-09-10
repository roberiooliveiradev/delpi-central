# E5.S6 — Entity enrichment cutover

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** E (plano 05)  
**Owner:** `ChatGroundedEnrichPlanningService` + `ChatEntityCapabilityCatalogService`  
**Harness:** `tests/unit/domain/services/test_e5_s6_entity_enrichment_cutover.py`

## Veredito

```text
NO_FIXED_ROUTE_MAP_REQUIRED = PASS
SEMANTIC_ENRICH_GOALS = PASS
BUDGET_CAPS_FAST_NORMAL_THINKER = PASS
UNKNOWN_ENTITY_DEFAULT_GOALS = PASS
MIXED_GOALS_DEDUPE = PASS
SCOPE_TO_ROUTE_JSON = deprecated observer (DELETE → E5.S7)
```

## Antes → depois

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Quais scopes enrich | `artifactToEnrichKey` + `enrichInsightScopes` | `semanticGoals.enrichByArtifact` (goals + queryHints) |
| `scopeToRouteId` | DEAD + não authority | `enrichMapsDeprecated` observer |
| Caps | `enrichInsightLimitsByMode` | **mantidos** (fast 2 / normal 4 / thinker 6) |
| Multi-scope `_SCOPE_TO_ROUTE` | LIVE (mensagem explícita) | **fora do cutover** (irmão; não E5.S6) |
| Pós-wave gap | E5.S4 coverage retry | inalterado |

## Aceite dos testes

| Caso | Resultado |
|------|-----------|
| Product (structure) | goals stock+profile; `reason=grounded_enrich_insight_goal_driven` |
| Unknown entity/API | group `default` → profile; sem depender de route map |
| Max routes | fast=2, thinker=6 |
| Mixed goals | stock+sales; actionIds deduplicados; ≤ max_calls |

## Não feito (proposital)

- DELETE de `scopeToRouteId` / `enrichInsightScopes` / `artifactToEnrichKey` → **E5.S7**
- Cutover de `_SCOPE_TO_ROUTE` multi-scope → fora do menor escopo
- Critic `followUpRouteIds` → irmão

## Próximo

**E5.S7** — cleanup: remover maps mortos; docs/help; só policies de budget.
