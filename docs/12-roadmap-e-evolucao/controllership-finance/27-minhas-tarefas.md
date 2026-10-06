# 27 — Minhas Tarefas

## Estado

**TARGET / DOCUMENTATION_GATE PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY**

Runtime do Portal Controladoria & Finanças: **NOT_IMPLEMENTED**.

A fase atual é exclusivamente documental:

```text
PORTAL_REVIEW_PHASE       = ACTIVE
IMPLEMENTATION_AUTHORIZED = NO
```

Este documento fecha o **Item 5 — Minhas tarefas** no nível de produto, UX, projection contract, AuthZ, estados, deep links, reuso do `@delpi/plugin-ui`, Help e matriz futura de testes.

## Objetivo

**Minhas tarefas** é a projeção pessoal das ações de negócio que dependem do usuário dentro do Portal Controladoria & Finanças.

```text
Minhas tarefas
= projection of existing owner work
!= generic task manager
!= new workflow
!= new business owner
```

A página deve responder:

> O que depende de mim agora, de onde veio e onde devo agir para concluir corretamente?

A worklist organiza e navega. Ela não duplica a regra dos owners.

## Decisões de produto congeladas

### D-TASK-01 — não existe tarefa livre na V1

```text
FREE_TASK_CREATION = NOT_INCLUDED_IN_V1
```

Não haverá botão `Nova tarefa` na V1.

Rationale:
- a página é projection de trabalho existente;
- criar tarefa genérica introduziria novo bounded context/estado;
- o Comercial possui task entity própria, mas isso é domínio Comercial;
- não copiar `POST /tasks`, `PATCH /tasks`, complete/defer/reassign do Comercial.

### D-TASK-02 — não existe editor genérico na V1

O `TaskEditorFrame` existe no kit, mas é **deliberadamente não utilizado** nesta versão.

```text
TASK_EDITOR_V1 = NOT_USED
```

Se no futuro o produto aprovar entidade de tarefa própria:
- reabrir contract;
- definir owner;
- definir lifecycle;
- então reutilizar `TaskEditorFrame`.

Não criar editor local agora.

### D-TASK-03 — escopo é somente self

```text
WORKLIST_SCOPE = MINE_ONLY
TEAM_SCOPE     = NOT_INCLUDED_IN_V1
```

Não copiar do Comercial:

```text
Minhas | Equipe
```

`MANAGE` não cria automaticamente visão de tarefas da equipe.

### D-TASK-04 — sem SLA global

```text
GLOBAL_SLA   = NONE
GLOBAL_DUE   = NONE
OVERDUE_RULE = NONE
```

Não usar por default `Atrasadas`, `Hoje`, `Depois`, `Vencendo` ou `Vencidas`.

Uma task projection pode carregar `dueAt` somente quando o owner original possuir prazo formal real.

Nesse caso:
- o prazo continua owned pela source;
- a worklist pode exibi-lo;
- não nasce SLA transversal no Portal.

### D-TASK-05 — ação V1 é abrir o owner

A ação primária canônica é `Abrir`.

```text
TaskProjection
→ deep link
→ página owner
→ caso de uso real
→ owner state changes
→ task projection recomputed
```

Na V1 não expor inline:
- Editar;
- Concluir;
- Cancelar;
- Adiar;
- Reatribuir.

### D-TASK-06 — não existe completed state local

```text
TASK_COMPLETION_LOCAL = NONE
```

Quando o owner deixa de exigir ação do usuário:
- o item deixa de ser acionável;
- a projeção aberta deixa de retorná-lo.

Histórico da decisão continua na página owner.

A V1 não mantém bucket local de `Concluídas`.

### D-TASK-07 — criar tarefa a partir da Sala fica fora da V1

O `plugin-ui` suporta `onCreateTask`, mas o Controladoria não possui task entity própria.

```text
CREATE_TASK_FROM_MESSAGE = NOT_INCLUDED_IN_V1
```

A Sala pode colaborar, referenciar e navegar ao owner. Ela não cria task genérica.

Uma evolução futura exige decisão explícita de produto e novo contract de task ownership.

## Rota

```text
/apps/controllership-finance/my-tasks
```

Permission:

```text
controllership-finance.access
```

`MANAGE` sozinho não implica ACCESS.

Não criar permission por tipo de tarefa, source, competência, filial ou botão.

## Família visual

```text
VISUAL_FAMILY       = TASK_WORKSPACE
PRIMARY_COMPONENT   = TaskWorkspacePage
PLUGIN_UI_FIRST     = REQUIRED
REFERENCE           = Portal Comercial / MyDay family
```

A experiência visual permanece comum aos Portais.

## Reuso obrigatório de @delpi/plugin-ui

Import preferencial:

```ts
import {
  TaskWorkspacePage,
  TaskWorklistSection,
  TaskItemsTable,
  TaskSearchField,
  TaskEmptyState,
  buildTaskWorkspaceHighlights,
  createDashboardPageHero,
  createDashboardScopeChipBar,
  StatusBadge,
  StateBanner,
  LoadingState,
  ActionButton,
} from "@delpi/plugin-ui/index";
```

Capability existente mas **não usada na V1**:

```ts
import {
  TaskEditorFrame,
} from "@delpi/plugin-ui/index";
```

Styles:

```ts
await import("@delpi/plugin-ui/styles");
```

### O kit já owns

- workspace;
- worklist section;
- busca;
- tabela;
- empty state;
- presentation helpers;
- editor frame;
- status chrome;
- responsive layout;
- light/dark;
- keyboard/focus estrutural.

### O Portal owns

- `TaskProjection`;
- source registry;
- projection mapping;
- source health;
- deep links;
- AuthZ;
- copy;
- filters;
- aggregation;
- owner navigation.

### DO NOT RECREATE

- task workspace;
- worklist section;
- task table;
- search field;
- empty state;
- editor frame;
- status badge;
- CSS `.delpi-ui-task-*`.

Se a V1 precisar ocultar colunas fixas de `TaskItemsTable` por ausência de semântica, isso deve virar evolução do `plugin-ui`, não tabela local duplicada.

## Wireframe — desktop

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Início | Visão geral | Sala | Minhas tarefas | Administração | Ajuda       │
│                                      Buscar | Favoritos | [avatar] Usuário │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ PORTAL CONTROLADORIA & FINANÇAS                              [Atualizar]     │
│ Minhas tarefas                                                               │
│ Ações dos processos do Portal que dependem de você.                         │
│                                                                              │
│ Pendentes                                                                    │
│ 8                                                                            │
│                                                                              │
│ Fonte: [Todas] [Checklist] [Classificações] [Pacote]*                       │
│ Competência: [Todas]                                                         │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ FILA                                                                         │
│ Itens em que sua atuação é necessária no contexto owner.                    │
│                                                                              │
│ [Buscar tarefas...]                                                         │
│                                                                              │
│ Tarefa                  Origem       Status      Prazo  Responsável Contexto │
│ ──────────────────────────────────────────────────────────────────────────── │
│ Anexar extrato          Checklist    Pendente    —      Você        09/2026  │
│ Validar evidência       Checklist    Revisão     —      Você        09/2026  │
│ Classificar lançamento  Pendência    Pendente    —      Você        09/2026  │
│                                                                     [Abrir] │
└──────────────────────────────────────────────────────────────────────────────┘

* Pacote só aparece quando P5 possuir responsabilidade individual comprovada.
```

## Wireframe — PARTIAL

```text
[!] Algumas fontes de tarefas estão temporariamente indisponíveis.
    A lista mostra somente itens confirmados pelas fontes disponíveis.

Pendentes
—

Fila
✓ Checklist disponível
✓ Classificações disponível
! Pacote indisponível

[itens conhecidos continuam visíveis]
```

Não apresentar contagem parcial como total.

## Wireframe — mobile

```text
TOPBAR COMPACTA

┌─────────────────────────────┐
│ Minhas tarefas  [Atualizar] │
│ Ações que dependem de você. │
│                             │
│ Pendentes                   │
│ 8                           │
│                             │
│ Fonte                       │
│ [Todas] [Checklist] [...]   │
│                             │
│ Competência                 │
│ [Todas]                     │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Fila                        │
│ [Buscar tarefas...]         │
│                             │
│ Tarefa                      │
│ Origem / Status             │
│ Contexto                    │
│ Prazo*                      │
│ [Abrir]                     │
└─────────────────────────────┘
```

Se `TaskItemsTable` não entregar experiência mobile suficiente no runtime futuro:
- provar gap;
- evoluir o kit;
- não recriar cards/tabela localmente.

## Hero

Usar `createDashboardPageHero` no slot `hero` de `TaskWorkspacePage`.

Eyebrow: `Portal Controladoria & Finanças`.

Título: `Minhas tarefas`.

Descrição:

```text
Ações dos processos do Portal que dependem de você.
```

### Highlight obrigatório

```text
Pendentes
```

Usar `buildTaskWorkspaceHighlights({ pending }, { includeDueBuckets: false })` ou composição equivalente do kit.

Não usar `dueSoon` / `overdue` enquanto não houver due formal nas sources.

### Partial

Se coverage estiver parcial:
- badge `Dados parciais`;
- valor agregado não deve parecer completo;
- lista de itens conhecidos pode permanecer.

## O que gera TaskProjection

Regra geral:

```text
owner context exists
AND owner state requires a human action
AND responsibility is explicitly attributable to current user
AND actor can access resource
→ TaskProjection
```

Não projetar item apenas porque:
- está pendente no processo;
- é blocker;
- possui warning;
- usuário pode visualizar;
- usuário está mencionado na Sala.

```text
PENDING != MY_TASK
BLOCKER != MY_TASK
MENTION != MY_TASK
```

É necessário existir **responsabilidade individual acionável**.

## Producers V1

### P2 — Checklist e Documentos

Pode produzir task projection quando a responsabilidade estiver atribuída ao usuário.

Tipos lógicos:

```text
CHECKLIST_EVIDENCE_REQUIRED
CHECKLIST_REPLACEMENT_REQUIRED
CHECKLIST_VALIDATION_REQUIRED
```

#### Evidence required

- usuário é provider/responsável;
- item aguarda evidência que ele deve fornecer.

#### Replacement required

- evidência foi rejeitada;
- owner state exige substituição;
- responsabilidade pertence ao usuário.

#### Validation required

- item/conjunto está `UNDER_REVIEW`;
- usuário é validator aplicável;
- owner permite decisão.

A task abre o detalhe P2. Não executa Aceitar/Rejeitar inline na V1.

### P4 — Classificações e Pendências

Pode produzir:

```text
CLASSIFICATION_RESOLUTION_REQUIRED
```

quando:
- pendência/classificação está atribuída/claimada ao usuário;
- state ainda exige resolução;
- recurso está acessível.

A worklist abre P4 no item correto. Não classifica inline.

### P5 — Pacote, Finalização e Envio

Classificação:

```text
CONDITIONAL_PRODUCER
```

Pode produzir task somente quando P5 possuir contract explícito de responsabilidade individual, por exemplo:

```text
PACKAGE_CLARIFICATION_REQUIRED
PACKAGE_CORRECTION_REQUIRED
```

O processo comprova esclarecimentos/correções, mas a atribuição user-centric deve ser revalidada.

Sem assignee individual comprovado:
- não gerar task;
- não inferir responsável por role, nome ou comentário.

### P1 / P3

Não são producers automáticos na V1.

- P1 compõe blockers, mas blocker sem assignee não é task.
- P3 possui readiness/conciliação, mas não existe assignment individual canônico documentado.

## Modelo lógico de TaskProjection

```text
TaskProjection
├── id
├── sourceType
├── sourceId
├── actionKind
├── title
├── description?
├── ownerPage
├── ownerState
├── statusLabel
├── assigneeUserId
├── context
│   ├── contextType
│   ├── contextId
│   ├── contextLabel
│   └── competence?
├── pendingSince?
├── dueAt?
├── sourceFreshness?
├── sourceStatus
├── deepLink
└── actionFlags
    └── canOpen
```

V1:

```text
canOpen     = true
canEdit     = false
canComplete = false
canCancel   = false
```

### ID estável

O ID lógico deve ser determinístico a partir de:

```text
(sourceType, sourceId, actionKind, assigneeUserId)
```

Não usar índice de array ou timestamp de leitura como identity.

## Source registry

O BFF deve possuir registry explícito:

```text
sourceType
→ owner
→ projection mapper
→ auth adapter
→ deep-link builder
→ freshness mapper
```

Não aceitar `deepLink` arbitrário vindo do frontend.

## Contract TARGET

Endpoint lógico:

```text
GET /apps/controllership-finance-api/me/tasks
```

Query conceitual:

```text
?source=all|checklist|classification|package
&competence=YYYY-MM
&q=...
&page=...
&page_size=...
```

O nome físico final entra no OpenAPI futuro.

### Response lógica

```json
{
  "summary": {
    "pending": 8,
    "coverage": "COMPLETE"
  },
  "items": [
    {
      "id": "stable-id",
      "sourceType": "CHECKLIST_VALIDATION_REQUIRED",
      "sourceId": "item-id",
      "actionKind": "VALIDATE_EVIDENCE",
      "title": "Validar extrato bancário",
      "ownerPage": "checklist",
      "ownerState": "UNDER_REVIEW",
      "statusLabel": "Aguardando validação",
      "context": {
        "contextType": "closing_competence",
        "contextId": "competence-id",
        "contextLabel": "09/2026",
        "competence": "2026-09"
      },
      "pendingSince": "2026-10-02T10:00:00-03:00",
      "dueAt": null,
      "sourceStatus": "AVAILABLE",
      "deepLink": "/apps/controllership-finance/...",
      "actions": {
        "canOpen": true,
        "canEdit": false,
        "canComplete": false,
        "canCancel": false
      }
    }
  ],
  "sources": [
    { "source": "checklist", "status": "AVAILABLE" },
    { "source": "classification", "status": "AVAILABLE" },
    { "source": "package", "status": "UNAVAILABLE" }
  ]
}
```

### Coverage

```text
COMPLETE
PARTIAL
```

Se qualquer producer obrigatório para o recorte falhar:
- `coverage = PARTIAL`;
- `summary.pending` não deve parecer total definitivo;
- itens conhecidos permanecem;
- source failure fica visível.

## Estratégia física da projeção

Produto/semântica estão fechados.

Implementação física permanece:

```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Opções técnicas:

```text
on-read composition
materialized read-model
event-driven projection
hybrid
```

A decisão deve considerar número de producers, latência, freshness, consistência, reprocessamento, auditoria, retry e disponibilidade parcial.

Não criar tabela de tasks preventivamente.

## AuthZ

A página é self-only.

```text
authenticated
AND effective_permission(controllership-finance.access)
AND projection.assignee_user_id = authenticated_user
AND owner_resource_access
```

Consequências:
- frontend não escolhe `userId`;
- endpoint usa `/me/tasks`;
- não aceitar `assignee_user_id` para listar terceiros;
- `MANAGE` não libera team worklist;
- source adapter autoriza recurso no owner;
- item stale sem acesso desaparece/falha fechado.

## Filtros V1

### Fonte

```text
Todas
Checklist
Classificações
Pacote*
```

`Pacote` somente quando producer P5 estiver realmente implementado.

### Competência

```text
Todas
YYYY-MM...
```

Default: todas as tarefas abertas do usuário.

Não esconder task antiga por mudar a competência corrente.

### Busca

Usar `TaskSearchField`.

Buscar apenas sobre campos seguros da projeção:
- title;
- source label;
- context label.

### Status

A V1 mostra somente trabalho acionável aberto.

```text
STATUS_FILTER = OPEN_ONLY
```

Não criar `Concluídas` localmente.

## URL / F5

```text
/apps/controllership-finance/my-tasks
?source=checklist
&competence=2026-09
&q=extrato
```

Regras:
- query válida reconstrói filtro;
- F5 preserva recorte;
- filtro inválido é normalizado/rejeitado;
- nenhuma query escolhe outro usuário;
- nenhuma arbitrary target URL entra na query.

## Ordenação

Sem SLA global.

Default:

```text
pendingSince ASC
→ source/context stable ordering
```

Itens aguardando há mais tempo aparecem primeiro.

Isso é idade factual, não classificação `atrasada`.

Se `pendingSince` não existir:
- usar ordenação estável do adapter;
- não inventar timestamp.

## Prazo / overdue

`TaskItemsTable` possui coluna Prazo e suporte visual a overdue.

Para Controladoria:

```text
dueAt = owner-provided only
overdue = owner-rule only
```

Se owner não possui prazo:
- `dueAt = null`;
- mostrar `—`;
- `overdue = false`.

Não derivar prazo de pendingSince, fim do mês, cutoff, data corrente ou prioridade visual.

### UI gap a validar

Como a V1 é self-only e muitos producers podem não ter due:
- Responsável tende a ser sempre `Você`;
- Prazo pode ser vazio em muitos itens.

```text
TASK_TABLE_COLUMN_CONFIG = TO_VALIDATE_IN_IMPLEMENTATION_INVENTORY
```

Se isso degradar UX:
- evoluir `TaskItemsTable` no `plugin-ui`;
- não criar tabela local.

## Mapeamento para TaskItemPresentation

```ts
{
  id: projection.id,
  title: projection.title,
  sourceLabel: sourceLabel(projection.sourceType),
  statusLabel: projection.statusLabel,
  statusTone: mapOwnerStateToTone(projection),
  assigneeLabel: "Você",
  dueDateLabel: projection.dueAt ? formatDate(projection.dueAt) : null,
  contextLabel: projection.context.contextLabel,
  overdue: projection.ownerDefinedOverdue === true,
  route: projection.deepLink,
  actions: {
    canOpen: true,
    canEdit: false,
    canComplete: false,
    canCancel: false,
  },
}
```

Tone é apresentação. Não transformar tone em regra de negócio.

## Ação Abrir

```text
projection.deepLink
→ owner page
→ selected context/resource
```

O BFF constrói/valida o deep link pelo registry.

A página owner:
- reautoriza;
- carrega state atual;
- oferece as ações válidas.

Se o item já tiver sido resolvido:
- owner state prevalece;
- refresh da worklist remove a projection;
- nenhuma ação é executada automaticamente.

## Integração com Home

```text
Home "Minhas tarefas"
→ same projection contract
→ no duplicate task rule
```

O highlight da Home:
- usa `summary.pending` apenas com `coverage=COMPLETE`;
- em `PARTIAL` mostra estado parcial, não total falso.

Preview:
- pode mostrar itens conhecidos;
- ação abre owner.

## Integração com Sala de interação

A V1 não cria task a partir de mensagem.

```text
Room message
→ collaboration only
```

Se mensagem aponta problema acionável:
- usuário abre owner context;
- owner state/responsibility produz TaskProjection.

```text
MESSAGE != TASK
MENTION != TASK
```

## Notifications

Minhas tarefas não cria notification stream paralelo.

Notifications continuam owned por P2/P4/P5 e pela capability canônica da Minha DELPI.

A worklist reflete estado; não notifica só porque um item apareceu na projeção.

## Freshness

Cada source adapter informa quando possível:

```text
sourceStatus
sourceFreshness
```

Não inventar timestamp.

## Estados da experiência

### INITIAL / LOADING
- Hero e shell visíveis;
- loading do kit;
- count não vira 0.

### REFRESHING
- manter itens anteriores quando seguro;
- indicar atualização;
- não limpar fila prematuramente.

### SUCCESS
Todas as sources do recorte responderam.

### EMPTY

Somente quando:

```text
coverage = COMPLETE
AND items = []
```

Copy:

```text
Nenhuma ação pendente para você agora.
```

Não usar `Tudo em dia` ou `Sem atrasos`.

### PARTIAL
- banner explícito;
- manter itens conhecidos;
- count não parece total.

### UNAVAILABLE_SOURCE
Identificar source afetada sem virar lista vazia.

### ERROR
Erro total quando nenhuma projeção confiável pode ser composta.

### FORBIDDEN
Sem ACCESS → 403.

### NOT_FOUND
Não é estado normal da worklist; pode ocorrer no owner deep link.

### STALE_ITEM
Se o item deixar de ser acionável entre leitura e abertura:
- owner state prevalece;
- não forçar ação;
- refresh remove projection resolvida.

## Light / dark

```text
SAME DOM
SAME TASK ORDER
SAME ACTIONS
+ THEME TOKENS
```

O kit owns table, search, badges, empty, workspace e focus/hover.

## Responsividade

Desktop:
- Hero;
- filtros;
- worklist/table.

Mobile:
- Hero compacto;
- filtros empilháveis;
- busca full-width;
- tabela usa estratégia do kit;
- Abrir permanece acessível;
- nada crítico depende de hover.

Se a tabela exigir evolução mobile:
- contribuir no kit.

## Acessibilidade

Obrigatório:
- landmarks/headings;
- busca com label;
- filtros por teclado;
- status textual;
- focus visível;
- ação Abrir acessível;
- refreshing/partial anunciados;
- estado não apenas por cor;
- owner link compreensível;
- due vazio não anunciado como zero.

## Help

Quando implementada, a Ajuda deve explicar:
- o que é TaskProjection;
- task vem de página owner;
- por que algo aparece;
- blocker nem sempre é tarefa;
- sources P2/P4 e P5 quando aplicável;
- busca e filtros;
- pendingSince não é SLA;
- due só existe se owner definir;
- ação padrão Abrir;
- conclusão ocorre no owner;
- sem Equipe na V1;
- sem Nova tarefa na V1;
- source indisponível != fila vazia;
- count pode ser parcial;
- Home usa a mesma projeção;
- Sala não cria task genérica na V1.

Não publicar capability ainda não implementada.

## RQ / AC

### RQ-TASK-01 — workspace comum
Aceite: `TaskWorkspacePage` e task primitives do kit; zero clone/CSS local.

### RQ-TASK-02 — projection, não entidade
Aceite: nenhum endpoint genérico de create/edit/complete/cancel/defer/reassign; nenhuma persistência criada para copiar owner state.

### RQ-TASK-03 — self only
Aceite: `/me/tasks`; frontend não escolhe usuário; sem team scope; MANAGE não implica team worklist.

### RQ-TASK-04 — producers governados
Aceite: P2/P4 só com responsabilidade individual; P5 só com contract user-centric; blocker/mention sozinho não gera task.

### RQ-TASK-05 — abrir owner
Aceite: única action V1 é Abrir; deep link por registry seguro; owner reautoriza.

### RQ-TASK-06 — sem SLA inventado
Aceite: sem buckets Atrasadas/Hoje/Depois; due/overdue só owner-provided; pendingSince é idade factual.

### RQ-TASK-07 — partial coverage
Aceite: falha de source não apaga siblings; count não parece total em partial; empty só com complete.

### RQ-TASK-08 — URL/F5
Aceite: source/competence/q preservados; F5 reconstrói; query não escolhe outro usuário/open redirect.

### RQ-TASK-09 — Home reusa projeção
Aceite: Home e My Tasks não duplicam regras; summary segue coverage.

### RQ-TASK-10 — Sala não cria task V1
Aceite: `onCreateTask` não exposto; message/mention não viram TaskProjection sem owner state.

### RQ-TASK-11 — light/dark/mobile/a11y
Aceite: mesmos componentes/tokens; desktop/mobile; teclado/foco.

### RQ-TASK-12 — Help sync
Aceite: manual acompanha producers reais; não promete team/free task/editor.

## Matriz futura de testes

### Positive
- ACCESS abre worklist self;
- P2 evidence required;
- P2 replacement required;
- P2 validation required;
- P4 assigned issue;
- P5 quando assignment contract existir;
- Abrir owner correto;
- filtro source;
- filtro competence;
- busca;
- refresh;
- pendingSince ordering;
- due real owner-provided;
- Home summary usa mesma contract.

### Sibling
- item A não gera task para item B;
- usuário A não vê task de B;
- resolver P2 não remove P4;
- falha P5 não apaga P2/P4;
- mesma sourceId com actionKind distinto não colide;
- troca de filtro não reutiliza stale item.

### Negative
- sem ACCESS;
- MANAGE sem ACCESS;
- listar terceiro;
- blocker sem assignee;
- mention sem owner responsibility;
- P5 sem assignee individual;
- criar task livre;
- editar/concluir/cancelar/adiar/reassign local;
- source unavailable tratado como empty;
- partial count como total;
- pendingSince como overdue;
- due inferido;
- deep link arbitrário/open redirect;
- resource sem acesso;
- stale item executando ação antiga.

### Experiência
- initial loading;
- refreshing;
- success;
- empty;
- partial;
- unavailable;
- error;
- 403;
- stale item;
- desktop;
- mobile;
- light;
- dark;
- keyboard/focus;
- URL/F5;
- Help.

## Scripts / validators planejados para futura implementação

Não criar agora.

```text
validate-task-projection-registry
validate-task-projection-ownership
validate-task-projection-coverage
validate-task-projection-due
validate-task-projection-links
validate-task-help
```

Responsabilidades:
- sourceType/owner/actionKind/AuthZ/deep-link conhecidos;
- projection não replica lifecycle;
- self-only;
- partial/empty corretos;
- due somente owner-provided;
- no open redirect;
- Help não promete capability ausente.

## Inventários técnicos restantes

### TSK01 — producer contracts físicos
```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```
Revalidar DTO/state/assignee de P2, P4 e P5 conditional.

### TSK02 — estratégia física de projection
```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```
Escolher on-read/materialized/event/hybrid com evidência.

### TSK03 — deep-link registry físico
```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```
Congelar rotas e selected-resource params reais.

### TSK04 — source health/freshness/cache
```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```
Definir partial aggregation, stale protection e cache conforme padrões vigentes.

### TSK05 — TaskItemsTable column configuration
```text
TO_VALIDATE
```
Se Responsável/Prazo forem redundantes, evoluir `plugin-ui`; não criar tabela local.

Nenhum desses itens reabre D-TASK-01..07.

## Gate

```text
VISUAL_FAMILY_DEFINED       = PASS
PLUGIN_UI_REUSE_DEFINED     = PASS
TASK_SEMANTICS_DEFINED      = PASS
FREE_TASK_POLICY_DEFINED    = PASS
SELF_SCOPE_DEFINED          = PASS
PRODUCERS_DEFINED           = PASS
PROJECTION_MODEL_DEFINED    = PASS
ACTION_POLICY_DEFINED       = PASS
AUTHZ_DEFINED               = PASS
DUE_SLA_POLICY_DEFINED      = PASS
PARTIAL_COVERAGE_DEFINED    = PASS
DEEP_LINK_DEFINED           = PASS
HOME_INTEGRATION_DEFINED    = PASS
ROOM_INTEGRATION_DEFINED    = PASS
LIGHT_DARK_DEFINED          = PASS
MOBILE_DEFINED              = PASS
RQ_AC_TEST_MATRIX_DEFINED   = PASS
HELP_CONTRACT_DEFINED       = PASS
IMPLEMENTATION              = NOT_AUTHORIZED
```

Estado:

```text
ITEM 5 = READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY
```

## Resultado esperado

```text
OWNER REQUIRES ACTION
→ PROJECT TO CURRENT USER
→ SHOW IN MINHAS TAREFAS
→ OPEN OWNER
→ OWNER HANDLES BUSINESS ACTION
→ PROJECTION DISAPPEARS WHEN NO LONGER ACTIONABLE
```

Sem task manager paralelo, sem lifecycle duplicado e sem regra de negócio no frontend.
