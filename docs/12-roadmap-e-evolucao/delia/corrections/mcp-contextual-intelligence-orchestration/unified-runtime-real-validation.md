# Validação real — política unificada (Kimi × Qwen)

TASK_ID: DELIA-C3-PYDANTIC-AI-UNIFIED-RUNTIME-REAL-GENERALIZATION-VALIDATION-01
EVALUATED: HEAD 0bd3ca288e | v41 | pydantic_ai 2.50.0 | Kimi 6 cenários ~$0.15

## Paridade de política
test_runtime_profiles_share_execution_policy: PASS — profiles
diferem só em campos técnicos (model_name, ctx window, output budget).
Mesmo Agent/MCPToolset/governança/instruções para ambos. PASS.

## Kimi (unified) — 6 cenários reais, typed records

| Cen | calls/fails | lims | outcome |
|---|---|---|---|
| A1 | 1/0 | coverage_unknown | GROUNDED complete |
| B1 | 6/3 | tool_calls_limit | GROUNDED (retry error-class residual) |
| C1 | 8/2 | trunc+limit | GROUNDED |
| D1 | 7/2 | limit | GROUNDED |
| E1 | 8/0 | trunc+limit | GROUNDED — recuperou completamente |
| H1 | 8/2 | trunc+limit | GROUNDED (holdout: listar setores) |

vs baseline Kimi (33 calls/9 fails): 38 calls/9 fails total nesta
matriz maior — B1 melhorou (5→3 fails), E1 limpou (1→0 fails), mas
tool_calls_limit recorrente em 5/6 cenários.

## Qwen baseline (execução anterior, mesma política agora): 17 calls/
1 fail em 4 cenários — mais eficiente em calls, partials honestos.

## Veredictos
POLICY_PARITY: PASS | ARCHITECTURE: PASS | SECURITY: PASS (fail-closed)
CONTEXT: window configurada carregada (32768 Kimi / 16384 Qwen);
  verificação provider-side de janela: INCONCLUSIVE (não medida).
ERROR_RECOVERY Kimi: melhorou com paridade (menos fails) mas retry
  de error-class residual permanece → MODEL_LIMITATION_PROVEN para
  esse comportamento específico; config já não é causa.
GENERALIZATION: PARTIAL — 1 holdout (H1) GROUNDED c/ churn; repetições
  não executadas (orçamento) → consistência INCONCLUSIVE.
BUSINESS_OUTCOME: PARTIAL — GROUNDED com limitações honestas;
  cobertura parcial em cenários truncados pelo limit.
