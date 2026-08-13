# Commercial API — worklist e carteiras em tempo real (WebSocket)

Atualização live da fila de tarefas (Meu dia / Início) **e** mutações de carteira
(toasts + refetch) via WebSocket nativo FastAPI — padrão Transformômetro/TV Dashboard.

## Endpoint

```
wss://{host}/apps/commercial-api/commercial/realtime/ws?token={jwt}&client_id={uuid}
```

- **Auth:** JWT em query `token` → `validate_token` + **RBAC via core-api** (`load_user_rbac`), igual ao middleware HTTP. Exige `commercial.accounts.view` **ou** `commercial.worklist.view` (somente canônicos). O access token Keycloak **não** carrega permissões Delpi — checar só o JWT quebrava o handshake (401 em loop).
- **Salas:** `user:{sub}` sempre; `team` se gestor (`commercial.seller-portfolios.manage`).
- **Keepalive:** cliente envia texto `ping`; servidor responde `{ "type": "pong" }`.
- **Middleware HTTP:** path `/commercial/realtime/ws` é público no JWT middleware (token na query; auth no handler).

## Eventos

### `presence.updated`

Emitido para a sala `team` (gestores com `seller-portfolios.manage`) quando o
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

Valores de `reason`: `task.created`, `task.updated`, `task.completed`, `task.deferred`, `task.reassigned`, `attachment.changed`.

`actorDisplayName` vem do usuário autenticado (RBAC `name` / `preferred_username` / e-mail via `bind_request_actor`); se ausente → «Alguém da equipe» (o MFE tenta resolver pelo diretório com `actorUserId`). Não usar o `display_name` da carteira como nome da pessoa. `assigneeDisplayName` é o responsável atual.

O payload `notification` no fio é genérico (audiência `team`). O MFE personaliza o toast com `assigneeUserIds` + usuário atual:

| Papel do usuário logado | Exemplo (atribuição) |
|-------------------------|----------------------|
| Responsável atual (`assigneeUserIds[0]`) | `{actor} atribuiu a você: {title}` |
| Responsável anterior | `{actor} reatribuiu a tarefa: {title}` |
| Gestor / equipe | `{actor} atribuiu: {title}` / `{actor} reatribuiu…` |

Assim gestores em `user:` + `team` não recebem toast duplicado.

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
3. Usuário sem membership → `GET …/audit` retorna 403.
