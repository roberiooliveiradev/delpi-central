# Commercial API — worklist e carteiras em tempo real (WebSocket)

Atualização live da fila de tarefas (Meu dia / Início) **e** mutações de carteira
(toasts + refetch) via WebSocket nativo FastAPI — padrão Transformômetro/TV Dashboard.

## Endpoint

```
wss://{host}/apps/commercial-api/commercial/realtime/ws?token={jwt}&client_id={uuid}
```

- **Auth:** JWT em query `token` → `validate_token` + **RBAC via core-api** (`load_user_rbac`), igual ao middleware HTTP. Exige `commercial.accounts.view` **ou** `commercial.worklist.view` (aliases inclusos). O access token Keycloak **não** carrega permissões Delpi — checar só o JWT quebrava o handshake (401 em loop).
- **Salas:** `user:{sub}` sempre; `team` se gestor (`commercial.seller-portfolios.manage`).
- **Keepalive:** cliente envia texto `ping`; servidor responde `{ "type": "pong" }`.
- **Middleware HTTP:** path `/commercial/realtime/ws` é público no JWT middleware (token na query; auth no handler).

## Eventos

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

`actorDisplayName` vem do usuário autenticado (RBAC `name`) e, se faltar, da carteira (`display_name`); se ausente → «Alguém da equipe». `assigneeDisplayName` é o responsável atual.

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
(transferência: união origem + destino). Textos em `seller_portfolio_messages.json` → `realtime`.

## Fan-out worklist

Após mutação HTTP (create/update/complete/defer/reassign/anexo), notify broadcast para:

- `user:{assignee}` (e assignee anterior em reassign/update)
- `team` (gestores com fila equipe)

O MFE:

1. **Refetch** `GET /me/worklist` (debounce ~400 ms) — Meu dia + contagens no Início.
2. **Toast** `FloatingNotice` via `resolveWorklistNotification` — **exceto** eco do mesmo `actorClientId` (a aba que mutou já tem `notifySuccess` local).

## Fan-out carteira

1. **Toast** via `resolvePortfolioNotification` (anti-eco `actorClientId`).
2. **Refetch** lista/detalhe admin e Histórico em Minha Carteira (`useCommercialPortfolioSync`).

## Anti-eco

Mutações enviam header `X-Commercial-Client-Id`; evento inclui `actorClientId`.

| Efeito | Eco local |
|--------|-----------|
| Refetch fila / carteira | Sempre (garante contagens/anexos/histórico) |
| Toast | Ignora se `actorClientId === clientId` local |

## Limitações

- Hub **in-memory** (processo Uvicorn único). Multi-réplica → backlog Redis pub-sub.
- Não usa Socket.IO do Portal/`core-api` (notificações globais do host) — só toasts do plugin Comercial.
- Rooms por `portfolio:{id}` (membership dinâmica no socket) ficam fora do v1 — publish resolve membros no momento do audit.

## Homologação

1. Dois browsers (vendedor + gestor): mutação worklist em um → fila do outro atualiza **e** toast aparece no outro sem **Atualizar**.
2. Dois browsers (membros da mesma carteira): vincular cliente / membro → toast `portfolio.changed` no outro; Histórico em Minha Carteira atualiza.
3. Usuário sem membership → `GET …/audit` retorna 403.
