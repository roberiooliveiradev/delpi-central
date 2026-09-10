# E6.S2 — Grounding contract (recommendations)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** F (plano 06)  
**Owner:** `ChatRecommendationGroundingService`  
**Caps:** `humanized_data_response.recommendationGrounding`  
**Harness:** `tests/unit/domain/services/test_e6_s2_recommendation_grounding_contract.py`

## Veredito

```text
GROUNDING_CONTRACT = PASS
NO_RAW_PAYLOAD = PASS
BUDGET_CAPS = PASS
CANDIDATE_SHAPE = PASS
ALLOWLIST_PLUS_EXECUTED_FILTER = PASS
NO_PRODUCER_CUTOVER = PASS
```

## Input mínimo (`RecommendationGroundingContext`)

| Campo | Origem típica | Cap content |
|-------|---------------|-------------|
| `userMessage` | turno / metadata | `maxMessageChars` |
| `userGoals` | plan goals / metadata | `maxUserGoals` |
| `facts` | dataAnswer / commentary | `maxFacts` + `maxFactChars` |
| `limitations` | dataAnswer | `maxLimitations` + `maxLimitationChars` |
| `resultRefs` | execution_results (actionId/path/status) | `maxResultRefs` |
| `allowedActionIds` | metadata allowlist | `maxAllowedActions` |
| `alreadyExecutedActionIds` | metadata + results ok | `maxAlreadyExecuted` |
| `alreadyExecutedGoalIds` | `goalCoverage.results` fulfilled | `maxAlreadyExecuted` |
| `profileKey` | presentation profile | — |
| `truncated` | qualquer clip | — |

**Proibido no contexto:** `data` / rows / payload bruto (`raw_data` aceito só para garantir exclusão).

## Output shape (parse; producer = E6.S3)

```json
{
  "label": "...",
  "query": "...",
  "reason": "...",
  "actionId": null,
  "source": "llm_contextual|profile_fallback|deterministic",
  "confidence": 0.0
}
```

`filter_candidates_against_grounding`: reusa `RecommendationActionValidator` + dropa `actionId` já executado.

## Invariantes

- Sem wiring no `ChatDataInsightService` nesta etapa (authority ainda = `recommendationQueries`).
- Caps no content JSON (policy), não hardcoded no use case.
- Recommendation nunca autoexecuta write.

## Próximo

**E6.S3** — contextual producer (síntese do turno / geração controlada) + validator no pipeline live.
