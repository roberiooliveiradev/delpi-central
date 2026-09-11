# Firmware ESP32-C3 — contador V1 (verde)

Família isolada do ESP8266. Contrato HTTP `/api/*` compatível; identidade pelo MAC Wi-Fi Station.

| Item | Valor |
|------|--------|
| Pasta Arduino | `esp32c3_counter_v1` |
| Arquivo | `esp32c3_counter_v1.ino` |
| Família / driver | `esp32c3_counter_v1` |
| `FIRMWARE_VERSION` | `esp32c3_counter_v1.1.0.0` |
| Catálogo OTA | versão `1.0.0` |
| Tema | **Verde** (UI + LED RGB `BACKEND_OK`) |
| Board | **ESP32C3 Dev Module** · core Espressif **3.3.11** |
| Partition | **Minimal SPIFFS** (dual OTA) |
| Par OTA | [`../esp32c3_counter_v2/`](../esp32c3_counter_v2/) (vermelho · `2.0.0`) |

## Particionamento OTA (1ª gravação USB)

Use `ota_0` + `ota_1` + `otadata`. Não use `No OTA` / `Huge APP` sem dual OTA.

## Placeholders

SSID `YOUR_SSID` / password `YOUR_PASSWORD`; `apiToken` vazio até `POST /api/config`. Sem secrets no README.

## Pinos (Super Mini V1601)

| Função | GPIO | Notas |
|--------|------|--------|
| INPUT_1 (pulso) | 0 | `INPUT_PULLUP`, active LOW |
| INPUT_2 (diagnóstico) | 1 | não altera contador |
| LED R / G / B | 4 / 5 / 6 | cátodo comum, HIGH liga |

## Identidade

`ESP32C3-` + MAC hex; Serial: `MAC WIFI STA - ENVIAR PARA TI: …`

## Backend freshness

`BACKEND_FRESHNESS_MS` = 120000. Contato autenticado recente → LED de marca (verde no V1).

Índice: [../README.md](../README.md). Detalhe histórico: pastas `esp32c3-super-mini/` no roadmap.
