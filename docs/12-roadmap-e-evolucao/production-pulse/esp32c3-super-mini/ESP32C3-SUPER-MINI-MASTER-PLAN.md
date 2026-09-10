# Plano mestre — ESP32-C3 Super Mini no Production Pulse

> **Status:** plano de implementação; não é contrato canônico e deve ser revalidado antes da execução.
>
> **Prompt associado:** [`ESP32C3-SUPER-MINI-IMPLEMENTATION-PROMPT.md`](./ESP32C3-SUPER-MINI-IMPLEMENTATION-PROMPT.md)
>
> **Planos especializados:** firmware, API/OTA e validação em documentos irmãos.

## Overview

Portar o contador atual para `esp32c3_counter_v1`, preservando o protocolo HTTP e OTA existentes do Minha DELPI, isolando a nova família de hardware e adicionando Wi-Fi C3, entradas opto-isoladas, RGB e diagnóstico operacional sem criar fontes paralelas.

## Leitura do pedido

### Objetivo principal

Entregar uma variante ESP32-C3 Super Mini V1601 compatível com o bounded context Production Pulse e com o fluxo atual `production-pulse-api ↔ device`, apta a ser instalada inicialmente por USB e atualizada depois por OTA.

### Restrições travadas

- basear-se no firmware ESP8266 V2 atual;
- não criar arquitetura paralela;
- manter APIs e campos JSON existentes;
- MAC para TI = Wi-Fi Station MAC;
- TX power 8,5 dBm + Wi-Fi sleep off nesta família;
- reconexão sem `WiFi.begin()` concorrente;
- `cfg.apiToken` + `X-Device-Token` preservados;
- OTA atual preservado;
- nova família `esp32c3_counter_v1`;
- `INPUT_1=GPIO0`, `INPUT_2=GPIO1`, active LOW;
- RGB `R=GPIO4`, `G=GPIO5`, `B=GPIO6`;
- não usar GPIO2/8/9 e reservar GPIO20/21;
- dual OTA app partitions + `otadata` na primeira gravação;
- diagnóstico HTML/Serial sem secrets.

## Ledger de requisitos

| Requisito | Descrição | Estado no plano |
|---|---|---|
| RQ-01 | Port do firmware ESP8266 V2 para ESP32-C3 | ATENDIDO_NO_PLANO |
| RQ-02 | Preservar endpoints, JSON, config, contador, reboot/factory reset | ATENDIDO_NO_PLANO |
| RQ-03 | Controller code derivado do STA MAC com aliases legados | ATENDIDO_NO_PLANO |
| RQ-04 | STA MAC único em Serial/HTML/status | ATENDIDO_NO_PLANO |
| RQ-05 | Sleep off + TX 8,5 dBm antes de conectar | ATENDIDO_NO_PLANO |
| RQ-06 | Reconexão stateful, sem begin concorrente, reason code | ATENDIDO_NO_PLANO |
| RQ-07 | Token atual preservado e redigido | ATENDIDO_NO_PLANO |
| RQ-08 | OTA pull/report atual preservado | ATENDIDO_NO_PLANO |
| RQ-09 | Família separada para bloquear binário cruzado | ATENDIDO_NO_PLANO |
| RQ-10 | Layout 4 MB com `ota_0`, `ota_1`, `otadata` | ATENDIDO_NO_PLANO |
| RQ-11 | Duas entradas isoladas; apenas INPUT_1 conta | ATENDIDO_NO_PLANO |
| RQ-12 | Active LOW + debounce por transição | ATENDIDO_NO_PLANO |
| RQ-13 | Estados das entradas no status | ATENDIDO_NO_PLANO |
| RQ-14 | RGB centralizado por estado operacional | ATENDIDO_NO_PLANO |
| RQ-15 | Definição coerente de backend freshness | ATENDIDO_NO_PLANO |
| RQ-16 | Pinos strapping/UART preservados | ATENDIDO_NO_PLANO |
| RQ-17 | HTML com identidade/rede/OTA | ATENDIDO_NO_PLANO |
| RQ-18 | Serial de bancada completo e periódico | ATENDIDO_NO_PLANO |
| RQ-19 | Preservar boundary MFE → production-pulse-api | HERDADO_POR_SOLUCAO_TRANSVERSAL |
| RQ-20 | Não confundir factory reset físico com sinais de máquina | ATENDIDO_NO_PLANO |
| RQ-21 | Diferenciar validação automatizada de validação live | ATENDIDO_NO_PLANO |

## Evidências confirmadas

**FATO — firmware base.** `firmware/esp8266_counter_v2/esp8266_counter_v2.ino` já implementa `DeviceConfig`, EEPROM, `X-Device-Token`, `/api/*`, OTA check/report/download, progresso, reconnect por backoff, página HTML, reboot e factory reset.

**FATO — contrato do driver.** `production_pulse_app/infrastructure/drivers/esp8266_counter_driver.py` consome `/api/contador`, `/api/status`, `/api/config` e os comandos existentes; `parse_controller_identity()` aceita `controllerCode`, `codigoControlador` ou `equipamento` e já lê `mac`, `ip`, `firmwareVersion`, `uptimeMs`, `freeHeap`, `rssi`, `wifiConnected`.

**FATO — HTTP support.** `device_http_support.py` adiciona `X-Device-Token` às chamadas do BFF quando o device possui token, inclusive GETs. Isso permite identificar passivamente poll legítimo no firmware sem tornar `/api/contador` privado.

**FATO — controller code.** `devices.controller_code` é `VARCHAR(64)`, suficiente para `ESP32C3-XXXXXXXXXXXX` sem migration.

**FATO — drivers.** `device_drivers.json` é fonte declarativa de `roleKey`, metrics, commands, `operatorSurface`, `counterRestore` e timeout.

**FATO — OTA compatibility.** `FirmwareUpdateJobService.create_job()` exige `device.driver_key == firmware.driver_key`; `DeviceFirmwareLinkService` também valida compatibilidade no vínculo. Uma família/driver C3 distinta impede selecionar artefato ESP8266 para C3 pelo fluxo normal.

**FATO — OTA atual.** `DeviceOtaService` usa `X-Device-Token`, target autorizado, `artifactToken` TTL, estados `downloading/applying/updated/failed` e persiste versão instalada após report `updated`.

**FATO — Admin Hub.** `production-pulse-admin-hub.mdc` define que compatibilidade não gera edge; `assignedFirmwareKey` é vínculo explícito e API é autoridade final.

## Hipóteses concorrentes e resolução

| Hipótese | Estado | Evidência/ação |
|---|---|---|
| H1: precisamos alterar schema para novo controller code | DESCARTADA | `controller_code VARCHAR(64)` já comporta formato alvo |
| H2: precisamos mudar `/api/contador` para autenticado para detectar backend | DESCARTADA | BFF já envia token opcionalmente em GET; firmware pode observar header válido sem quebrar leitura pública |
| H3: basta reutilizar `esp8266_counter_v1` como driver do C3 | DESCARTADA | isso permitiria misturar artefatos por `driver_key`; requisito pede isolamento de binário |
| H4: precisamos duplicar todo o driver HTTP em Python | DESCARTADA | os dois hardwares compartilham protocolo/capabilities; há 2 consumidores reais e a regra `.cursor` permite extração neutra quando semanticamente estável |
| H5: factory reset físico pode usar INPUT_1+INPUT_2 | DESCARTADA | no C3 serão sinais de máquina; combinação legítima não pode apagar config |
| H6: Minimal SPIFFS é necessariamente seguro por nome | HIPOTESE_A_VALIDAR | execução deve provar partition table efetiva e tamanho dos slots no Core 3.3.11 |

## Arquitetura CURRENT

```text
ESP8266 V2
  ├─ GPIO D5/D1 → contador + decremento + hold factory reset
  ├─ ESP8266 Wi-Fi + web server
  ├─ /api/* + X-Device-Token
  └─ OTA pull → production-pulse-api

production-pulse-api
  ├─ esp8266_counter_v1 declarativo
  ├─ Esp8266CounterDriver
  ├─ FirmwareUpdateJobService
  ├─ DeviceOtaService
  └─ Admin Hub/MFE consome catálogo e contratos
```

## Arquitetura TARGET

```text
ESP32-C3 Super Mini V1601
  ├─ INPUT_1 GPIO0 → counter
  ├─ INPUT_2 GPIO1 → diagnóstico/reserva
  ├─ RGB GPIO4/5/6 → state indicator
  ├─ STA MAC → mac + controllerCode
  ├─ Wi-Fi sleep off + 8.5 dBm
  ├─ stateful reconnect + disconnect reason
  ├─ mesmo /api/* + mesmo X-Device-Token
  └─ mesmo OTA pull/report
             ↓
production-pulse-api
  ├─ esp8266_counter_v1 (preservado)
  ├─ esp32c3_counter_v1 (novo)
  ├─ protocolo counter HTTP compartilhado no adapter correto
  ├─ compatibilidade OTA por driver_key existente
  └─ MFE permanece catálogo-driven
```

## Grafo de ownership e contratos

| Papel | Owner |
|---|---|
| hardware pins, Wi-Fi, STA MAC, LED, debounce | firmware `esp32c3_counter_v1` |
| device HTTP protocol | `production-pulse-api` infrastructure driver adapter |
| capabilities/metrics/operatorSurface | `device_drivers.json` |
| compatibilidade vínculo/OTA | application services da `production-pulse-api` |
| device auth OTA | `DeviceOtaService` + device token existente |
| vínculo explícito visual | API `assignedFirmwareKey`; MFE render-only |
| firmware artifact/jobs | `production-pulse-api` + Postgres/storage existentes |
| first-flash/partition settings | firmware README/runbook |

## Estado antes × depois

| Caso | Antes | Depois esperado | Deve mudar? |
|---|---|---|---|
| contador ESP8266 existente | funcional | funcional, regressão protegida | não |
| novo hardware C3 | sem suporte oficial | driver + firmware próprio | sim |
| identidade | `ESP-<chipId>` | `ESP32C3-<STA_MAC>` | sim no C3 |
| aliases identity | 3 campos iguais | continuam 3 campos iguais | não semanticamente |
| MAC | `WiFi.macAddress()` | STA MAC resolvido explicitamente | sim na implementação C3 |
| Wi-Fi reconnect | disconnect/begin por timer | uma tentativa em voo + backoff/event | sim |
| radio power | default | 8,5 dBm | sim C3 |
| INPUT_2 | inexistente | diagnóstico sem efeito no contador | sim |
| factory reset físico | hold D5+D1 | removido do sinal de máquina; endpoint HTTP preservado | sim C3 |
| OTA | pull/report | mesmo protocolo | não |
| família OTA | ESP8266 | família C3 separada | sim |
| Admin Hub | compatibilidade por catálogo | continua catálogo-driven | não |
| database schema | suporta campos atuais | sem migration prevista | não |

## Decisões travadas

- D-01: `esp32c3_counter_v1` é driver/família própria.
- D-02: versão inicial `esp32c3_counter_v1.0.0`.
- D-03: controller code `ESP32C3-` + STA MAC sem `:` e uppercase.
- D-04: `mac`, Serial e HTML derivam da mesma identidade STA.
- D-05: `WiFi.setSleep(false)` e `WIFI_POWER_8_5dBm` antes de `WiFi.begin()`.
- D-06: reconnect usa estados explícitos/eventos; `/api/config` não dispara begin fora desse fluxo.
- D-07: `/api/contador` continua compatível; token válido opcional atualiza backend freshness.
- D-08: factory reset físico por combinação de INPUT_1/INPUT_2 é proibido; endpoint autenticado permanece.
- D-09: INPUT_1 incrementa; INPUT_2 não altera counter.
- D-10: LED RGB tem único owner/state renderer.
- D-11: OTA não muda contrato; só adaptação de plataforma ESP32.
- D-12: backend mantém autoridade de driver/família; não há hardcode C3 no MFE.
- D-13: não criar migration nesta entrega salvo drift comprovado.
- D-14: layout OTA só é aceito após prova de `ota_0`, `ota_1`, `otadata` e capacidade do slot.

## Matriz de fluxos transversais

| Fluxo | Superfície/caminho | Classificação |
|---|---|---|
| poll counter | API → driver → `/api/contador` | P0 |
| test/probe | API → driver → status/config | P0 |
| configure | API → `/api/config` | P0 |
| commands | API → device POST commands | P0 |
| operator counter | MFE → API → driver | HERANÇA, sem nova UI |
| OTA link | Admin Hub → API link service | HERANÇA |
| OTA job | Admin Hub → FirmwareUpdateJobService | P0 regressão |
| OTA device check/download/report | device → API | P0 |
| HTML local | browser LAN → device | P0 diagnóstico |
| Serial maintenance | USB/UART → device | P0 diagnóstico |
| TOTVS | MFE/API → api-delpi | FORA; nenhum impacto requerido |
| migrations | production_pulse schema | FORA, salvo drift comprovado |

## Riscos e compatibilidade

- **Contrato:** novos status fields devem ser ADDITIVE.
- **Segurança:** nenhum secret em logs/HTML; token atual continua enforcement das rotas protegidas.
- **Firmware family:** reutilizar driver ESP8266 seria risco crítico de binário cruzado.
- **Hardware:** GPIO0/1 são sinais industriais isolados e não podem executar factory reset por gesto.
- **Runtime:** first flash com tabela errada impediria OTA futura.
- **Wi-Fi:** retries concorrentes podem produzir `sta is connecting, cannot set config`.
- **MFE:** hardcode inesperado de drivers pode exigir ajuste; não alterar antes de provar.
- **Rollback:** ESP8266 fica intacto; C3 deve poder receber versão C3 anterior por OTA conforme política atual do catálogo.

## Sequência de execução

### E1 — Firmware ESP32-C3

Executar [`ESP32C3-SUPER-MINI-FIRMWARE-PLAN.md`](./ESP32C3-SUPER-MINI-FIRMWARE-PLAN.md).

Pós-condição necessária para E2: sketch C3 compila, contrato `/api/*` documentado e identidade/pins/OTA definidos.

### E2 — API/driver/OTA compatibility

Executar [`ESP32C3-SUPER-MINI-API-OTA-PLAN.md`](./ESP32C3-SUPER-MINI-API-OTA-PLAN.md).

Pós-condição necessária para E3: novo driver registrado, ESP8266 regressão preservada e binário cruzado bloqueado por testes.

### E3 — Validação integrada e live

Executar [`ESP32C3-SUPER-MINI-VALIDATION-PLAN.md`](./ESP32C3-SUPER-MINI-VALIDATION-PLAN.md).

Pós-condição final: comportamento original comprovado em automação + bancada real, com itens não executáveis classificados como `INCONCLUSIVE`.

## Rastreabilidade

| RQ | Decisão | Plano/subetapas | Prova principal |
|---|---|---|---|
| 01-06 | D01-D06 | Firmware E1-E3 | build + Serial/Wi-Fi live |
| 07 | D07 | Firmware E2/E5 + API regressão | auth positive/negative + secret scan |
| 08-10 | D11/D14 | Firmware E4 + API E3 + Validation E2 | OTA contract/live + partition evidence |
| 11-13 | D09 | Firmware E3 | pulse/held-low/input2 negative |
| 14-15 | D10/D07 | Firmware E3 | LED state transitions |
| 16 | hardware contract | Firmware E1 | source/static review + bench |
| 17-18 | diagnostics | Firmware E5 | HTML/Serial inspection |
| 19 | boundary | D12 | architecture review/MFE tests if touched |
| 20 | D08 | Firmware E3 | no physical reset via inputs |
| 21 | validation discipline | Validation full plan | evidence matrix |

## Critérios de pronto do plano mestre

- todos RQ possuem etapa/teste/aceite;
- nenhum novo contrato paralelo foi criado;
- C3 e ESP8266 possuem `driver_key` distintos;
- endpoints e aliases legados do device permanecem compatíveis;
- OTA é o mesmo canal `/device-ota/*`;
- nenhum secret é exposto;
- tabela OTA efetiva foi provada, não inferida pelo menu da IDE;
- MFE permanece somente via `production-pulse-api`;
- teste live é reportado apenas quando realmente executado.

## Fora do escopo

- SHA-256 verify no chip (P1 já catalogado em OTA production-grade);
- secure boot / signed artifacts / anti-rollback hardware;
- semver/anti-downgrade policy nova;
- novo hardware abstraction framework;
- novo protocolo de autenticação;
- hard delete/migration estrutural;
- integração TOTVS;
- uso funcional do INPUT_2 além de diagnóstico.

## Revisão adversarial

1. **O plano poderia misturar binários?** Não: driver/família distinta e compatibilidade backend já depende de `driver_key`.
2. **Poderia apagar config por sinal real da máquina?** O plano remove explicitamente o hold físico de factory reset nos dois inputs.
3. **Poderia declarar MAC errado?** A decisão exige uma única fonte STA para controller code, status, HTML e log.
4. **Poderia ficar verde em unit tests e falhar na placa?** Sim; por isso o plano de validação separa compile/API tests de bench/LAN/OTA live.
5. **Poderia alterar MFE sem necessidade?** Não; mudança MFE é condicionada a evidência de hardcode real e tratada como drift/escopo comprovado.
6. **Poderia criar uma terceira abstração de driver?** Não; compartilhamento só deve extrair protocolo HTTP neutro existente e com dois consumidores reais.
7. **Minimal SPIFFS poderia não ter a capacidade esperada?** Sim; nome não é prova. O aceite exige inspeção da tabela/artefato efetivo.
8. **Como pode passar e ainda estar errado?** Se o STA MAC lido antes do modo correto, LED freshness atualizado por request público, ou OTA compilado para tabela diferente da primeira gravação. Cada risco tem teste/live dedicado no plano de validação.
