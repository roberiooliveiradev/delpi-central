# Especificação — Production Pulse (plugin + API)

> **Escopo:** cadastro de **dispositivos IoT**, amarração a **posto / máquina / equipamento** (CT TOTVS opcional), leituras e comandos por driver.

---

## 1. Objetivos

1. Cadastrar **N dispositivos** (IP, filial, driver) — contador, rpm, temperatura, multi-sensor.
2. Amarrar cada device a **um objeto operacional** (`anchor_type`): CT (atalho TOTVS), **máquina**, **equipamento**, área ou avulso. Vários devices no **mesmo** motor/CT/máquina.
3. Histórico genérico (`metrics` JSONB), painel e operador tablet.
4. CRUD + RBAC; drivers plugáveis sem migration SQL.

**Exemplos:**

| Medição | Device | Âncora |
|---------|--------|--------|
| Golpes prensa | ESP contador | `work_center` CT-53 |
| Rotação ventilador | ESP gauge | `equipment` «Ventilador exaustão A» — sem CT |
| °C motor bomba | ESP gauge | `equipment` «Motor bomba #2» |
| rpm + °C no torno | 2 devices | `machine` «Torno CNC #2» (+ CT opcional) |

---

## 2. Atores

| Ator | Capacidades |
|------|-------------|
| Operador | Hub por **posto/equipamento**; superfície conforme driver |
| Supervisor | CRUD dispositivo + amarração (qualquer `anchor_type`) |
| Admin filial | Comandos capability-gated |

---

## 3. Telas (MFE)

> **Responsivo:** wireframes **desktop + tablet (769–1100px) + mobile (≤768px)** em [WIREFRAMES.md](./WIREFRAMES.md) · CSS em [DESIGN-FRONTEND §7](./DESIGN-FRONTEND.md#7-responsividade).

### 3.1 Painel (`/apps/production-pulse`)

- Filtros: filial, **`anchor_type`**, CT (se houver), papel (`role`), busca por nome/placement.
- KPIs: total devices, online, offline.
- Vista **lista** ou **agrupada** por: CT | Máquina | Equipamento | Área (conforme `anchor_type`).
- Colunas: device, papel, **objeto** (`placement_label`), IP, métrica cache, status.

### 3.2 Cadastro / edição

**Seção A — Dispositivo (sempre):** nome, filial, IP, driver, poll, enabled, testar conexão.

**Seção B — Onde está instalado (`anchor_type`):**

| Tipo | Campos | CT TOTVS |
|------|--------|----------|
| Posto PCP | CT obrigatório | Autocomplete SHB010 |
| Máquina | `machine_label` obrigatório | Bloco **opcional** «Vincular ao TOTVS» |
| Equipamento | `equipment_label` obrigatório | Idem opcional |
| Área / linha | `area_label` | Opcional |
| Avulso | — (usa nome do device) | Não |

Bloco **TOTVS (atalho)** — colapsável, em qualquer tipo exceto `standalone`:

- Centro de trabalho (autocomplete)
- Recurso / ferramenta (P1)

Salvar exige amarração válida para o `anchor_type` escolhido — **não** exige CT para ventilador/motor.

### 3.3 Detalhe / histórico

Cabeçalho: **device** + `placement_label` + `anchor_type` badge; métricas live; gráfico/tabela/commands.

### 3.4 Modo operador (tablet)

- **Hub** (`GET /operator/placements`): cards por **`placement_label`** — CT, máquina ou equipamento.
- Filtros touch: Todos | Postos | Máquinas | Equipamentos.
- Picker → superfície por driver (`counter_pad`, `gauge_readout`, …).

Alias MVP: `GET /operator/work-centers` filtra `anchor_type=work_center`; hub unificado preferido.

---

## 4. API REST (production-pulse-api) — contrato fechado (MVP)

Base gateway: `/apps/production-pulse-api`  
Envelope: `{ success, message, data, meta? }` (padrão Delpi BFF).  
Auth: JWT em todas as rotas exceto `GET /health`.

### 4.1 Infra

| Método | Path | Auth | Resposta |
|--------|------|------|----------|
| `GET` | `/health` | público | `{ status: "online", service: "production-pulse-api" }` |

### 4.2 Dispositivos (CRUD)

| Método | Path | Permissão | Notas |
|--------|------|-----------|-------|
| `GET` | `/devices` | … | Query: `anchorType`, `workCenter`, `placementSearch`, … |
| `GET` | `/devices/{id}` | `devices.view` + filial | Binding vigente + `capabilities` embutidas do registry |
| `POST` | `/devices` | `devices.manage` + filial | Body: `driver_key` (obrig.) → API seta `role_key` do registry |
| `PUT` | `/devices/{id}` | `devices.manage` + filial | Replace campos device |
| `PATCH` | `/devices/{id}` | `devices.manage` + filial | Partial update |
| `DELETE` | `/devices/{id}` | `devices.manage` + filial | Soft delete: `enabled=false` |

### 4.3 Operador — placements (canônico)

| Método | Path | Permissão | Notas |
|--------|------|-----------|-------|
| `GET` | `/operator/placements/{placementKey}/devices` | `operator` + filial | Picker — devices elegíveis no placement |
| `GET` | `/work-centers/{code}/devices` | `devices.view` + filial | **Deprecated** → **308** para `/operator/placements/wc:{branch}:{code}/devices` — [ADR-004](./ADR-004-routes-and-legacy-aliases.md) |

Query picker: `branch`, opcional `role`, `operatorEligible=true` (default no operador).

### 4.4 Binding

| Método | Path | Permissão | Notas |
|--------|------|-----------|-------|
| `GET` | `/devices/{id}/binding` | `devices.view` | Binding vigente ou `null` |
| `PUT` | `/devices/{id}/binding` | `devices.manage` | Fecha binding anterior se CT mudar |
| `DELETE` | `/devices/{id}/binding` | `devices.manage` | Encerra binding vigente |
| `GET` | `/devices/{id}/bindings/history` | `devices.view` | Paginado |

### 4.5 Leituras e poll

| Método | Path | Permissão | Notas |
|--------|------|-----------|-------|
| `GET` | `/devices/{id}/readings` | `devices.view` | Query: `from`, `to`, `metric` (filtro chave), `page`, `pageSize` |
| `GET` | `/devices/{id}/live` | `devices.view` | Poll **sem persistir** — `{ metrics, status, online, recorded_at, capabilities }` — `status` via R9–R12 |
| `POST` | `/devices/{id}/poll` | `devices.view` | Poll + grava `readings` + atualiza `last_metrics` |
| `POST` | `/devices/poll-all` | `devices.manage` | Query: `branch`, opcional `role` |

### 4.6 Comandos e teste de conexão

| Método | Path | Permissão | Notas |
|--------|------|-----------|-------|
| **`POST`** | **`/devices/test-probe`** | `devices.manage` | **Cadastro novo** — body `{ branch, ip_address, driver_key }` — não persiste device/reading — [ADR-002](./ADR-002-poll-scheduler-and-lan.md) |
| `POST` | `/devices/{id}/test` | `devices.manage` | Mesmo fluxo HTTP do driver; device já existe (edição) |
| `POST` | `/devices/{id}/commands/{commandKey}` | `operator` **ou** `devices.command` **ou** `devices.manage` | Conforme rota + capability — [ADR-003](./ADR-003-rbac-mvp.md) |
| `GET` | `/devices/{id}/commands` | `devices.view` | Log auditado |

**Resposta test-probe / test (sucesso):**

```json
{
  "driverKey": "esp8266_counter_v1",
  "metrics": { "counter": 42 },
  "latencyMs": 87,
  "online": true
}
```

Rate limit: **10 req/min** por usuário (test-probe + test). Falha: `{ "online": false, "error": "timeout", "latencyMs": 3000 }`.

Atalhos MVP (alias estáveis):

| Método | Path | Capability |
|--------|------|------------|
| `POST` | `.../commands/reset` | `reset` |
| `POST` | `.../commands/increment` | `increment` |
| `POST` | `.../commands/decrement` | `decrement` |

Comandos operador (contador): auditados + reading `source=command` quando aplicável.

### 4.7 Resumo operacional (painel + operador)

| Método | Path | Permissão | Notas |
|--------|------|-----------|-------|
| `GET` | `/summary` | `devices.view` + filial | KPIs admin |
| `GET` | `/operator/placements` | `operator` + filial | Hub tablet: agrupa por `placement_label`; query `anchorType`, `search` |
| `GET` | `/operator/work-centers` | `operator` + filial | **Alias:** `GET /operator/placements?anchorType=work_center` |

### 4.8 Catálogo

| Método | Path | Permissão | Notas |
|--------|------|-----------|-------|
| `GET` | `/catalog/drivers` | `devices.view` | Registry JSON (labels PT, metrics, commands, operatorSurface) |
| `GET` | `/catalog/work-centers` | `devices.view` + filial | Proxy → api-delpi **`/production/appointments/work-centers`** (catálogo SHB010). Query: `branch`, `search` (filtro BFF). Ver [INTEGRATIONS-TOTVS.md](./INTEGRATIONS-TOTVS.md) |

---

## 5. Drivers, papéis e capabilities

### 5.1 Papéis (`role_key`)

| `role_key` | Uso | Comandos típicos | Superfície operador |
|------------|-----|------------------|---------------------|
| `pulse_counter` | Golpes / ciclos produção | increment, decrement, reset | `counter_pad` |
| `process_gauge` | Rotação, temperatura, pressão | — (somente leitura) | `gauge_readout` |
| `telemetry` | Multi-sensor / gateway | configurável | `telemetry_dashboard` (futuro) |

Papel é **derivado do driver** no save — admin não escolhe papel isolado (evita combinação inválida driver↔UI).

### 5.2 Port `DeviceDriver` (domain)

```text
read(device) → DeviceReading { metrics, recorded_at }
test(device) → DeviceReading (sem persistir)
execute(device, command_key, payload?) → CommandResult
capabilities() → frozen set from registry
```

Implementações MVP: `Esp8266CounterDriver` (`esp8266_counter_v1`). Futuro: `Esp8266GaugeDriver`, Modbus, MQTT.

Registry completo: [DEVICE-DRIVERS.md](./DEVICE-DRIVERS.md).

### 5.3 Normalização de leituras

- Driver retorna payload bruto; adapter mapeia para chaves canônicas do registry (`counter`, `rpm`, `temperature_c`).
- Poll grava `delta_metrics` só para métricas com `monotonic: true`.
- Reset físico contador: `delta_metrics.counter = 0`, `meta.counter_reset = true`.

---

## 6. Polling, conectividade e histórico

Referência: [ADR-002-poll-scheduler-and-lan.md](./ADR-002-poll-scheduler-and-lan.md).

### 6.1 Scheduler (background)

- Serviço único `DevicePollSchedulerService` no **lifespan** da API (sem Celery no MVP).
- Per-device `next_poll_at`; tick 1 s; jitter ±10% no intervalo.
- Concorrência máxima **10** polls HTTP simultâneos (`PP_POLL_MAX_CONCURRENT`).
- Poll apenas se `enabled=true` **e** binding vigente (R5).

### 6.2 HTTP LAN

- Timeout: `device_drivers.json` → `poll.timeoutMs` (default **3000** ms).
- Falha timeout/4xx/5xx: R13 — `last_error`, sem nova reading.
- Dev Docker: `network_mode: host` no serviço API — ver ADR-002.

### 6.3 Grace window (online / offline)

```text
grace_ms = clamp(poll_interval_ms × 2, min=2000, max=600000)
```

| `status` | Condição |
|----------|----------|
| `online` | `enabled` ∧ binding vigente ∧ `last_seen_at` ∧ `(now - last_seen_at) ≤ grace_seconds` |
| `offline` | `enabled` ∧ binding vigente ∧ ¬online |
| `disabled` | ¬`enabled` |
| `no_binding` | sem binding vigente (rascunho) |

KPI painel: **total** inclui rascunhos; **online/offline** só devices com binding; rascunhos entram em KPI «sem amarração».

### 6.4 Persistência

- Sucesso: reading `source=poll|manual|command`; update `last_metrics`, `last_seen_at`; clear `last_error`.
- Gauges (R15): gravar reading a cada poll agendado **bem-sucedido** mesmo com valor estável (continuidade time-series).
- Delta (R16): métricas `monotonic:true` → `delta = new - prev` se `new ≥ prev`; se `new < prev` → reset contador (`delta=new`, `meta.counter_reset=true`).

---

## 7. Regras de negócio (fechadas — MVP)

### 7.1 Cadastro e amarração

| # | Regra |
|---|--------|
| R1 | **1 dispositivo → 1 amarração vigente** (`device_bindings` com `effective_to` null). |
| R2 | **1 âncora → N dispositivos** (mesmo CT, mesma máquina ou mesmo equipamento). |
| R3 | **IP único por filial.** |
| R4 | Nome do device único por filial (recomendado). |
| R5 | Device sem binding = rascunho; fora de summary/hub operador. |
| R6 | Se `work_center_code` preenchido → deve existir no catálogo api-delpi (422). |
| R7 | Filial do device imutável após criação. |
| R8 | Soft delete: `enabled=false`. |
| **R27** | `anchor_type=work_center` → `work_center_code` **obrigatório**. |
| **R28** | `anchor_type=machine` → `machine_label` **obrigatório**; CT **opcional**. |
| **R29** | `anchor_type=equipment` → `equipment_label` **obrigatório**; CT **opcional**. |
| **R30** | `anchor_type=area` → `area_label` **obrigatório**. |
| **R31** | `anchor_type=standalone` → proíbe CT/máquina/equipamento; `placement_label` = `devices.name`. |
| **R32** | API compõe `placement_label` ao salvar (ver [SCHEMA.md](./SCHEMA.md)). |
| R24–R25 | Driver registry (igual antes). |

### 7.2 Polling, conectividade e leituras

| # | Regra |
|---|--------|
| **R9** | **Online:** dentro da grace window (§6.3) após último poll **bem-sucedido** (`last_seen_at`). |
| **R10** | **Offline:** enabled + binding vigente, fora da grace window ou nunca poll OK (`last_seen_at` null). |
| **R11** | **Disabled:** `enabled=false` — fora do scheduler, hub operador e contagem online/offline. |
| **R12** | **Sem amarração:** sem binding vigente — status `no_binding`; fora do hub operador; conta no KPI total e «sem amarração». |
| **R13** | Poll **falho:** atualiza `last_poll_attempt_at` + `last_error`; **não** insere reading; **não** altera `last_seen_at` / `last_metrics`. |
| **R14** | Poll **OK:** limpa `last_error`; atualiza `last_seen_at`, `last_metrics`; insere reading (`source=poll`). |
| **R15** | Drivers gauge/telemetria: cada poll OK gera reading mesmo se métrica igual (heartbeat). |
| **R16** | `delta_metrics` só para chaves `monotonic:true`; rollover contador → `meta.counter_reset=true`. |

### 7.3 Comandos e auditoria

| # | Regra |
|---|--------|
| R17 | Todo comando gera `device_commands`. |
| R18 | Comando exige permissão **e** capability do driver. |
| R19 | Comandos operador contador: firmware + audit + reading quando retorna novo valor. |
| **R26** | `POST .../commands/increment` em device `process_gauge` → **422** «Comando não suportado por este dispositivo». |

### 7.4 Segurança, escopo e RBAC

Matriz completa: [ADR-003-rbac-mvp.md](./ADR-003-rbac-mvp.md).

| # | Regra |
|---|--------|
| **R20** | JWT obrigatório exceto `GET /health`. |
| **R21** | Gate filial em toda rota com escopo de branch. |
| **R22** | MFE **não** chama api-delpi nem IP LAN direto. |
| **R23** | Poll HTTP LAN só na **production-pulse-api** (container com rota de rede adequada — ADR-002). |
| **R33** | `POST /devices/test-probe`: só `devices.manage`; rate limit 10/min/usuário. |
| **R34** | Comandos hardware: permissão de rota **e** capability do driver (R18). |
| **R35** | Rota `/operator/*`: gate `production-pulse.operator` — **não** exige `devices.view`. |

### 7.5 Validações HTTP (resumo)

| Situação | Código |
|----------|--------|
| Comando não suportado pelo driver | `422` |
| Driver desconhecido | `422` |
| (demais iguais § anterior) | |

---

## 9. Exemplos JSON (API)

### POST /devices/test-probe — antes do save

```json
POST /devices/test-probe
{
  "branch": "01",
  "ip_address": "192.168.20.2",
  "driver_key": "esp8266_counter_v1"
}

→ 200
{
  "driverKey": "esp8266_counter_v1",
  "metrics": { "counter": 42 },
  "latencyMs": 95,
  "online": true
}
```

### POST /devices + PUT /binding — ventilador (equipment, sem CT)

```json
POST /devices
{
  "name": "ESP ventilador setor A",
  "branch": "01",
  "ip_address": "192.168.20.15",
  "driver_key": "esp8266_gauge_v1",
  "pollIntervalMs": 30000,
  "enabled": true
}

PUT /devices/{id}/binding
{
  "anchor_type": "equipment",
  "equipment_label": "Ventilador exaustão setor A"
}
```

Resposta binding: `placement_key: "e:01:ventilador-exaustao-setor-a"`, `placement_label: "Ventilador exaustão setor A"`.

### PUT /binding — contador no posto PCP

```json
{
  "anchor_type": "work_center",
  "work_center_code": "CT-53",
  "work_center_name": "Usinagem CNC",
  "equipment_label": "Sensor golpe principal"
}
```

### GET /devices/{id} (trecho)

```json
{
  "id": "…",
  "name": "ESP ventilador setor A",
  "driver_key": "esp8266_gauge_v1",
  "role_key": "process_gauge",
  "last_metrics": { "rpm": 1180, "temperature_c": 42.1 },
  "status": "online",
  "binding": {
    "anchor_type": "equipment",
    "placement_key": "e:01:ventilador-exaustao-setor-a",
    "placement_label": "Ventilador exaustão setor A"
  },
  "capabilities": {
    "metrics": ["rpm", "temperature_c"],
    "commands": [],
    "operatorSurface": "gauge_readout"
  }
}
```

Registry completo: [DEVICE-DRIVERS.md](./DEVICE-DRIVERS.md).

---

## 10. Fora do MVP

- Driver `esp8266_gauge_v1` implementado + WF-PP-OP-GAUGE.
- Sincronizar delta contador com apontamento TOTVS / SH8.
- Widget cockpit PCP.
- WebSocket push.
- Alertas (contador parado, temperatura acima limite).
- Modbus / MQTT.
- Integração chat / agente.

