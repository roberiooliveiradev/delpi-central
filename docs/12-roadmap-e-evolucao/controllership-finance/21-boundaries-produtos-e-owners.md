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
| Minha DELPI — notificações | capability de plataforma | superfície/canal canônico de notificação conforme binding T02 |
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
