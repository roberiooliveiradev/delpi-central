# E2.S4 — Authority shadow + cutovers por família

**Status:** `CUTOVER_ALL_FAMILIES_CANARY` (2026-09-10)  
**Onda:** C (plano 02)

## Famílias

| Família | Dial | Modo authority |
|---------|------|----------------|
| product | `true` | mapper-first + fallback legado |
| production | `true` | **agree-gated** (só troca quando mapper == legado) |
| kpi | `true` | **agree-gated** (path_token igual) |

Production/KPI usam agree-gate para não regressar casos em que o mapper ainda é mais grosso que o legado (ex.: OP status com código, finished-without-consumption).

## Aceite

```text
PRODUCT_CUTOVER_ON = PASS
PRODUCTION_KPI_DIALS_ON = PASS
AGREE_GATED_NO_REGRESSION = PASS (89 unitários)
MAPPER_SCHEDULE_CONSUMPTION_PURCHASES = PASS
MAPPER_KPI_ROL_EBITDA = PASS
NEGATIVE_AGENDA / PRODUCT_CODE = PASS
DELETE_HEURISTICS = BLOCKED
```

## Rollback

`families.production=false` / `families.kpi=false` / `cutoverEnabled=false`.

## Próximo

- Elevar production/KPI de agree-gated → mapper-first (após cobertura)
- E2.S5 intent_router / analysis
- E2.S7 DELETE heurísticas
