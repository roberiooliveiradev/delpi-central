# E4.S1 — Inventário de consumers (capabilities / registry)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** E (plano 04)  
**Fontes:** greps HEAD + `capability_registry.json` (sem migração runtime)

## Veredito

```text
PATHRULES_ZERO_CONSUMERS = PASS
ROUTEHINTS_DEAD = PASS
ACTION_STAR_STILL_AUTHORITY_IN_DISCOVERY = PASS
HELP_ALREADY_ACTION_CATALOG = PASS
NO_RUNTIME_MIGRATION = PASS
```

## pathRules

| Item | Estado |
|------|--------|
| `capabilities.pathRules` / `pathRuleDefault` | Ausentes no JSON; **zero** reads em `app/`/`tests/` `*.py` |
| Hits `pathRules` em Python | Só `presentation_profiles` (outro bundle) + literal `pathRulesVersion` no generator |

R04-02 / E4.S6 permanece **ATENDIDO** — não reabrir.

## Matriz registry vs Action Catalog

| symbol | file | reads | class | E4 |
|--------|------|-------|-------|-----|
| `ChatCapabilityRegistryService` | `chat_capability_registry_service.py` | loader bundle | AUTHORITY | S5 |
| `ChatCapabilityDiscoveryService._score` | `chat_capability_discovery_service.py` | `whenToUse`/`whenNot`/`descriptionForModel` | AUTHORITY | S5 |
| `routeHints` | JSON only | — | **DEAD** | S5 cleanup |
| `readWrite`/`parallelSafe`/`risk` | JSON; sem key-reads | — | DEAD content | S5 |
| `ChatTaskPlannerService` | via discovery | `capabilityId` | AUTHORITY | S4–S5 |
| Turn preparation | via discovery/planner | candidates / task plan | AUTHORITY | S2/S4 |
| `CapabilityUxClassifierService` | import OpenAPI | `uxCapability` | ACTION_CATALOG | S3 |
| `ChatCapabilitiesCatalogAnswerService` | Action Catalog + ux | help | ACTION_CATALOG | S4 (parcial) |
| Composer `includePathRulesFromCapabilities` | `keywordRules` UX | UX | S3/S4 |

## Dívida restante

- `action.product_*` (3) ainda alimentam discovery/TaskPlan.
- Não-OpenAPI (`rag`/`web`/`skill`/`transform`) devem permanecer no registry (R04-01).

## Próximo

**E4.S2** — baseline de capability discovery (+ help Action Catalog).
