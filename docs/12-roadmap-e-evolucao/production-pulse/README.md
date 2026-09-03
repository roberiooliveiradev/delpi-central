# Production Pulse — IoT industrial (dispositivos, máquinas, sensores)

> **Produto:** Minha DELPI  
> **Plugin:** `production-pulse`  
> **API:** `production-pulse-api`  
> **Status:** MVP implementado — homologação (set/2026)

Plataforma de **dispositivos IoT** na rede industrial: contadores de golpe, rotação de ventilador, temperatura de motor, pressão, etc. Cada **hardware** (IP + driver) amarra-se a um **objeto operacional** — centro de trabalho (atalho TOTVS), **máquina**, **equipamento**, área ou avulso.

**MVP:** contador ESP8266 + hub operador. **Arquitetura:** drivers + `anchor_type` + leituras JSONB — CT **opcional** quando o sensor não está num posto PCP.

---

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| [ROADMAP.md](./ROADMAP.md) | Fases, subetapas e critérios de pronto (inclui **P3** telemetria) |
| [TELEMETRY-PERSISTENCE-P3.md](./TELEMETRY-PERSISTENCE-P3.md) | Persistência seletiva, heartbeat, rollups, retenção (padrão mercado) |
| [ESPECIFICACAO-PLUGIN.md](./ESPECIFICACAO-PLUGIN.md) | Telas, drivers/papéis, regras, API |
| [SCHEMA.md](./SCHEMA.md) | Modelo Postgres + leituras genéricas (`metrics` JSONB) |
| [DESIGN-FRONTEND.md](./DESIGN-FRONTEND.md) | Cores, tokens, componentes plugin-ui, estrutura MFE |
| [VISUAL-WIREFRAMES-AND-COLORS.md](./VISUAL-WIREFRAMES-AND-COLORS.md) | Wireframes coloridos por página/componente + mapa de tokens |
| [INTEGRATIONS-TOTVS.md](./INTEGRATIONS-TOTVS.md) | Matriz api-delpi / TOTVS vs dados locais |
| [DEVICE-DRIVERS.md](./DEVICE-DRIVERS.md) | Registry JSON de drivers e métricas |
| [GLOSSARY.md](./GLOSSARY.md) | Vocabulário device × âncora × CT |
| [USER-JOURNEYS.md](./USER-JOURNEYS.md) | Jornadas supervisor / operador / admin |
| [ADR-001-operator-layout.md](./ADR-001-operator-layout.md) | Sidebar vs quiosque tablet |
| [ADR-002-poll-scheduler-and-lan.md](./ADR-002-poll-scheduler-and-lan.md) | Scheduler, grace online, LAN Docker, test-probe |
| [ADR-003-rbac-mvp.md](./ADR-003-rbac-mvp.md) | Matriz operador vs supervisor (MVP) |
| [ADR-004-routes-and-legacy-aliases.md](./ADR-004-routes-and-legacy-aliases.md) | Rotas canônicas + redirect 308 |
| [HELP-CONTENT.md](./HELP-CONTENT.md) | Helps por componente + mapa wireframe |
| [content/helpTooltips.ts](./content/helpTooltips.ts) | Fonte `PP_HELP` (copiar no scaffold MFE) |
| [content/sectionIntros.ts](./content/sectionIntros.ts) | Copy visível abaixo dos títulos de seção |
| [WIREFRAMES.md](./WIREFRAMES.md) | Wireframes ASCII (admin + operador + P2 TEMP/ROTATION/COMBO) |
| [OPERATOR-SURFACES-P2.md](./OPERATOR-SURFACES-P2.md) | Spec P2: temperatura, rotação, painel combinado, alertas, metas, % |
| [API-ROUTES-AND-BUSINESS-RULES.md](./API-ROUTES-AND-BUSINESS-RULES.md) | Rotas REST + regras R1–R51 (R46–R51 P3 planejado) |
| [API-MFE-DEVICE-EVOLUTION.md](./API-MFE-DEVICE-EVOLUTION.md) | Plano evolução API + MFE a partir do contador e padrão de mercado |
| [HOMOLOGACAO-E6-S2.md](./HOMOLOGACAO-E6-S2.md) | Checklist verify live ESP8266 (UI + smoke) |
| [MANIFEST-DRAFT.md](./MANIFEST-DRAFT.md) | Rotas menu e permissões (rascunho) |

---

## Identificação

| Campo | Valor |
|-------|--------|
| `id` (plugin) | `production-pulse` |
| Nome exibido | Pulso de Produção |
| `basePath` | `/apps/production-pulse` |
| API gateway | `/apps/production-pulse-api` |
| Container MFE | `delpi-production-pulse` |
| Container API | `delpi-production-pulse-api` |
| Schema Postgres | `production_pulse` (postgres-plugins) |
| Dispositivo piloto | `http://192.168.20.2/` (ESP8266, dev) |

---

## Arquitetura

```text
Portal → MFE production-pulse
           ↓ JWT + X-Delpi-Caller-App: production-pulse
Gateway → production-pulse-api
           ├→ Postgres (devices, bindings, readings)
           ├→ HTTP LAN → drivers plugáveis (ESP contador, futuros sensores)
           └→ api-delpi (opcional — CT/recurso TOTVS como atalho)
```

**Bounded context:** cadastro, **registry de drivers**, polling, histórico genérico e RBAC na **production-pulse-api**. TOTVS na **api-delpi**. MFE **não** chama api-delpi direto.

---

## Modelo extensível (drivers + âncoras)

| Camada | Exemplo |
|--------|---------|
| **`devices`** | ESP no IP — o que **mede** (driver: contador, rpm, °C) |
| **`anchor_type`** | Onde está: `work_center`, `machine`, `equipment`, `area`, `standalone` |
| **TOTVS (CT)** | Atalho **opcional** — autocomplete SHB010 quando couber PCP |
| **`readings.metrics`** | `{ "rpm": 1200 }`, `{ "temperature_c": 78 }`, `{ "counter": 42 }` |

```text
Cadastro device (IP + driver) → amarração (âncora) → poll → histórico + operador
CT TOTVS = enriquecimento opcional, não pré-requisito do sensor
```

Detalhe: [SCHEMA.md § device_bindings](./SCHEMA.md) · [INTEGRATIONS-TOTVS.md](./INTEGRATIONS-TOTVS.md).

---

## Protocolo do dispositivo piloto (ESP8266 contador v1)

| Método | Rota | Corpo / resposta |
|--------|------|------------------|
| `GET` | `/api/contador` | `{"contador": <int>}` — **única rota pública** (sem token) |
| `GET` | `/api/status` | `controllerCode`, IP, MAC, contador + health (`firmwareVersion`, `uptimeMs`, `freeHeap`, `rssi`, `wifiConnected`) — exige `X-Device-Token` se token setado |
| `GET` | `/api/config` | `ssid`, `debounceMs`, `passwordSet`, `apiTokenSet`, `wifiConfigured` |
| `POST` | `/api/config` | body parcial: `ssid`, `password`, `debounceMs`, `apiToken` |
| `POST` | `/api/incrementar` | `{"contador": <int>}` |
| `POST` | `/api/decrementar` | `{"contador": <int>}` |
| `POST` | `/api/reset` | `{"contador": 0}` |
| `POST` | `/api/definir` | body `{"contador": <int>}` → `{"contador": <int>}` |
| `POST` | `/api/reboot` | reinicia o chip (auth com token se setado) |

Firmware de referência: [`firmware/esp8266_counter_v1/`](./firmware/esp8266_counter_v1/).

Comando plataforma: `POST /devices/{id}/commands/set` com `{"counter": <int>}` (aliases `contador` / `value`).

Ao detectar queda do contador no **poll** sem comando recente de `decrement` / `reset` / `set` (provenance), a API trata como perda de memória/reboot: tenta `set` com o valor lógico persistido (+ golpes pós-reboot) ou aplica offset em `last_metrics`. Quedas explicadas por comando do pad (janela `intentionalDecreaseCommandGraceMs`) **não** disparam restore. Não há mais limiar por magnitude (`maxIntentionalDecrease`).

Driver interno: `esp8266_counter_v1` — primeiro entry do registry; novos firmwares = novo `driver_key`, mesmo schema de leituras.

### ESP8266 gauge v1 (`esp8266_gauge_v1`)

| Método | Rota | Corpo / resposta |
|--------|------|------------------|
| `GET` | `/api/sensores` | `{"rpm": <number>, "temperatura": <number>}` |

Chaves canônicas na API: `rpm`, `temperature_c`. O driver aceita aliases `rotacao` / `temperatura` / `temperature_c` no JSON do firmware.

Referências: `maintenance-api`, `production-control-api`, `travel-expenses-api`.

---

## Permissões (manifesto — matriz MVP)

Detalhe: [ADR-003-rbac-mvp.md](./ADR-003-rbac-mvp.md).

| Código | Uso |
|--------|-----|
| `production-pulse.access` | Abrir o plugin |
| `production-pulse.devices.view` | Ver dispositivos e leituras (painel admin) |
| `production-pulse.devices.manage` | CRUD + binding + test-probe + poll-all |
| `production-pulse.devices.command` | Comandos hardware no **painel admin** |
| `production-pulse.operator` | Hub + superfície operador + comandos **na rota operador** (sem exigir `view`) |
| `production-pulse.view.filial-01` | Escopo filial SC |
| `production-pulse.view.filial-02` | Escopo filial ES |
| `production-pulse.admin` | Todas filiais + operações administrativas |

Matriz fina por filial/delegação: Fase 4 (ROADMAP E4).
