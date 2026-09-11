# E2.S6 — Pedidos compostos e dependências

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** C (plano 02)

## Feito

- TU decompõe goals; TaskPlanner preserva ordem / `dependsOn` / `parallelGroup`
- Harness: `test_e2_s6_compound_depends_harness.py`
- **Cutover ON:** `featureFlags.taskPlannerEnabled=true` (rollback via `CHAT_TASK_PLANNER_ENABLED=false`)
- Fast mode permanece em `executionDisabledModes` (execução None; shadow 1 step)
- Aceite offline composto: `test_e2_plano02_acceptance_offline.py`

## Métricas

| Métrica | Status |
|---------|--------|
| `task_decomposition_recall` (proxy offline) | **PASS_OFFLINE** |
| Live HTTP plano-02 | **PASS** (`e2-plano02-cutover-live.md` — 4/4) |
| `multi_request_completion_rate` (outcome L1–L4) | **PASS_OFFLINE_STRUCTURAL** + live compound multi-tool |

## Aceite

```text
COMPOUND_SPLIT_ORDER = PASS
DEPENDENT_REFERENCE_DEPENDS_ON = PASS
SINGLE_GOAL_NO_SPURIOUS_DEPENDS = PASS
TASK_PLANNER_DEFAULT_ON = PASS
FAST_EXECUTION_STILL_DISABLED = PASS
LIVE_PLANO02_HTTP = PASS (4/4)
```
