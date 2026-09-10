# E1.S4 — Selection shadow registry vs retrieval (evidência)

**Status:** `SHADOW_ON` (2026-09-10) — não é cutover  
**Onda:** B (plano 01)  
**Não remove** markers nem altera a action escolhida.

## O que entrou

| Peça | Path |
|------|------|
| Flag | `openapi_tool_routing.json` → `registrySelectionShadow.enabled=true` |
| Wiring | `ExternalActionSelectionService._select_registry_route_via_openapi` anexa `metadata.registrySelectionShadow` |
| Scoring shadow | `RetrieveActionCandidatesService` **lexical-only** (`semantic_ranker=None`) no allowlist completo |
| Testes | `tests/unit/application/services/test_e1_s4_registry_selection_shadow.py` (3 passed) |

## Contrato do metadata

```json
{
  "routeId": "product.stock",
  "legacyActionId": "…",
  "markerMatchedIds": ["…"],
  "candidateTopIds": ["…"],
  "agree": true
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
PRODUCT_INTENT_SEGMENT_PREEMPTION_SHADOW = PENDING
CUTOVER_DEFAULT_CANDIDATE = NOT_STARTED
```

## Próximo

1. Telemetria/admin: agregar taxa `agree` em live.  
2. Shadow também no preemption `intent+route_segment` (product).  
3. Só após divergências explicáveis + E1.S3 corpus estável → E1.S5/S6 cutover.
