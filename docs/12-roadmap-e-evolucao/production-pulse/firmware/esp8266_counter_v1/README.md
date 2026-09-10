# Firmware ESP8266 — contador v1

Fonte de referência: `Teste.ino` (flash no Arduino IDE / PlatformIO).

**Arduino IDE 1.x:** qualquer `</tag>` literal no `.ino` é corrompido pelo IDE — no sketch as tags de fechamento HTML usam concatenação `"</" "tag>"`.

**Core ESP8266 (2.x / 3.x):**
- `collectHeaders`: core ≥3 variádico; core 2.x usa array + count (`#if ARDUINO_ESP8266_MAJOR`).
- OTA: `Update.begin` com `Content-Length` do artefato — **não** usar `UPDATE_SIZE_UNKNOWN` (símbolo do ESP32; quebra no ESP8266).
- Download em chunks com report de `progressPercent` (throttle); ver lab em [`../esp8266_counter_v2/README.md`](../esp8266_counter_v2/README.md).
- Redirects HTTP: `HTTPC_STRICT_FOLLOW_REDIRECTS` quando o core exporta o enum.

`FIRMWARE_VERSION` atual: `esp8266_counter_v1.3.0`.

## Endpoints

| Método | Rota | Auth | Notas |
|--------|------|------|--------|
| `GET` | `/` | não | Página somente leitura: código do controlador + contagem |
| `GET` | `/api/contador` | **não** (única API pública) | `{"contador": N}` |
| `GET` | `/api/status` | `X-Device-Token` se `apiToken` setado | Identidade + contador + health: `firmwareVersion`, `uptimeMs`, `freeHeap`, `rssi`, `wifiConnected` |
| `GET` | `/api/config` | idem | `ssid`, `debounceMs`, `passwordSet`, `apiTokenSet`, `otaBaseUrl`, `branch`, `wifiConfigured` — **sem** secrets Wi‑Fi/token |
| `POST` | `/api/config` | idem (aberto se token vazio) | body parcial EN: `ssid`, `password`, `debounceMs`, `apiToken`, `otaBaseUrl`, `branch` |
| `POST` | `/api/incrementar` | idem | +1 |
| `POST` | `/api/decrementar` | idem | −1 |
| `POST` | `/api/reset` | idem | zera |
| `POST` | `/api/definir` | idem | body `{"contador": N}` — restore pela API Delpi |
| `POST` | `/api/reboot` | idem | responde JSON e reinicia o chip |
| `POST` | `/api/factory-reset` | idem | restaura EEPROM (defaults); reinicia — contador em RAM zera |

### Autenticação

- Header: `X-Device-Token: <token>`
- Token vazio no EEPROM = bootstrap
- Token setado = só `GET /api/contador` público; demais `/api/*` exigem header igual ou `401`

### Config persistida (EEPROM)

`ssid`, `password`, `apiToken`, `debounceMs`, `otaBaseUrl`, `branch`. Magic `0x50505302`.

### OTA remota (P4 — implementado)

Pull autorizado contra a Production Pulse API ([FIRMWARE-OTA-P4.md](../../FIRMWARE-OTA-P4.md)):

1. Configure via `POST /api/config` (sem URL de produção no binário):
   - `otaBaseUrl`: origem **HTTP** do gateway, ex. `http://192.168.x.x/apps/production-pulse-api` (sem trailing slash)
   - `branch`: `01` / `02`
   - `apiToken`: igual ao `device_api_token` no cadastro
2. No admin: publique o `.bin`, amarre o IoT em `/firmware-links` (1 IoT = 1 firmware), crie campanha OTA.
3. O chip (~1 min após boot, depois a cada ~10 min) chama:
   - `GET {otaBaseUrl}/device-ota/check?controllerCode=…&branch=…` com `X-Device-Token`
   - Parse do envelope `{ "success", "data": { "updateAvailable", "artifactToken", … } }`
   - Download `GET …/device-ota/artifacts/{token}` e `Updater`
   - `POST …/device-ota/report` (`downloading` → `applying` → `updated|failed`) **antes** do stream de download (evita segundo HTTP concorrente)
   - Reports terminais (`updated` antes do `ESP.restart()`, e `failed` antes de abandonar o apply) usam `reportTerminalWithRetry` (até 3 tentativas, backoff 200/400/800 ms + `ESP.wdtFeed`); falha do ACK **não** impede o restart — o backend reconcilia
4. MVP do sketch: **HTTP na VLAN** (sem BearSSL/HTTPS).

Checklist lab: [HOMOLOGACAO-OTA-P4.md](../../HOMOLOGACAO-OTA-P4.md).
