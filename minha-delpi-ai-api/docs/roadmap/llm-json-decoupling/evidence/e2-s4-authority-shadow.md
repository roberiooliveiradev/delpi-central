# E2.S4 — Authority vs TU shadow (sem cutover)

**Status:** `SHADOW_ON` (2026-09-10) — **não** é cutover de product/production/KPI  
**Onda:** C (plano 02)

## O que entrou

| Peça | Path |
|------|------|
| Compare | `TurnUnderstandingAuthorityShadowService.compare` |
| Telemetria | log `turn_understanding_authority_shadow` |
| Wiring | `shadowTurnUnderstanding.authorityShadow` no prepare |

## Contrato metadata

```json
{
  "kind": "turn_understanding_authority",
  "cutover": false,
  "agree": true,
  "agreeProduct": true,
  "agreeProduction": true,
  "agreeKpi": true,
  "agreeCompound": true,
  "productIntent": "stock",
  "productionKind": null,
  "kpiMatched": false,
  "goalCount": 1
}
```

Authority continua em `product_query_intent` / `production_operational_intent` / `department_kpi_rules`.

## Aceite parcial

```text
SHADOW_COMPARE_WIRED = PASS
SHADOW_DOES_NOT_CHANGE_SELECTION = PASS
CUTOVER_PRODUCT_PRODUCTION_KPI = NOT_STARTED
```

## Deferred (bloqueia Onda C ATENDIDO pleno)

- Cutover por família com agree ≥ limiar
- E2.S5 intent_router migration
- E2.S6 métricas compound live
- E2.S7 DELETE de heurísticas
