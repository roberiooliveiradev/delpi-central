# E2 — plano-02 cutover live validation

**Status:** `PASS` (2026-09-10)  
**Runner:** `scripts/smoke_plano02_cutover_live.py`  
**Evidência JSON:** [`e2-plano02-cutover-live.json`](./e2-plano02-cutover-live.json)

## Ambiente

- Keycloak religado (`delpi-keycloak` estava Exited)
- `minha-delpi-ai-api` reiniciada (volume `/app` com código atual)
- Flags runtime: `taskPlannerEnabled=true`, `data_interpretation=true`

## Resultados

| Caso | Status | Tools | Wall ms | Nota |
|------|--------|------:|--------:|------|
| no_tool_smalltalk | PASS | 0 | ~148s | sem tools; prosa OK |
| product_stock | PASS | 1 | ~123s | estoque 10080001 |
| compound_enum | PASS | 3 | ~332s | estoque+fornecedores+resumo |
| compare_insight | PASS | 1 | ~116s | responde com limitação de série temporal |

```text
VERDICT = PASS
CASES = 4/4
```

## Observações

- `activeTaskPlan` / `shadowTaskPlan` não apareceram nas keys de `adminDebug.intelligence` deste shape; compound validado por **multi-tool (3)** + prosa consolidada.
- Smoke C4 separado: agent hardcoded antigo → 400; com `SMOKE_AGENT_ID` do agent live, reexecutar à parte.

## Rollback live

`CHAT_TASK_PLANNER_ENABLED=false` ou dials `families.*=false`.
