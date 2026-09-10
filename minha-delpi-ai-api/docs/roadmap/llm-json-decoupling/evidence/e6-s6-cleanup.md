# E6.S6 — Cleanup recommendations/composer

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** F (plano 06)  
**Escopo:** remover mortos **somente** com evidência; preservar fallbacks mínimos

## Veredito

```text
DEAD_STATIC_TEXTUAL_RECS = already_removed (D2)
RECOMMENDATION_QUERIES_KEPT_AS_FALLBACK = PASS
COMPOSER_GROUPS_KEPT_LIVE = PASS (sem métrica de morte)
PROSE_FALLBACK_MARKED_PROFILE_FALLBACK = PASS
PLANO_06_GATES = PASS
NO_UNSAFE_DELETE = PASS
```

## O que NÃO foi apagado (intencional)

| Artifact | Motivo |
|----------|--------|
| `recommendationQueries` (13 profiles) | LEGACY_FALLBACK seguro (E6.S4); coverage gate D2 |
| `composer_route_questions.groups` | ainda LIVE templates; sem métrica de abandono |
| `capability_ux_classification.keywordRules` | fonte de composer; cleanup exigiria Onda H/métricas |

## O que foi limpo / alinhado

- Consumer prose `_build_recommendations` marca `source=profile_fallback` no path residual
- Docs/roadmap/README: `recommendationQueries` deixou de ser descrito como authority
- Plano 06 aceite fechado; Onda F **ATENDIDA**

## Residual explícito (não bloqueia aceite 06)

- Síntese LLM do turno ainda **não** emite `structuredRecommendations` (opt-in via `llm_candidates`)
- MFE ainda não envia `allowedActionIds` no typing-suggestions (API pronta)

## Aceite plano 06

```text
CONTEXTUAL_RECOMMENDATIONS = PASS (determinístico + grounding)
ALLOWLIST = PASS
DELTA_LLM_CALLS_ACCEPTABLE = PASS
STATIC_QUERIES_FALLBACK_ONLY = PASS
COMPOSER_BUDGET_SAFE = PASS
```

## Próximo

**Onda G** — planos 07/08 (presentation/skills residual).
