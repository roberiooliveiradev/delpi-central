# Commercial API — worklist em tempo real (WebSocket)

Atualização live da fila de tarefas (Meu dia / Início) **e** toasts in-app via WebSocket nativo FastAPI — padrão Transformômetro/TV Dashboard.

## Endpoint

```
wss://{host}/apps/commercial-api/commercial/realtime/ws?token={jwt}&client_id={uuid}
```

- **Auth:** JWT em query `token` (`validate_token`); exige permissão `commercial.worklist.view` (ou alias legado).
- **Salas:** `user:{sub}` sempre; `team` se gestor (`commercial.seller-portfolios.manage`).
- **Keepalive:** cliente envia texto `ping`; servidor responde `{ "type": "pong" }`.

## Evento

```json
{
  "type": "worklist.changed",
  "reason": "task.created",
  "taskId": "uuid",
  "taskTitle": "Ligar ACME",
  "assigneeUserIds": ["seller-a"],
  "actorUserId": "manager-1",
  "actorClientId": "client-uuid",
  "notification": {
    "title": "Nova tarefa",
    "message": "Foi atribuída a você (ou à equipe): Ligar ACME",
    "variant": "info"
  }
}
```

Valores de `reason`: `task.created`, `task.updated`, `task.completed`, `task.deferred`, `task.reassigned`, `attachment.changed`.

## Fan-out

Após mutação HTTP (create/update/complete/defer/reassign/anexo), notify broadcast para:

- `user:{assignee}` (e assignee anterior em reassign/update)
- `team` (gestores com fila equipe)

O MFE:

1. **Refetch** `GET /me/worklist` (debounce ~400 ms) — Meu dia + contagens no Início.
2. **Toast** `FloatingNotice` com `notification` — **exceto** eco do mesmo `actorClientId` (a aba que mutou já tem `notifySuccess` local).

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
2. Na aba que mutou: toast local de sucesso; toast WS **não** duplica.
3. Gateway: `Upgrade` + `Connection` em `/apps/commercial-api/` (prod e dev).
4. Reconnect após F5.
