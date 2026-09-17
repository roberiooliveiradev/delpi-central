# Firmware ESP32-WROOM — contador V2 (vermelho)

Segundo binário da família `esp32_counter_v1` para lab OTA.

| Item | Valor |
|------|--------|
| Pasta / arquivo | `esp32_counter_v2` / `esp32_counter_v2.ino` |
| Família / driver | `esp32_counter_v1` |
| `FIRMWARE_VERSION` | `esp32_counter_v1.2.0.0` |
| Catálogo OTA | versão `2.0.0` |
| Tema UI `/` | **Vermelho** (`VERSION_THEME_IS_RED = true`) — não muda LED operacional |
| Par | [`../esp32_counter_v1/`](../esp32_counter_v1/) (UI verde · `1.0.0`) |

Contrato HTTP e pinos iguais ao V1. LED RGB: mesma tabela operacional do V1 ([../README.md](../README.md#sinais-do-led-rgb-esp32--esp32-c3)). Healthy Pulse = **verde sólido** também no V2.

