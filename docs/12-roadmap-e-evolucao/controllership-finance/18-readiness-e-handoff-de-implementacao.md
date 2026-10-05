# 18 — Readiness e Handoff de Implementação

## Gate documental

O pacote funcional de implementação está organizado em:

- [20-transforma-plus-coverage.md](./20-transforma-plus-coverage.md) — cobertura completa CTL/CORE e residuais;
- [21-boundaries-produtos-e-owners.md](./21-boundaries-produtos-e-owners.md) — boundaries e owners;
- [22-handoff-implementacao-p1-p6.md](./22-handoff-implementacao-p1-p6.md) — handoff uniforme por página;
- [23-ledger-rq-ac-testes.md](./23-ledger-rq-ac-testes.md) — requisitos, aceite e testes;
- [15.1-p3-criterios-paridade-monetaria.md](./15.1-p3-criterios-paridade-monetaria.md) — regra centavo-exata P3.

`DOCUMENTATION_GATE` não prova runtime e não substitui o inventário técnico da página.

## Readiness

| Página / slice | Estado | Stop / inventário material |
|---|---|---|
| P1 | READY_FOR_IMPLEMENTATION_INVENTORY | T01 para bindings; T05 para effective permissions/AuthZ |
| P2 | READY_FOR_IMPLEMENTATION_INVENTORY | E05/E06, T02 e T05 conforme slice |
| P3 | READY_WITH_STOP_CONDITION_ON_T03 | T01 para bindings; T03 obrigatório para STOCK_CLOSED |
| P4 | READY_FOR_IMPLEMENTATION_INVENTORY | T01/T05; não expandir CTL-005 além do fechamento |
| P5 — pacote/finalização | READY_FOR_IMPLEMENTATION_INVENTORY | owners/sources aplicáveis |
| P5 — envio real | BLOCKED_WITH_EVIDENCE | Q22 depende E04/T04 |
| P6 | READY_FOR_IMPLEMENTATION_INVENTORY | E01/E05/E06 e T02/T05 conforme configuração |

Readiness não é autorização global. O Portal evolui uma página/slice por vez.

## Interpretação dos estados

`READY_FOR_IMPLEMENTATION_INVENTORY`:
- produto/regra/RQ/AC suficientes para iniciar inventário técnico;
- bindings, contracts e runtime ainda precisam ser provados no HEAD;
- não autoriza inventar nome técnico ou owner.

`READY_WITH_STOP_CONDITION_ON_T03`:
- P3 pode avançar em inventário/contrato;
- nenhuma implementação pode fechar `STOCK_CLOSED` por fallback manual silencioso;
- T03 precisa provar o estado canônico antes do slice dependente.

`BLOCKED_WITH_EVIDENCE` no envio P5:
- package/finalize/versioning não estão bloqueados;
- enviar por canal real continua bloqueado até E04/T04;
- não assumir e-mail, Teams, pasta ou serviço novo.

## Antes de qualquer diff técnico

1. obter HEAD e `git status`;
2. ler authorities oficiais e regras `.cursor` materiais;
3. ler README + docs 20–23 + documento canônico da página;
4. abrir E/T aplicáveis;
5. identificar owner e producer/consumer reais;
6. provar contracts/bindings no HEAD;
7. confirmar AuthZ/Core effective permissions e resource ownership aplicável;
8. confirmar gate do slice;
9. selecionar RQs do [23-ledger-rq-ac-testes.md](./23-ledger-rq-ac-testes.md);
10. definir evidência positive + sibling + negative;
11. parar se evidência nova invalidar premissa necessária do TARGET.

## Arquitetura técnica

Continuam não definidos por esta documentação:
- plugin id;
- rota/basePath;
- BFF/service name;
- storage;
- manifest;
- schemas físicos;
- migrations;
- deployment topology.

Decidir somente após inventário do HEAD, owners e contracts.

O Portal Financeiro P0 não é template obrigatório do novo Portal.

## Ordem funcional sugerida

A ordem inicial de investigação permanece:

```text
fundação técnica mínima
→ P1
→ P2
→ P3
→ P4
→ P5 package/finalization
→ P5 send quando E04/T04 fecharem
→ P6 evolutivo conforme dependências
```

Não seguir mecanicamente se o inventário técnico provar outra dependência. Mudança material deve ser registrada como rationale ou `EXECUTION_DRIFT` quando invalidar premissa necessária.

## Gate por página

Antes de implementar uma página/slice, o brief deve conter:

- TASK;
- GOAL;
- RQ/AC selecionados do ledger;
- AUTHORITIES;
- OWNER;
- CURRENT_STATE;
- EVIDENCE_REQUIRED;
- ALLOWED_SCOPE;
- FORBIDDEN_SCOPE;
- CONTRACTS;
- SECURITY;
- ACCEPTANCE;
- TESTS;
- STOP_CONDITION.

## Report obrigatório

O executor deve devolver:

- BASE HEAD;
- FINAL HEAD;
- STATUS;
- FACTS PROVEN;
- TO_INVENTORY;
- EXECUTION_DRIFT;
- FILES INSPECTED/CHANGED;
- CONTRACT IMPACT;
- TESTS;
- SECURITY CHECKS;
- RQ/AC COVERAGE;
- RESIDUAL SEARCH;
- POSTCONDITION/OUTCOME;
- UNRESOLVED;
- NEXT STEP.

## Review

GPT conclui somente:
- ACCEPT;
- ACCEPT_WITH_RESIDUAL;
- REWORK;
- EXECUTION_DRIFT;
- INCONCLUSIVE.

Smoke não executado quando material = INCONCLUSIVE, nunca PASS inferido.

## Estado das decisões

- Q01–Q21 e Q23–Q30: fechadas;
- Q22: depende E04/T04;
- E01–E06: `PENDING_IMPLEMENTATION_CONFIRMATION`;
- T01–T05: `TO_INVENTORY_DURING_IMPLEMENTATION`.

`PENDING_IMPLEMENTATION != OPEN_PRODUCT_DESIGN`.

Não reabrir E/T como problema de produto sem evidência nova material.

## Gate para primeiro brief de implementação

A documentação funcional permite preparar o primeiro brief técnico quando:

```text
HEAD reancorado
AND authorities/.cursor lidos
AND owner/runtime inventariado
AND RQs da página selecionados
AND E/T aplicáveis classificados
AND gate do slice confirmado
```

A primeira execução técnica ainda deve inventariar a fundação do produto; este documento não presume o resultado desse inventário.
