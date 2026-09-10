# E8.S4 — Mixed bundles: copy UX fora de `actionSelection`

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** G (plano 08)  
**Harness:** `tests/unit/domain/services/test_e8_s4_ear_mixed_bundle_copy_split.py`

## Veredito

```text
POLICY_OWNERSHIP = PASS
UX_COPY_SEPARATED = PASS
ROUTING_AUTHORITY_UNCHANGED = PASS
HTTP_EXECUTION_UNTOUCHED = PASS
EMPTY_RIVAL_PARITY = PASS
```

## Feito

Novo bloco top-level `actionSelectionCopy` em `external_action_responses.json`:

| Campo | Origem |
|-------|--------|
| `routeClarification` | saiu de `actionSelection` |
| `refinementFallbackMessages` | saiu de `actionSelection` |
| `emptyRivalSuggestions` | saiu de `emptyRivalRecommendations[].suggestions` |

Matchers (`operationIds` / `pathMarkers` / `profileKeys`) permanecem em `actionSelection.emptyRivalRecommendations`.

Consumers atualizados: score-gap, catalog-miss, invoice direction resolver, refinement fallbacks, empty-rival.

## Não feito (dívida documentada)

- `siblingDisambiguation`, `*Path`/`*OperationId`, `candidateDiscovery`, `readPolicy`, vocabulário `*Terms` — PATH_COUPLED/POLICY LIVE (onda futura OpenAPI-first)
- `httpExecution` timeout/retry — **proibido** mover para prompt

## Freeze

`actionSelection` keys: **61 → 59**

## Próximo

**E8.S5** — audit gate contra nova duplicação técnica em assistant content.
