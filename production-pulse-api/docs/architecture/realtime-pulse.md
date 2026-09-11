# Production Pulse API — realtime (WebSocket)

Atualização live do Admin Hub (canvas, KPIs, jobs OTA) via WebSocket nativo
FastAPI — mesmo padrão de [requests](../../../requests-api/docs/architecture/realtime-requests.md)
e commercial worklist.

O WS envia **hints leves**. A fonte de verdade continua sendo REST: o MFE faz
debounce + soft refetch (`devices` / `firmwares` / `summary` / `jobs` / targets).

## Endpoint

```
wss://{host}/apps/production-pulse-api/v1/realtime/ws?token={jwt}&client_id={uuid}
```

- **Auth:** JWT em query `token` → `validate_token` + RBAC via core-api. Exige
  `production-pulse.access` / `devices.view` / admin equivalente.
- **Salas no connect:** `user:{sub}` sempre; `branch:{01|02}` conforme escopo de filial
  quando o usuário pode ver devices.
- **Salas sob demanda (opcional):** `device:{uuid}` / `ota.job:{uuid}` via subscribe
  (fail-closed por filial + `devices.view`).
- **Keepalive:** cliente envia texto `ping`; servidor responde `{ "type": "pong" }`.
- **Middleware HTTP:** path `/v1/realtime/ws` é público no JWT middleware (token na
  query; auth no handler).
- **Flag:** `PP_REALTIME_ENABLED` (default `true`). `false` desliga notify e rejeita
  o handshake.

## Eventos (P0)

| type | Rooms | Trigger | MFE |
|------|-------|---------|-----|
| `device.updated` | `branch:{b}`; `device:{id}` | CRUD/link/binding/enable/poll (throttle) | softReloadGraph |
| `firmware.catalog.updated` | `branch:01`+`02` | create/publish/archive/delete/family | softReloadGraph |
| `ota.job.updated` | `branch`; `ota.job:{id}` | create/cancel/finish | reloadJobs |
| `ota.target.updated` | `branch`; job; device | status/progress (throttle 1s / 5pp) | refresh targets + soft graph |

Payload leve (exemplo):

```json
{
  "type": "ota.target.updated",
  "reason": "updated",
  "targetId": "uuid",
  "jobId": "uuid",
  "deviceId": "uuid",
  "branch": "01",
  "status": "updated",
  "progressPercent": 100
}
```

## Persist-before-publish

Writers persistem no Postgres e só então chamam `safe_realtime(notify_*)`. Falha de
fan-out **não** reverte o write.

## Gateway

`location /apps/production-pulse-api/` (dev+prod) deve enviar:

- `proxy_http_version 1.1`
- `Upgrade` / `Connection $connection_upgrade`
- `proxy_buffering off`
- `proxy_read_timeout` longo

## MFE

- `ProductionPulseRealtimeProvider` no `App`
- Hub: `useProductionPulseHubSync` → soft reload com guarda de interação
  (linkMode / drag / overlays / aba oculta)
- Fallback poll 30s só com WS desconectado
- Monitor OTA: poll 3s só com WS down e job ativo

## Fora de escopo

- Telemetria contínua (`device.reading.updated` high-rate)
- Outbox / sino Portal
- SSE / Socket.IO Core
