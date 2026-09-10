# E6.S4 — recommendationQueries → LEGACY_FALLBACK

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** F (plano 06)  
**Owner:** `ChatContextualRecommendationProducerService.produce_with_dual_run`  
**Wiring:** `ChatDataInsightService._attach_turn_structured_recommendations` → `commentary.recommendationDualRun`  
**Harness:** `tests/unit/domain/services/test_e6_s4_recommendation_queries_fallback.py`

## Veredito

```text
STATIC_QUERIES_FALLBACK_ONLY = PASS
DUAL_RUN_REPORT = PASS
FALSE_SUGGESTION_PROFILE_PATH = 0
IMPORTANT_PROFILES_COVERED = 13/13
DELTA_LLM_CALLS = 0
```

## Autoridade (pós-S4)

```text
1. llm_candidates | existing          → authority=llm_or_existing
2. profile queries *filtradas*        → authority=contextual_candidate (source=deterministic)
3. recommendationQueries bruto        → authority=profile_fallback (LEGACY_FALLBACK)
                                         só se candidate vazio
```

`humanized_data_response.recommendationQueries` deixa de ser autoridade principal do turno.

## Dual-run

| Campo | Significado |
|-------|-------------|
| `staticQueries` | catálogo bruto do profile |
| `candidateQueries` | emitido no turno |
| `onlyInStatic` | filtrado pelo grounding (ex.: paginação sem truncamento) |
| `onlyInCandidate` | false suggestion vs catálogo (0 no path profile-derived) |
| `usedProfileFallback` | candidate vazio → elevação bruta segura |
| `falseSuggestionCount` | `len(onlyInCandidate)` |

## Aceite plano 06 (parcial)

| Gate | Estado |
|------|--------|
| `STATIC_QUERIES_FALLBACK_ONLY` | PASS |
| `ALLOWLIST` | PASS (S2/S3) |
| `DELTA_LLM_CALLS_ACCEPTABLE` | PASS (=0) |
| `CONTEXTUAL_RECOMMENDATIONS` | PARCIAL (determinístico; LLM síntese ainda opt-in) |
| `COMPOSER_BUDGET_SAFE` | ABERTO → E6.S5 |

## Próximo

**E6.S5** — composer contextual (draft + entities + allowlist; debounce/cache).
