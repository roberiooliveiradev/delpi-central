# 21 — Boundaries de Produto, Owners e Integrações

## Objetivo

Fixar as fronteiras funcionais e de ownership necessárias para implementar o Portal Controladoria & Finanças sem absorver produtos existentes, duplicar regras ou inventar ownership técnico.

Este documento complementa [01-visao-produto-naming-e-escopo.md](./01-visao-produto-naming-e-escopo.md). Não define nomes técnicos ainda não inventariados.

## Boundary principal

| Contexto | Estado | Responsabilidade |
|---|---|---|
| Portal Controladoria & Finanças | TARGET / NOT_STARTED | UX/composição funcional da Controladoria & Finanças; Central de Fechamento é a primeira funcionalidade |
| Portal Financeiro P0 | PROVEN / runtime atual | gestão à vista, faturamento, inadimplência, despesas por CC, frete, indicadores; permanece `plugins/financial` + `financial-api` |
| Core | authority de plataforma | apps, manifest, rotas, effective permissions, RBAC, usuários e auditoria de plataforma |
| api-delpi | owner de integração TOTVS/Protheus | SQL, consultas e regras canônicas de acesso aos dados TOTVS conforme contracts vigentes |
| Portal Suprimentos / owners de Suprimentos | contexto distinto | custos/importações e demais regras próprias; CTL-007 não autoriza duplicação de fonte |
| Planejamento Orçamentário | contexto distinto | orçamento, aprovações e capacidades próprias; não é fechamento mensal da Controladoria |
| Lançamento de NF | contexto distinto | fluxo próprio de notas; não é automaticamente parte interna da Central de Fechamento |
| Minha DELPI — notificações | capability de plataforma | notification in-app + e-mail conforme configuração/preferência; não transporta package P5 |
| demais contextos | owners próprios | regras de domínio permanecem no contexto que as possui |

## Produto novo ≠ Portal Financeiro P0

O Portal Controladoria & Finanças não implica:

- absorção automática de `plugins/financial`;
- desativação de `financial-api`;
- migração de telas do P0;
- banco compartilhado por conveniência;
- transferência de permissions;
- mudança de ownership de despesas por centro de custo;
- reutilização automática da arquitetura técnica do Portal Financeiro.

Integração ou navegação entre os produtos pode ser proposta durante implementação, mas deve seguir contratos e owners reais.

## Centro de custo / classificação

A P4 trata a **fatia de classificação e pendências necessária ao fechamento**.

O fato de o Portal Financeiro P0 já possuir despesas por centro de custo não torna P4 duplicata do P0.

Regra de boundary:

```text
P0 financial cost-centers
!=
P4 closing classification assistance
```

P4 V1:
- pode explicar/sugerir;
- exige confirmação humana;
- registra decisão no Portal;
- não grava correção no ERP;
- owner da autoridade de CC permanece gestor/solicitante quando aplicável.

Expansão para classificação corporativa fora do fechamento exige decisão específica.

## Importações / custos de importação

O fechamento pode consumir entregáveis de importação quando necessários ao PROC-0072.

Isso não autoriza o Portal a criar uma segunda fonte de custos de importação.

```text
MESMA FONTE AUTORIZADA
→ VISÕES DIFERENTES POR PERFIL/CONTEXTO
```

CTL-007 amplo permanece candidato futuro e depende do owner/binding de Suprimentos/ACSI.

## TOTVS / Protheus

O Portal não se torna owner de regra TOTVS.

Bindings físicos — endpoints, tabelas, campos, relatórios, filtros, códigos e freshness — são inventariados em T01 e validados no owner competente.

V1 não assume escrita ERP para:
- sacramentação de estoque;
- classificação/centro de custo.

## AuthN / AuthZ

JWT identifica e contextualiza; não é fonte final de permissions.

A autorização segue:

```text
capability
AND resource_scope / ownership
AND business_rule
```

Core resolve effective permissions. O backend do produto, quando definido, deve autorizar server-side e fail-closed.

`ACCESS` opera. `MANAGE` administra. Validator não é sinônimo de MANAGE.

T05 define os bindings reais sem criar permission por botão/tela/CRUD.

Para este Portal, não haverá permission code por filial/unidade. Unidade pode existir como contexto/filtro de dados, não como dimensão de RBAC própria do produto.

## Notificações

O Portal gera eventos de negócio. A superfície/capability canônica é Minha DELPI.

Não criar SMTP, opt-in, preference store ou canal paralelo no produto por conveniência.

T02 inventaria API/evento/templates/preferences/delivery/deep links.

## Regra de integração entre contextos

Integração deve ocorrer por contrato autorizado — HTTP, evento ou outro contrato formal vigente.

Não:
- importar `domain/application` de contexto vizinho;
- ler banco de outro contexto diretamente;
- espelhar estado TOTVS sem decisão explícita;
- duplicar catálogo/regra de outro owner apenas para reduzir chamadas.

## Runtime técnico do novo Portal

Identidade técnica já congelada:

```text
plugin id     = controllership-finance
plugin folder = plugins/controllership-finance
basePath      = /apps/controllership-finance
BFF/service   = controllership-finance-api
BFF baseUrl   = /apps/controllership-finance-api
CSS root      = .portal-controllership-finance
```

Continuam `TO_INVENTORY` conforme o slice:

- necessidade real de storage;
- schemas físicos;
- migrations;
- deployment topology;
- bindings externos;
- contratos físicos/OpenAPI ainda não implementados.

Essas decisões não devem ser derivadas do Portal Financeiro P0.

### TaskProjection / Minhas tarefas

Para [27-minhas-tarefas.md](./27-minhas-tarefas.md):
- `controllership-finance-api` compõe uma projeção read-only das responsabilidades dos owners;
- P2/P4 permanecem owners do business state;
- P5 só entra quando houver responsabilidade individual comprovada;
- não existe task entity genérica na V1;
- não importar task/domain do Comercial;
- não copiar endpoints `/tasks` do `commercial-api`;
- não persistir lifecycle paralelo apenas para montar worklist;
- a estratégia física da projection pode ser on-read/materialized/event-driven, mas deve preservar owner/source e partial coverage;
- a ação V1 navega ao owner; business writes continuam no contexto owner.

### P5 / reviewers externos

Para [12-p5-pacote-finalizacao-e-envio.md](./12-p5-pacote-finalizacao-e-envio.md):

- package/version/finalization/submission/review state permanecem owned por `controllership-finance-api`;
- package permanece na Minha DELPI;
- reviewer externo é Core identity com app access;
- reviewer usa `controllership-finance.access` + resource scope/assignment;
- não criar permission `.review`;
- Core Notifications owns notification delivery in-app/e-mail;
- e-mail é aviso/deep link, não transport do package;
- TaskProjection pode projetar review acionável, mas P5 permanece owner;
- reviewer não recebe MANAGE por ser destinatário.

### Administração / master data

Para [28-administracao.md](./28-administracao.md):
- `controllership-finance-api` é owner do estado próprio de templates, catálogos, vigências e auditoria administrativa do produto;
- Core continua owner de identidade, app access, effective permissions e RBAC;
- responsible/validator/recipient armazenam referências a identidades do Core, não cópias autoritativas nem permission grants;
- Minha DELPI continua owner da capability de notificações; P6 configura targets lógicos, não SMTP/preferences;
- api-delpi/TOTVS não recebe write direto de P6 apenas porque um catálogo representa banco/conta ou outro dado operacional;
- snapshots de competências abertas permanecem no owner operacional e não são reescritos por publicação nova;
- não importar domain/application do Comercial para copiar administração;
- não usar banco de outro Portal como master-data store.

### Identidade de usuário

Para a Página do usuário:
- Core é owner de diretório, person profile, foto e effective permissions;
- o Portal principal Minha DELPI é a superfície canônica de **autoedição** do person profile e da foto, usando `/core-api/me/person-profile` e `/core-api/me/person-profile/photo`;
- `controllership-finance-api` compõe e autoriza apenas a leitura necessária ao produto;
- o MFE de Controladoria apresenta esses dados em modo read-only e redireciona o self para Meu Perfil quando houver intenção de editar;
- não importar internals de Core nem ler seu banco;
- não persistir cópia local de identidade/foto;
- não criar proxy de write, editor de cargo/contatos nem upload de foto dentro do Portal Controladoria & Finanças.

Fonte: [31-pagina-do-usuario.md](./31-pagina-do-usuario.md).

## Regra de conflito

Se a implementação real no HEAD provar owner, contrato ou capability diferente do presumido neste handoff:

```text
EXECUTION_DRIFT
→ parar subgrafo afetado
→ registrar evidência
→ revalidar documentação/plano
```

Não adaptar silenciosamente o produto para contornar o owner real.


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

**DECISION_REQUIRED / ainda não inferir:** (1) efeito de reatribuição formal sobre aceite já registrado; (2) procedimento de alteração do próprio aceite compatível com irreversibilidade da UI V1; (3) mapeamento/configuração de áreas obrigatórias e elegibilidade corporativa; (4) momento e autoridade da rejeição terminal da competência quando mais de uma área participa; (5) tratamento das tarefas pendentes dos demais revisores após rejeição terminal. Separar decisões de produto de inventários físicos (DTO, Core eligibility resolver, storage, adapters).

**Gate:** `PRODUCT_CONTRACT_FREEZE = PENDING_DERIVED_RULES`; `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `IMPLEMENTATION_AUTHORIZED = NO`. Estes textos registram decisões de produto, não demonstram testes, código, contratos físicos, rebase nem execução de smoke.


## Decisões PO P5-F a P5-J — consolidação contratual vigente (16/10/2026)

**TARGET / PO_APPROVED / DOCUMENTED_NOT_IMPLEMENTED.** Este adendo é superveniente aos registros de perguntas abertas P5-F..J e prevalece quando notas históricas anteriores conflitarem. C2, D-P5-02..05 e P5-A..E permanecem válidas nos termos abaixo. A antiga unanimidade de *pessoas* em D-P5-01 foi substituída pela unanimidade das *áreas obrigatórias* em P5-A.

| ID | Resultado aprovado | Invariante |
|---|---|---|
| **P5-F = A** | Substituição de responsável mantém válido o aceite já realizado para a mesma área e PackageVersion; a autoria permanece a do executor original. Substituto assume somente ações futuras. | REASSIGNMENT != INVALIDATE_PRIOR_ACCEPTANCE |
| **P5-G = A** | Aceite P5 não é reversível/alterável pela UI V1. Eventual erro exige processo excepcional separado, formal, auditado e **não autorizado enquanto seu contrato não for aprovado**. | NO_P5_ACCEPTANCE_REVERSAL_IN_V1 |
| **P5-H = A** | P6 configura por tipo de pacote as áreas/especialidades obrigatórias em versão governada; P5 congela a configuração aplicável na submissão. Core fornece identidade, effective permissions e atributos de grupo/função conforme contrato a inventariar. | REVIEW_AREA_SET_SNAPSHOTTED_ON_SUBMISSION |
| **P5-I = B** | Reviewer elegível registra rejeição do pacote em nome da área; uma **autoridade operacional formalmente definida**, distinta da simples permission MANAGE, confirma com justificativa e auditoria a rejeição terminal da competência. | AREA_PACKAGE_REJECTION != TERMINAL_COMPETENCE_REJECTION |
| **P5-J = A** | Após confirmação da rejeição terminal, a competência fica rejeitada e todas as projeções/tarefas de revisão ainda acionáveis deixam de sê-lo; histórico, decisões e autoria permanecem consultáveis conforme AuthZ. | REJECTED_COMPETENCE != MONTHLY_CLOSING_COMPLETED |

### Compatibilidade com regras anteriores

- **C2:** competência concluída somente se TODOS os pacotes aplicáveis foram submetidos, TODAS as áreas obrigatórias aceitaram a PackageVersion vigente e NÃO há esclarecimento aberto. Competência rejeitada nunca satisfaz `MONTHLY_CLOSING_COMPLETED`.
- **P5-A / D-P5-01:** quorum de um aceite por área obrigatória, executado por qualquer usuário elegível; não por indivíduo. Dois elegíveis na mesma área não criam dois aceites necessários.
- **P5-B / D-P5-03 / P5-G:** ninguém sobrescreve aceites; nem o autor pode revertê-los pela UI V1. A referência antiga a “autor pode alterar” é **superseded para aceite P5 na V1**. Reatribuição formal não autoriza mutação de decisões anteriores.
- **P5-C / D-P5-04:** ACCESS efetivo + grupo/função corporativa elegível + escopo do recurso + regra da ação; avaliação server-side fail-closed; reviewer assignment nunca se torna novo permission code.
- **D-P5-02 / P5-E:** esclarecer sem alterar conteúdo preserva versão; qualquer alteração de conteúdo cria nova PackageVersion e **exige novos aceites de todas as áreas obrigatórias**; histórico de versões anteriores preservado.
- **D-P5-05 / P5-D / P5-I:** `CHANGES_REQUESTED` não é `REVIEW_REJECTED`; rejeição da área/pacote não encerra competência automaticamente; só confirmação por autoridade operacional a leva ao estado terminal rejeitado.
- **P5-F / P5-H:** reatribuir elegível não altera aceite já registrado, nem o snapshot de áreas obrigatórias da submissão; edição futura do catálogo P6 não altera snapshots abertos.
- **P5-J:** `TaskProjection != TaskEntity`; P5 continua owner do lifecycle; revisão terminal rejeitada remove acionabilidade, sem hard delete nem apagamento de evidências.

### Trilha de auditoria obrigatória

Preservar identidade Core do ator, data/hora, ação, contexto competência/recipient package, versão, área obrigatória, elegibilidade/scope verificados, motivo/justificativa quando exigidos, estado anterior/posterior, autor original do aceite, referência a reatribuições, confirmação formal da rejeição e correlação da projeção/notificação. Histórico é append-only no nível semântico; **schema físico não definido**.

### Pendências reais — sem aprovação presumida

1. **DECISION_REQUIRED:** quem é a autoridade operacional de confirmação de rejeição terminal; como é designada e substituída, e se a confirmação pode ser negada (e qual estado fica então). Não equiparar automaticamente a `manage`.
2. **DECISION_REQUIRED:** procedimento excepcional de correção de aceite P5 fora da UI V1 (owner, autorização, efeitos na conclusão mensal e revalidação), se for implementado nesta versão; na ausência de decisão, **capability não existe na V1**.
3. **TO_INVENTORY / STOP ON DRIFT:** fonte canônica dos grupos/funções corporativas e sua associação às áreas, contract Core (T05), elegibilidade de múltiplos usuários; não presumir que RBAC do Core tem os atributos necessários.
4. **CONTRACT_PENDING:** mapa versionado tipo de pacote → áreas obrigatórias em P6; regras de publicação/vigência/snapshot, defaults inválidos, configuração ausente e concorrência; não inventar tabelas/migrations.
5. **CONTRACT_PENDING:** outcome de rejeição do pacote versus confirmação terminal da competência, estados técnicos definitivos, falha/conflito no commit, event projection/notifications/Help e matrizes de testes positive+sibling+negative.

**Gates:** `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `PRODUCT_CONTRACT_FREEZE = PENDING_DERIVED_CONTRACT_AND_OWNER`; `IMPLEMENTATION_AUTHORIZED = NO`. Nenhum teste de runtime foi executado; `TEST_NOT_RUN`. Nenhum merge/rebase autorizado por este registro.
