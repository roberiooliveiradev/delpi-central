# Plano 06 — Recommendations e composer -> sugestões contextuais grounded

**Prioridade:** P1  
**Objetivo perceptível:** próximos passos e sugestões devem considerar o pedido atual, os fatos retornados, limitações, contexto multi-turn e actions permitidas, em vez de listas estáticas por profile.

## CURRENT

Fontes prioritárias:

- `humanized_data_response.json`, especialmente `recommendationQueries`, `nextActions` e fallbacks;
- `composer_route_questions.json`;
- producers de `structuredRecommendations`;
- consumers no MFE/UI e síntese final.

Padrão residual:

```text
profileKey
-> recommendationQueries estáticas
-> structuredRecommendations
```

ou:

```text
prefix/marker digitado
-> group estático
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

| ID | Requisito |
|---|---|
| R06-01 | Recomendações não podem citar capability/action inexistente ou não autorizada. |
| R06-02 | Evitar recomendação redundante com algo já executado no turno. |
| R06-03 | Preferir reutilizar chamada LLM já existente; delta de LLM calls deve ser zero quando viável. |
| R06-04 | Preservar fallback determinístico seguro em timeout/falha. |
| R06-05 | Composer não pode gerar chamadas LLM caras a cada tecla sem budget/debounce/cache. |

## Contrato alvo

`structuredRecommendations` deve ser materializado no turno com campos validados, por exemplo:

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

Se houver `actionId`, ele deve pertencer às actions permitidas. Recommendation nunca autoexecuta write.

## Etapas

### E6.S1 — Inventário e baseline

**Fazer:** mapear origem, transformação, persistência e UI de recommendations/chips; congelar exemplos por profile e contexto.

**Teste:** recommendation relevance, duplication, unavailable capability, multi-turn relevance e latency.

### E6.S2 — Grounding contract

**Fazer:** definir input mínimo: user goals, facts/dataAnswer, limitations, result refs, allowed actions/capabilities e already-executed goals.

**Não fazer:** enviar payload bruto ilimitado ao LLM.

### E6.S3 — Contextual producer

**Fazer:** acoplar produção estruturada à síntese operacional existente quando arquitetura permitir; validar output, tamanho, duplicação e action allowlist.

**Teste:** malformed output, unauthorized actionId, hallucinated query, empty result.

### E6.S4 — Static profile queries -> fallback

**Fazer:** mover `recommendationQueries` de autoridade principal para fallback temporário; medir divergência/relevância candidate vs static.

**Pronto quando:** candidate cobre profiles importantes sem aumentar false suggestions.

### E6.S5 — Composer contextual

**Fazer:** usar draft + current entities + allowed capabilities para sugerir perguntas; desenhar debounce/cache/trigger controlado; considerar modelo menor quando houver chamada dedicada.

**Não fazer:** executar tool automaticamente a partir da sugestão.

**Teste:** draft curto, rápido, typo, ambiguous; agent com capabilities diferentes; no action available.

### E6.S6 — Cleanup

**Fazer:** remover blocos estáticos mortos apenas após métricas; manter copy genérica e fallback seguro mínimo.

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

## Invariantes

- Sem actionId inventado.
- Sem write autoexecutado por recommendation.
- Falha de recommendation não quebra resposta principal.
- History/F5 usa recommendation materializada; não precisa reinferir.

## Aceite

```text
CONTEXTUAL_RECOMMENDATIONS = PASS
AUTHORIZED_ONLY = PASS
NO_REDUNDANT_SUGGESTION = PASS
LLM_CALL_BUDGET = PASS
COMPOSER_AGENT_AWARE = PASS
PERSIST_RELOAD = PASS
```
