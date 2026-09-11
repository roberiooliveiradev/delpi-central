# Firmware ESP8266 — contador V1 (verde)

Fonte: `esp8266_counter_v1.ino` (abra **esta** pasta no Arduino IDE).

| Item | Valor |
|------|--------|
| Família / driver | `esp8266_counter_v1` |
| `FIRMWARE_VERSION` | `esp8266_counter_v1.1.0.0` |
| Catálogo OTA | versão `1.0.0` |
| Tema | **Verde** (badge + accent na página `/`) |
| Par OTA | [`../esp8266_counter_v2/`](../esp8266_counter_v2/) (vermelho · `2.0.0`) |

**Arduino IDE 1.x:** qualquer `</tag>` literal no `.ino` é corrompido — tags de fechamento HTML usam concatenação `"</" "tag>"`.

**Core ESP8266 (2.x / 3.x):**
- `collectHeaders`: core ≥3 variádico; core 2.x usa array + count (`#if ARDUINO_ESP8266_MAJOR`).
- OTA: `Update.begin` com `Content-Length` do artefato — **não** usar `UPDATE_SIZE_UNKNOWN`.
- Download em chunks com `progressPercent`; lab em [`../esp8266_counter_v2/README.md`](../esp8266_counter_v2/README.md).

## Endpoints

| Método | Rota | Auth | Notas |
|--------|------|------|--------|
| `GET` | `/` | não | Página somente leitura (tema verde) |
| `GET` | `/api/contador` | **não** | Contador + identidade |
| `GET` | `/api/status` | `X-Device-Token` se setado | `firmwareVersion`, health |
| `GET`/`POST` | `/api/config` | idem | Wi‑Fi, token, `otaBaseUrl`, `branch` |
| `POST` | `/api/incrementar` · `decrementar` · `reset` · `definir` · `reboot` · `factory-reset` | idem | |
| `POST` | `/api/ota/check-now` | idem | **202**; flash só no loop |

### OTA remota

1. `otaBaseUrl`: origem **HTTP** do gateway, ex. `http://192.168.1.237/apps/production-pulse-api`
2. `branch` + `apiToken` iguais ao cadastro
3. Publique o `.bin`, vincule o IoT, dispare campanha

Checklist: [HOMOLOGACAO-OTA-P4.md](../../HOMOLOGACAO-OTA-P4.md). Índice: [../README.md](../README.md).
