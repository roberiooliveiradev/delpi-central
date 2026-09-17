# Firmware ESP32-WROOM — contador V1 (verde)

| Item | Valor |
|------|--------|
| Pasta / arquivo | `esp32_counter_v1` / `esp32_counter_v1.ino` |
| Família / driver | `esp32_counter_v1` |
| `FIRMWARE_VERSION` | `esp32_counter_v1.1.0.0` |
| Catálogo OTA | versão `1.0.0` |
| Tema UI `/` | **Verde** (`VERSION_THEME_IS_RED = false`) — não muda LED operacional |
| Board / FQBN | ESP32 Dev Module · `esp32:esp32:esp32` |
| Par OTA | [`../esp32_counter_v2/`](../esp32_counter_v2/) (UI vermelha · `2.0.0`) |

## Flash

1. Abra a pasta `esp32_counter_v1` no Arduino IDE.
2. Partition scheme com dual OTA (ex.: Minimal SPIFFS / Large APP with OTA).
3. Publique o `.bin` no Admin Pulse.

## Pinos

| Função | GPIO |
|--------|------|
| INPUT_1 / INPUT_2 | 18 / 19 |
| LED R / G / B | 25 / 26 / 27 (cátodo comum, HIGH liga) |

## LED RGB

Sinais operacionais **iguais em V1 e V2** (vermelho/azul/verde/amarelo). Tabela canônica: [../README.md](../README.md#sinais-do-led-rgb-esp32--esp32-c3).

Índice: [../README.md](../README.md).
