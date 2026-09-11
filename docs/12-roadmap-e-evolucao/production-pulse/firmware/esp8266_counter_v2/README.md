# Firmware ESP8266 — contador v2 (lab de troca OTA)

Sketch irmão de [`../esp8266_counter_v1/Teste.ino`](../esp8266_counter_v1/Teste.ino) para homologar OTA com progresso.

| Item | Valor |
|------|--------|
| Pasta Arduino | abra **esta** pasta (`esp8266_counter_v2`) — não misture `.ino` na pasta v1 |
| `FIRMWARE_VERSION` | `esp8266_counter_v2.0.1` |
| Contrato `/api/*` | Idêntico ao v1 (driver `esp8266_counter_v1`) + `POST /api/ota/check-now` (202) |
| Pull OTA | ~60 s + jitter 0–15 s; backoff em erro; wake via check-now |
| UI `/` | Badge **V2**, accent verde, exibe versão |

## Lab swap v1 ↔ v2

1. Compile/publique o `.bin` do v1 (`esp8266_counter_v1.3.1`) e do v2 (`esp8266_counter_v2.0.1`) no catálogo OTA (mesma `firmwareKey` / `driverKey`).
2. Amarre o IoT em `/firmware-links`.
3. Dispare campanha para a versão alvo.
4. No detalhe do device (aba Firmware): acompanhe **% real** + fases PT.
5. Após reboot, **Em execução** deve mostrar a nova `FIRMWARE_VERSION` (live `/api/status`).

## Progresso byte a byte

Durante o download o sketch envia `POST /device-ota/report` com `bytesReceived`, `bytesTotal`, `progressPercent` (throttle ~5% / 32 KiB / máx. 1×/2 s). Falha do report intermediário **não** aborta o flash.

Reports terminais (`updated` antes do restart e `failed` ao abandonar o apply) usam `reportTerminalWithRetry` (até 3 tentativas, backoff 200/400/800 ms). Falha do ACK **não** impede o restart.
