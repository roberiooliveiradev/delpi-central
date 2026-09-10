# E1.S4 — Selection shadow registry vs retrieval (evidência)

**Status:** `SHADOW_ON` (2026-09-10) — não é cutover  
**Onda:** B (plano 01)  
**Não remove** markers nem altera a action escolhida.

## O que entrou

| Peça | Path |
|------|------|
| Flag | `openapi_tool_routing.json` → `registrySelectionShadow.enabled=true` |
| Wiring registry | `select_registry_route_id` → `metadata.registrySelectionShadow` |
| Wiring product | `select_action_for_product` (intent/segment) → `metadata.productSelectionShadow` |
| Scoring shadow | `RetrieveActionCandidatesService` **lexical-only** no allowlist completo |
| Telemetria | `RegistrySelectionShadowObservabilityService.record` → log `registry_selection_shadow` |
| Testes | `test_e1_s4_registry_selection_shadow.py` (**15** asserts / 6 tests no arquivo + E1.S3) |

## Contrato do metadata

```json
{
  "kind": "registry_route_id | product_intent_segment",
  "routeId": "product.stock | product.intent:stock|segment:stock",
  "legacyActionId": "…",
  "markerMatchedIds": ["…"],
  "candidateTopIds": ["…"],
  "agree": true,
  "intent": "stock",
  "routeSegment": "stock"
}
```

- `agree=true` → legacy ∈ candidate top-K  
- `agree=false` → divergência observável (authority continua legacy)

## Aceite parcial E1.S4

```text
SHADOW_COMPARE_WIRED = PASS
SHADOW_DOES_NOT_CHANGE_SELECTION = PASS
AGREE_CASE = PASS
DIVERGE_CASE = PASS
FLAG_OFF_SKIPS_SHADOW = PASS
PRODUCT_INTENT_SEGMENT_PREEMPTION_SHADOW = PASS
STRUCTURED_OBSERVABILITY_LOG = PASS
AGREE_RATE_ADMIN_SUMMARY = PASS
CUTOVER_DEFAULT_CANDIDATE = PASS
```

Evidência cutover: [`e1-s6b-selection-cutover.md`](./e1-s6b-selection-cutover.md).

## Próximo

1. Monitorar `agreeRate` live pós-cutover via admin summary.  
2. DELETE de fields técnicos do registry → Onda H (após migrar readiness/lint).  
3. Parameter strategy binding já cutoverado (E1.S5) + switch tipado removido (E1.S6A).
