# 18 — I02-R3B · Revisão independente da implementação tipada

**DATA:** 2026-10-19  
**REVIEWED_IMPLEMENTATION_SHA:** `cda4963e52ae5cadc66392a5f4fcf37fb3c5aa17`  
**REVIEWED_MAIN_SHA:** `609b8dfb52dfc1c7a2d94f16fc2bf28bc9d5c883`  
**SOURCE:** [17](./17-i02r3b-typed-capability-goal-selection-implementation.md), `orchestration.py`, `test_i02r3b_typed_capability_goal_selection.py`, ledger §6.258.  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` **somente para a implementação tipada e sua caracterização sintética**; não é aceite I02 nem prova live.

## Findings

- `_select_capability_with_goal` usa o `_propose` existente, aceita campos adicionais de goal, valida `remote_name` na superfície de capabilities invocáveis e aplica o validador existente `_turn_goal_from_proposal`; cold-start com `goal_class` presente pode dispensar uma proposta `turn_goal`.
- Ausência de `goal_class` provoca fallback ao estágio separado; classe inválida produz `_TurnGoal()` neutro. Isso deve ser medido com modelo real (frequência de omissão, classes inválidas, qualidade de intenção WRITE, fallback latency).
- Continuidade multiturn usa early goal anterior; multi-group native assessment, owner discovery, write demotion, budget 30s, defaults de stage-cap e arguments-headroom não foram alterados pela otimização.
- Testes específicos e full backend PASS **segundo execução do Cursor**. Nesta revisão remota os testes não foram reexecutados independentemente: `TEST_NOT_RUN`. Ganho −1 call foi caracterizado sinteticamente, não em produção.
- **Sem prova:** sucesso K1 sob perfil de falha ~30s, latência real/pre-owner, K2 mesma conversa live, K3 VISTA live, taxa real de `goal_class`, impacto de seleção sob modelo real. `AC-10=INCONCLUSIVE`.

## Decisão e próximo bounded step

Aceitar apenas o diff bounded como candidato técnico de melhoria, com resíduos explícitos; **não declarar correção funcional completa**. Próxima tarefa não é nova investigação arquitetural: **validação live autenticada no SHA/config/model comprovados**, sem alterar o planner nem ativar guard/stage cap. Rodar conjunto bounded K1→K2 na mesma conversa e K3 VISTA; registrar por purpose durations, calls, presence de goal_class (sem payloads sensíveis), selection/write/foreign/grounding e ACT=0; comparar contra baseline histórico com ressalvas de configuração. Em falha, delimitar uma correção mínima a partir do estágio real, sem refatoração ampla. Deployment somente pelos gates canônicos.

```text
I02_R3B_CODE_REVIEW=ACCEPT_WITH_RESIDUAL
MODEL_CALL_REDUCTION=PROVEN_SYNTHETIC_ELIGIBLE_COLD_START
LIVE_K1_K2_K3=TEST_NOT_RUN
LIVE_LATENCY_IMPROVEMENT=INCONCLUSIVE
INDEPENDENT_TEST_REPLAY=TEST_NOT_RUN
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=I02_R3B_AUTHENTICATED_LIVE_OUTCOME_VALIDATION
```
