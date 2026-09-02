# Firmware ESP8266 — contador v1

Fonte de referência: `Teste.ino` (flash no Arduino IDE / PlatformIO).

## Endpoints

| Método | Rota | Notas |
|--------|------|--------|
| `GET` | `/` | Página somente leitura: **código do controlador** + contagem (sem botões web) |
| `GET` | `/api/contador` | `{"contador": N}` |
| `GET` | `/api/status` | Inclui `codigoControlador` / `controllerCode`, IP, MAC |
| `POST` | `/api/incrementar` | +1 |
| `POST` | `/api/decrementar` | −1 |
| `POST` | `/api/reset` | zera |
| `POST` | `/api/definir` | body `{"contador": N}` — restore pela API Delpi |

O código do controlador é `ESP-` + `ESP.getChipId()` em hex — estável após reboot.

No Production Pulse: campo **Código do controlador** no cadastro; «Testar conexão» preenche a partir de `/api/status`.

**Wi-Fi:** use placeholders `YOUR_SSID` / `YOUR_PASSWORD` neste arquivo do repo; o `.ino` operacional fica na máquina do flash (Downloads).
