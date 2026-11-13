# Realtime no plugin-ui

Transporte neutro. Não conhece LNF, Engineering nem token.

`RealtimeSocketClient` continua com reconnect fixo de 4s e reenvio das
salas desejadas quando as opções novas não são passadas.

Opções aditivas: `reconnect` (`fixed` | `exponential`), `resolveUrl`,
`shouldReconnect`, `resubscribeOnReconnect` (default true, que já era o
comportamento), `onResync`, `getStatus` / `onStatusChange`.

`useRealtimeRooms` assina salas, deduplica por `eventId` e agrega a rajada.
`enabled: false` não abre socket.

`RealtimeStatusIndicator` e `ConcurrentChangeNotice` são o selo e o aviso.
Não recebem foco sozinhos.

Follow-up: MFEs que abrem `new WebSocket` por conta (requests, commercial e
outros) ainda não usam este cliente.
