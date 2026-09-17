# Firmwares IoT — Production Pulse

Sketches de referência para flash USB / publicação OTA. Cada **família** (`firmwareKey` / `driverKey`) tem **duas versões** para lab OTA.

| Tema (UI `/` apenas) | Papel | Cor da página |
|------|--------|----------------|
| **V1** | Baseline / primeira publicação | **Verde** (`#22c55e`) |
| **V2** | Alvo OTA / segunda publicação | **Vermelho** (`#ef4444`) |

O tema V1/V2 **não** altera as cores operacionais do LED RGB. Espelho HTML (`VERSION_THEME_IS_RED`) é só identidade visual da página.

## Sinais do LED RGB (ESP32 / ESP32-C3)

Hardware: LED **cátodo comum**, HIGH liga o canal (resistores ~220 Ω). Owner único: `resolveRgbVisualState` + `updateRgbState`.

| Estado | Significado | Cor | Padrão | Timing |
|--------|-------------|-----|--------|--------|
| Boot / Wi‑Fi offline | Sem associação Wi‑Fi | **Vermelho** | Sólido | — |
| Connecting / backoff | Tentando conectar ou reconectar | **Vermelho** | Pisca | ~500 ms |
| Wi‑Fi OK, sem Pulse auth | Wi‑Fi ok; ainda **não** houve contato autenticado com a API | **Azul** | Sólido | — |
| Pulse healthy | Contato autenticado recente (`X-Device-Token` válido ou OTA HTTP autenticado) | **Verde** | Sólido | freshness &lt; 120 s |
| Pulse stale | Wi‑Fi ok; freshness expirou | **Azul** | Pisca | ~500 ms |
| OTA em andamento | Check / download / apply | **Amarelo** (R+G) | Pisca | ~350 ms |
| Falha auth ou OTA apply | 401 de token **ou** falha ao aplicar binário OTA | **Vermelho** | Pisca rápido | ~100 ms por ~5 s |

Prioridade: falha auth/OTA → OTA em andamento → connecting/offline → freshness.

### O que **não** deixa o LED verde

- Só conectar no Wi‑Fi (fica **azul sólido**).
- Poll/visita a `GET /api/contador` **sem** `X-Device-Token` válido (rota pública de métrica).
- Token no chip divergente do `device_api_token` no Postgres (Pulse pode marcar Online via contador público; freshness não atualiza).

### ESP8266

Sem RGB: apenas `LED_BUILTIN` (connecting / online / auth). Cores V1/V2 só na página `/`.

## Famílias

| Família (`firmwareKey`) | V1 Verde (UI) | V2 Vermelho (UI) | `FIRMWARE_VERSION` |
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

1. Flash USB com V1 (UI verde; LED operacional conforme tabela acima).
2. Publique V1 e V2 no Admin (mesma família).
3. Vincule o IoT → dispare campanha para `2.0.0`.
4. Após reboot, `/api/status` deve reportar `….2.0.0` e a UI `/` fica vermelha; o LED healthy continua **verde** se a Pulse autenticar.

`otaBaseUrl` no chip = URL HTTP da API alcançável na VLAN (`PP_DEVICE_OTA_BASE_URL`), não o IP do IoT.
