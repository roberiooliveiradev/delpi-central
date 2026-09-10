# Registry de drivers — banco + protocolo em código

> **Fonte de verdade runtime:** tabela `production_pulse.device_drivers` (V014).  
> **Seed histórico:** [`device_drivers.json`](../../../production-pulse-api/production_pulse_app/content/device_drivers.json) (bootstrap/migration).  
> **Implementação HTTP:** `protocol_kind` → factory Python (`http_counter` | `http_gauge`).

## Conceitos (não confundir)

| Conceito | Campo | O que é |
|----------|-------|---------|
| **Tipo de driver** | `driver_key` | Perfil + protocolo do IoT (poll, comandos, superfície operador) |
| **Família OTA** | `firmware_key` | Catálogo de versões (`.ino` / `.bin`) publicáveis |
| **Protocolo** | `protocol_kind` | Classe de código; só muda com deploy se for protocolo **novo** |

Novo tipo com o mesmo protocolo (ex. outro contador HTTP) = **CRUD no Admin Hub**, sem redeploy da API.

## CRUD Admin

Painel Hub `panel=drivers` + modais `driver-create` / `driver-detail`.  
API: `GET/POST /drivers`, `GET/PATCH /drivers/{driverKey}`, `POST …/archive|unarchive`.  
RBAC: `production-pulse.devices.view` / `.manage`.

## Schema da tabela

Ver [SCHEMA.md](./SCHEMA.md) — `device_drivers`.

Campos principais espelham o catálogo antigo (camelCase na API):

- `protocolKind`, `roleKey`, `labelPt`, `descriptionPt`
- `metrics[]`, `commands[]`, `operatorSurface`, `operatorEligible`
- `poll.timeoutMs`, `thresholds`, `counterRestore` (opcional)
- soft-archive: `archivedAt`

## Protocol kinds

| kind | Implementação | Uso típico |
|------|---------------|------------|
| `http_counter` | `HttpCounterDriver` | Contador ESP8266 / ESP32-C3 |
| `http_gauge` | `HttpGaugeDriver` | rpm / temperatura |

`GET /catalog/drivers` e `GET /firmware-drivers` listam **apenas ativos** (não arquivados).

## Seed MVP

- `esp8266_counter_v1` → `http_counter`
- `esp32c3_counter_v1` → `http_counter`
- `esp8266_gauge_v1` → `http_gauge`

## Extensão

1. **Mesmo protocolo:** Admin → Novo tipo de driver → escolher `protocolKind`.
2. **Protocolo novo:** adicionar valor no CHECK SQL + factory em `DeviceDriverRegistryService` + classe em `infrastructure/drivers/` (deploy).
