# E9.S12.C — registry `operationIds` canônicos; DELETE path markers

**Status:** ATENDIDO  
**Data:** 2026-09-10  
**Autorização:** «siga» após STOP-THE-LINE de limpeza total

## Feito

| Antes | Depois |
|-------|--------|
| `pathMarkers` / `operationIdMarkers` / `excludePathMarkers` / `pathSuffix` / `pathExactEnd` | **DELETE** do JSON |
| Match substring path/op | `route.operationIds` — match **exato** OpenAPI |
| 29 rotas só-path | backfill via `api-delpi/openapi_baseline.json` |
| `resolve_route_action` | authority `operationIds`; pathMarkers só compat (KPI virtual/testes) |
| autoTierC CI | regenerado (412) alinhado à cobertura manual |

## Não removido nesta fatia

- `routeSegment` (refinement/pagination) → **E9.S12.D ATENDIDO**
- `parameters.strategy` / domain `parameterStrategy` → **E9.S12.E ATENDIDO**
- TU heuristics → plano-02

## Evidência

- DOCIE lint OK
- 65 testes registry/selection OK
- `cleanupMeta.pathMarkersDeletedAt=E9.S12.C`

## Runtime

Reiniciar `delpi-minha-delpi-ai-api`.
