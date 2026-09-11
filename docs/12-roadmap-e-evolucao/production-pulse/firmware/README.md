# Firmwares IoT — Production Pulse

Sketches de referência para flash USB / publicação OTA. Cada **família** (`firmwareKey` / `driverKey`) tem **duas versões** para lab OTA:

| Tema | Papel | Cor (UI + LED*) |
|------|--------|------------------|
| **V1** | Baseline / primeira publicação | **Verde** (`#22c55e`) |
| **V2** | Alvo OTA / segunda publicação | **Vermelho** (`#ef4444`) |

\* ESP32 / ESP32-C3: LED RGB no estado `BACKEND_OK`. ESP8266: cor na página `/` (só `LED_BUILTIN` para status Wi‑Fi).

## Famílias

| Família (`firmwareKey`) | V1 Verde | V2 Vermelho | `FIRMWARE_VERSION` |
|-------------------------|----------|-------------|--------------------|
| `esp8266_counter_v1` | [`esp8266_counter_v1/`](./esp8266_counter_v1/) | [`esp8266_counter_v2/`](./esp8266_counter_v2/) | `….1.0.0` / `….2.0.0` |
| `esp32_counter_v1` | [`esp32_counter_v1/`](./esp32_counter_v1/) | [`esp32_counter_v2/`](./esp32_counter_v2/) | `….1.0.0` / `….2.0.0` |
| `esp32c3_counter_v1` | [`esp32c3_counter_v1/`](./esp32c3_counter_v1/) | [`esp32c3_counter_v2/`](./esp32c3_counter_v2/) | `….1.0.0` / `….2.0.0` |

## Nomenclatura canônica

```text
pasta Arduino     = nome do .ino (obrigatório no IDE)
arquivo           = {familia_pasta}.ino
FIRMWARE_VERSION  = {firmwareKey}.{major}.{minor}.{patch}
catálogo OTA      = firmwareKey estável + version = major.minor.patch
```

Exemplos:

- Sketch V1: `esp8266_counter_v1.1.0.0` → publicar como família `esp8266_counter_v1`, versão `1.0.0`
- Sketch V2: `esp8266_counter_v1.2.0.0` → mesma família, versão `2.0.0`

A pasta `*_v2` é só o **segundo binário** da mesma família (não muda `driverKey`).

## Lab OTA (resumo)

1. Flash USB com V1 (verde).
2. Publique V1 e V2 no Admin (mesma família).
3. Vincule o IoT → dispare campanha para `2.0.0`.
4. Após reboot, `/api/status` deve reportar `….2.0.0` e a UI `/` fica vermelha.

`otaBaseUrl` no chip = URL HTTP da API alcançável na VLAN (`PP_DEVICE_OTA_BASE_URL`), não o IP do IoT.
