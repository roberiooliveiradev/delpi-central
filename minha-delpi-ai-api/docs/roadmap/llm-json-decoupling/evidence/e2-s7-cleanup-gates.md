# E2.S7 — Cleanup heurísticas (plano-02)

**Status:** `JUSTIFIED_KEEP` / gates atualizados (2026-09-10)  
**Onda:** C (plano 02)

## Decisão

Nenhum DELETE dos catálogos major nesta fatia. Authority residual permanece **justificada** até:

1. E2.S5 full (analysis multi-consumer + cascade)
2. E2.S6 live metrics com `taskPlannerEnabled` ON
3. Corpus R1–R11 sem regressão material

## KEEP (não apagar)

| Superfície | Motivo |
|------------|--------|
| `intent_router.json` | cascade ainda authority; overlay E2.S5 é parcial |
| `analysis_intent_vocabulary.json` | consumers fora do router |
| `product_query_intent.json` | fallback mapper-first product |
| `production_operational_intent.json` | fallback mapper-first production |
| `department_kpi_rules.json` | fallback mapper-first KPI |

## Gate fixture

`tests/fixtures/intelligence_baseline/e9_s6_cleanup_gates.json` → `turn_understanding_heuristics_json` permanece **BLOCKED** com razão atualizada (E2.S4 mapper-first + E2.S5 slice; DELETE ainda BLOCKED).

## Aceite

```text
NO_UNAUTHORIZED_DELETE = PASS
MAJOR_HEURISTICS_JUSTIFIED_KEEP = PASS
DELETE_WHEN_GATES_PASS = BLOCKED
```
