# Firmware ESP32-WROOM — contador v1 (Production Pulse)

Família oficial WROOM, isolada de ESP8266 e ESP32-C3. Mesmo contrato HTTP `/api/*` + OTA híbrido (wake + pull).

| Item | Valor |
|------|--------|
| Pasta Arduino | `esp32_counter_v1` |
| Arquivo | `esp32_counter_v1.ino` |
| `FIRMWARE_VERSION` | `esp32_counter_v1.0.0` |
| `driverKey` / `firmwareKey` | `esp32_counter_v1` |
| Board | **ESP32 Dev Module** (WROOM-32) |
| FQBN | `esp32:esp32:esp32` |
| Arduino core | Espressif 2.x / 3.x |
| Flash | 4 MB, **QIO**, dual OTA |
| Partition | Minimal SPIFFS / Default with dual OTA (`ota_0` + `ota_1`) |
| Pull OTA | ~60 s + jitter 0–15 s; backoff em erro de check |
| Wake | `POST /api/ota/check-now` → **202** (flag; flash só no loop) |

## Bootstrap USB (1ª gravação)

1. Abra a pasta `esp32_counter_v1` no Arduino IDE / `arduino-cli`.
2. Board: **ESP32 Dev Module** (`esp32:esp32:esp32`).
3. Partition Scheme com `ota_0` + `ota_1` (não use “No OTA”).
4. Grave via USB; no Serial: `MAC WIFI STA - ENVIAR PARA TI` e `controllerCode` (`ESP32-` + MAC hex).
5. Configure `ssid` / `password` / `apiToken` / `otaBaseUrl` / `branch` via `POST /api/config` (token vazio = bootstrap aberto).
6. A API deve empurrar `otaBaseUrl` + `branch` no configure (`PP_DEVICE_OTA_BASE_URL`).

Placeholders de fábrica: `YOUR_SSID` / `YOUR_PASSWORD` — sem secrets reais no sketch.

## Pinos (defaults do sketch)

| Função | GPIO | Notas |
|--------|------|--------|
| INPUT_1 (pulso) | 18 | `INPUT_PULLUP`, active LOW; incrementa contador |
| INPUT_2 (diagnóstico) | 19 | active LOW; **não** altera contador |
| LED R / G / B | 25 / 26 / 27 | cátodo comum externo (~220 Ω); HIGH liga |

Ajuste no `.ino` se o hardware divergir. Evite GPIO0/2/15 (strapping) para sinais permanentes.

## Endpoints

Contrato alinhado aos contadores irmãos: `GET /api/contador` público; demais `/api/*` com `X-Device-Token` quando token setado; `POST /api/ota/check-now` autenticado → 202.

## EEPROM

`CONFIG_MAGIC = 0x50505731` (`PPW1`) — distinto de ESP8266 (`PPS\x02`) e C3 (`PPC1`).

## COMPILACAO_FISICA_PENDENTE

Compile com `arduino-cli` quando o core ESP32 estiver instalado. Smoke OTA físico A–K permanece **PENDENTE** até lab com WROOM.
