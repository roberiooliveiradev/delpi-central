# E6.S3 — Contextual recommendation producer

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** F (plano 06)  
**Owner:** `ChatContextualRecommendationProducerService`  
**Wiring:** `ChatDataInsightService._attach_turn_structured_recommendations`  
**Harness:** `tests/unit/domain/services/test_e6_s3_contextual_recommendation_producer.py`

## Veredito

```text
CONTEXTUAL_PRODUCER = PASS
DELTA_LLM_CALLS = 0
ALLOWLIST_FILTER = PASS
PAGINATION_CONTEXT_FILTER = PASS
SOURCE_PROPAGATED = PASS
MALFORMED_DROPPED = PASS
NO_SYNTHESIS_SCHEMA_EXPANSION = PASS (opt-in via llm_candidates / existing)
```

## Ordem de autoridade

```text
1. llm_candidates | commentary.structuredRecommendations já presentes
   → source llm_contextual (ou deterministic se existing sem source)
2. profile recommendationQueries filtradas por grounding
   → source deterministic (ou profile_fallback se só elevação sem filtro)
→ filter_candidates_against_grounding
→ dedupe(query) ≤ maxRecommendations
→ dataAnswer.recommendations (+ source/confidence)
```

## Filtros determinísticos (sem LLM)

| Regra | Efeito |
|-------|--------|
| Query de paginação sem sinal em `limitations` | omitida |
| `actionId` ∉ allowlist | drop |
| `actionId` já executado | drop |
| malformed (sem query) | drop |
| dedupe casefold(query) | 1ª vence |

## Invariantes

- Sem chamada LLM dedicada (R06-03).
- Síntese operacional ainda não emite o campo; producer aceita `llm_candidates` quando houver (dual-run / S4).
- `recommendationQueries` ainda alimenta o path determinístico (autoridade até E6.S4 = fallback).

## Próximo

**E6.S4** — rebaixar `recommendationQueries` a LEGACY_FALLBACK; medir divergência candidate vs static.
