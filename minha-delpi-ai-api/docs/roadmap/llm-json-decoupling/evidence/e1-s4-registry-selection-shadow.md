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
CUTOVER_DEFAULT_CANDIDATE = NOT_STARTED
```

## Próximo

1. Agregar taxa `agree` em live/admin a partir dos logs (ou painel quando houver consumidor).  
2. Só após divergências explicáveis + corpus estável → E1.S5 (parameter strategy) / E1.S6 cutover.
