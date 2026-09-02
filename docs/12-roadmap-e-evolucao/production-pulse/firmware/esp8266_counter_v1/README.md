# Firmware ESP8266 — contador v1

Fonte de referência: `Teste.ino` (flash no Arduino IDE / PlatformIO).

## Endpoints

| Método | Rota | Auth | Notas |
|--------|------|------|--------|
| `GET` | `/` | não | Página somente leitura: código do controlador + contagem |
| `GET` | `/api/contador` | **não** (única API pública) | `{"contador": N}` |
| `GET` | `/api/status` | `X-Device-Token` se `apiToken` setado | Identidade + contador + health: `firmwareVersion`, `uptimeMs`, `freeHeap`, `rssi`, `wifiConnected` |
| `GET` | `/api/config` | idem | `ssid`, `debounceMs`, `passwordSet`, `apiTokenSet`, `wifiConfigured` — **sem** secrets |
| `POST` | `/api/config` | idem (aberto se token vazio) | body parcial EN: `ssid`, `password`, `debounceMs`, `apiToken` |
| `POST` | `/api/incrementar` | idem | +1 |
| `POST` | `/api/decrementar` | idem | −1 |
| `POST` | `/api/reset` | idem | zera |
| `POST` | `/api/definir` | idem | body `{"contador": N}` — restore pela API Delpi |
| `POST` | `/api/reboot` | idem | responde JSON e reinicia o chip |
| `POST` | `/api/factory-reset` | idem | restaura EEPROM (defaults); reinicia — contador em RAM zera |

### Autenticação

- Header: `X-Device-Token: <token>`
- Token vazio no EEPROM = bootstrap (rotas `/api/*` abertas, exceto a política futura)
- Token setado = só `GET /api/contador` público; demais `/api/*` exigem header igual ou `401`

### Config persistida (EEPROM)

`ssid`, `password`, `apiToken`, `debounceMs`. Defaults de fábrica: `YOUR_SSID` / `YOUR_PASSWORD`, debounce 100 ms, token vazio.

O código do controlador é `ESP-` + `ESP.getChipId()` em hex — estável após reboot.

Wi‑Fi: tentativa limitada no boot; no `loop`, reconnect com backoff via `millis()` (sem `delay` longo) + `ESP.wdtFeed()`.

mDNS: hostname = `controllerCode` em minúsculas (ex.: `esp-00a1b2c3.local`).

Factory reset: `POST /api/factory-reset` (auth) ou hold **D5+D1** por 10 s. Não apaga readings no Postgres; no chip, restart zera o contador em RAM.

No Production Pulse: cadastro com Wi‑Fi/debounce/token; «Testar conexão» e Salvar (modo A) usam `/api/config` e `/api/status`.
