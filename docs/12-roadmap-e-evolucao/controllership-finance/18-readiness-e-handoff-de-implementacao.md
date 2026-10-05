# 18 — Readiness e Handoff de Implementação

## Readiness

| Página | Estado |
|---|---|
| P1 | READY_FOR_IMPLEMENTATION_INVENTORY |
| P2 | READY_FOR_IMPLEMENTATION_INVENTORY |
| P3 | READY_WITH_STOP_CONDITION_ON_T03 |
| P4 | READY_FOR_IMPLEMENTATION_INVENTORY |
| P5 | PARTIALLY_READY — Q22 depende E04/T04 |
| P6 | READY_FOR_IMPLEMENTATION_INVENTORY |

Readiness não é autorização global.

## Antes de qualquer diff

1. obter HEAD e status;
2. ler authorities oficiais;
3. aplicar regras `.cursor`;
4. ler docs desta pasta;
5. abrir E/T aplicáveis;
6. identificar owner;
7. confirmar contrato;
8. confirmar AuthZ;
9. confirmar gate da página;
10. definir evidência de aceite.

## Arquitetura técnica

Não assumir plugin id, BFF, rota, banco ou service name.

Decidir após inventário do HEAD e owners.

## Ordem funcional sugerida

1. fundação técnica/config mínima;
2. P1;
3. P2;
4. P3;
5. P4;
6. P5;
7. P6 evolutivo.

Não seguir cegamente se as dependencies reais indicarem outra ordem.

## Brief mínimo

- TASK
- GOAL
- RQ/AC
- AUTHORITIES
- OWNER
- CURRENT_STATE
- EVIDENCE_REQUIRED
- ALLOWED_SCOPE
- FORBIDDEN_SCOPE
- CONTRACTS
- SECURITY
- ACCEPTANCE
- TESTS
- STOP_CONDITION

## Report obrigatório

- BASE HEAD
- FINAL HEAD
- STATUS
- FACTS PROVEN
- TO_INVENTORY
- EXECUTION_DRIFT
- FILES INSPECTED/CHANGED
- CONTRACT IMPACT
- TESTS
- SECURITY CHECKS
- RQ/AC COVERAGE
- RESIDUAL SEARCH
- OUTCOME
- UNRESOLVED
- NEXT STEP

## Review

- ACCEPT
- ACCEPT_WITH_RESIDUAL
- REWORK
- EXECUTION_DRIFT
- INCONCLUSIVE

Smoke não executado = INCONCLUSIVE, nunca PASS inferido.

## Estado das decisões

Q01–Q21 e Q23–Q30: fechadas.

Q22: depende E04/T04.

E01–E06: confirmar na implementação.

T01–T05: inventariar na implementação.
