# Firmware ESP8266 — contador V2 (vermelho)

Segundo binário da família `esp8266_counter_v1` para homologar OTA. Contrato `/api/*` idêntico ao V1.

| Item | Valor |
|------|--------|
| Pasta Arduino | `esp8266_counter_v2` (não misture `.ino` na pasta v1) |
| Arquivo | `esp8266_counter_v2.ino` |
| Família / driver | `esp8266_counter_v1` (igual ao V1) |
| `FIRMWARE_VERSION` | `esp8266_counter_v1.2.0.0` |
| Catálogo OTA | versão `2.0.0` |
| Tema | **Vermelho** (badge + accent na página `/`) |
| Par | [`../esp8266_counter_v1/`](../esp8266_counter_v1/) (verde · `1.0.0`) |

## Lab OTA

1. Compile/publique V1 (`1.0.0`) e V2 (`2.0.0`) na mesma família.
2. Flash USB com V1; vincule o IoT; dispare campanha para `2.0.0`.
3. Após reboot, `/` deve mostrar badge **V2 · Vermelho** e `firmwareVersion` `….2.0.0`.

Índice: [../README.md](../README.md).
