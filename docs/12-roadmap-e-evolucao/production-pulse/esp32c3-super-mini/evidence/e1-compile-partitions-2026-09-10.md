# Evidência — VALIDATION E1.S1 / E1.S2 (compile + partitions)

> Sessão: 2026-09-10 · ambiente: WSL2 Linux x86_64 · **sem hardware USB** nesta etapa.

## Resultado

| Item | Status |
|------|--------|
| E1.S1 Compile perfil documentado | **PASS** |
| E1.S2 Partition `otadata` + `ota_0` + `ota_1` | **PASS** (CSV efetiva do Core 3.3.11) |
| Live USB / Serial / Wi-Fi | **PENDENTE** (sem placa nesta sessão) |

## Toolchain

| Campo | Valor |
|-------|--------|
| arduino-cli | 1.5.1 |
| Core | `esp32:esp32@3.3.11` |
| FQBN | `esp32:esp32:esp32c3:UploadSpeed=115200,CPUFreq=160,FlashFreq=80,FlashMode=qio,FlashSize=4M,PartitionScheme=min_spiffs` |

Comando reproduzível:

```bash
export PATH="$HOME/bin:$PATH"
arduino-cli compile \
  --fqbn 'esp32:esp32:esp32c3:UploadSpeed=115200,CPUFreq=160,FlashFreq=80,FlashMode=qio,FlashSize=4M,PartitionScheme=min_spiffs' \
  --output-dir /tmp/esp32c3_counter_v1_build \
  docs/12-roadmap-e-evolucao/production-pulse/firmware/esp32c3_counter_v1
```

## Artefato

| Campo | Valor |
|-------|--------|
| Sketch size (report) | 1 108 601 bytes (56% de 1 966 080) |
| `.bin` | 1 108 752 bytes |
| Slot `ota_*` | 0x1E0000 = 1 966 080 bytes |
| Cabe no slot? | **sim** (margem 857 328 bytes ≈ 43,6%) |
| Globals | 40 696 bytes (12% de 327 680) |

## Partition table efetiva (`min_spiffs.csv` Core 3.3.11)

Fonte: `~/.arduino15/packages/esp32/hardware/esp32/3.3.11/tools/partitions/min_spiffs.csv`

```text
nvs,      data, nvs,     0x9000,  0x5000,
otadata,  data, ota,     0xe000,  0x2000,
app0,     app,  ota_0,   0x10000, 0x1E0000,
app1,     app,  ota_1,   0x1F0000,0x1E0000,
spiffs,   data, spiffs,  0x3D0000,0x20000,
coredump, data, coredump,0x3F0000,0x10000,
```

Confirmado: **`otadata`**, **`ota_0`** (`app0`), **`ota_1`** (`app1`).

## Correções feitas durante a prova

1. `HTTPClient.setTimeout(120000)` → `60000` — API ESP32 usa `uint16_t` (overflow silencioso para 54464).
2. Removido `blink` não usado em `updateRgbState()` (warning `-Wunused-but-set-variable`).

## Não alegado

- Flash USB, boot Serial, MAC STA live, Wi-Fi, OTA E2E — exigem Super Mini V1601 na bancada (VALIDATION E2+).
