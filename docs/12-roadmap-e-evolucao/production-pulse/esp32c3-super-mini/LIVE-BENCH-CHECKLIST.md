# Bancada live — ESP32-C3 Super Mini (checklist)

> Pré-requisito: E1 PASS ([evidence/e1-compile-partitions-2026-09-10.md](./evidence/e1-compile-partitions-2026-09-10.md)).
> Sem secrets na evidência. Classificar cada item `PASS` / `FAIL` / `INCONCLUSIVE`.

## Ambiente WSL2

1. No Windows (admin): `usbipd list` → anotar BUSID do CP210x/CH340/ESP.
2. `usbipd bind --busid <BUSID>` (uma vez) e `usbipd attach --wsl --busid <BUSID>`.
3. No WSL: `./scripts/c3_flash.sh list` deve listar a porta (`/dev/ttyACM*` ou `/dev/ttyUSB*`).

## Flash

```bash
chmod +x docs/12-roadmap-e-evolucao/production-pulse/esp32c3-super-mini/scripts/c3_flash.sh
./docs/12-roadmap-e-evolucao/production-pulse/esp32c3-super-mini/scripts/c3_flash.sh upload /dev/ttyACM0
./docs/12-roadmap-e-evolucao/production-pulse/esp32c3-super-mini/scripts/c3_flash.sh monitor /dev/ttyACM0
```

FQBN fixo: `PartitionScheme=min_spiffs` (dual OTA).

## Checklist E2–E7 (preencher na sessão live)

| ID | Asserção | Resultado | Nota |
|----|----------|-----------|------|
| E2.S1 | Serial: `MAC WIFI STA - ENVIAR PARA TI: …` | | |
| E2.S1 | `controllerCode` = `ESP32C3-` + MAC sem `:` | | |
| E2.S1 | `/api/status` + HTML = mesmo MAC | | |
| E2.S2 | Serial/HTML: token só `configurado\|não`; sem password | | |
| E3.S1 | Sleep off + 8.5 dBm no boot; associa 2.4 GHz | | |
| E3.S2 | Disconnect reason code; sem begin concorrente | | |
| E3.S3 | `POST /api/config` Wi-Fi reconecta via SM | | |
| E4.S1 | INPUT_1 HIGH→LOW incrementa 1× | | |
| E4.S2 | INPUT_2 LOW não altera contador | | |
| E4.S3 | INPUT_1+2 LOW 10s **não** factory-reset | | |
| E5.S1 | Endpoints `/api/*` + token | | |
| E5.S2 | Freshness/RGB coerentes | | |
| E6.S1 | BFF poll/probe C3 | | |
| E7.* | Publish/link/job OTA família C3 | | |

## Evidência mínima a anexar

- data/hora, core 3.3.11, `FIRMWARE_VERSION`
- tamanho `.bin` + partition scheme
- STA MAC (ok publicar — não é secret)
- SSID testado **sem** password
- trecho Serial redigido
- PASS/FAIL por linha da tabela

Quando a placa estiver anexada ao WSL, pedir ao agente: «placa em /dev/ttyACM0 — continue E2».
