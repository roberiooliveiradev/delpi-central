# Firmware ESP32-C3 — contador v1 (Production Pulse)

Família nova, isolada do ESP8266. Contrato HTTP `/api/*` compatível com o contador V2; identidade baseada no MAC Wi-Fi Station.

| Item | Valor |
|------|--------|
| Pasta Arduino | abra **esta** pasta (`esp32c3_counter_v1`) |
| `FIRMWARE_VERSION` | `esp32c3_counter_v1.0.0` |
| Board | **ESP32C3 Dev Module** |
| Arduino core | Espressif **3.3.11** |
| CPU | 160 MHz |
| Flash | 4 MB, **QIO**, 80 MHz |
| Upload | 115200 |
| Partition scheme | **Minimal SPIFFS** (ou equivalente com dual OTA) |

## Particionamento OTA (obrigatório na 1ª gravação USB)

Use um esquema com:

- `ota_0` + `ota_1` + `otadata`
- **Não** use `No OTA` nem `Huge APP` sem dual OTA

No Arduino IDE / esp32 core 3.3.11: **Tools → Partition Scheme → Minimal SPIFFS (Large APPS with OTA)** (rótulo pode variar ligeiramente; o que importa é a tabela efetiva com dois slots app).

Aceite operacional: tamanho do `.bin` < menor slot `ota_*`, com margem.

## Placeholders (sem secrets reais)

No primeiro boot / EEPROM vazia:

- SSID: `YOUR_SSID`
- Password: `YOUR_PASSWORD`
- `apiToken` vazio até `POST /api/config`

Nunca grave senha, token de device ou artifact token neste README ou no sketch.

## Mapa de pinos (Super Mini V1601)

| Função | GPIO | Notas |
|--------|------|--------|
| INPUT_1 (pulso) | 0 | `INPUT_PULLUP`, active LOW; único que incrementa o contador |
| INPUT_2 (diagnóstico) | 1 | `INPUT_PULLUP`, active LOW; **não** altera o contador |
| LED R | 4 | Cátodo comum, **HIGH liga** (~220 Ω externo) |
| LED G | 5 | idem |
| LED B | 6 | idem |

Sinais industriais 12/24 V ficam no lado isolado do opto; o MCU só vê 3,3 V.

**Não usar** para sinais permanentes: GPIO2/8/9 (strapping), GPIO20/21 (UART/debug futuro).

## Factory reset

Esta família **não** possui gesto físico de factory reset em INPUT_1/INPUT_2 (sinais de máquina).

Reset de fábrica: `POST /api/factory-reset` autenticado com `X-Device-Token`.

## Rádio Wi-Fi (obrigatório antes do `begin`)

Após `WiFi.mode(WIFI_STA)` e antes de qualquer associação:

1. `WiFi.setSleep(false)`
2. `WiFi.setTxPower(WIFI_POWER_8_5dBm)` — limite da variante Super Mini V1601

Reconexão: máquina de estados (`idle` / `connecting` / `connected` / `backoff`); no máximo uma tentativa `WiFi.begin` em voo; backoff exponencial até 30 s. Mudança de SSID/senha via `/api/config` só solicita reconnect — **nunca** chama `WiFi.begin` no handler HTTP.

## Identidade

- Fonte única: `esp_read_mac(..., ESP_MAC_WIFI_STA)` após `WIFI_STA`
- `mac`: `XX:XX:XX:XX:XX:XX`
- `controllerCode` / `codigoControlador` / `equipamento`: `ESP32C3-` + hex uppercase sem separadores
- Serial no boot: `MAC WIFI STA - ENVIAR PARA TI: ...`

## Backend freshness (LED)

`BACKEND_FRESHNESS_MS` = 120000 (2 min). Contato autenticado recente marca “Minha DELPI OK” (verde). Visitas públicas sem token **não** renovam freshness.

## Endpoints preservados

`GET /`, `GET /api/contador`, `GET /api/status`, `GET|POST /api/config`, `POST /api/incrementar|decrementar|reset|definir|reboot|factory-reset`.

Status aditivo: `input1` / `input2` como `0|1` raw (`0` = LOW/ativo).

## EEPROM

`CONFIG_MAGIC = 0x50504331` (`PPC1`) — distinto do ESP8266 (`PPS\x02`). Config ESP8266 **não** é migrada automaticamente.
