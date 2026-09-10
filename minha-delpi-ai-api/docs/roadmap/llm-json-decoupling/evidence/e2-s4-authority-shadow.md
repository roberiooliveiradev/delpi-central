# E2.S4 — Product-family cutover dial (default OFF)

**Status:** `CUTOVER_PARTIAL` (2026-09-10) — família **product** instrumentada; dial `cutoverEnabled=false`  
**Onda:** C (plano 02)

## O que entrou

| Peça | Path |
|------|------|
| Dial | `conversational_intelligence.json` → `productFamilyAuthorityShadow` |
| Flag | `ChatConversationalIntelligenceFlagService.product_family_cutover_enabled` |
| Mapper | `TurnUnderstandingProductIntentMapperService` (goals → enum) |
| Cutover point | `ChatProductQueryIntentDetectionService.detect` / `refine_*` |
| Shadow | `candidateProductIntent` + `cutover` do dial; legacy via `force_legacy=True` |

## Dial (default seguro)

```json
"productFamilyAuthorityShadow": {
  "enabled": true,
  "cutoverEnabled": false,
  "families": { "product": true, "production": false, "kpi": false }
}
```

Com `cutoverEnabled=false`: comportamento idêntico ao pré-cutover (SHADOW_DOES_NOT_CHANGE_SELECTION).

## Aceite

```text
SHADOW_COMPARE_WIRED = PASS
SHADOW_DOES_NOT_CHANGE_SELECTION = PASS (dial OFF)
PRODUCT_MAPPER_STOCK_SYNONYM = PASS
PRODUCT_MAPPER_COMPOUND_MULTI_SCOPE = PASS
PRODUCT_MAPPER_NEGATIVE_SMALLTALK = PASS
CUTOVER_PRODUCT_DIAL = READY (OFF in prod JSON)
CUTOVER_PRODUCTION_KPI = NOT_STARTED
DELETE_HEURISTICS = BLOCKED
```

## Não feito nesta fatia

- Ligar `cutoverEnabled=true` em produção
- Production / KPI families
- E2.S5 intent_router / analysis vocabulary
- E2.S7 DELETE de `product_query_intent` heuristics
