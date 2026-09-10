# E6.S5 — Composer contextual

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** F (plano 06)  
**Owner:** `ChatComposerRouteQuestionSuggestionService`  
**HTTP:** `POST /chat/typing-suggestions` (`allowedActionIds` opcional)  
**Harness:** `tests/unit/domain/services/test_e6_s5_composer_contextual.py`

## Veredito

```text
COMPOSER_BUDGET_SAFE = PASS
NO_LLM_PER_KEYSTROKE = PASS
SERVER_CACHE = PASS
ALLOWLIST_FILTER = PASS
ENTITY_PRODUCT_CODE = PASS
NO_AUTO_EXECUTE = PASS
```

## Contrato

```text
draft
+ entity (productCode extraído)
+ allowedActionIds? (hints por groupId / category)
+ cache TTL (content: composer_route_questions.cache)
→ routeQuestions[] (queries textuais; sem actionId)
```

Debounce **500ms** permanece no MFE (`useChatTypingCorrection`).  
Sem chamada LLM dedicada no composer (R06-05).

## Content

| Campo | Papel |
|-------|-------|
| `cache.ttlSeconds` / `maxEntries` | budget server-side |
| `groupActionHints` | filtro semântico vs allowlist |
| `groups` / `keywordRules` | templates (ainda LIVE; cleanup = E6.S6) |

## Aceite plano 06

| Gate | Estado |
|------|--------|
| `COMPOSER_BUDGET_SAFE` | PASS |
| `STATIC_QUERIES_FALLBACK_ONLY` | PASS (E6.S4) |
| `ALLOWLIST` | PASS |
| `DELTA_LLM_CALLS_ACCEPTABLE` | PASS |
| `CONTEXTUAL_RECOMMENDATIONS` | PARCIAL (recs determinísticas; LLM turn opt-in) |

## Próximo

**E6.S6** — cleanup de blocos estáticos mortos; manter fallback mínimo.
