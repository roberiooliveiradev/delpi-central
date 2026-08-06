# Commercial API — worklist em tempo real (WebSocket)

Atualização live da fila de tarefas (Meu dia / Início) **e** toasts in-app via WebSocket nativo FastAPI — padrão Transformômetro/TV Dashboard.

## Endpoint

```
wss://{host}/apps/commercial-api/commercial/realtime/ws?token={jwt}&client_id={uuid}
```

- **Auth:** JWT em query `token` → `validate_token` + **RBAC via core-api** (`load_user_rbac`), igual ao middleware HTTP. Exige `commercial.worklist.view` (ou alias). O access token Keycloak **não** carrega permissões Delpi — checar só o JWT quebrava o handshake (401 em loop).
- **Salas:** `user:{sub}` sempre; `team` se gestor (`commercial.seller-portfolios.manage`).
- **Keepalive:** cliente envia texto `ping`; servidor responde `{ "type": "pong" }`.
- **Middleware HTTP:** path `/commercial/realtime/ws` é público no JWT middleware (token na query; auth no handler).

## Evento

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

O payload `notification` no fio é genérico (audiência `team`). O MFE personaliza o toast com `assigneeUserIds` + `myPortfolio.user_id`:

| Papel do usuário logado | Exemplo (atribuição) |
|-------------------------|----------------------|
| Responsável atual (`assigneeUserIds[0]`) | `{actor} atribuiu a você: {title}` |
| Responsável anterior | `{actor} reatribuiu a tarefa: {title}` |
| Gestor / equipe | `{actor} atribuiu: {title}` / `{actor} reatribuiu…` |

Assim gestores em `user:` + `team` não recebem toast duplicado.

## Fan-out

Após mutação HTTP (create/update/complete/defer/reassign/anexo), notify broadcast para:

- `user:{assignee}` (e assignee anterior em reassign/update)
- `team` (gestores com fila equipe)

O MFE:

1. **Refetch** `GET /me/worklist` (debounce ~400 ms) — Meu dia + contagens no Início.
2. **Toast** `FloatingNotice` via `resolveWorklistNotification` — **exceto** eco do mesmo `actorClientId` (a aba que mutou já tem `notifySuccess` local).

## Anti-eco

Mutações enviam header `X-Commercial-Client-Id`; evento inclui `actorClientId`.

| Efeito | Eco local |
|--------|-----------|
| Refetch fila | Sempre (garante contagens/anexos) |
| Toast | Ignora se `actorClientId === clientId` local |

## Limitações

- Hub **in-memory** (processo Uvicorn único). Multi-réplica → backlog Redis pub-sub.
- Não usa Socket.IO do Portal/`core-api` (notificações globais do host) — só toasts do plugin Comercial.
- Carteiras/contas: fora do escopo.

## Homologação

1. Dois browsers (vendedor + gestor): mutação em um → fila do outro atualiza **e** toast aparece no outro sem **Atualizar**.
2. Atribuição/reatribuição: o responsável vê «{nome} atribuiu a você: …»; gestor vê texto genérico com o mesmo ator.
3. Na aba que mutou: toast local de sucesso; toast WS **não** duplica.
4. Gateway: `Upgrade` + `Connection` em `/apps/commercial-api/` (prod e dev).
5. Reconnect após F5.
