# Firmware ESP32-WROOM — contador v1 (Production Pulse)

Família oficial WROOM, isolada de ESP8266 e ESP32-C3. Mesmo contrato HTTP `/api/*` + OTA híbrido (wake + pull).

| Item | Valor |
|------|--------|
| Pasta Arduino | `esp32_counter_v1` |
| `FIRMWARE_VERSION` | `esp32_counter_v1.0.0` |
| `driverKey` | `esp32_counter_v1` |
| Board | **ESP32 Dev Module** (WROOM-32) |
| Arduino core | Espressif 2.x / 3.x |
| Flash | 4 MB, dual OTA |
| Pull OTA | ~60 s + jitter 0–15 s |
| Wake | `POST /api/ota/check-now` → 202 (flash no loop) |

## Bootstrap USB

1. Selecione board **ESP32 Dev Module**.
2. Partition Scheme com `ota_0` + `ota_1` (não use “No OTA”).
3. Grave o sketch; configure Wi-Fi/`apiToken`/`otaBaseUrl`/`branch` via `POST /api/config` (ou portal local).
4. A API Production Pulse deve enviar `otaBaseUrl` + `branch` no configure push (`PP_DEVICE_OTA_BASE_URL`).

## Pinos (defaults do sketch)

| Função | GPIO |
|--------|------|
| Input 1 | 18 |
| Input 2 | 19 |
| LED R/G/B | 25 / 26 / 27 |

Ajuste no `.ino` se o hardware diverge.

## COMPILACAO_FISICA_PENDENTE

Validação em hardware físico e smoke OTA A–K ficam **PENDENTE** até lab com ESP32-WROOM disponível.
