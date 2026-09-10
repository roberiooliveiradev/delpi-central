# E1.S6B — Selection cutover (authority OpenAPI-first)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** B (plano 01)  
**Harness:** `tests/unit/application/services/test_e1_s6b_selection_cutover.py`

## Decisão

```text
registrySelectionShadow.cutoverEnabled = true
→ select_registry_route_id: authority = OpenAPI-first no allowlist completo
→ select_action_for_product (intent/segment): authority = OpenAPI-first
→ markers / product intent tipado = observer (legacyActionId no shadow)
```

Divergências explicáveis (markers forçando família errada) passam a **corrigir** a seleção em vez de só observar.

## Aceite

```text
CUTOVER_DEFAULT_CANDIDATE = PASS
CUTOVER_PREFERS_RETRIEVAL_OVER_WRONG_MARKERS = PASS
CUTOVER_PRODUCT_INTENT = PASS
UNKNOWN_OPENAPI_PROVIDER = PASS
METAMORPHIC_RENAME = PASS
OFFLINE_CORPUS_AGREE_RATE_GE_95 = PASS
SHADOW_STILL_RECORDED = PASS
SQL_POLICY_UNTOUCHED = PASS
```

## Fora desta fatia (correto)

- **DELETE** de `pathMarkers` / `operationIdMarkers` / `routeSegment` / `parameters.strategy` no JSON do registry → consumers residuais (readiness/lint/resolve_route_action UI) ainda leem fields; ledger exige cleanup em onda H após migração.
- Agregação live admin continua útil para monitorar pós-cutover.

## Evidências irmãs

- Shadow pré-cutover: [`e1-s4-registry-selection-shadow.md`](./e1-s4-registry-selection-shadow.md)
- Agree admin: [`e1-s4-agree-aggregation.md`](./e1-s4-agree-aggregation.md)
- Cleanup switch binding: [`e1-s6-cleanup-partial.md`](./e1-s6-cleanup-partial.md)
