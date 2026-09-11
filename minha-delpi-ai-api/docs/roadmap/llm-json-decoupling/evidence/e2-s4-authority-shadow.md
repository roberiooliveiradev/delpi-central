# E2.S4 — Authority shadow + cutovers por família

**Status:** `CUTOVER_PRODUCT_CANARY` + `PRODUCTION_KPI_SHADOW_READY` (2026-09-10)  
**Onda:** C (plano 02)

## Famílias

| Família | Dial `families.*` | Estado |
|---------|-------------------|--------|
| product | `true` | **CANARY ON** (`cutoverEnabled=true`) |
| production | `false` | mapper + wire + shadow candidates; dial OFF |
| kpi | `false` | mapper + wire + shadow candidates; dial OFF |

## Peças

| Peça | Path |
|------|------|
| Dial | `productFamilyAuthorityShadow` |
| Flag | `family_cutover_enabled(name)` |
| Product mapper | `TurnUnderstandingProductIntentMapperService` |
| Production mapper | `TurnUnderstandingProductionIntentMapperService` |
| KPI mapper | `TurnUnderstandingKpiIntentMapperService` |
| Chokes | `detect` / `resolve(..., force_legacy=)` |
| Shadow | `candidateProductIntent`, `candidateProductionKind`, `candidateKpi`, `cutover*` |

## Aceite

```text
PRODUCT_CUTOVER_ON = PASS
PRODUCTION_KPI_DIAL_OFF = PASS
MAPPER_SCHEDULE_TODAY = PASS
MAPPER_KPI_ROL = PASS
NEGATIVE_AGENDA / PRODUCT_CODE = PASS
SHADOW_CANDIDATES = PASS
FORCE_LEGACY_PARITY_WHEN_OFF = PASS
DELETE_HEURISTICS = BLOCKED
```

## Extra nesta fatia

- `_matches_kind` normaliza terms/excludes do JSON (paridade com stemming `comprados`→`compras`).

## Próximo

- Canary production/KPI (`families.*=true`) após agree offline
- E2.S5 intent_router / analysis
- E2.S7 DELETE heurísticas
