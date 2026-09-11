# Requests API — realtime (WebSocket)

Atualização live de Minhas Solicitações (fila, minhas, detalhe) via WebSocket
nativo FastAPI — mesmo padrão do [commercial worklist](../../../commercial-api/docs/architecture/realtime-worklist.md).

**Não substitui** o outbox → Core (`POST /integrations/notifications`) do sino do Portal.
O WS só invalida UI aberta no MFE; o MFE faz debounce + HTTP refetch.

## Dual-channel (WS + sino)

| Canal | Quando | Destino |
|-------|--------|---------|
| WebSocket | Qualquer create/transition/edit/comment/files | MFE conectado (hint + refetch) |
| Outbox → Core sino | Create | `permissionCodes: [{type}.process]` (exclui criador) |
| Outbox → Core sino | Transição em **gate principal** e ator ≠ criador | `userIds: [created_by_user_id]` |
| Outbox → Core sino | Comentário / transição com assignee e ator ≠ assignee | `userIds: [assignee]` |
| Outbox → Core sino | Comentário do atendente | `userIds: [created_by_user_id]` |

Gates do criador (journey): início de atendimento (`service`/`in_progress`), `waiting_requester`, `succeeded`, `rejected`, `cancelled`. Create **não** notifica o criador. Políticas: `creator_portal_notification_policy.py`, `attendant_portal_notification_policy.py`. Payload Core: `message` + `action.portal_route` + `userIds` / `permissionCodes` (não `body`/`link`).

## Endpoint

```
wss://{host}/apps/requests-api/v1/realtime/ws?token={jwt}&client_id={uuid}
```

- **Auth:** JWT em query `token` → `validate_token` + RBAC via core-api (`load_user_rbac`). Exige `my-requests.access` (ou `view-all` / `manage`).
- **Salas no connect:** `user:{sub}` sempre; `work-queue` se `*.process` / `view-all` / `manage`.
- **Salas sob demanda:** `request:{uuid}` após `subscribe` (fail-closed: owner / process / view-all / manage + filial).
- **Keepalive:** cliente envia texto `ping`; servidor responde `{ "type": "pong" }`.
- **Middleware HTTP:** path `/v1/realtime/ws` é público no JWT middleware (token na query; auth no handler).
- **Flag:** `REQUESTS_REALTIME_ENABLED` (default `true`). `false` desliga hub notify e rejeita o handshake.

## Subscribe

```json
{ "type": "subscribe", "requestId": "<uuid>" }
```

```json
{ "type": "unsubscribe", "requestId": "<uuid>" }
```

Acks: `subscribed` | `unsubscribed` | `error` (`requestIdInvalid` | `accessDenied` | …).

## Eventos (P0)

| type | Rooms | Trigger | MFE |
|------|-------|---------|-----|
| `request.created` | `work-queue`; `user:{owner}` | create | refetch Mine/WorkQueue |
| `request.changed` | `request:{id}`; `user:{owner}`; `user:{assignee?}`; `work-queue` | transition, payload edit | refetch detail + listas |
| `request.timeline` | `request:{id}`; `user:{owner}`; `user:{assignee?}` | comment, attachment, artifact | refetch events/painéis |

Payload leve (exemplo):

```json
{
  "type": "request.changed",
  "reason": "transition.start",
  "requestId": "uuid",
  "requestNumber": "REQ-…",
  "status": "in_progress",
  "actorUserId": "…",
  "actorClientId": "…",
  "ownerUserId": "…",
  "notification": { "title": "…", "message": "…", "variant": "info" }
}
```

`notification` é opcional. O MFE ignora toast quando `actorClientId` = client id da aba (header `X-My-Requests-Client-Id`).

## Código

| Peça | Path |
|------|------|
| Hub | `requests_app/application/services/requests_realtime_hub.py` |
| Notify | `requests_app/application/services/requests_realtime_notify.py` |
| Protocol | `requests_app/application/services/requests_realtime_protocol.py` |
| Route | `requests_app/interface/http/routes/realtime_routes.py` |
| MFE | `plugins/my-requests/src/app/MyRequestsRealtimeProvider.tsx` |

## Gateway

`/apps/requests-api/` em `gateway/nginx.conf` e `nginx.dev.conf` com `Upgrade`, `Connection`, `proxy_read_timeout 86400`, `proxy_buffering off`.
