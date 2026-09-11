# J-R10 — contextual recommendations

**Status:** COMPLETE_GATE = PASS  
**Gates:** `CONTEXTUAL_RECOMMENDATIONS=PASS` · `LEGACY_RECOMMENDATION_FALLBACK=0`

## Problema

Producer e consumers ainda usavam `recommendationQueries` bruto como `LEGACY_FALLBACK` / `profile_fallback` quando o candidate filtrado ficava vazio.

## Correção

| Antes | Depois |
|---|---|
| candidate vazio → dump do profile estático | candidate vazio → `contextual_generic` (goals/limitations/message) |
| `staticFallbackRole=LEGACY_FALLBACK` | `staticFallbackRole=REMOVED` · `legacyRecommendationFallback=0` |
| UI/humanized dump `profile_fallback` | sem dump; chips via producer/attach |

`recommendationQueries` permanece como **seed determinístico filtrado** (observabilidade dual-run), não como authority de fallback.

## Testes

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q \
  tests/unit/domain/services/test_j_r10_contextual_recommendations.py \
  tests/unit/domain/services/test_e6_s4_recommendation_queries_fallback.py
```

## Gate

```text
CONTEXTUAL_RECOMMENDATIONS = PASS
LEGACY_RECOMMENDATION_FALLBACK = 0
COMPLETE_GATE (J-R10) = PASS
NEXT = J-R11
```
