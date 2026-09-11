# E2.S6 — Pedidos compostos e dependências

**Status:** `ATENDIDO_PARCIAL` (2026-09-10)  
**Onda:** C (plano 02)

## Feito (harness offline)

- TU decompõe goals em pedido enumerado
- `ChatTaskPlannerService.build_from_understanding` preserva ordem, aplica `dependsOn` (heurística prior-code) e `parallelGroup` quando tool sem dependência
- Testes: `tests/unit/domain/services/test_e2_s6_compound_depends_harness.py` (P0 + sibling + negative)

## BLOCKED / não READY

| Item | Motivo |
|------|--------|
| `taskPlannerEnabled` cutover ON | dial permanece `false` (execução live fora desta fatia) |
| `multi_request_completion_rate` / `task_decomposition_recall` | meta live/R-family — corpus plano-09; sem baseline numérico fechado aqui |
| Partial failure / presentation-only joiners end-to-end | requer orquestração live |

## Aceite parcial

```text
COMPOUND_SPLIT_ORDER = PASS
DEPENDENT_REFERENCE_DEPENDS_ON = PASS
SINGLE_GOAL_NO_SPURIOUS_DEPENDS = PASS
LIVE_METRICS = BLOCKED (taskPlanner OFF)
```
