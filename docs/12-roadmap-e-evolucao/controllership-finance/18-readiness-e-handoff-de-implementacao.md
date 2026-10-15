# 18 — Readiness e Handoff de Implementação

## Gate documental

O pacote funcional de implementação está organizado em:

- [20-transforma-plus-coverage.md](./20-transforma-plus-coverage.md) — cobertura completa CTL/CORE e residuais;
- [21-boundaries-produtos-e-owners.md](./21-boundaries-produtos-e-owners.md) — boundaries e owners;
- [22-handoff-implementacao-p1-p6.md](./22-handoff-implementacao-p1-p6.md) — handoff uniforme por página;
- [23-ledger-rq-ac-testes.md](./23-ledger-rq-ac-testes.md) — requisitos, aceite e testes;
- [15.1-p3-criterios-paridade-monetaria.md](./15.1-p3-criterios-paridade-monetaria.md) — regra centavo-exata P3.

`DOCUMENTATION_GATE` não prova runtime e não substitui o inventário técnico da página.

## Gate global da fase atual

```text
PORTAL_REVIEW_PHASE = ACTIVE
DOCUMENTATION_CLOSURE_PHASE = ACTIVE
DOCUMENTATION_CLOSURE_COMPLETE = NO
IMPLEMENTATION_AUTHORIZED = NO
```

Os estados `READY_FOR_IMPLEMENTATION_*` abaixo medem **maturidade documental**, não autorização de execução. Nenhum diff runtime deve começar antes do fechamento da revisão de todas as páginas e de um `PORTAL_DESIGN_FREEZE = PASS` explícito.

O plano obrigatório de fechamento está em [33-plano-mestre-fechamento-documental.md](./33-plano-mestre-fechamento-documental.md). Antes dos freezes transversais, deve existir `DOCUMENTATION_CLOSURE_COMPLETE = PASS`.

## Interpretação durante a FASE A / Gate V2

A partir do Page Documentation Gate V2:

```text
DOCUMENTED != IMPLEMENTED
READY_FOR_IMPLEMENTATION_BRIEF != IMPLEMENTATION_AUTHORIZED
```

Estados históricos desta tabela representam maturidade documental acumulada. A fila futura só aceita uma página depois de ela ser revalidada no pacote V2 definido no documento 33.

## Readiness

### Superfícies da topbar

| Página | Estado | Stop / inventário material |
|---|---|---|
| Início | PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY | A02 fechado; H01/H03/H04 e TSK aplicáveis continuam inventário físico; runtime não autorizado |
| Visão geral | PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY | A03 fechado; O04 físico permanece inventário; O05 é stop condition de source/fórmula |
| Sala de interação | PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY | A05 fechado; R01–R05 permanecem inventários físicos; create-task-from-message continua fora da V1 |
| Minhas tarefas | PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY | A04 fechado; TSK01–TSK05 permanecem inventários físicos/futuros do brief |
| Administração | PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY | A06 fechado; ADM01–ADM07/E01/E05/E06 permanecem inventories; Core notification capability PROVEN, adapter do produto permanece inventário |
| Ajuda | PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF | A07 fechado; HELP01–HELP04 permanecem inventories físicos; conteúdo runtime continua capability-gated e feature-by-feature |

A topbar usa somente `controllership-finance.access` e `controllership-finance.manage`. Não existe permission code por filial/unidade neste Portal.


Contrato Home: [32-inicio-home.md](./32-inicio-home.md).

Contrato da Visão geral: [25-visao-geral-indicadores-financeiros.md](./25-visao-geral-indicadores-financeiros.md).

Contrato da Sala de interação: [26-sala-de-interacao.md](./26-sala-de-interacao.md).

Contrato de Minhas tarefas: [27-minhas-tarefas.md](./27-minhas-tarefas.md).

Contrato de Administração: [28-administracao.md](./28-administracao.md).

Contrato de Ajuda: [29-ajuda.md](./29-ajuda.md). Manual kit, conteúdo versionado no MFE, runtime-only publication, capability gating, contextual deep links e feature-help-sync estão fechados. Arquitetura Painel/Templates/Catálogos/Histórico, lifecycle, snapshot, MANAGE-only, inativação, audit e plugin-ui estão fechados; persistência/seeds/integrations/concurrency permanecem inventories técnicos. O modelo de projection, self-only, producers, action policy, sem SLA global e integração Home/Sala estão fechados; apenas a estratégia física e bindings permanecem inventories técnicos. O modelo de contexto, AuthZ, mensagem, attachment boundary, deep link e full-page reuse estão fechados; transport/storage/retention permanecem inventories técnicos do futuro slice. D-OVW-01=C congela núcleo + contexto operacional + desempenho estratégico; D-OVW-02=A congela mês atual; D-OVW-03=A congela Consolidado. O04/O05 permanecem inventários técnicos para o futuro brief, sem autorização de implementação.

O Início tem design/UX/RQ/AC fechados, mas mantém inventories conhecidos para persistência de favoritos e projeções dinâmicas. Isso não autoriza implementação durante a fase atual de revisão global.

### Superfícies transversais

| Página | Estado | Stop / inventário material |
|---|---|---|
| Página do usuário | PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF | A01 fechado documentalmente; runtime NOT_IMPLEMENTED; bindings físicos/Core adapters serão revalidados apenas no futuro brief |

Contrato funcional/visual: [31-pagina-do-usuario.md](./31-pagina-do-usuario.md).

Decisões congeladas:
- D1=B: viewer com `controllership-finance.access` pode consultar outro usuário com acesso ao mesmo Portal;
- D2=A: no próprio perfil, exibir label + códigos técnicos `controllership-finance.access/manage`;
- permissions/capabilities de outro usuário permanecem ocultas;
- identidade/foto continuam owned pelo Core, sem persistência local no Portal.

### Central de Fechamento

| Página / slice | Estado | Stop / inventário material |
|---|---|---|
| P1 | PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY | A08 fechado; T01/T05 e contracts físicos de composição permanecem inventário |
| P2 | PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY | A09 fechado; E05/E06/T05 e bindings físicos permanecem inventário; Core notification capability PROVEN, adapter do produto a inventariar |
| P3 | PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY / STOP_CONDITION_ON_T03 | A10 fechado; E02 = STOCK_CLOSED terminal no Portal V1; T03 continua stop técnico para owner canônico |
| P4 | PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY | A11 fechado; T01/T05 e contracts físicos permanecem inventário |
| P5 — pacote/finalização/review | PAGE_DOCUMENTATION_GATE_V2 PARTIAL | portal-first submission/review model PASS; monthly completion rule DECISION_REQUIRED |
| P5 — envio para análise | PRODUCT_MODEL_DEFINED / REVIEW_COMPLETION_DECISION_REQUIRED | package stays in Minha DELPI; reviewers authenticated; e-mail notification only; doc 37 |
| P6 | PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY | A13 fechado em 13+28; Core notifications PROVEN; persistência/seeds/people/concurrency e adapter do produto permanecem inventário |

Readiness não é autorização global. Depois do freeze transversal, o Portal evoluirá uma página/slice por vez.

## Interpretação dos estados

`READY_FOR_IMPLEMENTATION_INVENTORY`:
- produto/regra/RQ/AC suficientes para iniciar inventário técnico;
- bindings, contracts e runtime ainda precisam ser provados no HEAD;
- não autoriza inventar nome técnico ou owner.

`READY_WITH_STOP_CONDITION_ON_T03`:
- P3 pode avançar em inventário/contrato;
- nenhuma implementação pode fechar `STOCK_CLOSED` por fallback manual silencioso;
- T03 precisa provar o estado canônico antes do slice dependente.

P5 após clarificação do Product Owner:
- package/finalize/versioning não estão bloqueados;
- E04/T04 external delivery = CLOSED / NOT_REQUIRED_IN_V1;
- "Enviar" = submit for review dentro da Minha DELPI;
- reviewers usam login + ACCESS + resource scope;
- notifications podem chegar in-app e por e-mail;
- residual material: `D-P5-REVIEW-COMPLETION` no doc 37.

## Freeze readiness após A15

```text
PORTAL_DESIGN_FREEZE           = PASS
FRONTEND_PATTERN_FREEZE        = PASS
SECURITY_MODEL_FREEZE          = PASS
TEST_STRATEGY_FREEZE           = PASS
PRODUCT_CONTRACT_FREEZE        = DECISION_REQUIRED_P5_REVIEW_COMPLETION
DOCUMENTATION_CLOSURE_COMPLETE = NO
IMPLEMENTATION_AUTHORIZED      = NO
```

Authority de consolidação:
- [34-revisao-transversal-gate-v2.md](./34-revisao-transversal-gate-v2.md);
- [35-contratos-regras-scripts-test-matrix-gate-v2.md](./35-contratos-regras-scripts-test-matrix-gate-v2.md).

## Antes de qualquer diff técnico

1. obter HEAD e `git status`;
2. ler authorities oficiais e regras `.cursor` materiais;
3. ler README + docs 20–23 + documento canônico da página (31 para Página do usuário; 32 para Início);
4. abrir E/T aplicáveis;
5. identificar owner e producer/consumer reais;
6. provar contracts/bindings no HEAD;
7. confirmar AuthZ/Core effective permissions e resource ownership aplicável;
8. confirmar gate do slice;
9. selecionar RQs do [23-ledger-rq-ac-testes.md](./23-ledger-rq-ac-testes.md);
10. definir evidência positive + sibling + negative;
11. parar se evidência nova invalidar premissa necessária do TARGET.

## Arquitetura técnica

Identidade técnica já congelada:

```text
plugin id     = controllership-finance
plugin folder = plugins/controllership-finance
basePath      = /apps/controllership-finance
BFF/service   = controllership-finance-api
BFF baseUrl   = /apps/controllership-finance-api
CSS root      = .portal-controllership-finance
```

Continuam dependentes de inventário/contrato do slice:

- necessidade real de storage;
- schemas físicos;
- migrations;
- deployment topology;
- OpenAPI/DTOs físicos de cada capability;
- bindings externos e infraestrutura necessária.

Não criar tabela/migration antecipadamente apenas para "ter a fundação". Persistência nasce de contrato stateful comprovado.

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


## Adendo de governança — decisões PO C2 e D-P5-01 a D-P5-05 (15/10/2026)

**TARGET / DECIDED_BY_PRODUCT_OWNER / DOCUMENTATION_REBASELINE_PENDING**. Registro de decisão, não evidência de runtime nem aprovação de freeze. Este adendo prevalece sobre referências anteriores a C1/C2/C3 como decisão aberta; semânticas derivadas ainda pendentes não devem ser inferidas.

- **C2:** conclusão mensal exige todos os pacotes aplicáveis submetidos, todas as revisões obrigatórias aceitas e nenhum esclarecimento aberto. Submissão ou e-mail de notificação não concluem fechamento.
- **D-P5-01:** podem existir múltiplos reviewers por RecipientPackage; **todos os reviewers obrigatórios** precisam aceitar. Aceite parcial não atende ao quorum.
- **D-P5-02:** esclarecimento sem mudança de conteúdo mantém PackageVersion; qualquer conteúdo modificado exige nova PackageVersion, preservando a anterior e seu histórico.
- **D-P5-03:** aceite não pode ser revertido pela UI V1; correção extraordinária não está automaticamente autorizada.
- **D-P5-04:** ao perder ACCESS efetivo, reviewer perde a capacidade de agir; atribuição e histórico são preservados; substituição exige reatribuição autorizada, auditável e validada pela BFF/Core (fail-closed).
- **D-P5-05:** solicitação de alterações (CHANGES_REQUESTED) e rejeição terminal (REVIEW_REJECTED) são outcomes distintos; não usar um como alias do outro.

Regra alvo:

```text
ALL_APPLICABLE_PACKAGES_SUBMITTED
AND ALL_REQUIRED_REVIEWS = REVIEW_ACCEPTED
AND NO_OPEN_CLARIFICATION
=> MONTHLY_CLOSING_COMPLETED
```

**DECISION_REQUIRED / NO CHANGE TO BEHAVIOR:** definir escopo da terminalidade de REVIEW_REJECTED (submissão vs pacote), regra de substituição/aceite anterior, congelamento ou alteração auditada do conjunto de reviewers obrigatórios, necessidade de novo quorum por versão e tratamento da competência quando houver rejeição terminal. Nenhum endpoint, migration, scaffold ou permission adicional está autorizado.

**Evidência pendente:** rebase do main, .cursor aplicável, ledger RQ/AC, Core effective permissions, test matrix positive/sibling/negative, Help, postcondition. `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `IMPLEMENTATION_AUTHORIZED = NO`.
