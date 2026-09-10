# E4.S5 — Remove action mini-catalog

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** E (plano 04)

## Mudança

```text
ANTES: capability_registry.action.* (+ routeHints mortos) authority no discovery
DEPOIS: Action Catalog → capabilities_from_actions → capabilityId action:<actionId>
        registry só rag/web/skill/transform
```

| Peça | Path |
|------|------|
| Discovery | `ChatCapabilityDiscoveryService.capabilities_from_actions` / `discover(..., action_catalog=)` |
| Wiring | `chat_turn_preparation_service` carrega catalog via `load_action_catalog_for_agent` |
| Planner | `ChatTaskPlannerService` propaga `action_catalog` / `allowed_action_ids` |
| Content | `capability_registry.json` sem `action.*` / `routeHints` |

## Aceite

```text
NO_DUPLICATE_ACTION_REGISTRY = PASS
AUTHORIZED_ONLY_IN_DISCOVERY = PASS
LEGACY_ACTION_STAR_ABSENT = PASS
NON_OPENAPI_REGISTRY_KEPT = PASS
```

## Próximo

Plano **05** (E5.S1 inventário composition) ou Onda F.
