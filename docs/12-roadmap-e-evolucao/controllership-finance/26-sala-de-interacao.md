# 26 — Sala de Interação

## Estado

**TARGET / DOCUMENTATION_GATE PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY**

Runtime do Portal Controladoria & Finanças: **NOT_IMPLEMENTED**.

A fase atual é exclusivamente documental:

```text
PORTAL_REVIEW_PHASE       = ACTIVE
IMPLEMENTATION_AUTHORIZED = NO
```

Este documento fecha o **Item 4 — Sala de interação** no nível de produto, UX, boundary, AuthZ, estados, contratos lógicos e reuso do `@delpi/plugin-ui`.

## Objetivo

A **Sala de interação** é a superfície de colaboração contextual do Portal Controladoria & Finanças.

Ela deve permitir discutir um objeto real de trabalho sem transformar conversa em regra de negócio e sem criar um chat genérico paralelo à plataforma.

Princípio:

```text
CONTEXT FIRST
→ COLLABORATE
→ REFERENCE EVIDENCE
→ OPEN THE OWNER
```

Nunca:

```text
CHAT
→ DECIDE BUSINESS STATE BY COMMENT
```

## Família visual

```text
VISUAL_FAMILY       = INTERACTION
FULL_PAGE_PLUGIN_UI = InteractionRoomPage
REFERENCE           = Portal Comercial
PLUGIN_UI_FIRST     = REQUIRED
```

A Sala do Controladoria deve usar a mesma experiência visual dos demais Portais.

O domínio fornece dados, contexto e comandos. O `plugin-ui` controla o canvas de colaboração.

## Full-page canônica

Import principal:

```ts
import {
  InteractionRoomPage,
  INTERACTION_ROOM_PAGE_LABELS_PT,
  PluginErrorBoundary,
} from "@delpi/plugin-ui/index";
```

Primitives disponíveis quando houver extensão comprovada:

```ts
import {
  RoomInboxPanel,
  RoomInboxList,
  RoomHeader,
  RoomContextPanel,
  RoomSidePanel,
  RoomMessageFindPanel,
  RoomSharedItemList,
  RoomConversationShell,
  RoomConversationChatColumn,
  MessageThread,
  MentionComposer,
  MentionMenu,
  MentionText,
  EntityUnfurlCard,
  ReactionBar,
  ReactionQuickBar,
  ConversationFileDropLayer,
  ResizableColumns,
  StateBanner,
  EmptyGuidance,
  ActionButton,
} from "@delpi/plugin-ui/index";
```

Estilos:

```ts
await import("@delpi/plugin-ui/styles");
```

Regra:

```text
InteractionRoomPage first
→ primitives only for proven extension
→ no copied Commercial UI
```

### DO NOT RECREATE

- inbox shell;
- split desktop;
- comportamento mobile inbox ↔ thread;
- room header;
- message thread;
- composer;
- mentions;
- reply;
- reactions;
- pin;
- shared files/links;
- context side panel;
- find-in-chat;
- attachment chrome;
- generic loading/empty/error;
- CSS `.delpi-ui-interaction-room*`.

## O que o plugin-ui já resolve

**PROVEN** no HEAD atual:

- inbox;
- busca;
- chips/filtros;
- unread/mentioned states;
- split desktop;
- stacked mobile;
- `ResizableColumns`;
- header;
- participantes;
- mensagens;
- reply;
- edição inline;
- exclusão visual;
- pin/unpin;
- reações;
- emojis;
- menções;
- rich composer;
- anexos;
- drag & drop;
- imagens inline;
- arquivos/links compartilhados;
- busca dentro da conversa;
- painel "Neste chat";
- entity context;
- load older;
- auto-scroll;
- light/dark;
- teclado/acessibilidade estrutural.

Consequência:

```text
ITEM 4 = DOMAIN + CONTRACT + AUTHZ REVIEW
not visual redesign
```

## Rotas

Inbox:

```text
/apps/controllership-finance/interaction-rooms
```

Sala:

```text
/apps/controllership-finance/interaction-rooms/{roomId}
```

Query do inbox:

```text
?filter=all|unread|mentioned
&q={query}
```

O nome físico final dos query params deve ser congelado no OpenAPI/router futuro, preservando a semântica acima.

F5 deve reconstruir:
- filtro;
- busca;
- sala selecionada.

## Decisões de produto congeladas

### D-ROOM-01 — não existe chat genérico na V1

```text
GLOBAL_WALL = NOT_INCLUDED
FREE_ROOM_CREATION = NOT_INCLUDED
```

Toda sala nasce de contexto de trabalho reconhecido.

Rationale:
- a documentação já define colaboração contextual;
- evita canal paralelo sem owner;
- evita rooms sem boundary de acesso;
- evita duplicar chat corporativo genérico.

### D-ROOM-02 — granularidade de contexto

A V1 usa uma sala estável por **contexto operacional relevante**, não por cada arquivo/anexo.

Tipos conceituais:

```text
closing_competence
checklist_item
classification_issue
closing_package
```

Mapeamento:

| Contexto | Owner visual |
|---|---|
| `closing_competence` | P1 Cockpit |
| `checklist_item` | P2 Checklist e Documentos |
| `classification_issue` | P4 Classificações e Pendências |
| `closing_package` | P5 Pacote, Finalização e Envio |

P3 usa a sala da competência enquanto não houver evidência de necessidade de sala própria por reconciliação.

Não criar sala própria para:
- attachment;
- evidence version;
- source line;
- KPI;
- mensagem;
- usuário.

Esses itens podem ser referenciados dentro da sala do contexto owner.

### D-ROOM-03 — resolve idempotente

Abertura a partir de um contexto usa operação lógica:

```text
RESOLVE(context_type, context_id)
→ existing room OR create exactly one room
```

Evitar salas duplicadas para o mesmo contexto.

A Inbox não oferece botão "Nova sala" na V1.

### D-ROOM-04 — título deriva do contexto

O título principal é derivado do contexto owner.

Exemplos de UX:

```text
Fechamento 09/2026
Checklist — Extratos bancários
Pendência — Classificação CC 4100
Pacote de fechamento — 09/2026
```

```text
RENAME_ROOM = NOT_INCLUDED_IN_V1
```

Rationale:
- preserva rastreabilidade;
- evita perder vínculo semântico;
- simplifica deep links e auditoria.

### D-ROOM-05 — participants não são ACL

```text
ROOM_MEMBER != AUTHORIZATION_GRANT
```

Participants/members servem para:
- avatar stack;
- quem falou;
- read state;
- unread;
- mention UX;
- mute/preference futura quando houver contract.

Acesso real à sala depende do recurso/contexto.

### D-ROOM-06 — edição/exclusão de mensagem

Autor pode editar a própria mensagem de texto.

Excluir significa:

```text
SOFT_DELETE
!= HARD_DELETE
```

Regras:
- somente autor pode editar/excluir sua mensagem normal;
- system message não é editável pelo usuário;
- mensagem editada mantém `edited_at`;
- exclusão preserva tombstone/metadata necessária à auditoria;
- attachments vinculados seguem policy do storage/retention, não hard-delete silencioso.

### D-ROOM-07 — pin/reaction/reply

Usuário autorizado ao contexto pode:
- responder;
- reagir;
- pin/unpin mensagem acessível.

Pin não transforma mensagem em aprovação/decisão.

### D-ROOM-08 — create task from message

O `plugin-ui` suporta `onCreateTask`, mas o Item 5 confirmou que a V1 não possui task entity própria.

Para Controladoria:

```text
CREATE_TASK_FROM_MESSAGE = NOT_INCLUDED_IN_V1
```

Não expor a ação na V1.

Uma evolução futura exige decisão explícita sobre entidade/owner/lifecycle de task. A Sala nunca cria TaskProjection diretamente; projection nasce de state/responsibility do owner.

## Invariantes de negócio

```text
MESSAGE != BUSINESS_DECISION
COMMENT != VALIDATION
COMMENT != APPROVAL
COMMENT != NOT_APPLICABLE
COMMENT != CUTOFF
COMMENT != STOCK_CLOSED
COMMENT != PACKAGE_FINALIZED
COMMENT != PACKAGE_SENT
REACTION != APPROVAL
PIN != APPROVAL
```

Ações do processo continuam nas páginas owners.

A Sala pode:
- explicar;
- discutir;
- mencionar;
- anexar;
- referenciar;
- navegar ao owner.

A Sala não altera state machine de P1–P5 por inferência.

## Modelo conceitual

```text
InteractionRoom
├── id
├── contextType
├── contextId
├── titleDerived
├── createdBy
├── createdAt
├── updatedAt
├── readState
├── messages[]
├── pins[]
├── sharedItems[]
└── audit metadata

InteractionMessage
├── id
├── roomId
├── author
├── kind
├── body
├── parentId
├── mentions[]
├── reactions[]
├── attachments[]
├── createdAt
├── editedAt
└── deletedAt
```

Esse é modelo lógico, não schema físico.

## Ownership

### controllership-finance-api

Owner de:
- rooms;
- messages;
- room-message attachments metadata;
- read state;
- pins;
- reactions;
- context resolution;
- domain adapters;
- AuthZ;
- audit events próprios;
- integração realtime quando selecionada;
- integração com notifications quando aplicável.

Esse estado é próprio do Portal e pode exigir persistência própria.

### Core API

Owner de:
- identidade;
- effective permissions;
- diretório/person profile necessário a avatar/mention;
- app access.

### P1–P5 / context owners

Owner de:
- existência do contexto;
- business state;
- resource access;
- labels/dados usados pelo context panel;
- navegação ao recurso.

A Sala nunca replica o estado canônico do contexto.

### plugin-ui

Owner da experiência visual e behavior genérico.

## AuthZ

Regra base:

```text
authenticated
AND effective_permission(controllership-finance.access)
AND context_exists
AND actor_can_access_context
AND business_rule_allows_collaboration
```

Consequências:
- `MANAGE` sozinho não implica acesso à Sala;
- não criar permission por sala;
- não criar permission por mensagem;
- não criar permission por contexto;
- unidade/filial não vira permission code;
- membership da room não concede acesso;
- mention não concede acesso;
- favorite/deep link não concede acesso.

### 403 / 404

Sem ACCESS:
- `403`.

Room inexistente:
- `404`.

Room existe, mas contexto não está acessível ao ator:
- resposta deve ser fail-closed;
- preferir não expor existência desnecessária do contexto;
- contract físico definirá 403/404 conforme padrão de enumeração da plataforma.

Não retornar cached messages quando o contexto deixou de ser acessível.

## Resolve de sala

Contrato lógico:

```text
POST /apps/controllership-finance-api/interaction-rooms/resolve
```

Body conceitual:

```json
{
  "contextType": "checklist_item",
  "contextId": "stable-id"
}
```

O backend:
1. autoriza o actor;
2. resolve context owner;
3. valida acesso ao contexto;
4. deriva title/context summary;
5. retorna sala existente ou cria uma;
6. registra audit metadata.

Não aceitar title/context data arbitrários do frontend como authority.

## Inbox

Contrato lógico:

```text
GET /apps/controllership-finance-api/interaction-rooms
```

Filtros V1:

```text
all
unread
mentioned
```

Não incluir por padrão:
- `wall`;
- filtros de SLA;
- status inventados;
- owner/team scope não provado.

Pode adicionar filtro por context type futuramente se a volumetria justificar.

### Busca

Busca inicialmente por:
- title derivado;
- context label/index autorizado;
- preview autorizado quando o contract permitir.

Nunca usar busca para revelar contexto sem acesso.

## Workspace

Desktop:

```text
┌──────────────────────────┬───────────────────────────────────────────────┐
│ INBOX                    │ THREAD                                        │
│ busca                    │ header / context / participants               │
│ filtros                  │ Chat | Arquivos e links                       │
│ rooms                    │                                               │
│                          │ messages                                      │
│                          │                                               │
│                          │ composer                                      │
└──────────────────────────┴───────────────────────────────────────────────┘
```

Com sala selecionada, usar split redimensionável do kit.

Sem sala:
- inbox ocupa o workspace.

Mobile:

```text
Inbox
→ selecionar
→ Thread full-width
→ voltar para Inbox preservando filter/q
```

## Header da sala

Mostrar:
- title derivado;
- context chips factuais;
- participants;
- alternância Conversa / Arquivos e links;
- localizar;
- "Neste chat";
- copiar deep link quando permitido.

O title pode abrir o recurso owner.

Não mostrar botão de rename na V1.

## Context panel — "Neste chat"

Usar `RoomContextPanel`.

Estrutura:

```text
Sobre
→ identificador principal
→ campos do contexto
→ Abrir recurso

Quem falou
→ avatar stack

Fixadas
→ pins
```

Exemplos:

### Competência

```text
09/2026
Unidade: Consolidado
Estado: READY_TO_CLOSE
```

### Checklist item

```text
Extratos bancários
Competência: 09/2026
Status: Pendente
```

Mostrar apenas campos autorizados e necessários.

## Mensagens

Tipos lógicos V1:

```text
text
system
```

`task_ref` entra somente com Item 5.

System messages são permitidas apenas quando produzidas por evento/owner explícito.

Exemplos:
- contexto criado;
- item rejeitado;
- cutoff confirmado;
- package finalized;

mas somente quando existir producer/event contract.

A Sala não infere system message consultando tela.

## Menções

V1:
- menção de usuário.

Sugestões devem retornar apenas usuários:
- com acesso ao Portal;
- autorizados ao contexto quando essa regra puder ser comprovada;
- filtrados server-side.

Não expor diretório inteiro desnecessariamente.

Menção:
- não adiciona ACCESS;
- não adiciona resource scope;
- não torna membro ACL.

## Perfil de usuário

Avatar/nome e click de pessoa usam os contratos definidos em [31-pagina-do-usuario.md](./31-pagina-do-usuario.md).

Quando permitido, clique em usuário pode abrir:

```text
/apps/controllership-finance/users/{userId}
```

Sem duplicar perfil no chat.

## Reply

Reply usa referência de parent message.

A UI deve permitir:
- ver quote/preview;
- navegar/focar parent quando disponível;
- tratar parent soft-deleted sem quebrar thread.

## Reactions

Reactions:
- expressão social;
- não business state;
- não audit approval;
- não substituem validation/rejection.

Catálogo usa o `plugin-ui`.

## Pins

Pins:
- destacam informação;
- aparecem em "Neste chat";
- não alteram owner state;
- não representam decisão formal.

## Edit / delete

### Edit

Somente self e message kind editável.

Visual:
- marker "editada" quando kit/contract expuser.

### Delete

Soft-delete.

O histórico deve preservar:
- id;
- author reference;
- timestamps;
- metadata mínima;
- audit/correlation.

A UI não reexibe conteúdo apagado se policy definir tombstone.

## Attachments

A Sala suporta anexos porque o `plugin-ui` já possui:
- pending attachments;
- file drop;
- preview;
- inline images;
- shared files.

Boundary:

```text
room attachment
!= checklist evidence
```

Anexo de conversa não vira evidência formal de P2 automaticamente.

Se um documento precisa valer como evidência:
- usar ação/processo owner de P2;
- registrar vínculo explícito.

### Storage físico

```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Requisitos:
- durable storage;
- metadata persistida;
- auth na leitura;
- content-type/size validation;
- filename sanitization;
- no secrets;
- no DB blob se o padrão de plataforma vigente usar object/file storage.

Não copiar path/storage do Comercial sem revalidar padrão atual.

## Arquivos e links compartilhados

Usar `RoomSharedItemList`.

Views:
- Recentes;
- Arquivos;
- Links.

A lista é derivada das mensagens da room.

Não criar repository paralelo só para "shared items" quando puder ser projection.

## Find in chat

Usar `RoomMessageFindPanel`.

Busca:
- escopo somente da room autorizada;
- server-side quando necessário à paginação/histórico;
- sem varrer rooms sem autorização;
- highlight no kit.

## Read state / unread

Room read state é estado próprio do produto.

Conceitos:
- `lastReadAt`;
- unread count;
- mentioned state.

Pode ser persistido no BFF.

Não usar unread como regra de processo.

## Realtime

Experiência TARGET:
- novas mensagens aparecem sem recarregar página quando a infraestrutura suportar;
- inbox/unread atualiza;
- reconnection state é visível;
- perda de realtime não torna a Sala inutilizável.

Implementação:

```text
REALTIME_TRANSPORT = TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Inventariar:
- transport vigente da plataforma;
- provider compartilhado;
- SSE/WebSocket/polling;
- heartbeat/reconnect;
- auth;
- multi-instance/pubsub.

Não copiar `CommercialRealtimeProvider` nem hub interno.

Fallback funcional deve seguir o padrão aprovado no futuro slice.

## Notificações

Usar a capability canônica da Minha DELPI.

Não criar:
- SMTP próprio;
- preference store próprio;
- notification center paralelo.

Triggers TARGET V1:
- menção explícita ao usuário;
- task criada a partir de mensagem quando Item 5 habilitar isso.

Não notificar toda mensagem por default.

Outros triggers exigem evidência de negócio.

## "Criar tarefa" a partir de mensagem

UI já suporta `onCreateTask`.

Estado:

```text
WAITING_FOR_ITEM_5_TASK_CONTRACT
```

Quando habilitado:
- task owner cria a tarefa;
- mensagem ganha referência `task_ref`/equivalente;
- attachment migration/copy policy precisa ser explícita;
- task não é owned pela Sala.

## Auditoria

Eventos próprios mínimos:
- room resolved/created;
- message posted;
- message edited;
- message soft-deleted;
- reaction changed;
- pin changed;
- attachment uploaded/removed;
- read-state changes apenas se audit requirement justificar.

Não duplicar corpo completo da mensagem em audit log comum se a própria message store já é system of record e isso ampliar exposição.

Business events continuam auditados pelos owners P1–P5.

## Retenção

```text
RETENTION_POLICY = TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Não inventar prazo.

Requisitos:
- política da plataforma/LGPD aplicável;
- tombstone e audit coerentes;
- attachments alinhados à retenção da mensagem;
- eventual legal hold/backup segue policy corporativa.

Retenção é governance técnico/legal, não permission code.

## Estados da experiência

### LOADING
- inbox/thread usam loading do kit;
- não limpar thread antiga prematuramente em refresh seguro.

### REFRESHING
- manter conteúdo existente;
- indicar atualização.

### EMPTY — inbox
```text
Nenhuma conversa ainda.
Abra um contexto de trabalho para iniciar uma interação.
```

Sem CTA "Criar sala".

### EMPTY — thread
```text
Nenhuma mensagem ainda.
Escreva a primeira mensagem nesta sala.
```

### PARTIAL
Exemplos:
- room/messages disponíveis, realtime indisponível;
- thread disponível, participants profile parcial;
- shared items falhando, chat disponível.

### CONNECTION_DEGRADED
Banner explícito; chat continua pelo mecanismo suportado.

### ERROR
Erro contextual por módulo quando possível.

### FORBIDDEN
Sem ACCESS/context access.

### NOT_FOUND
room/context não existe ou não pode ser resolvido conforme policy de enumeração.

### CONTEXT_UNAVAILABLE
A room pode existir historicamente, mas se o contexto owner não estiver mais acessível:
- não mostrar conteúdo cached;
- fail-closed;
- instrução de recovery quando aplicável.

## Light / dark

Mesma árvore:

```text
SAME DOM
SAME PANES
SAME MESSAGE ORDER
SAME ACTIONS
+ THEME TOKENS
```

O CSS canônico do `plugin-ui` controla:
- canvas;
- inbox;
- selected/unread row;
- thread;
- composer;
- toolbar;
- shared panel;
- side panel;
- focus/hover.

O Portal apenas mapeia tokens.

## Responsividade

Comportamento canônico já implementado no kit:
- breakpoint narrow em torno de 900px;
- desktop: inbox + thread;
- mobile/narrow: inbox **ou** thread;
- back retorna ao inbox;
- filters/search preservados.

Não criar split comprimido no mobile.

## Acessibilidade

Coberta pelo kit e complementada pelo host:
- nav/regions;
- aria labels PT;
- keyboard;
- focus;
- accessible composer;
- message action toolbar;
- search;
- mention menu;
- attachment controls;
- context panel;
- selected room state.

O host deve fornecer labels e content acessíveis.

## Deep links

Inbox:

```text
/apps/controllership-finance/interaction-rooms?filter=mentioned&q=...
```

Thread:

```text
/apps/controllership-finance/interaction-rooms/{roomId}?filter=mentioned&q=...
```

Ao abrir uma sala a partir de P1–P5:
- resolve room;
- navega para room;
- retorno ao contexto pode ser preservado por `returnTo` validado no basePath do Portal.

Nunca open redirect.

## Contract surface lógica

Os nomes físicos finais entram no OpenAPI futuro.

### Inbox / resolve
```text
GET  /interaction-rooms
POST /interaction-rooms/resolve
GET  /interaction-rooms/{roomId}
```

### Messages
```text
GET    /interaction-rooms/{roomId}/messages
POST   /interaction-rooms/{roomId}/messages
PATCH  /interaction-rooms/{roomId}/messages/{messageId}
DELETE /interaction-rooms/{roomId}/messages/{messageId}
```

### Read state
```text
POST /interaction-rooms/{roomId}/read
```

### Mentions
```text
GET /interaction-rooms/{roomId}/mention-suggest
```

### Reactions / pins
```text
PUT    /interaction-rooms/{roomId}/messages/{messageId}/reactions/{code}
DELETE /interaction-rooms/{roomId}/messages/{messageId}/reactions/{code}
PUT    /interaction-rooms/{roomId}/messages/{messageId}/pin
DELETE /interaction-rooms/{roomId}/messages/{messageId}/pin
```

### Shared / find
```text
GET /interaction-rooms/{roomId}/shared
GET /interaction-rooms/{roomId}/find?q=...
```

### Attachments
Contract físico `TO_INVENTORY`, mantendo owner room/message.

### Realtime
Contract físico `TO_INVENTORY`.

## RQ / AC

### RQ-ROOM-01 — full-page comum
Aceite:
- `InteractionRoomPage` é o canvas principal;
- zero clone local do chat;
- desktop/mobile/dark/light pelo kit.

### RQ-ROOM-02 — somente contexto
Aceite:
- sem global wall;
- sem criação livre;
- resolve somente context types aprovados.

### RQ-ROOM-03 — uma sala por contexto
Aceite:
- resolve idempotente;
- concorrência não cria duplicatas;
- title deriva do owner.

### RQ-ROOM-04 — AuthZ por contexto
Aceite:
- ACCESS + context access;
- members/mentions não concedem acesso;
- MANAGE sozinho não implica ACCESS.

### RQ-ROOM-05 — mensagem não muda business state
Aceite:
- reply/reaction/pin/comment não validam/rejeitam/finalizam/enviam;
- ações reais continuam owners.

### RQ-ROOM-06 — edit/delete seguros
Aceite:
- autor edita própria text message;
- delete soft;
- system message imutável para usuário;
- audit/timestamps preservados.

### RQ-ROOM-07 — attachments não viram evidência
Aceite:
- attachment de chat fica no domínio room;
- P2 evidence exige ação owner explícita.

### RQ-ROOM-08 — mentions seguras
Aceite:
- suggestions server-side;
- apenas targets permitidos;
- mention não concede access.

### RQ-ROOM-09 — realtime degradável
Aceite:
- perda do transport mostra degraded state;
- leitura/envio continuam conforme fallback aprovado;
- transport não é hardcoded na documentação.

### RQ-ROOM-10 — notifications canônicas
Aceite:
- mention usa capability da plataforma;
- sem SMTP/preferences local;
- não notificar toda mensagem.

### RQ-ROOM-11 — create task não existe na V1
Aceite:
- `onCreateTask` não é exposto;
- mensagem/menção não criam TaskProjection;
- evolução futura exige contract de task entity e owner separado da Sala.

### RQ-ROOM-12 — Help sync
Aceite:
- manual explica conversa vs ação de processo;
- context, mentions, attachments, pins, edit/delete e limits da IA;
- conteúdo só publica quando runtime existir.

## Matriz futura de testes

### Positive
- ACCESS + context access abre inbox;
- resolve competência;
- resolve checklist item;
- resolve pendência/classificação;
- resolve pacote;
- resolve repetido retorna mesma room;
- enviar message;
- reply;
- reaction;
- pin;
- edit own;
- soft-delete own;
- mention;
- attachment;
- shared files/links;
- find;
- unread/read;
- deep link/F5.

### Sibling
- room A não recebe message de B;
- context A não resolve mesma room de B;
- unread A não altera B;
- attachment A não aparece em B;
- pin A não aparece em B;
- user profile parcial não derruba thread;
- realtime de room A não atualiza room B incorretamente.

### Negative
- sem ACCESS;
- MANAGE sem ACCESS;
- context inacessível;
- room id de outro context;
- member sem context access;
- mention target sem acesso;
- editar mensagem de outro autor;
- hard delete;
- editar system message;
- criar room livre;
- resolver context type não registrado;
- attachment de chat tratado como evidence;
- message alterando business state;
- stale/cached room vazando após perda de acesso;
- open redirect em returnTo.

### Experiência
- loading;
- refreshing;
- empty inbox;
- empty thread;
- partial;
- connection degraded;
- error;
- 403;
- 404;
- desktop split;
- resize/collapse;
- mobile inbox → thread → back;
- light;
- dark;
- keyboard/focus;
- Help.

## Scripts/validators planejados para a implementação futura

Não criar agora.

```text
validate-interaction-context-registry
- contextType registrado
- owner conhecido
- deep link conhecido
- title resolver conhecido
- context AuthZ adapter conhecido

validate-interaction-route-contracts
- inbox/room deep links
- filter/q roundtrip
- F5
- returnTo restrito ao basePath

validate-interaction-authz
- ACCESS + context access
- membership/mention não concedem acesso
- fail-closed

validate-interaction-message-policy
- edit own
- soft delete
- system immutability
- no business state mutation

validate-interaction-attachment-boundary
- chat attachment != P2 evidence
- auth/read policy
- size/content-type policy

validate-interaction-help
- docs apenas de capabilities implementadas
```

Nomes/localização são conceituais; devem seguir o padrão do HEAD futuro.

## Inventários técnicos restantes

### R01 — persistência física

```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Definir migrations/tables/repositories apenas no slice stateful.

### R02 — attachment storage

```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Revalidar storage adapter canônico.

### R03 — realtime transport

```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Não copiar hub/provider Comercial.

### R04 — notification integration

```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Amarrar T02/capability canônica da Minha DELPI.

### R05 — retention

```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Policy técnica/legal.

### R06 — TaskProjection

```text
CLOSED_PRODUCT_BOUNDARY
```

Item 5 definiu que TaskProjection deriva dos owners e não é criada pela Sala. `CREATE_TASK_FROM_MESSAGE = NOT_INCLUDED_IN_V1`.

Nenhum desses inventários é decisão de produto aberta.

## Gate

```text
VISUAL_FAMILY_DEFINED        = PASS
FULL_PAGE_REUSE_DEFINED      = PASS
CONTEXT_MODEL_DEFINED        = PASS
ROOM_CREATION_DEFINED        = PASS
AUTHZ_DEFINED                = PASS
MESSAGE_POLICY_DEFINED       = PASS
ATTACHMENT_BOUNDARY_DEFINED  = PASS
MENTION_POLICY_DEFINED       = PASS
REALTIME_BEHAVIOR_DEFINED    = PASS
NOTIFICATION_POLICY_DEFINED  = PASS
DEEP_LINK_DEFINED            = PASS
LIGHT_DARK_DEFINED           = PASS
MOBILE_DEFINED               = PASS
RQ_AC_TEST_MATRIX_DEFINED    = PASS
IMPLEMENTATION               = NOT_AUTHORIZED
```

Estado:

```text
ITEM 4 = READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY
```

## Resultado esperado

A Sala de interação deve ser uma **conversation layer contextual** sobre o trabalho real do Portal.

```text
OPEN CONTEXT
→ RESOLVE ROOM
→ COLLABORATE
→ REFERENCE
→ RETURN TO OWNER
```

Sem transformar conversa em workflow, permission ou system of record de negócio.
