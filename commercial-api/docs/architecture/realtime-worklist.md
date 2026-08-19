# Commercial API — worklist, carteiras e sala de interação (WebSocket)

Atualização live da fila de tarefas (Meu dia / Início), mutações de carteira
(toasts + refetch) **e** sala de interação (mensagens / reações / menções / anexos)
via WebSocket nativo FastAPI — padrão Transformômetro/TV Dashboard.

**Path inalterado:** um único endpoint serve worklist e salas de interação.
Join em `room:{uuid}` só via mensagem de cliente `subscribe` (não no handshake).

## Endpoint

```
wss://{host}/apps/commercial-api/commercial/realtime/ws?token={jwt}&client_id={uuid}
```

- **Auth:** JWT em query `token` → `validate_token` + **RBAC via core-api** (`load_user_rbac`), igual ao middleware HTTP. Exige `commercial.access`. O access token Keycloak **não** carrega permissões Delpi — checar só o JWT quebrava o handshake (401 em loop).
- **Salas no connect:** `user:{sub}` sempre; `interaction` (inbox leve) para todo `commercial.access`; `team` se gestor (`commercial.manage`).
- **Salas sob demanda:** `room:{uuid}` após `subscribe` (qualquer usuário com `commercial.access`; sala deve existir).
- **Keepalive:** cliente envia texto `ping`; servidor responde `{ "type": "pong" }`.
- **Outros textos JSON:** `subscribe` / `unsubscribe` (protocolo da sala — abaixo).
- **Middleware HTTP:** path `/commercial/realtime/ws` é público no JWT middleware (token na query; auth no handler).
- **Código:** `commercial_realtime_protocol.py` (parse/ack), `commercial_realtime_hub.py` (`join_room` / `leave_room`), `commercial_realtime_notify.py` (fan-out), gate `can_subscribe_interaction_room` em `realtime_routes.py`.

## Sala de interação (subscribe / fan-out)

### Cliente → servidor

Texto JSON no mesmo socket (além de `ping`):

```json
{ "type": "subscribe", "roomId": "<uuid>" }
```

```json
{ "type": "unsubscribe", "roomId": "<uuid>" }
```

Aceita `room_id` como alias de `roomId`. Outros `type` (exceto `ping`) são ignorados pelo handler da sala.

### Ack servidor → cliente

| type | Quando |
|------|--------|
| `subscribed` | Join OK → socket entra em `room:{uuid}` (`roomKey` no ack) |
| `unsubscribed` | Leave OK |
| `error` | `code`: `roomIdInvalid` \| `accessDenied` \| `subscribeFailed` \| `unsubscribeFailed` |

`accessDenied`: sala **inexistente** ou removida (fail-closed via repositório). UUID inválido → `roomIdInvalid` **sem** tentar join. Acesso à plataforma (`commercial.access`) é validado no handshake WS — **não** exige linha em `interaction_room_members`.

### Chave de sala

`interaction_room_key(room_id)` → `room:{uuid}` (minúsculas do UUID canônico). **Não** confundir com `user:{sub}` nem com `team`.

### Eventos no fio (`room:*`)

Fan-out **só** para sockets que fizeram `subscribe` naquela sala (não para todo membro online).

#### `room.message.created` | `room.message.updated` | `room.message.deleted`

Após POST/PATCH/DELETE em `/interaction-rooms/{id}/messages`.

```json
{
  "type": "room.message.created",
  "roomId": "uuid",
  "messageId": "uuid",
  "message": { "...": "to_dict da mensagem" },
  "actorUserId": "seller-a",
  "actorDisplayName": "Ana",
  "actorClientId": "client-uuid"
}
```

#### `room.reaction`

Após PUT/DELETE de reação na mensagem.

```json
{
  "type": "room.reaction",
  "roomId": "uuid",
  "messageId": "uuid",
  "code": "thumbsup",
  "action": "set",
  "userId": "seller-a",
  "actorUserId": "seller-a",
  "actorDisplayName": "Ana",
  "actorClientId": "client-uuid"
}
```

`action`: `set` | `clear`.

#### `room.pin`

Após POST/DELETE pin. Fan-out em `room:{uuid}` + sinal de inbox.

```json
{
  "type": "room.pin",
  "roomId": "uuid",
  "messageId": "uuid",
  "action": "set",
  "actorUserId": "seller-a",
  "actorDisplayName": "Ana",
  "actorClientId": "client-uuid"
}
```

`action`: `set` | `clear`.

### Eventos no fio (`user:` — sem exigir subscribe da sala)

#### `room.mention`

Menção `kind=user` na mensagem (exclui o autor). Broadcast em `user:{mentioned}`.

Se o destinatário estiver **offline** no Comercial → Core notificação categoria `commercial_collaboration` (`TaskPortalNotificationDeliveryPolicy` + `mention_event_type()` do JSON).

```json
{
  "type": "room.mention",
  "roomId": "uuid",
  "messageId": "uuid",
  "mentionedUserIds": ["seller-b"],
  "actorUserId": "seller-a",
  "actorDisplayName": "Ana",
  "actorClientId": "client-uuid",
  "notification": {
    "title": "…",
    "message": "…",
    "variant": "info"
  }
}
```

#### `room.attachment`

Upload/delete de anexo com `owner_type=room_message`. Fan-out em `room:{uuid}` (sem `notification`, thread inscrita) **e** toast em `user:` dos membros atuais. **Não** emite `worklist.changed`. Inbox recebe `room.inbox.changed`.

```json
{
  "type": "room.attachment",
  "reason": "attachment.uploaded",
  "roomId": "uuid",
  "messageId": "uuid",
  "attachmentId": "uuid",
  "fileName": "spec.pdf",
  "memberUserIds": ["seller-a", "seller-b"],
  "actorUserId": "seller-a",
  "actorDisplayName": "Ana",
  "notification": {
    "title": "…",
    "message": "…",
    "variant": "info"
  }
}
```

### Inbox (`interaction` + HTTP)

Handshake: todo socket com `commercial.access` entra na sala `interaction`.

`room.inbox.changed` `{ "type": "room.inbox.changed", "roomId": "<uuid>" }` — **sem** body da mensagem. O MFE faz debounce (400 ms) e chama `GET /interaction-rooms` (`operation_id=list_interaction_rooms`).

Eventos de mensagem/pin/system/anexo também emitem este sinal.

## Eventos (worklist / carteira / conta)

### `presence.updated`

Emitido para a sala `team` (gestores com `commercial.manage`) quando o
conjunto de usuários online muda, e como **snapshot** ao entrar na sala `team`.

```json
{
  "type": "presence.updated",
  "onlineUserIds": ["seller-a", "manager-1"]
}
```

- **Online** = usuário com ≥1 socket ativo no Portal Comercial (multi-aba conta
  como um único online).
- Desconectar a última aba → remove o `user_id` da lista.
- Idle: sem `ping` por ~75s o servidor fecha o socket (defesa contra unmount
  incompleto do remote federado).
- Quem vê: só clientes na sala `team` (Admin Equipe). Operacional (só `user:`)
  não recebe fan-out de presença.
- O GET `/administration/team-roster` **não** inclui online — presença é só WS.

### `worklist.changed`

```json
{
  "type": "worklist.changed",
  "reason": "task.reassigned",
  "taskId": "uuid",
  "taskTitle": "Ligar ACME",
  "assigneeUserIds": ["seller-b", "seller-a"],
  "actorUserId": "manager-1",
  "actorDisplayName": "Ana Gestora",
  "assigneeDisplayName": "Bruno Vendedor",
  "actorClientId": "client-uuid",
  "notification": {
    "title": "Tarefa reatribuída",
    "message": "Ana Gestora reatribuiu a Bruno Vendedor: Ligar ACME",
    "variant": "info"
  }
}
```

Valores de `reason`: `task.created`, `task.updated`, `task.completed`, `task.deferred`, `task.reassigned`, `task.deleted`, `task.due_soon`, `task.overdue`, `attachment.changed`.

`actorDisplayName` vem do usuário autenticado (RBAC `name` / `preferred_username` / e-mail via `bind_request_actor`); se ausente → «Alguém da equipe» (o MFE tenta resolver pelo diretório com `actorUserId`). Não usar o `display_name` da carteira como nome da pessoa. `assigneeDisplayName` é o responsável atual.

O payload `notification` no fio é genérico (audiência `team`). O MFE personaliza o toast com `assigneeUserIds` + usuário atual:

| Papel do usuário logado | Exemplo (atribuição) |
|-------------------------|----------------------|
| Responsável atual (`assigneeUserIds[0]`) | `{actor} atribuiu a você: {title}` |
| Responsável anterior | `{actor} reatribuiu a tarefa: {title}` |
| Gestor / equipe | `{actor} atribuiu: {title}` / `{actor} reatribuiu…` |

Assim gestores em `user:` + `team` não recebem toast duplicado.

Lembretes `task.due_soon` / `task.overdue` saem do job de due scan: se o destinatário está **online** no Comercial, o publish da outbox emite toast WS (em vez do sino Minha Delpi).

### `orders.ready_to_invoice`

Emitido no publish da outbox quando uma linha entra em Pronto para faturar e o destinatário está **online** no Comercial (WS). Offline continua no sino Minha Delpi (categoria `commercial`).

```json
{
  "type": "orders.ready_to_invoice",
  "lineKey": "01|102655|05",
  "pedido": "102655",
  "linha": "05",
  "cliente": "WEG MOTORES",
  "filial": "01",
  "actionTarget": "/apps/commercial/open-orders?stage=ready_to_invoice&q=102655&branch=01",
  "userIds": ["seller-a"],
  "notification": {
    "title": "Pedido pronto para faturar",
    "message": "A linha 102655/05 do cliente WEG MOTORES entrou em Pronto para faturar.",
    "variant": "info"
  }
}
```

### Portal vs toast (presença)

`TaskPortalNotificationDeliveryPolicy` consulta `CommercialRealtimeHub.is_user_online`. Online → toast WS; offline → Core `/integrations/notifications`. Cobre eventos de tarefa (`commercial.task.*`), `commercial.order.ready_to_invoice` e menção da sala (`mention_event_type()` em `interaction_room.json`).

### `portfolio.changed`

Emitido após gravar `audit_log` em mutações de carteira (`_append_audit`).

```json
{
  "type": "portfolio.changed",
  "reason": "seller_portfolio.add_customer",
  "portfolioId": "uuid",
  "portfolioIds": ["uuid-origem", "uuid-destino"],
  "displayName": "Sul",
  "memberUserIds": ["seller-a", "seller-b"],
  "actorUserId": "manager-1",
  "actorDisplayName": "Ana Gestora",
  "actorClientId": "client-uuid",
  "notification": {
    "title": "Cliente vinculado",
    "message": "…",
    "variant": "info"
  }
}
```

Fan-out: salas `user:{id}` dos **membros ativos** da(s) carteira(s) afetada(s)
**e** sala `team` (gestores com `seller-portfolios.manage` / team scope no WS).
Transferência: união origem + destino nos `memberUserIds`. Textos em
`seller_portfolio_messages.json` → `realtime`.

Gestores em `team` passam a receber `portfolio.changed` mesmo sem membership na
carteira mutada — necessário para `reloadScope` / Equipe fresca no MFE.

### `account.changed`

Emitido após gravar `audit_log` em mutações de **conta** (contatos e avatar).

```json
{
  "type": "account.changed",
  "reason": "account.contact.created",
  "customerCode": "000001",
  "customerStore": "01",
  "memberUserIds": ["seller-a"],
  "actorUserId": "manager-1",
  "actorDisplayName": "Ana Gestora",
  "actorClientId": "client-uuid",
  "notification": {
    "title": "Contato criado",
    "message": "Ana Gestora: Contato «…» adicionado à conta.",
    "variant": "success"
  }
}
```

Valores de `reason`: `account.contact.created|updated|deleted`,
`account.avatar.uploaded|deleted`.

Fan-out: salas `user:` dos membros das carteiras que possuem o cliente **e**
sala `team`. Textos em `audit_messages.json`. No MFE,
`useCommercialAccountSync` atualiza contatos / histórico / avatar sem F5.

## Fan-out worklist

Após mutação HTTP (create/update/complete/defer/reassign/anexo), notify broadcast para:

- `user:{assignee}` (e assignee anterior em reassign/update)
- `team` (gestores com fila equipe)

O MFE:

1. **Refetch** `GET /me/worklist` (debounce ~400 ms) — Meu dia + contagens no Início.
2. **Toast** `FloatingNotice` via `resolveWorklistNotification` — **exceto** eco do mesmo `actorClientId` (a aba que mutou já tem `notifySuccess` local).

## Fan-out carteira

1. **Toast** via `resolvePortfolioNotification` (anti-eco `actorClientId`).
2. **Refetch** lista/detalhe admin, Histórico em Minha Carteira e **escopo**
   (`reloadScope` no MFE via `useCommercialPortfolioSync` + bridge global).
3. Gestores na sala `team` recebem o mesmo evento (além dos membros em `user:`).

## Anti-eco

Mutações enviam header `X-Commercial-Client-Id`; evento inclui `actorClientId`.

| Efeito | Eco local |
|--------|-----------|
| Refetch fila / carteira | Sempre (garante contagens/anexos/histórico) |
| Toast | Ignora se `actorClientId === clientId` local |

## Limitações

- Hub **in-memory** (processo Uvicorn único). Multi-réplica → backlog Redis pub-sub
  (presença e `room:{uuid}` incluídos — contagem/join por processo).
- Não usa Socket.IO do Portal/`core-api` (notificações globais do host) — só toasts do plugin Comercial.
- Rooms por `portfolio:{id}` (membership dinâmica no socket) ficam fora do v1 — publish resolve membros no momento do audit.
- Mensagem/reação da sala **exigem** `subscribe`; menção/anexo usam `user:` para alcançar quem não está com a thread aberta.

## Homologação

1. Dois browsers (vendedor + gestor): mutação worklist em um → fila do outro atualiza **e** toast aparece no outro sem **Atualizar**.
2. Dois browsers (membros da mesma carteira): vincular cliente / membro → toast `portfolio.changed` no outro; Histórico em Minha Carteira atualiza.
3. Dois browsers na mesma conta: criar/editar contato ou avatar → toast `account.changed` no outro; Histórico da conta / lista de contatos atualizam sem F5.
4. Usuário sem membership → `GET …/audit` retorna 403.
5. Dois browsers membros da mesma sala: um faz `subscribe` + POST mensagem → o outro recebe `room.message.created` sem F5; quem **não** assinou a sala não recebe o evento `room.message.*`.
6. Menção `@user` com destinatário offline → sino Minha Delpi (`commercial_collaboration`); online → `room.mention` no `user:`.
7. Anexo em mensagem da sala → `room.attachment` nos `user:` dos membros (sem `worklist.changed`).
