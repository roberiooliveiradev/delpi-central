# E9.S12.D — DELETE registry `routeSegment`; inferência OpenAPI

**Status:** ATENDIDO  
**Data:** 2026-09-10  
**Autorização:** «continuar as alterações e limpeza dos jsons»

## Feito

| Antes | Depois |
|-------|--------|
| `route.routeSegment` em 23 rotas do registry | **DELETE** |
| `routes_by_segment` / refinement map leem JSON | `RouteSegmentInferenceService` via `operationIds` → `openapi_operation_id_inventory` path-tail |
| Continuity keys (`open-orders`, `inbound-invoice`, …) | Normalização de path (`sales/open-orders`, `*-items`, collection `/products/directives/{id}`) |
| Virtual department KPI com markers em `operationIds` | `operationIds=[]`; markers só em path/operationIdMarkers (residual S12.C) |

## KEEP (fora desta fatia)

- `operational_follow_up_routing.json` `followUpTypes.*.routeSegment`
- `dateInheritance.routeSegments`
- Metadata de sessão `activeQuery.routeSegment` (runtime, não JSON de rota)

## Aceite

- DOCIE lint OK
- Paridade 23/23 continuity keys vs JSON pré-delete
- Positive: `guide` / `stock` / `open-orders` / `inbound-invoice`
- Sibling: `shipping-status` derivado sem campo legado
- Negative: `structure/exclusivity` **não** polui índice `structure`
- pytest: registry + selection + inference + refinement

## Evidência de código

- `app/domain/services/route_segment_inference_service.py`
- `cleanupMeta.routeSegmentDeletedAt=E9.S12.D`
- `tests/unit/domain/services/test_route_segment_inference_service.py`

## Ainda residual (Onda H)

- Turn Understanding heuristics / cutover (plano-02)
