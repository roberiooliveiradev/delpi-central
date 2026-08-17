# Commercial API — worklist e carteiras em tempo real (WebSocket)

Atualização live da fila de tarefas (Meu dia / Início) **e** mutações de carteira
(toasts + refetch) via WebSocket nativo FastAPI — padrão Transformômetro/TV Dashboard.

## Endpoint

```
wss://{host}/apps/commercial-api/commercial/realtime/ws?token={jwt}&client_id={uuid}
```

- **Auth:** JWT em query `token` → `validate_token` + **RBAC via core-api** (`load_user_rbac`), igual ao middleware HTTP. Exige `commercial.access`. O access token Keycloak **não** carrega permissões Delpi — checar só o JWT quebrava o handshake (401 em loop).
- **Salas:** `user:{sub}` sempre; `team` se gestor (`commercial.manage`).
- **Keepalive:** cliente envia texto `ping`; servidor responde `{ "type": "pong" }`.
- **Middleware HTTP:** path `/commercial/realtime/ws` é público no JWT middleware (token na query; auth no handler).

## Eventos

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

`TaskPortalNotificationDeliveryPolicy` consulta `CommercialRealtimeHub.is_user_online`. Online → toast WS; offline → Core `/integrations/notifications`. Cobre eventos de tarefa (`commercial.task.*`) e `commercial.order.ready_to_invoice`.

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
  (presença incluída — contagem por processo).
- Não usa Socket.IO do Portal/`core-api` (notificações globais do host) — só toasts do plugin Comercial.
- Rooms por `portfolio:{id}` (membership dinâmica no socket) ficam fora do v1 — publish resolve membros no momento do audit.

## Homologação

1. Dois browsers (vendedor + gestor): mutação worklist em um → fila do outro atualiza **e** toast aparece no outro sem **Atualizar**.
2. Dois browsers (membros da mesma carteira): vincular cliente / membro → toast `portfolio.changed` no outro; Histórico em Minha Carteira atualiza.
3. Dois browsers na mesma conta: criar/editar contato ou avatar → toast `account.changed` no outro; Histórico da conta / lista de contatos atualizam sem F5.
4. Usuário sem membership → `GET …/audit` retorna 403.
