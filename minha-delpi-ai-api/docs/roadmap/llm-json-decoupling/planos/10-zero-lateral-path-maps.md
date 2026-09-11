# Plano 10 — Zero mapa lateral por path/rota

**Prioridade:** P0  
**Status execução:** Onda I · **ATENDIDO** (2026-09-11)  
**Depende de:** Ondas A–H ATENDIDAS (`globalReleasePass=true`)  
**Evidência:** [`../evidence/execution-ledger.md`](../evidence/execution-ledger.md) · [`../evidence/e10-s1-lateral-path-maps-inventory.md`](../evidence/e10-s1-lateral-path-maps-inventory.md)  
**Objetivo perceptível:** nenhuma classificação, hint, factual, enrichment ou response map no `assistant/*.json` usa `pathMarkers` / pathContains / pathToken / pathRules como **mapa lateral** paralelo ao OpenAPI indexado.

## Decisão de produto (2026-09-11)

```text
NENHUM MAPA LATERAL DEVE EXISTIR.
```

## Entrega

| Subetapa | Status |
|---|---|
| E10.S1 inventário + gate | **ATENDIDO** |
| E10.S2 domínio sem pathMarkers | **ATENDIDO** (`ApiRouteDomainInferenceService` + stamp import) |
| E10.S3 factual/sufficiency/enrichment/responses | **ATENDIDO** |
| E10.S4 KPI catalogToken + pathRules DELETE + audit | **ATENDIDO** |
| E10.S5 docs/ledger/residuals | **ATENDIDO** |
| E10 live smoke | **ATENDIDO** (`smoke_e10_zero_lateral_path_maps_live.py`) |

## Aceite da Onda I

```text
NO_LATERAL_PATH_MAP = PASS
API_ROUTE_DOMAINS_PATH_MAP_REMOVED = PASS
CONTENT_PATHMARKERS_COUNT = 0
DOMAIN_FROM_OPENAPI_OR_CATALOG = PASS
UNKNOWN_PROVIDER_STILL_WORKS = PASS (E9.S10 offline)
NO_NEW_PATH_MAP_SUBSTITUTE = PASS (gate + inference bridge documentada)
LIVE_PRODUCT_STOCK_DOMAIN = PASS
LIVE_DEPARTMENT_KPI_SIBLING = PASS
LIVE_UNKNOWN_SAFE = PASS
```

Gate: `tests/unit/domain/services/test_e10_zero_lateral_path_maps.py`  
Live: `scripts/smoke_e10_zero_lateral_path_maps_live.py` → [`../evidence/e10-zero-lateral-path-maps-live.md`](../evidence/e10-zero-lateral-path-maps-live.md)

## Nota de bridge

`ApiRouteDomainInferenceService` deriva domínio a partir do **path do contrato OpenAPI** da action (e `delpiMetadata.apiRouteDomain` quando presente). Não há mapa lateral em content JSON. Evolução desejável: publicar `x-delpi.apiRouteDomain` na api-delpi para eliminar a inferência por fragmento de path no AI.
