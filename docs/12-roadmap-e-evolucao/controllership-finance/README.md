# Portal Controladoria & Finanças

> **Status:** TARGET consolidado / implementação não iniciada  
> **Produto:** Portal Controladoria & Finanças  
> **Primeira funcionalidade:** Central de Fechamento  
> **Primeiro processo:** PROC-0072 — Gestão do Fechamento Mensal da Controladoria  
> **Consolidação:** 05/10/2026

## Objetivo

O **Portal Controladoria & Finanças** é o produto multi-macroprocesso da Minha DELPI para concentrar processos, automações, visões operacionais, evidências, pendências, decisões e capacidades de gestão do domínio de Controladoria & Finanças.

A primeira funcionalidade é a **Central de Fechamento**. O primeiro processo especificado é o **PROC-0072 — Gestão do Fechamento Mensal da Controladoria**.

```text
Minha DELPI
└── Portal Controladoria & Finanças
    ├── Central de Fechamento
    │   └── Fechamento Mensal / PROC-0072
    └── futuros macroprocessos
```

O portal não deve ser tratado como aplicação exclusiva de fechamento. A arquitetura deve permitir novos macroprocessos sem renaming do produto.

## Estado

- AS-IS PROC-0072: **CLOSED / ACCEPTED**
- baseline: **1 fechamento/mês; 960 min INFORMED**
- TO-BE: **TARGET consolidado**
- implementação: **NOT_STARTED**
- A14 revisão transversal: **PASS**
- A15 contracts/regras/scripts/test matrix: **PASS_WITH_RESIDUAL_E04_T04**
- `PORTAL_DESIGN_FREEZE`: **PASS**
- `FRONTEND_PATTERN_FREEZE`: **PASS**
- `SECURITY_MODEL_FREEZE`: **PASS**
- `TEST_STRATEGY_FREEZE`: **PASS**
- `PRODUCT_CONTRACT_FREEZE`: **DECISION_REQUIRED_P5_REVIEW_COMPLETION**
- `DOCUMENTATION_CLOSURE_COMPLETE`: **NO**
- ROI: **não calculado**
- P1/P2: **PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY**
- P3: **PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY / STOP_CONDITION_ON_T03**
- P4: **PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY**
- P5 pacote/finalização: **PAGE_DOCUMENTATION_GATE_V2 PACKAGE_FINALIZATION_READY**
- P6/Administração: **PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY**
- P5 envio para análise: **PORTAL-FIRST MODEL DEFINED**; package fica na Minha DELPI; residual é a regra de monthly completion após review
- handoff funcional P1–P6: **DOCUMENTED**, sujeito aos inventories E/T da página

## Documentação

| Documento | Finalidade |
|---|---|
| [00-governanca-e-authorities.md](./00-governanca-e-authorities.md) | autoridades, evidência e drift |
| [01-visao-produto-naming-e-escopo.md](./01-visao-produto-naming-e-escopo.md) | naming, escopo e fronteiras |
| [02-proc-0072-as-is-e-baseline.md](./02-proc-0072-as-is-e-baseline.md) | processo atual e baseline |
| [03-evidencias-proveniencia-e-rastreabilidade.md](./03-evidencias-proveniencia-e-rastreabilidade.md) | fontes e proveniência |
| [04-regras-de-negocio-consolidadas.md](./04-regras-de-negocio-consolidadas.md) | GAP-RULE-01 a 07 |
| [05-diagnostico-gaps-e-oportunidades.md](./05-diagnostico-gaps-e-oportunidades.md) | diagnóstico e oportunidades |
| [06-arquitetura-funcional-to-be.md](./06-arquitetura-funcional-to-be.md) | modelo funcional |
| [07-ux-jornadas-e-estados-de-experiencia.md](./07-ux-jornadas-e-estados-de-experiencia.md) | UX transversal |
| [08-p1-cockpit-da-competencia.md](./08-p1-cockpit-da-competencia.md) | P1 |
| [09-p2-checklist-e-documentos.md](./09-p2-checklist-e-documentos.md) | P2 |
| [10-p3-estoque-cutoff-e-conciliacao.md](./10-p3-estoque-cutoff-e-conciliacao.md) | P3 |
| [11-p4-classificacoes-e-pendencias.md](./11-p4-classificacoes-e-pendencias.md) | P4 |
| [12-p5-pacote-finalizacao-e-envio.md](./12-p5-pacote-finalizacao-e-envio.md) | P5 |
| [13-p6-administracao-e-configuracao.md](./13-p6-administracao-e-configuracao.md) | P6 |
| [14-seguranca-rbac-auditoria-e-ia.md](./14-seguranca-rbac-auditoria-e-ia.md) | AuthZ, auditoria e IA |
| [15-requisitos-criterios-de-aceite-e-testes.md](./15-requisitos-criterios-de-aceite-e-testes.md) | RQ/AC e testes transversais |
| [15.1-p3-criterios-paridade-monetaria.md](./15.1-p3-criterios-paridade-monetaria.md) | ACs específicos de paridade monetária P3 |
| [16-configuracoes-catalogos-e-notificacoes.md](./16-configuracoes-catalogos-e-notificacoes.md) | configurações e notificações |
| [17-backlog-de-confirmacoes-e-inventarios.md](./17-backlog-de-confirmacoes-e-inventarios.md) | E01–E06 e T01–T05 |
| [18-readiness-e-handoff-de-implementacao.md](./18-readiness-e-handoff-de-implementacao.md) | readiness e handoff |
| [19-rastreabilidade-teo.md](./19-rastreabilidade-teo.md) | mapa dos registros TÉO |
| [20-transforma-plus-coverage.md](./20-transforma-plus-coverage.md) | cobertura CTL/CORE e residuais Transforma+ |
| [21-boundaries-produtos-e-owners.md](./21-boundaries-produtos-e-owners.md) | boundaries, owners e integrações |
| [22-handoff-implementacao-p1-p6.md](./22-handoff-implementacao-p1-p6.md) | handoff funcional uniforme P1–P6 |
| [23-ledger-rq-ac-testes.md](./23-ledger-rq-ac-testes.md) | ledger RQ → AC → teste → dependência |
| [24-inicio-e-navegacao-principal.md](./24-inicio-e-navegacao-principal.md) | topbar e página Início |
| [25-visao-geral-indicadores-financeiros.md](./25-visao-geral-indicadores-financeiros.md) | Visão geral com indicadores financeiros |
| [26-sala-de-interacao.md](./26-sala-de-interacao.md) | Sala de interação contextual |
| [27-minhas-tarefas.md](./27-minhas-tarefas.md) | projeção pessoal de tarefas |
| [28-administracao.md](./28-administracao.md) | página de Administração / P6 |
| [29-ajuda.md](./29-ajuda.md) | manual e Help contextual |
| [30-plugin-ui-reuse-map.md](./30-plugin-ui-reuse-map.md) | mapa canônico página → componente → import de `@delpi/plugin-ui` |
| [31-pagina-do-usuario.md](./31-pagina-do-usuario.md) | perfil de usuário, wireframes, contracts, AuthZ e reuso full-page do `plugin-ui` |
| [32-inicio-home.md](./32-inicio-home.md) | Home comum do Portal, wireframes, launcher, eventos, busca, recentes e favoritos |
| [33-plano-mestre-fechamento-documental.md](./33-plano-mestre-fechamento-documental.md) | plano mestre para fechar páginas, regras, RQ/AC, Help e gates antes de runtime |
| [34-revisao-transversal-gate-v2.md](./34-revisao-transversal-gate-v2.md) | revisão transversal de naming, owners, security, routes, plugin-ui, states, Help e contracts |
| [35-contratos-regras-scripts-test-matrix-gate-v2.md](./35-contratos-regras-scripts-test-matrix-gate-v2.md) | consolidação A15 de contracts, regras, validators/scripts e test matrix |
| [36-e04-t04-package-delivery-decision-packet.md](./36-e04-t04-package-delivery-decision-packet.md) | histórico superseded do inventário de delivery externo; premissa invalidada |
| [37-p5-submissao-e-revisao-no-portal.md](./37-p5-submissao-e-revisao-no-portal.md) | contrato TARGET de submit/review in-portal, reviewers autenticados e notifications |

## Página do usuário

A página transversal de perfil está especificada em [31-pagina-do-usuario.md](./31-pagina-do-usuario.md).

Decisões congeladas:

- usuário com `controllership-finance.access` pode consultar o perfil corporativo básico de outro usuário com acesso ao mesmo Portal;
- permissions/capabilities de outro usuário não são expostas;
- no próprio perfil, exibir label amigável + códigos técnicos `controllership-finance.access` / `controllership-finance.manage` quando efetivos;
- identidade/foto continuam owned pelo Core; não criar persistência local no Portal;
- usar `createDashboardPortalUserProfilePage` como full-page reusable antes de qualquer composição local.

A rota é deep route e **não** adiciona item à topbar.

## Início

O Item 2 — Início está fechado documentalmente em [32-inicio-home.md](./32-inicio-home.md).

A Home segue a família visual comum dos Portais Minha DELPI: saudação/Hero → Eventos e interações → Caminhos e funcionalidades → Últimos acessos/cards. Indicadores financeiros permanecem na Visão geral. Implementação continua não autorizada nesta fase de revisão global.

## Sala de interação

O Item 4 — Sala de interação está fechado documentalmente em [26-sala-de-interacao.md](./26-sala-de-interacao.md).

Decisões congeladas:
- usar `InteractionRoomPage` do `@delpi/plugin-ui`;
- sem chat genérico/global wall na V1;
- uma sala contextual estável por competência, checklist item, pendência/classificação ou pacote;
- participants não são ACL;
- ACCESS + acesso ao contexto;
- edição própria + soft-delete;
- chat attachment não vira evidência P2 automaticamente;
- realtime/storage/retention são inventories técnicos futuros;
- criar tarefa a partir de mensagem fica fora da V1; evolução futura exige entidade/owner de task explicitamente aprovados.

Implementação permanece não autorizada durante o review global.

## Minhas tarefas

O Item 5 — Minhas tarefas está fechado documentalmente em [27-minhas-tarefas.md](./27-minhas-tarefas.md).

Decisões congeladas:
- usar `TaskWorkspacePage` e primitives de tasks do `@delpi/plugin-ui`;
- `TaskProjection` é projeção de trabalho dos owners, não entidade genérica;
- sem `Nova tarefa`, editor genérico, team scope ou completed bucket na V1;
- ação V1 é `Abrir` o contexto owner;
- P2/P4 são producers quando houver responsabilidade individual; P5 é conditional até provar assignee user-centric;
- sem SLA global; due/overdue só quando o owner fornecer;
- Home consome a mesma projeção;
- Sala não cria task genérica na V1;
- estratégia física de projection permanece inventário técnico.

Implementação permanece não autorizada durante o review global.

## Administração

O Item 6 — Administração está fechado documentalmente em [28-administracao.md](./28-administracao.md).

Decisões congeladas:
- uma única permission administrativa: `controllership-finance.manage`;
- MANAGE não implica ACCESS operacional;
- subáreas: Painel, Templates, Catálogos e Histórico;
- catálogos não viram topbar nem permission;
- template segue DRAFT → REVIEW → PUBLISH → EFFECTIVE_FROM;
- publicação não altera snapshots de competências abertas;
- inativação é prospectiva e sem hard delete;
- responsáveis/validators/destinatários referenciam identidades do Core, sem criar usuário/RBAC;
- notification targets configuram destinatários lógicos, não infraestrutura SMTP;
- optimistic concurrency é obrigatório; mecanismo físico fica para inventário;
- `@delpi/plugin-ui` fornece o chrome administrativo reutilizável.

Implementação permanece não autorizada durante o review global.

## Ajuda

O Item 7 — Ajuda está fechado documentalmente em [29-ajuda.md](./29-ajuda.md).

Decisões congeladas:
- usar `createDashboardUserManual` do `@delpi/plugin-ui`;
- conteúdo do manual é versionado no MFE, sem BFF/DB/CMS/editor administrativo na V1;
- runtime Help documenta somente capabilities realmente implementadas;
- Help contextual aponta para `/help#manual-{sectionId}`;
- Administração só entra no manual para viewer com `controllership-finance.manage`;
- tool links usam registry tipado e nunca URL arbitrária;
- sem search engine própria no manual V1;
- FAQ, glossário e guide table seguem o kit;
- mudança user-facing material exige Help sync no mesmo gate.

Implementação permanece não autorizada durante o review global.

## Navegação principal

A topbar do Portal é:

```text
Início | Visão geral | Sala de interação | Minhas tarefas | Administração | Ajuda
```

As páginas P1–P5 pertencem à Central de Fechamento e não viram itens independentes da topbar.

A Visão geral é a superfície analítica financeira do Portal. O padrão visual, filtros, states, drilldowns e conjunto V1 estão documentados em [25-visao-geral-indicadores-financeiros.md](./25-visao-geral-indicadores-financeiros.md). Decisões congeladas: D-OVW-01=C (núcleo financeiro + contexto operacional + desempenho estratégico), D-OVW-02=A (mês atual) e D-OVW-03=A (Consolidado).

## Invariantes

1. `STOCK_CLOSED != PACKAGE_SENT != MONTHLY_CLOSING_COMPLETED`
2. `ATTACHED != VALIDATED`
3. ausência/erro de source != zero
4. pre-cutoff dependente != final
5. último upload != auto-send
6. Finalizar != Enviar
7. PACKAGE_SENT é imutável
8. mudança mestre não altera snapshot
9. listas operacionais são configuráveis
10. IA sugere/explica; humano decide
11. `ACCESS != MANAGE`
12. aprovação administrativa != validação
13. sem SLA formal
14. V1 sem escrita ERP para sacramentação/classificação
15. paridade monetária da conciliação tripla exige exatamente R$ 0,00; não existe tolerância de centavos

## Produtos existentes

`plugins/financial` + `financial-api` e o roadmap `financeiro-controladoria` continuam distintos. O novo portal não absorve nem remove esses contextos automaticamente.

## UI kit

Toda implementação frontend deve seguir [30-plugin-ui-reuse-map.md](./30-plugin-ui-reuse-map.md). A página de usuário segue também o contrato visual/funcional de [31-pagina-do-usuario.md](./31-pagina-do-usuario.md). O Início segue [32-inicio-home.md](./32-inicio-home.md). Minhas tarefas segue [27-minhas-tarefas.md](./27-minhas-tarefas.md). Administração segue [28-administracao.md](./28-administracao.md). Ajuda segue [29-ajuda.md](./29-ajuda.md).

Import runtime canônico para MFE federado:

```ts
import { ... } from "@delpi/plugin-ui/index";
await import("@delpi/plugin-ui/styles");
```

Não recriar localmente componentes já exportados pelo kit.

## Handoff para implementação

A cobertura Transforma+, boundaries, handoff P1–P6 e ledger de requisitos estão consolidados em 20–23.

Isso permite preparar briefs técnicos página por página. A identidade técnica do produto está congelada como `controllership-finance` + `controllership-finance-api`, com base paths `/apps/controllership-finance` e `/apps/controllership-finance-api`. Storage, schemas físicos, migrations e deployment continuam dependentes de inventário do HEAD.

## FASE A — Design / Documentação Completa

Gate vigente:

```text
DOCUMENTED != IMPLEMENTED
```

A ordem e o pacote uniforme de fechamento são canônicos em [33-plano-mestre-fechamento-documental.md](./33-plano-mestre-fechamento-documental.md).

Nenhum `DOCUMENTATION_GATE PASS` anterior ao Page Documentation Gate V2 é autorização ou fechamento final da FASE A; cada página será revalidada na ordem A01–A13.

## Gate global de revisão

O fechamento documental integral é governado por [33-plano-mestre-fechamento-documental.md](./33-plano-mestre-fechamento-documental.md).

A fase atual é exclusivamente documental/design/contratos:

```text
PORTAL_REVIEW_PHASE = ACTIVE
DOCUMENTATION_CLOSURE_PHASE = ACTIVE
PAGE_DOCUMENTATION_GATE = V2
DOCUMENTATION_CLOSURE_COMPLETE = NO
IMPLEMENTATION_AUTHORIZED = NO
```

Nenhuma página deve ser implementada enquanto não forem revisadas e fechadas todas as superfícies do Portal, incluindo páginas comuns, P1–P6, padrões visuais, contracts, AuthZ, estados, Help, RQ/AC e matriz de testes/scripts planejados.

`READY_FOR_IMPLEMENTATION_BRIEF` significa somente que a página já possui documentação suficiente para um brief futuro.

Somente após um gate transversal explícito do produto:

```text
PORTAL_DESIGN_FREEZE = PASS
PRODUCT_CONTRACT_FREEZE = PASS
SECURITY_MODEL_FREEZE = PASS
TEST_STRATEGY_FREEZE = PASS
```

poderá começar a implementação page-by-page.

## Execução

```text
READ → INVENTORY → VERIFY → CLASSIFY → DECIDE
→ IMPLEMENT MINIMAL DIFF → TEST → VERIFY OUTCOME
→ RESIDUAL SEARCH → DOCUMENT → REPORT
```
