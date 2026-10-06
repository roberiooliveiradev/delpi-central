# 33 — Plano Mestre de Fechamento Documental

## Estado

**TARGET / DOCUMENTATION_CLOSURE_PHASE ACTIVE**

```text
IMPLEMENTATION_AUTHORIZED = NO
DOCUMENTATION_CLOSURE_COMPLETE = NO
PORTAL_DESIGN_FREEZE = PENDING_DOCUMENTATION_CLOSURE
PRODUCT_CONTRACT_FREEZE = PENDING_DOCUMENTATION_CLOSURE
FRONTEND_PATTERN_FREEZE = PENDING_DOCUMENTATION_CLOSURE
SECURITY_MODEL_FREEZE = PENDING_DOCUMENTATION_CLOSURE
TEST_STRATEGY_FREEZE = PENDING_DOCUMENTATION_CLOSURE
```

Este documento governa a fase anterior a qualquer implementação do Portal Controladoria & Finanças.

A decisão de lifecycle é explícita:

> primeiro fechar toda a documentação funcional, visual, de regras de negócio, segurança, Help, RQ/AC e testes planejados; somente depois reavaliar os freezes transversais e discutir autorização de runtime.

Nenhum estado `READY_FOR_IMPLEMENTATION_*` isolado autoriza código.

## Baseline e authorities

Produto:
- Portal Controladoria & Finanças;
- primeira funcionalidade: Central de Fechamento;
- primeiro processo: PROC-0072 — Gestão do Fechamento Mensal da Controladoria.

Authority:
1. instruções oficiais do arquiteto;
2. `.cursor` aplicável;
3. ADRs/contratos canônicos;
4. HEAD;
5. testes;
6. docs técnicas vigentes;
7. roadmap/planos;
8. legado/histórico.

Divisão de authority:
- TÉO / Transformômetro: AS-IS, proveniência e evidência de processo;
- GitHub: TARGET, contratos, ADRs, código, testes e SHAs.

AS-IS autoritativo do PROC-0072 confirma a cadeia macro:

```text
abertura da competência / checklist
→ geração e coleta dos entregáveis
→ conferência / conciliação / pendências
→ cutoff / revalidação / fechamento de estoque
→ consolidação / pacote / envio
→ dúvidas / complementos
→ conclusão mensal
```

A conciliação monetária exige paridade exata em centavos.

## Gate de trabalho vigente — FASE A

Decisão do Product Owner em 06/10/2026:

```text
DOCUMENTED != IMPLEMENTED
```

Não haverá implementação de nenhuma página durante a FASE A.

Ordem obrigatória de fechamento:

```text
Página do usuário
→ Início
→ Visão geral
→ Minhas tarefas
→ Sala de interação
→ Administração
→ Ajuda
→ P1 Cockpit da Competência
→ P2 Checklist e Documentos
→ P3 Estoque e Conciliação
→ P4 Classificações e Pendências
→ P5 Pacote, Finalização e Envio
→ P6 Administração / Configuração
→ REVISÃO TRANSVERSAL FINAL
→ CONTRATOS + REGRAS + SCRIPTS + TEST MATRIX
→ futura IMPLEMENTAÇÃO PAGE-BY-PAGE
```

Uma página entra na fila futura somente quando:

```text
VISUAL_SPEC_DEFINED
+ CONTRACT_DEFINED
+ AUTHZ_DEFINED
+ PLUGIN_UI_REUSE_DEFINED
+ STATES_DEFINED
+ TEST_MATRIX_DEFINED
= READY_FOR_IMPLEMENTATION_BRIEF
```

Mesmo `READY_FOR_IMPLEMENTATION_BRIEF` significa apenas maturidade documental.

### Page Documentation Gate V2

O pacote uniforme de cada página deve conter:

1. objetivo e responsabilidade;
2. owners de dados/regras e explicit non-goals;
3. família visual canônica;
4. wireframes desktop/mobile;
5. paridade light/dark;
6. componentes/full-pages do `@delpi/plugin-ui`, imports exatos e `DO NOT RECREATE`;
7. topbar/PageHero/PagePath/filtros/tabelas/master-detail/navegação conforme aplicável;
8. contratos TARGET MFE → BFF → owners, distinguindo contrato semântico de binding físico;
9. AuthZ somente com `controllership-finance.access` / `controllership-finance.manage`;
10. estados `LOADING / SUCCESS / EMPTY / PARTIAL / UNAVAILABLE / ERROR / 403 / 404`;
11. deep link/F5;
12. responsividade;
13. teclado/foco/acessibilidade;
14. Help sincronizada;
15. RQ/AC;
16. matriz positive + sibling + negative + experiência;
17. scripts/validators/artefatos PLANNED para futura implementação e teste;
18. inventories/stop conditions;
19. gate final `READY_FOR_IMPLEMENTATION_BRIEF` ou pendência explícita.

Qualquer `DOCUMENTATION_GATE PASS` emitido antes deste Gate V2 é tratado como **documentação existente a revalidar**, não como fechamento definitivo da FASE A.

## Regra de fechamento documental

Uma página só recebe `DOCUMENTATION_GATE PASS` quando existir evidência documental explícita para, conforme aplicável:

- objetivo/job;
- ownership e boundary;
- regras de negócio;
- atores e AuthZ;
- arquitetura de informação;
- jornada;
- desktop;
- mobile;
- light/dark;
- teclado/foco/acessibilidade;
- estados de experiência;
- source/freshness/partial;
- URL/deep link/F5;
- `@delpi/plugin-ui` reuse map;
- Help;
- RQ/AC;
- matriz futura positive/sibling/negative;
- inventários físicos restantes classificados;
- stop conditions;
- declaração `IMPLEMENTATION_AUTHORIZED = NO`.

A ausência de binding físico não impede o gate documental quando a semântica de produto estiver fechada e o binding estiver corretamente classificado como `TO_INVENTORY`.

Uma pendência **impede** o fechamento documental se ainda puder alterar materialmente:
- comportamento de negócio;
- owner;
- lifecycle/state machine;
- permission model;
- boundary;
- persistência semântica;
- integração obrigatória;
- experiência central da página.

## Progresso Gate V2

| Etapa | Página | Estado |
|---|---|---|
| A01 | Página do usuário | **PASS / READY_FOR_IMPLEMENTATION_BRIEF** |
| A02 | Início | **PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY** |
| A03 | Visão geral | **PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY** |
| A04 | Minhas tarefas | **PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY** |
| A05 | Sala de interação | **PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY** |
| A06 | Administração | **PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY** |
| A07 | Ajuda | **IN_REVIEW** |
| A08–A13 | Demais páginas | PENDING_V2_REVALIDATION |

A01 está apenas na fila futura. Runtime permanece inexistente.

## Inventário completo de superfícies V1

### Navegação e superfícies comuns

| Superfície | Authority principal | Estado atual | Trabalho documental restante |
|---|---|---|---|
| Navegação principal | 24 | DOCUMENTED | revisão final de coerência com Home, rotas e permission model |
| Início / Home | 32 | DOCUMENTATION_GATE PASS | residual scan após fechamento da Central |
| Visão geral | 25 | DOCUMENTATION_GATE PASS | residual scan; O04/O05 permanecem inventário físico |
| Sala de interação | 26 | DOCUMENTATION_GATE PASS | residual scan; R01–R05 técnicos |
| Minhas tarefas | 27 | DOCUMENTATION_GATE PASS | residual scan; TSK01–TSK05 técnicos |
| Administração | 28 | DOCUMENTATION_GATE PASS | residual scan; ADM01–ADM07 técnicos |
| Ajuda | 29 | DOCUMENTATION_GATE PASS | **revalidar por último**, após todas as features |
| Página do usuário | 31 | DOCUMENTATION_GATE PASS | residual scan / Core contract inventory |
| Topbar / shell | 24 + 30 | DOCUMENTED | confirmar que nenhuma rota futura/roadmap aparece como runtime |

### Central de Fechamento

| Página | Authority principal | Estado atual | Trabalho documental restante |
|---|---|---|---|
| P1 — Cockpit da Competência | 08 | DOCUMENTATION_GATE PASS | fechado; residual somente físico T01/T05 |
| P2 — Checklist e Documentos | 09 | DOCUMENTATION_GATE PASS | TÉO 31.3–31.13 reconciliado; residual seed/binding E05/E06/T02/T05 |
| P3 — Estoque, Cutoff e Conciliação | 10 + 15.1 | DOCUMENTATION_GATE BLOCKED_BY_E02 / STOP T03 | E02 exige decisão/evidência de regra pós-STOCK_CLOSED; T03 permanece stop técnico/owner |
| P4 — Classificações e Pendências | 11 | DOCUMENTATION_GATE PASS | residual cross-check com ledger/Help |
| P5 — Pacote, Finalização e Envio | 12 | DOCUMENTATION_GATE PASS para package/finalization | residual; envio real continua BLOCKED_WITH_EVIDENCE por E04/T04 |
| P6 — Administração e Configuração | 13 + 28 | page gate em 28 | alinhar 13 como authority de regra com o contrato completo de 28 |

Não criar nova página V1 apenas para eliminar backlog histórico.

## Sequência de fechamento das páginas

### DOC-PAGE-01 — P1

Fechar:
- status para `DOCUMENTATION_GATE PASS`;
- vínculo explícito com `RQ-P1-*` do ledger 23;
- matriz de testes futura;
- inventários T01/T05 separados de regras;
- gate final da página.

Não alterar:
- P1 continua composição/read-only;
- P1 não sacramenta;
- P1 não valida evidência;
- P1 não envia pacote;
- eixos Estoque/Documentos/Pacote permanecem independentes.

### DOC-PAGE-02 — P2

Reconciliar contra TÉO:
- 31.3 validação/rejeição/substituição/versionamento;
- 31.4 multi-anexo;
- 31.5 notificações;
- 31.6 sem SLA;
- 31.7 reversão;
- 31.8 notificação de reversão;
- 31.9 item excepcional;
- 31.10 edição;
- 31.11 cancelamento;
- 31.12 correção estrutural;
- 31.12.1 autoaprovação MANAGE;
- 31.13 decisões residuais.

Fechar explicitamente:
- snapshot;
- REQUIRED / CONDITIONAL / OPTIONAL;
- ATTACHED != VALIDATED;
- PER_ATTACHMENT / WHOLE_SET;
- rejeição e replacement;
- reversão;
- NOT_APPLICABLE;
- item excepcional;
- CANCELLED;
- structural correction;
- promoção ao mestre;
- notifications;
- ausência de SLA.

Depois:
- adicionar gate documental explícito;
- mapear cada regra a RQ/AC/Help/teste.

### DOC-PAGE-03 — P3

Fechar explicitamente:
- PRELIMINARY;
- WAITING_FOR_CUTOFF;
- REVALIDATION_REQUIRED;
- READY_TO_CLOSE;
- STOCK_CLOSED;
- cutoff humano;
- revalidação;
- source/freshness;
- zero pré-cutoff não final;
- paridade exata `R$ 0,00`;
- qualquer centavo diferente de zero bloqueia;
- V1 não grava sacramentação ERP.

T03 continua:
`TO_INVENTORY / STOP_CONDITION` para o estado canônico do owner.

T03 não reabre:
- fórmula;
- tolerância;
- visual state machine;
- boundary Portal != ERP authority.

Adicionar:
- gate documental explícito;
- RQ/AC trace;
- testes e Help linkage.

### DOC-PAGE-04 — P4

Já fechado page-level.

Executar somente:
- residual search contra 23 e 29;
- validar que nenhum RQ novo foi criado fora do ledger;
- confirmar boundary com Portal Financeiro P0.

### DOC-PAGE-05 — P5

Package/finalization está fechado.

Executar:
- residual search com ledger/Help;
- separar claramente:
  - `PACKAGE_FINALIZATION_DESIGN = PASS`;
  - `SEND_RUNTIME_CAPABILITY = BLOCKED_WITH_EVIDENCE`.

Nenhum fallback de envio é aceitável.

### DOC-PAGE-06 — P6

Usar:
- 13 como authority das regras funcionais;
- 28 como contrato completo de página.

Reconciliar:
- DRAFT → REVIEW → PUBLISH → EFFECTIVE_FROM;
- snapshot;
- prospective inactivation;
- um MANAGE publica com auditoria;
- catálogos tipados;
- referências a identidades Core;
- notifications como target lógico;
- optimistic concurrency;
- no hard delete.

Ao fim, 13 deve apontar explicitamente para o gate documental PASS de 28 sem duplicar UX.

### DOC-PAGE-07 — superfícies comuns

Depois de P1–P6:
- revisar 24, 25, 26, 27, 28, 31 e 32 por referências antigas;
- atualizar rotas, labels, states e links internos;
- nenhuma página pode expor capability ainda não implementada como runtime.

### DOC-PAGE-08 — Help final

29 é a última superfície a ser fechada novamente.

Validar:
- conceitos;
- FAQ;
- glossário;
- P1–P5;
- Administração;
- tarefas;
- sala;
- perfil;
- feature gating;
- deep links;
- ACCESS/MANAGE;
- envio real bloqueado;
- zero tolerance P3;
- source unavailable != zero;
- `pending_since != overdue`.

## Plano de consolidação das regras de negócio

O documento 04 deve se tornar o índice canônico de regras de negócio do TARGET, sem apagar proveniência AS-IS.

### RULE-01 — competência e snapshot

Consolidar:
- abertura de competência;
- template version;
- snapshot;
- publicação futura não altera competência aberta;
- histórico preserva versão usada.

### RULE-02 — requirement e satisfaction

Consolidar:
- REQUIRED;
- CONDITIONAL;
- OPTIONAL;
- ATTACHMENT_PRESENT;
- VALIDATION_REQUIRED;
- NOT_APPLICABLE;
- regras de bloqueio.

### RULE-03 — evidência e validação

Consolidar:
- ATTACHED != VALIDATED;
- multi-anexo;
- PER_ATTACHMENT;
- WHOLE_SET;
- rejection;
- replacement;
- reversão;
- evidência histórica imutável.

### RULE-04 — item excepcional e correção estrutural

Consolidar:
- item por competência;
- edição pré-execução;
- CANCELLED;
- pós-execução por request/review/nova revisão;
- MANAGE pode autoaprovar com trilhas separadas;
- promoção ao mestre não é retroativa.

### RULE-05 — fontes e completude

Consolidar:
- source unavailable != zero;
- source unavailable != empty;
- preliminary != final;
- freshness/proveniência;
- partial isolation;
- conta sem movimento pode continuar aplicável;
- `NO_MOVEMENT != NOT_APPLICABLE`.

### RULE-06 — regras financeiras/relatórios confirmados

Preservar do 04 atual:
- SD1 / centro de custo;
- Kardex 01;
- Kardex 99;
- Faturamento × MOD;
- FINR190;
- P7 / MATR460;
- MATR860 != P7;
- vocabulário fiscal;
- sem inferência de campo físico Protheus.

### RULE-07 — conciliação monetária

Canônico:

```text
DIVERGENCIA = ENTRADAS_SAIDAS - P7 - H02
PARIDADE_OK <=> DIVERGENCIA = R$ 0,00
TOLERANCIA_MONETARIA = NONE
```

Nenhum epsilon/tolerância.

### RULE-08 — cutoff e fechamento de estoque

Consolidar:
- cutoff não é horário fixo;
- confirmação humana;
- revalidação pós-cutoff;
- READY_TO_CLOSE;
- STOCK_CLOSED canônico do owner se existir;
- V1 não grava fechamento ERP.

### RULE-09 — classificação e pendências

Consolidar:
- IA sugere;
- humano confirma;
- Portal registra decisão;
- sem write ERP V1;
- ownership/fila;
- claim/reassign;
- OPEN / IN_ANALYSIS / WAITING_EXTERNAL / RESOLVED / DISMISSED;
- dismiss com justificativa;
- sem SLA/overdue.

### RULE-10 — pacote e conclusão mensal

Consolidar:

```text
READY_TO_FINALIZE
!= PACKAGE_FINALIZED
!= PACKAGE_SENT
!= MONTHLY_CLOSING_COMPLETED
```

Mais:
- versões;
- reabertura antes do envio;
- recipient packages independentes;
- PACKAGE_SENT imutável;
- complemento/nova versão pós-envio;
- esclarecimentos;
- conclusão somente com todos pacotes aplicáveis enviados e zero esclarecimento aberto;
- acknowledgement opcional.

### RULE-11 — administração e catálogos

Consolidar:
- draft/review/publish/effective_from;
- snapshot;
- sem hard delete;
- listas operacionais configuráveis;
- bancos/contas;
- motivos de rejeição;
- attachment roles;
- people references Core;
- notification targets;
- effective dating.

### RULE-12 — notificações e temporalidade

Consolidar:
- Minha DELPI como superfície;
- e-mail conforme plataforma;
- failure não muda business state;
- histórico de delivery;
- sem SLA global;
- `PENDING_SINCE = YES`;
- `DUE_DATE / OVERDUE / SLA_BREACH = NO` salvo owner explícito.

### RULE-13 — AuthZ

Canônico:

```text
JWT = identity/context
Core = effective permission authority

allow
= capability
AND resource_scope / ownership
AND business_rule
```

Somente:
- `controllership-finance.access`;
- `controllership-finance.manage`.

### RULE-14 — IA

Consolidar:
- explicar/resumir/sugerir;
- somente dados autorizados;
- não muda state;
- não valida;
- não sacramenta;
- não envia;
- não contorna owner/permission.

### RULE-15 — colaboração e tarefas

Consolidar:
- mensagem != decisão de negócio;
- room participant != ACL;
- chat attachment != evidência P2;
- TaskProjection != task entity;
- self-only;
- ação genérica = abrir owner;
- nenhum SLA global derivado.

## Revisão dos residuais E01–E06

A fase documental deve reavaliar os E-items para separar **dado de implantação** de **regra material ainda incompleta**.

| ID | Tema | Tratamento no fechamento documental |
|---|---|---|
| E01 | seed bancário | tentar fechar owner/semântica; valores seed podem permanecer implantação se não alterarem contract |
| E02 | correção pós-STOCK_CLOSED | **DECISION_REQUIRED**: evidência AS-IS/TÉO atual não define reabertura/correção após sacramentação; precisa regra explícita antes do freeze |
| E03 | executor/permissões de sacramentação | provar owner/segregação até o nível necessário para boundary/Help; binding físico pode ficar T03/T05 |
| E04 | canal real de envio | não inventar; enquanto ausente, envio real permanece slice bloqueado |
| E05 | attachment roles | semântica já fechada; seed pode ficar implantação |
| E06 | motivos de rejeição | modelo já fechado; seed/cobertura inicial pode ficar implantação |

Regra:

```text
implementation data
!=
open product design
```

Mas:

```text
material business behavior unresolved
=
DOCUMENTATION BLOCKER
```

## Revisão dos inventários T01–T05

T01–T05 permanecem inventários técnicos **quando** não alterarem o contrato de negócio.

- T01 — bindings DAVI/api-delpi;
- T02 — notificações Minha DELPI;
- T03 — owner/canonical STOCK_CLOSED;
- T04 — capability corporativa de envio;
- T05 — Core effective permissions/scopes.

Se o inventário provar semântica incompatível com o TARGET:
`EXECUTION_DRIFT`.

## RQ / AC / testes

23 deve ser revalidado após a consolidação das páginas e regras.

Critérios:
- todo RQ material tem aceite;
- todo RQ material tem teste mínimo ou referência explícita à matriz transversal;
- nenhum RQ é PASS por associação;
- P3 mantém AC-P3-PARITY-01..07;
- AuthZ inclui positive/sibling/negative;
- source unavailable/partial têm sibling tests;
- deep link/F5;
- light/dark;
- mobile;
- keyboard/focus;
- Help;
- state-machine negatives;
- no permission proliferation.

Residual atual conhecido:
- RQ-SEC-01..06 e RQ-UX-01..06 precisam rastreabilidade explícita para a matriz de testes, mesmo que a estratégia transversal já exista.

## Cobertura histórica / futuros macroprocessos

20 permanece backlog de preservação, não escopo implícito da Central.

Não bloquear o V1 atual por:
- CTL-006 — custo de mão de obra homologado/versionado;
- CTL-007 — visão ampla de custos de importação;
- expansão CTL-005 além do fechamento;
- KPIs históricos sem fórmula/owner.

Esses itens exigem futuro gate de produto quando forem promovidos para escopo.

## Ordem de execução documental — Gate V2

```text
A01 Página do usuário
A02 Início
A03 Visão geral
A04 Minhas tarefas
A05 Sala de interação
A06 Administração
A07 Ajuda
A08 P1 Cockpit da Competência
A09 P2 Checklist e Documentos
A10 P3 Estoque e Conciliação
A11 P4 Classificações e Pendências
A12 P5 Pacote, Finalização e Envio
A13 P6 Administração / Configuração
A14 Revisão transversal final
A15 Consolidação contracts + regras + scripts + test matrix
A16 Documentation closure review
```

Nenhum passo A01–A16 inclui scaffold, endpoint runtime, migration, permission, schema físico ou implementação de página.

## Gate final de fechamento documental

`DOCUMENTATION_CLOSURE_COMPLETE = PASS` somente se:

- [ ] todas as superfícies V1 possuem authority clara;
- [ ] P1–P6 possuem gate documental explícito ou contrato page-level canônico referenciado;
- [ ] páginas comuns permanecem sincronizadas;
- [ ] 04 consolida todas as regras TARGET materiais;
- [ ] AS-IS/TARGET estão separados;
- [ ] nenhuma regra material usa `UNKNOWN` como sucesso;
- [ ] nenhuma escolha de produto aberta está escondida como inventário;
- [ ] E01–E06 foram reclassificados por materialidade;
- [ ] T01–T05 estão claramente técnicos ou viraram drift;
- [ ] 14/16/21 não contradizem páginas;
- [ ] 23 cobre RQ/AC/testes;
- [ ] 29 está sincronizado com todas as páginas;
- [ ] 30 cobre todas as páginas que reutilizam plugin-ui;
- [ ] 19 continua rastreável ao TÉO;
- [ ] README e 18 refletem o estado final;
- [ ] residual search não encontra permission extra, state conflitante, owner duplicado ou capability antecipada;
- [ ] `IMPLEMENTATION_AUTHORIZED = NO`.

Somente depois deste gate devem ser reavaliados:

```text
PORTAL_DESIGN_FREEZE
PRODUCT_CONTRACT_FREEZE
SECURITY_MODEL_FREEZE
TEST_STRATEGY_FREEZE
```

E mesmo com os quatro em PASS, runtime só começa após decisão explícita posterior do usuário.

## Stop condition

Durante o fechamento documental, se surgir escolha real de:
- produto;
- owner;
- boundary;
- permission;
- lifecycle;
- state machine;
- integração;
- persistência semântica;
- breaking contract;
- escopo V1;

retornar `DECISION_REQUIRED` e não preencher a lacuna por preferência.
