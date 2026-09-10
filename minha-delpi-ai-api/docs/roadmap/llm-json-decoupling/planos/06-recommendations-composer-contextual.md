# Plano 06 — Recommendations e composer -> sugestões contextuais grounded

**Prioridade:** P1  
**Status execução:** Onda F · E6.S1–S4 **ATENDIDO** · próxima E6.S5 · `recommendationQueries` = LEGACY_FALLBACK  
**Evidência:** [`../evidence/e6-s1-recommendations-inventory.md`](../evidence/e6-s1-recommendations-inventory.md) · [`../evidence/e6-s2-recommendation-grounding-contract.md`](../evidence/e6-s2-recommendation-grounding-contract.md) · [`../evidence/e6-s3-contextual-recommendation-producer.md`](../evidence/e6-s3-contextual-recommendation-producer.md) · [`../evidence/e6-s4-recommendation-queries-fallback.md`](../evidence/e6-s4-recommendation-queries-fallback.md) · [`../evidence/execution-ledger.md`](../evidence/execution-ledger.md)  
**Objetivo perceptível:** próximos passos e sugestões devem considerar o pedido atual, os fatos retornados, limitações, contexto multi-turn e actions permitidas, em vez de listas estáticas por profile.

**HEAD revalidado:** pós-E6.S3 (`6a311b8f0`+)

## EXECUTION_DRIFT (2026-09-10)

| Item | Estado no código | Impacto neste plano |
|------|------------------|---------------------|
| Nó estático `humanized_data_response.recommendations` (lista textual) | **REMOVIDO** | Cleanup legado path→display **DONE** — não confundir com aceite deste plano |
| `recommendationQueries` por `commentaryProfileKey` | **LEGACY_FALLBACK** (E6.S4); dual-run em `recommendationDualRun` | Candidate contextual é autoridade; bruto só se candidate vazio |
| Coverage 27/27 profiles | Gate D2 PASS | Prova cobertura estática, **não** relevância contextual grounded |
| Composer | `composer_route_questions` + UX classification keywords | Ainda templates/heurística; E6.S5 aberto |

**D2 ≠ Plano 06.** D2 fechou fallback textual paralelo. Este plano exige recomendações **contextuais** (facts/goals/allowed actions), preferencialmente via síntese LLM já existente no turno.

## CURRENT

Fontes prioritárias:

- `humanized_data_response.json` → `recommendationQueries`, `nextActions`;
- `composer_route_questions.json`;
- producers de `structuredRecommendations`;
- consumers no MFE/UI e síntese final.

Padrão residual atual:

```text
profileKey
-> recommendationQueries estáticas
-> structuredRecommendations
```

ou:

```text
prefix/marker digitado
-> group estático / keywordRules
-> question template
```

## TARGET

```text
user goal
+ current data/facts/limitations
+ result references
+ conversation context
+ allowed capabilities/actions
+ remaining budget
-> existing turn LLM synthesis ou geração semântica controlada
-> structured recommendations
-> validator/allowlist
-> UI
```

## Requisitos

| ID | Requisito | Estado |
|---|---|---|
| R06-01 | Recomendações não citam capability/action inexistente ou não autorizada | PARCIAL (actionId allowlist; query textual livre) |
| R06-02 | Evitar recomendação redundante com o já executado no turno | PARCIAL (actionId + pagination filter) |
| R06-03 | Reutilizar chamada LLM do turno; delta ≈ 0 quando viável | ATENDIDO (delta=0) |
| R06-04 | Fallback determinístico seguro em timeout/falha | ATENDIDO (`profile_fallback`) |
| R06-05 | Composer sem LLM caro por tecla (debounce/cache) | ABERTO → E6.S5 |

## Contrato alvo

`structuredRecommendations` materializado no turno com campos validados, por exemplo:

```json
{
  "label": "Comparar com o período anterior",
  "query": "Compare este indicador com o período anterior",
  "reason": "Avaliar tendência",
  "actionId": null,
  "source": "llm_contextual",
  "confidence": 0.88
}
```

Se houver `actionId`, deve pertencer às actions permitidas. Recommendation nunca autoexecuta write.

`source` pode ser `llm_contextual` | `profile_fallback` | `deterministic` durante dual-run.

## Etapas

### E6.S1 — Inventário e baseline — **ATENDIDO** (2026-09-10)

**Fazer:** mapear origem/transformação/persistência/UI; baseline com producer atual (`recommendationQueries`) vs desejado contextual.

**Feito:** inventário `e6-s1-recommendations-inventory.md`; freeze 6 famílias em `test_e6_s1_recommendations_baseline.py` (profile static, no-dedupe, unauthorized actionId parcial, skip-if-present, composer prefix/negative). Cobertura profiles = **13/13** (drift vs E16 “27/27”).

**Teste:** relevance (= JSON), duplication gap, unavailable capability (parcial), composer prefix/short; multi-turn/latency documentados no inventário.

### E6.S2 — Grounding contract — **ATENDIDO** (2026-09-10)

**Fazer:** input mínimo: user goals, facts/dataAnswer, limitations, result refs, allowed actions, already-executed goals.

**Feito:** `ChatRecommendationGroundingService` + caps `recommendationGrounding` em `humanized_data_response.json`; shape `StructuredRecommendationCandidate`; filter allowlist + already-executed. Sem cutover do producer.

**Não fazer:** payload bruto ilimitado ao LLM — **garantido** (raw_data excluído; caps).

### E6.S3 — Contextual producer — **ATENDIDO** (2026-09-10)

**Fazer:** acoplar à síntese operacional existente quando possível; validar output, tamanho, duplicação e allowlist.

**Feito:** `ChatContextualRecommendationProducerService` + wiring no attach; filtros pagination/allowlist/dedupe; `source`/`confidence` no `dataAnswer`; aceita `llm_candidates` (síntese ainda não emite — opt-in). Delta LLM=0.

**Teste:** malformed, unauthorized actionId, already-executed, empty, pagination sibling.

### E6.S4 — Static profile queries -> fallback — **ATENDIDO** (2026-09-10)

**Fazer:** mover `recommendationQueries` de autoridade principal para **LEGACY_FALLBACK**; medir divergência candidate vs static.

**Feito:** `produce_with_dual_run` + `recommendationDualRun` no commentary; path profile-derived com `falseSuggestionCount=0` em 13/13 profiles; bruto só se candidate vazio (`source=profile_fallback`).

**Pronto quando:** candidate cobre profiles importantes sem aumentar false suggestions — **PASS**.

### E6.S5 — Composer contextual

**Fazer:** draft + entities + allowed capabilities; debounce/cache; modelo menor se call dedicada.

**Não fazer:** auto-executar tool a partir da sugestão.

### E6.S6 — Cleanup

**Fazer:** remover blocos estáticos mortos só após métricas; manter fallback seguro mínimo.

## Métricas específicas

```text
recommendation_relevance_rate
recommendation_action_allowlist_accuracy
recommendation_duplicate_rate
recommendation_follow_through_success
composer_acceptance_rate
llm_calls_per_turn
p50/p95 recommendation latency
```

## Aceite

```text
CONTEXTUAL_RECOMMENDATIONS = PASS
ALLOWLIST = PASS
DELTA_LLM_CALLS_ACCEPTABLE = PASS
STATIC_QUERIES_FALLBACK_ONLY = PASS
COMPOSER_BUDGET_SAFE = PASS
```
