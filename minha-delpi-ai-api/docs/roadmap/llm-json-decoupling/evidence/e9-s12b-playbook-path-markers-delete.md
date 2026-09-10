# E9.S12.B — DELETE `playbookPathMarkers` (+ narrative path families)

**Status:** ATENDIDO  
**Data:** 2026-09-10  
**Autorização:** «limpe todos» — fatia migrável; registry/strategy/TU = STOP-THE-LINE

## Feito

| Surface | Removido | Authority nova |
|---------|----------|----------------|
| `operational_follow_up_routing.json` | `playbookPathMarkers` | `dateInheritance.routeSegments` em `is_playbook_date_route` |
| `operational_narrative_synthesis.json` | `pathMarkers`, `playbookPathMarkers`, `sqlPathMarkers`, `kpiPathMarkers` | entity families (`SQL_PRESENT` / `kpi` / `playbookOperational`) + fallback path mínimo KPI/SQL |

## Antes → depois

| Caso | Antes | Depois |
|------|-------|--------|
| Date inherit factory/shipping path | `playbookPathMarkers` substring | `dateInheritance.routeSegments` |
| Narrative SQL/KPI policy | path marker lists | entity family (+ path token fallback se entity ausente) |
| Follow-up terms | já removido E9.S12.A | intacto |

## STOP-THE-LINE (não deletado)

```text
EXECUTION_DRIFT / SAFE_HOLD
PLAN_SAID: limpar todos residuals gated
CURRENT_EVIDENCE:
  - 29 registry routes só com pathMarkers (sem operationId)
  - resolve_route_action / vocabulary / domain selection ainda AUTHORITY por markers
  - parameterStrategy ainda discriminante do binder
  - TU heuristics ainda shadow-only (E2.S4)
  - preferredRouteId + KPI pathToken = JUSTIFIED (não são DELETE)
INVALIDATED_DECISION: DELETE registry markers / parameters.strategy / TU nesta fatia
AFFECTED_STEPS: E9.S12.C / E9.S12.E / plano-02
SAFE_ACTION: não apagar JSON registry/strategy/heuristics até stop-read + backfill operationIds
```

## Runtime

Reiniciar `delpi-minha-delpi-ai-api` (content `lru_cache`).
