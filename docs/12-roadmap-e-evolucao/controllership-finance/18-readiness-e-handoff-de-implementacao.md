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

**Rebaseline vigente:** [38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md](./38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md). Estados PASS históricos de A12/A14/A15 não substituem a revisão datada.

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
| P5 — pacote/finalização/review | TARGET / A12 POSTMERGE_REVALIDATION_INCONCLUSIVE | C2, P5-A..J, DEC-01..04 aprovados; regras semânticas no doc 37; binding Core T05/estado técnico a inventariar |
| P5 — envio para análise | PRODUCT_MODEL_DEFINED / P5_C2_APPROVED_DERIVED_CONTRACT_REVALIDATE | package stays in Minha DELPI; reviewers authenticated; e-mail notification only; doc 37 |
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
- C2 e o quorum por área obrigatória estão aprovados no doc 37; residual é de contrato físico/elegibilidade Core T05, não nova escolha C1/C2/C3.

## Freeze readiness após A15

```text
PORTAL_DESIGN_FREEZE           = HISTORICAL_PASS_REVALIDATE
FRONTEND_PATTERN_FREEZE        = PASS
SECURITY_MODEL_FREEZE          = HISTORICAL_PASS_REVALIDATE
TEST_STRATEGY_FREEZE           = HISTORICAL_PASS_REVALIDATE
PRODUCT_CONTRACT_FREEZE        = PENDING_CORE_T05_AND_CONTRACT_BINDINGS
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

## Ordem funcional futura — baseline executiva V1

A ordem atual é [39 — Roadmap Mestre](./39-roadmap-mestre-implementacao-v1.md), detalhada em [40 — Slices e Dependências](./40-matriz-dependencias-e-slices-v1.md), [41 — Testes/Gates](./41-estrategia-validacao-e-gates-implementacao-v1.md), [42 — Cursor](./42-playbook-brief-cursor-execution-report-v1.md) e [43 — Release](./43-rollout-operacao-e-handoff-v1.md). **Esta é ordem de planejamento, não autorização de runtime.**

```text
IMP-00 inventário/gate A12/A14/A15/A16 → four freezes → PO authorize
→ A01 Página do usuário → A02 Início → A03 Visão geral
→ A04 Minhas tarefas → A05 Sala de interação → A06 Administração
→ A07 Ajuda (com Help sync em todo slice user-facing)
→ A08 P1 → A09 P2 → A10 P3 → A11 P4 → A12 P5 → A13 P6
→ regressão, operação e gate de release
```

E04/T04 de entrega externa por anexo foram superados pelo **envio in-portal** do doc 37; não bloquear P5 por esse contrato histórico. P5 permanece condicionado ao Core T05 e ao contrato físico de áreas P6 versionadas. P6 pode exigir micro-slice predecessor de contrato/owner antes de P2/P5; não antecipar toda UI. Alterar ordem apenas com dependência demonstrada, gate e rationale/`EXECUTION_DRIFT` se a premissa aprovada caiu.

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
- Q22: contrato portal-first/C2 aprovado e vigente no doc 37; E04/T04 entrega externa não é requerida na V1;
- E01/E05/E06: catálogos/seeds TO_INVENTORY conforme slice; E04/T04 delivery externo SUPERSEDED/NOT_REQUIRED_IN_V1; demais E conforme owner e materialidade;
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

- **C2:** conclusão mensal exige todos os pacotes aplicáveis submetidos, todas as áreas obrigatórias com aceite da versão vigente e nenhum esclarecimento aberto. Submissão ou e-mail de notificação não concluem fechamento.
- **D-P5-01:** podem existir múltiplos reviewers por RecipientPackage; **todas as áreas obrigatórias** precisam de um aceite válido da PackageVersion atual (P5-A refinou D-P5-01). Aceite parcial não atende ao quorum.
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


## Decisões supervenientes do Product Owner — P5-A a P5-E (15/10/2026)

**TARGET / PO_APPROVED / DOCUMENTATION_ONLY — no runtime changes.** Este registro complementa C2 e prevalece sobre a interpretação anterior de D-P5-01 (unanimidade por identidade): o quórum é por **área/especialidade obrigatória**, não por cada usuário elegível. A multiplicidade de pessoas elegíveis na mesma área não cria múltiplos votos obrigatórios.

| Decisão | Regra aprovada | Relação com decisão anterior |
|---|---|---|
| P5-A | Um aceite por área obrigatória, executável por qualquer usuário elegível daquela área | D-P5-01 reinterpretada: unanimidade de áreas obrigatórias, não de pessoas |
| P5-B | Somente autor de um aceite pode alterá-lo; outra pessoa atua somente com reatribuição formal | Complementa D-P5-03; sem reversão livre na UI V1, preservar trilha imutável |
| P5-C | ACCESS efetivo + grupo/função corporativa + escopo do recurso + regra de negócio | Complementa D-P5-04; Core é owner da identidade/effective permissions; P5 controla workflow e scope |
| P5-D | Rejeição terminal encerra a competência em estado REJECTED, distinto de MONTHLY_CLOSING_COMPLETED; não exige ressubmissão | Concretiza D-P5-05, mantendo CHANGES_REQUESTED distinto de rejeição terminal |
| P5-E | Nova PackageVersion exige novo aceite de todas as áreas obrigatórias, sem herdar aceites da versão anterior | Complementa D-P5-02 e preserva versionamento imutável |

**C2 atualizado semanticamente:** conclusão mensal requer todos os pacotes aplicáveis submetidos, aceites válidos da **versão vigente** para cada área obrigatória e nenhuma clarification aberta. Qualquer rejeição terminal impede MONTHLY_CLOSING_COMPLETED e resulta no desfecho de competência rejeitada, com auditoria. Não inferir que uma permission genérica concede approval irrestrito.

**AuthZ invariant:** JWT identifica; Core resolve `controllership-finance.access` efetivo; BFF valida função/grupo corporativo elegível, área obrigatória, resource scope/ownership e business rule, fail-closed. A origem/contrato preciso do grupo/função Core permanece **TO_INVENTORY (T05)**; não criar permission code para reviewer, área, botão, filial ou unidade. `controllership-finance.manage` não substitui ACCESS.

**Auditoria mínima:** ator Core, ação, instante, competência, recipient package, PackageVersion, área/atribuição usada, decisão e justificativa quando aplicável, mudança de responsável e referência ao evento anterior. Registro original não é apagado ou reatribuído retroativamente; mudança é novo evento auditável.

**SUPERSEDED / PO_APPROVED (16/10/2026):** reatribuição mantém aceite/autoria (P5-F); nenhuma reversão na UI ou endpoint V1 (P5-G/DEC-03); P6 congela áreas obrigatórias em snapshot (P5-H/DEC-04); revisão por área + confirmação de competência pelo coordenador formal com ACCESS/vínculo/scope (P5-I/DEC-01/02); rejeição terminal torna TaskProjections inativas sem apagar histórico (P5-J). Residual exclusivamente técnico a inventariar: Core T05 corp group/function S2S, DTOs/eventos, state IDs, P6 storage/OCC e consumers. Não reabrir decisões PO sem evidência material nova.

**Gate:** `PRODUCT_CONTRACT_FREEZE = PENDING_DERIVED_RULES`; `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `IMPLEMENTATION_AUTHORIZED = NO`. Estes textos registram decisões de produto, não demonstram testes, código, contratos físicos, rebase nem execução de smoke.

**Rebaseline P5-A..E:** antigos status `D-P5-01 unanimidade de reviewers individuais` e `C2 pendente` são históricos/superseded quando conflitantes. Não inferir `PORTAL_DESIGN_FREEZE = PASS` vigente após mudança de semântica; revalidar A12/A14/A15 e matriz RQ/AC antes de novo gate explícito.


## Rebaseline P5-F..J — decisões PO aprovadas (16/10/2026)

**TARGET / DOCUMENTED_NOT_IMPLEMENTED.** P5-F: reatribuição preserva aceite válido da área/versão, autor original e histórico; substituto só atua no futuro. P5-G: aceite P5 não pode ser revertido pela UI V1; correção excepcional necessita contrato separado, não autorizado. P5-H: P6 versiona áreas obrigatórias por tipo de pacote; P5 congela áreas na submissão; elegibilidade Core + ACCESS + grupo/função + scope + regra (T05 pendente). P5-I: rejeição pelo reviewer/área não encerra automaticamente a competência; confirmação terminal exige autoridade operacional formal definida, justificativa e auditoria. P5-J: após confirmação terminal, tarefas/reviews deixam de ser acionáveis, preservando histórico.

C2 permanece: conclusão apenas com todos os pacotes aplicáveis submetidos, todas as áreas obrigatórias aceitando a versão vigente e nenhuma clarification aberta. Competência rejeitada é terminal distinto de `MONTHLY_CLOSING_COMPLETED`. D-P5-01 = unanimidade de áreas obrigatórias, não pessoas. Aceites de PackageVersion anterior não são herdados por versão nova. Referências anteriores contraditórias permanecem históricas/superseded; não são contratos vigentes.

**DECISION_REQUIRED:** identidade/critério da autoridade operacional que confirma rejeição e comportamento quando não confirma; especificação de processo excepcional de correção (não implementá-lo sem autorização). **CONTRACT_PENDING/TO_INVENTORY:** mapeamento P6 de áreas/tipos e fonte Core de elegibilidade, DTO/estado, notification/projection/tests.

`DOCUMENTATION_CLOSURE_COMPLETE=NO`; `PRODUCT_CONTRACT_FREEZE=PENDING`; `IMPLEMENTATION_AUTHORIZED=NO`; `TEST_NOT_RUN`. Revalidar A12/A14/A15 e main antes de freeze.


## Decisões finais do PO — DEC-01 a DEC-04 (16/10/2026)

**TARGET / PO_APPROVED / NOT_IMPLEMENTED.** Vigência: este contrato substitui referências históricas a `DECISION_REQUIRED` sobre autoridade de rejeição, negativa de confirmação, exceção de reversão na V1 e publicador P6. Não equivale a evidence de testes ou freeze.

| ID | Decisão aprovada | Contrato normativo |
|---|---|---|
| DEC-01 | Responsável formal da Controladoria | A pessoa designada para coordenar o fechamento da competência pode confirmar rejeição terminal **somente** com `controllership-finance.access` efetivo, vínculo operacional, escopo do recurso e business rule verificados server-side. `manage` isolado não concede essa autoridade. A designação/substituição deve ser auditada; owner da identidade/permissão é Core; owner do vínculo operacional é o contexto P5. |
| DEC-02 | Rejeição pendente se não confirmada | Rejeição pela área/pacote cria proposta de rejeição da competência; até decisão formal ela não está `MONTHLY_CLOSING_COMPLETED` nem terminalmente rejeitada. Autoridade registra decisão/motivo; pode devolver análise para esclarecimento ou correção nas transições autorizadas. Não apagar evento original. |
| DEC-03 | Sem correção excepcional de aceite P5 na V1 | Aceite P5 é irreversível pela UI e não existe endpoint de reversão/retificação na V1. Incidentes são registrados e encaminhados a processo **fora do fluxo do Portal**, sem presumir ação técnica, override, database edit ou reversão automática. P2 validação de evidência mantém contrato próprio. |
| DEC-04 | P6 publica configuração com MANAGE | Usuário com `controllership-finance.manage` efetivo **e** escopo administrativo publica nova configuração versionada de áreas obrigatórias por tipo de pacote, com justificativa, auditoria e vigência prospectiva. Competências e submissões existentes mantêm snapshots; MANAGE não implica ACCESS operacional. |

### Consistência transversal

C2 continua exigindo todos os pacotes aplicáveis submetidos, **um aceite válido de cada área obrigatória** sobre a versão atual, e nenhuma clarification aberta. Uma competência terminalmente rejeitada é desfecho diferente de conclusão, dependente de confirmação DEC-01. P5-A..J permanecem vigentes: aceites auditados por ator; reatribuição não troca autoria ou invalida aceite vigente; nova versão reinicia aceites obrigatórios; envio é submissão interna; rejeição terminal desativa TaskProjections acionáveis e preserva histórico. `CHANGES_REQUESTED` não é `REVIEW_REJECTED`.

### AC mínimos (PLANNED / TEST_NOT_RUN)

- DEC-01: reviewer de área não consegue encerrar competência; coordenador com ACCESS + vínculo + scope consegue confirmar; MANAGE sem vínculo/ACCESS falha; ausência de Core/elegibilidade falha fechada.
- DEC-02: rejeição de área sem confirmação mantém estado pendente; negativa motivada permanece auditável e permite devolução somente por transição contratada; nenhuma conclusão automática.
- DEC-03: nenhum endpoint ou ação UI V1 altera aceite P5; eventos originais imutáveis e incidentes externos não falsificam C2.
- DEC-04: MANAGE + escopo publica com motivação e versionamento; ACCESS sem MANAGE não publica; submissão anterior não muda; nova submissão adota versão conforme vigência autorizada.

### Pendências técnicas distintas de escolhas PO

**TO_INVENTORY:** contrato Core T05 de effective permissions e atributos corporativos; source do coordenador/vínculo/eligibilidade; owner/contrato físico de persistência e eventos; formato de estados/DTOs, versionamento P6 e CAS/concorrência; UX, notifications, help e projections. **CONTRACT_PENDING:** mapear transições específicas e outcomes da negativa no ledger e testes; identificar .cursor e padrões HEAD aplicáveis. Não declarar `PASS` sem inspeção de código/producers/consumers/testes e reconciliação da branch com main.

`DECISION_REQUIRED_PRODUCT_P5=NONE_IDENTIFIED_AFTER_DEC01_DEC04` (sujeito a inventário material posterior); `DOCUMENTATION_CLOSURE_COMPLETE=NO`; `IMPLEMENTATION_AUTHORIZED=NO`; `TEST_NOT_RUN`.


## Decisoes PO DEC-01..04 aprovadas — baseline 16/10/2026

**TARGET / PO_APPROVED**. DEC-01: coordenador formal da competencia, com ACCESS efetivo, vinculo operacional, scope e business rule, confirma rejeicao terminal; MANAGE sozinho nao autoriza. DEC-02: rejeicao nao confirmada permanece pendente, exige motivo e pode retornar a esclarecimento/correcao auditavel. DEC-03: nenhuma reversao/retificacao de aceite P5 por UI ou endpoint V1; incidentes tratados fora do fluxo do Portal. DEC-04: MANAGE efetivo + escopo administrativo publica configuracoes de areas obrigatorias por tipo de pacote com auditoria e vigencia prospectiva; snapshots existentes preservados. Decisoes anteriores C2, P5-A..J permanecem compatibilizadas no doc 37. Nao criar permission code adicional.

**TO_INVENTORY:** Core T05 e ligacao do coordenador, configuracao P6 e contratos fisicos P5, eventos/projections/testes, regras aplicaveis no HEAD. **GATE:** DOCUMENTATION_CLOSURE_COMPLETE=NO; IMPLEMENTATION_AUTHORIZED=NO; TEST_NOT_RUN. Flags PASS antigas requerem revalidacao apos rebase.


## Revisão documental transversal — baseline 16/10/2026

**TARGET / REVIEW_INCONCLUSIVE / NO_RUNTIME_AUTHORIZATION.** Fonte de verdade das decisões P5: documento 37, decisões C2, D-P5-01..05 (conforme refinadas), P5-A..J e DEC-01..04. Quórum = um aceite por área obrigatória configurada e congelada na submissão; nova versão exige todos os aceites; reatribuição mantém autoria e aceite válido; P5 não possui reversão de aceite pela UI/endpoint V1; área pode rejeitar pacote e só o coordenador formal de competência com ACCESS efetivo, vínculo e scope pode confirmar rejeição terminal; não confirmação mantém decisão pendente e registra justificativa; rejeição terminal inativa ações projetadas, não apaga auditoria. P6 MANAGE + administrative_scope publica catálogo versionado prospectivo.

**Correção de interpretação:** menções anteriores a C2 pendente, unanimidade de indivíduos, delivery por e-mail de anexos e DEC-01..04 pendentes são histórico **STALE_EVIDENCE / SUPERSEDED**, não critérios vigentes. Referências `PASS` antigas de A12/A14/A15 ou dos freezes não se revalidam automaticamente por adendo; não usar essas flags para autorizar execução.

**Evidência verificada no GitHub:** `main` e branch documental foram comparados; a branch está divergente e a árvore combinada não foi verificada como limpa. O GitHub connector não fornece `git status` de workspace local. Inventário .cursor, consumers/producers, contratos atuais do Core/T05 e testes do HEAD não estão completos. Não foi executado smoke, e documento não prova runtime.

**Gate vigente:** `DECISION_REQUIRED_PRODUCT_P5=NONE_IDENTIFIED_AFTER_DEC01_DEC04` (reabrir somente com nova evidência); `GIT_INTEGRATION=PR78_MERGED_TO_MAIN_VERIFIED`; `CONTRACTS_AND_TEST_MATRIX=REVALIDATE`; `A12=REVALIDATE`; `A14=STALE_EVIDENCE`; `A15=STALE_EVIDENCE`; `DOCUMENTATION_CLOSURE_COMPLETE=NO`; `IMPLEMENTATION_AUTHORIZED=NO`. Antes do gate PASS: reconciliar branch com main, inventariar .cursor/T05 e contracts, verificar RQ/AC e teste matrix, harmonizar Help e declarar autorização transversal explícita. `TEST_NOT_RUN`.
