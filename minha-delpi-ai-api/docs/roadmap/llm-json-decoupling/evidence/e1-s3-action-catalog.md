# E1.S3 — Action Catalog suficiente (evidência)

**Status:** `PASS` (2026-09-10)  
**Onda:** B (plano 01)  
**Harness:** `tests/unit/application/services/test_e1_s3_registry_family_topk_retrieval.py` (9 passed)

## Veredito

```text
ACTION_CATALOG_FIELDS_PRESENT = PASS
RETRIEVAL_SCORING_USES_CATALOG = PASS
UNKNOWN_OPENAPI_IN_RETRIEVAL_UNIT = PASS
REGISTRY_FAMILY_TOPK_WITHOUT_MARKERS = PASS
METAMORPHIC_PATH_OPERATION_RENAME = PASS
NEGATIVE_DISTRACTOR = PASS
RESIDUAL_MARKER_FILTERS = DEFERRED_E1_S4
E1.S3_READY_TO_PASS = YES
```

## Cobertura do harness

| Case | Mensagem (família) | Esperado |
|------|--------------------|----------|
| product_search | liste top 50 terminais pino | `acme.products.search` ∈ top-K |
| product_stock | estoque do produto | `acme.products.stock` |
| product_description | descrição do produto | `acme.products.description` |
| production | agenda de produção hoje | `acme.production.schedule` |
| kpi_scalar | receita consolidada filial | `acme.kpi.site-revenue` |
| sibling | receita por filial ranking | `acme.kpi.revenue-by-site` #1 |
| negative | remessa tracking | não força product_search |
| metamorphic | path/operationId/actionId rename | recall preservado |
| guard | catálogo sem pathMarkers | PASS |

Catálogo sintético: prose OpenAPI apenas — **zero** `pathMarkers` / `operationIdMarkers` / `routeSegment`.

## Residual (não bloqueia E1.S3)

Autoridade residual em runtime (`select_registry_route_id` com markers; product `intent+route_segment`) → **E1.S4 shadow**, não invalida suficiência do catálogo para retrieval.

Ver inventário: [`onda-a-inventory.md`](./onda-a-inventory.md).
