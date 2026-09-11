# E11.S5 — Registry/operationIds sem autoridade de routing

**Status:** COMPLETE_GATE  
**Cobre:** RQ11-04 (RQ11-11 parcial: unit unknown + metamorphic; live final em E11.S9)

## CUTOVER

- `select_registry_route_id` / `_select_registry_route_via_openapi`: **sempre** OpenAPI-first no allowlist completo (`cutover=True`); `operationIds`/markers só shadow/telemetry.
- `OperationalRouteActionResolverService.resolve_route_action`: preferred `operationIds` = soft first-pass; miss → allowlist completo + affinity por continuity facets (sem hard filter `operation_id in set`).
- Grounded path eligibility e playbook readiness: facets / route id quando catálogo técnico não é authority.
- Registry `cleanupMeta.operationIdsRuntimeAuthority=false` + `operationIdsRole=observer`.
- Gate `SEMANTIC_TECHNICAL_OPERATION_ID_CATALOG` full-tree: **0** (authority runtime removida; arrays observer não contam).

## GENERALIZAÇÃO (unit)

| Caso | Resultado |
|---|---|
| known route + empty operationIds + full allowlist | PASS (`test_select_registry_route_id_never_narrows_*`) |
| sibling facet structure vs stock | PASS |
| unknown vendorx API sem registry ops | PASS |
| metamorphic rename operationId + legacy preferred miss | PASS (fallback allowlist + facet) |
| e1_s6b cutover corpus | PASS |

## CLEANUP parcial

- Removido ramo `cutover=false` que estreitava `matched_ids`.
- Lint autoTierC aceita metadata semântica sem markers.
- Arrays `route.operationIds` **mantidos como observer** (cobertura CI / soft prefer) até DELETE em E11.S10 quando sem consumer legítimo.

## Residual

- Observer arrays ainda no JSON (não authority).
- Soft pathMarkers/operationIdMarkers residual em resolver quando presentes (rotas virtuais KPI).
- RQ11-11 live unknown API: E11.S9 candidate.
