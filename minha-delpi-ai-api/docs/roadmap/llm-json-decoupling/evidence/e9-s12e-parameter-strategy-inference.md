# E9.S12.E — DELETE `parameters.strategy` / `parameterStrategy`

**Status:** ATENDIDO  
**Data:** 2026-09-10

## Feito

| Surface | Ação |
|---------|------|
| `operational_route_registry.json` `parameters.strategy` | **DELETE** (84 rotas) |
| `api_route_domains.json` `domains.*.parameterStrategy` | **DELETE** (22) |
| `ParameterStrategyInferenceService` | authority OpenAPI path/operationId |
| `build_parameters` / affinity / vocabulary | consomem inferência |
| autoTierC | regenerado sem strategy obrigatória |
| `parameterStrategies` catalog | mantido como enum/docs |
| dial `parameterStrategyShadow` | mantido (compare/observability) |

## Aceite

- Inferência = 0 mismatch vs strategies pré-delete (84/84)
- DOCIE lint OK
- Positive product_code / sibling date_branch / negative none

## Ainda residual

- `routeSegment` (E9.S12.D)
- TU heuristics (plano-02)
