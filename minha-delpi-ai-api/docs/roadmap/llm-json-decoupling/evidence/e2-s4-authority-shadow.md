# E2.S4 — Authority shadow + cutovers por família

**Status:** `MAPPER_FIRST_ALL_FAMILIES` (2026-09-10)  
**Onda:** C (plano 02)

## Famílias

| Família | Dial | Modo authority |
|---------|------|----------------|
| product | `true` | mapper-first + fallback legado |
| production | `true` | **mapper-first + fallback legado** |
| kpi | `true` | **mapper-first + fallback legado** |

Cobertura production ampliada (`programado` / `na programacao` / `ops em aberto`). KPI tokens ampliados (ROL variants, meta comercial, OEE, …).

## Aceite

```text
PRODUCT_CUTOVER_ON = PASS
PRODUCTION_KPI_MAPPER_FIRST = PASS
MEMBERSHIP_SCHEDULE_OPS_OPEN = PASS
MAPPER_KPI_ROL_META_OEE = PASS
NEGATIVE_AGENDA / PRODUCT_CODE = PASS
DELETE_HEURISTICS = BLOCKED (E2.S7)
```

## Rollback

`families.production=false` / `families.kpi=false` / `cutoverEnabled=false`.

## Próximo (histórico)

E2.S5–S7 — ver evidências `e2-s5-*`, `e2-s6-*`, `e2-s7-*`.
