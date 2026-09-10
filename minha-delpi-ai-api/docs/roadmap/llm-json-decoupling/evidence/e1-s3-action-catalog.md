# E1.S3 — Action Catalog suficiente (evidência)

**Status:** `GAPS_BLOCKING`  
**Data:** 2026-09-10  
**Onda:** B (plano 01)  
**Não altera runtime.**

## Veredito

```text
ACTION_CATALOG_FIELDS_PRESENT = PASS
RETRIEVAL_SCORING_USES_CATALOG = PASS
UNKNOWN_OPENAPI_IN_RETRIEVAL_UNIT = PASS
REGISTRY_FAMILY_TOPK_WITHOUT_MARKERS = PENDING
RESIDUAL_MARKER_FILTERS = FAIL (documentado)
E1.S3_READY_TO_PASS = NO → GAPS_BLOCKING
```

## O que já está provado

- Import persiste summary/description/tags/params/schemas/sensitivity/embedding (`openapi_action_importer.py` → `ExternalActionModel`).
- `RetrieveActionCandidatesService` ranqueia vector+lexical+schema_token_boost+whenToUse — **sem** `pathMarkers` do registry.
- Unknown OpenAPI (logistics / Nebula / Orion) entra no top-K em unit tests; smoke live opcional.

## Gaps que bloqueiam aceite E1.S3

1. Sem harness top-K das families registry (product search, stock, description, production, KPI) contra catálogo **real** com markers desligados.
2. Residual: `select_registry_route_id` / product `intent+route_segment` ainda preemptam (E1.S4+).
3. `candidateDiscovery.orIlike` em path = acoplamento técnico paralelo.
4. Lexical omite param descriptions — risco se OpenAPI prose for pobre (mitigar no import genérico, não com metadata por endpoint).

## Próximos passos (runtime — autorizar explicitamente)

1. Harness E1.S3: messages × actionId esperado; assert ∈ top-K sem `OperationalRouteRegistryService`.
2. Prova metamorphic: path/operationId rename, summary estável → recall.
3. Se prose pobre: enriquecer embed com param descriptions do OpenAPI.
4. Reduzir `orIlike` path quando `allowed_action_ids` presente.
5. **Não** em E1.S3: cutover de `select_registry_route_id` (E1.S4).

Ver inventário: [`onda-a-inventory.md`](./onda-a-inventory.md).
