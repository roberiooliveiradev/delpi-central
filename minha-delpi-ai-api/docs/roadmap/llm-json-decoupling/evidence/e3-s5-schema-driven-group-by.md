# E3.S5 — Group-by/refetch sem acoplamento a path

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** D (plano 03)  
**Harness:** `tests/unit/domain/services/test_e3_s5_schema_driven_group_by.py` (+ legado group_by)

## Owner

| Peça | Path |
|------|------|
| Schema-driven planner | `app/domain/services/schema_driven_group_by_refinement_service.py` |
| Identity por actionId | `ChatOperationalGroupByRefinementService.match_route_for_action_id` + `collect_recent_action` |
| Session vs refetch | `ChatOperationalSessionDataRefinementService` (reuso) |
| Vocabulário UX (terms) | `operational_group_by_refinement.json` **por `actionIdDefault`**, não por path |

## Decisão

```text
actionId + OpenAPI group_by.enum  → autoridade de capacidade
vocabulary route (actionId)       → terms/strategy/local fields (UX)
path / operationId                → observabilidade / fallback legado apenas
```

`pathContains` permanece no JSON como fallback quando `actionId` ausente — não é mais a chave primária em `collect_recent_action`.

## Aceite

```text
GROUP_BY_FROM_SCHEMA_ENUM = PASS
ACTION_ID_IDENTITY = PASS
METAMORPHIC_PATH_OPERATION_RENAME = PASS
SESSION_VS_REFETCH = PASS
NO_GROUP_BY_CLARIFY = PASS
DIMENSION_OUTSIDE_ENUM = PASS
LEGACY_TESTS_GREEN = PASS
```

## Próximo

**E3.S6** — pagination/filter fast paths com delta só em params do schema.
