# E6.S1 — Inventário e baseline: recommendations + composer

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** F (plano 06)  
**HEAD:** pós-E5.S7 (`8093707cd`+)  
**Fontes:** greps HEAD + JSON `content/pt-BR/assistant/` + consumers MFE (sem migração runtime)

## Veredito

```text
ORIGIN_TO_UI_MAPPED = PASS
RECOMMENDATION_QUERIES_LIVE_AUTHORITY = PASS
COMPOSER_TEMPLATES_LIVE_AUTHORITY = PASS
BASELINE_FAMILIES_FROZEN = PASS
NO_RUNTIME_MIGRATION = PASS
D2_NOT_PLAN06_ACCEPTANCE = PASS
```

## Pipeline atual (recommendations)

```text
commentaryProfileKey
→ humanized_data_response.recommendationQueries[profile]
→ ChatDataInsightService._attach_turn_structured_recommendations
→ commentary.structuredRecommendations
→ ChatHumanizedDataResponseService.to_data_answer
→ dataAnswer.recommendations[{label,query,reason,(actionId)}]
→ SSE/toolCalls metadata → MFE (AssistantContentChrome)
```

Delta LLM no attach = **0** (elevação estática).  
Síntese operacional do turno **não** emite `structuredRecommendations`.

## Pipeline atual (composer)

```text
MFE draft (debounce 500ms)
→ POST /chat/typing-suggestions
→ ChatComposerRouteQuestionSuggestionService.suggest
→ composer_route_questions.groups + capability_ux_classification.keywordRules
→ routeQuestions[]
```

Cache server-side por draft: **ausente**.

## Matriz de classificação

| Artifact | Runtime | Class |
|----------|---------|-------|
| `recommendationQueries[*]` (13 profiles) | LIVE | LIVE_AUTHORITY (alvo E6.S4 = LEGACY_FALLBACK) |
| `commentary.structuredRecommendations` | LIVE | elevação estática (= queries) |
| `dataAnswer.recommendations` | LIVE | contrato UI |
| `nextActions[*]` | LIVE prosa | LEGACY_FALLBACK / summary |
| `humanized_data_response.recommendations` (lista textual) | DEAD | removido D2 |
| `RecommendationActionValidator` | LIVE parcial | só dropa se `actionId` ∉ allowlist; query livre passa |
| `presentationDecision.recommendations` | LIVE sibling | formato/view — não next-step |
| `followUpSuggestions` / interactivity chips | LIVE sibling | canal paralelo; pode zerar `dataAnswer.recommendations` |
| `composer_route_questions.groups` (3) | LIVE | LIVE_AUTHORITY templates |
| `capability_ux_classification.keywordRules` | LIVE | LIVE_AUTHORITY + SEMANTIC_METADATA |
| `source` / `confidence` / `llm_contextual` (contrato alvo) | ausente | DEAD / a criar S2–S3 |

## Cobertura profiles (drift vs E16)

| Fonte | Contagem HEAD |
|-------|---------------|
| `commentaryProfileKey` únicos em `presentation_profiles.json` | **13** |
| keys em `recommendationQueries` | **13** (1:1; coverage gate D2 verde) |
| Evidência E16 “27/27” | LEGADO_OU_POSSIVELMENTE_OBSOLETO (contagem antiga de nós de profile) |

## Famílias baseline (freeze)

| Família | Sinal atual (authority) | Gap vs TARGET 06 |
|---------|-------------------------|------------------|
| `profile_static_queries` | stock/factory → labels = JSON do profile | sem facts/goals |
| `already_executed_no_dedupe` | queries do profile sobem mesmo se tool já rodou | R06-02 aberto |
| `unauthorized_action_id` | `actionId` fora allowlist dropado; query sem id passa | R06-01 parcial |
| `multi_turn_persist` | `dataAnswer.recommendations` em metadata/toolCalls | F5 OK; interactivity clear sibling |
| `composer_prefix` | `"analise"` / `"estoque "` → groups | templates, não contextual |
| `composer_negative_short` | draft `< minDraftLength(3)` → vazio | budget ok; sem cache |

Corpus executável: `tests/unit/domain/services/test_e6_s1_recommendations_baseline.py`.

## Gaps vs TARGET

| TARGET | Estado HEAD |
|--------|-------------|
| user goal + facts + limitations + result refs | não entram no producer |
| already-executed / multi-turn grounding | não |
| allowed actions semântico | só se `actionId` presente |
| LLM síntese do turno → structured recs | não |
| `source: llm_contextual \| profile_fallback` | ausente |
| Composer contextual + cache | debounce MFE ok; sem LLM/cache server |

```text
ATUAL:  profileKey → recommendationQueries → structuredRecommendations → UI
ALVO:   goal+facts+allowed+context → síntese turno → validator → UI (+ queries só fallback)
```

## Ledger R06 (pós-S1)

| RQ | Estado |
|----|--------|
| R06-01 allowlist capability | ABERTO (parcial só actionId) |
| R06-02 anti-redundância | ABERTO |
| R06-03 delta LLM ≈ 0 | PARCIAL (hoje via estático) |
| R06-04 fallback seguro | PARCIAL (`recommendationQueries` = authority) |
| R06-05 composer budget | ABERTO (debounce only) |

## Próximo

**E6.S2** — grounding contract (input mínimo: goals, facts, limitations, allowed actions, already-executed).
