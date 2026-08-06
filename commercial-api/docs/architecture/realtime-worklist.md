# Commercial API — worklist em tempo real (WebSocket)

Atualização live da fila de tarefas (Meu dia / Início) via WebSocket nativo FastAPI — padrão Transformômetro/TV Dashboard.

## Endpoint

```
wss://{host}/apps/commercial-api/commercial/realtime/ws?token={jwt}&client_id={uuid}
```

- **Auth:** JWT em query `token` (`validate_token`); exige permissão `commercial.worklist.view` (ou alias legado).
- **Salas:** `user:{sub}` sempre; `team` se gestor (`commercial.seller-portfolios.manage`).
- **Keepalive:** cliente envia texto `ping`; servidor responde `{ "type": "pong" }`.

## Evento v1

```json
{
  "type": "worklist.changed",
  "reason": "task.created",
  "taskId": "uuid",
  "assigneeUserIds": ["seller-a"],
  "actorClientId": "client-uuid"
}
```

Valores de `reason`: `task.created`, `task.updated`, `task.completed`, `task.deferred`, `task.reassigned`, `attachment.changed`.

## Fan-out

Após mutação HTTP (create/update/complete/defer/reassign/anexo), notify broadcast para:

- `user:{assignee}` (e assignee anterior em reassign/update)
- `team` (gestores com fila equipe)

Payload **só invalidação** — MFE refaz `GET /me/worklist`.

## Anti-eco

Mutações enviam header `X-Commercial-Client-Id`; evento inclui `actorClientId`. v1: MFE sempre refetch (debounce ~400 ms).

## Limitações

- Hub **in-memory** (processo Uvicorn único). Multi-réplica → backlog Redis pub-sub.
- Carteiras/contas: fora do escopo v1.

## Homologação

1. Dois browsers (vendedor + gestor): mutação em um → fila do outro atualiza sem **Atualizar**.
2. Gateway: `Upgrade` + `Connection` em `/apps/commercial-api/` (prod e dev).
3. Reconnect após F5.
