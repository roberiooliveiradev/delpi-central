# Schema — production_pulse (Postgres plugins)

> Schema dedicado em `postgres-plugins`. Migrations via runner da API (`PRODUCTION_PULSE_RUN_MIGRATIONS_ON_STARTUP`).

---

## Princípios

1. **Dispositivo IoT** (`devices`) é a entidade central — IP, driver, leituras.
2. **Amarração** (`device_bindings`) diz **onde** o sensor está no chão de fábrica — CT, máquina, equipamento ou avulso.
3. **CT TOTVS** é **atalho opcional** — enriquece contexto PCP; **não** é obrigatório para ventilador, motor auxiliar, etc.
4. **Leituras genéricas** — `metrics` JSONB (golpes, rpm, °C, …) conforme `driver_key`.

---

## Entidades

### `devices`

Cadastro de **hardware** na rede (ESP, gateway, futuro Modbus).

| Coluna | Tipo | Notas |
|--------|------|-------|
| `id` | `uuid` PK | |
| `branch` | `varchar(2)` | `01` / `02` |
| `name` | `varchar(120)` | Rótulo do **dispositivo** («ESP ventilador A», «Contador prensa») |
| `ip_address` | `inet` | Ex.: `192.168.20.2` |
| `controller_code` | `varchar(64)` | Identidade do chip no firmware (ex.: `ESP-00A1B2C3`); opcional; único por filial quando informado |
| `driver_key` | `varchar(40)` | Protocolo — `esp8266_counter_v1`, `esp8266_gauge_v1`, … |
| `role_key` | `varchar(40)` | `pulse_counter`, `process_gauge`, `telemetry` — do registry |
| `enabled` | `boolean` | Polling ativo |
| `poll_interval_ms` | `int` | Default 30000; clamp 1–300000 (fonte: `device_validation_content.json`) |
| `last_seen_at` | `timestamptz` | Último poll OK |
| `last_metrics` | `jsonb` | Ex.: `{"counter": 1284}` ou `{"rpm": 1850, "temperature_c": 67.2}` |
| `last_error` | `text` | Timeout/offline |
| `created_at` / `updated_at` | `timestamptz` | |
| `created_by` / `updated_by` | `varchar(64)` | `sub` JWT |

**Unique:** `(branch, ip_address)`.

**Índices:** `(branch, role_key)`, `(branch, enabled)`.

---

### `device_bindings`

**Uma amarração vigente por dispositivo** — define o **objeto monitorado** e links opcionais ao TOTVS.

#### Tipos de âncora (`anchor_type`)

| `anchor_type` | Uso | Campo principal | CT TOTVS |
|---------------|-----|-----------------|----------|
| `work_center` | Sensor/contador **no posto** PCP | `work_center_code` | **Obrigatório** (validado SHB010) |
| `machine` | **Máquina** (torno, prensa, compressor) | `machine_label` + opcional `machine_code` | Opcional (atalho) |
| `equipment` | **Equipamento** medido (ventilador, motor, bomba) | `equipment_label` | Opcional |
| `area` | Zona / linha («Sala HVAC», «Subestação») | `area_label` | Opcional |
| `standalone` | Só o dispositivo — sem lugar fixo no cadastro | usa `devices.name` | Não |

Exemplos:

| Cenário | `anchor_type` | Binding |
|---------|---------------|---------|
| Golpes na prensa do CT-53 | `work_center` | CT-53 + equipment «Sensor golpe» |
| Rotação ventilador exaustão | `equipment` | equipment «Ventilador exaustão setor A» — **sem CT** |
| Temperatura motor bomba | `equipment` | equipment «Motor bomba recirculação» |
| Contador + temp no mesmo torno | 2 devices, `machine` | machine «Torno CNC #2» — CT opcional CT-12 |

| Coluna | Tipo | Notas |
|--------|------|-------|
| `id` | `uuid` PK | |
| `device_id` | `uuid` FK → `devices` | **Unique** WHERE `effective_to IS NULL` |
| `anchor_type` | `varchar(20)` | `work_center` \| `machine` \| `equipment` \| `area` \| `standalone` |
| `placement_label` | `varchar(120)` | Rótulo **canônico para UI** (hub operador, agrupamento) — preenchido pela API a partir dos campos abaixo |
| `work_center_code` | `varchar(20)` | Opcional exceto `anchor_type=work_center` |
| `work_center_name` | `varchar(120)` | Snapshot autocomplete TOTVS |
| `machine_code` | `varchar(40)` | Opcional — recurso TOTVS (P1) ou código interno |
| `machine_label` | `varchar(120)` | Obrigatório se `anchor_type=machine` |
| `equipment_label` | `varchar(120)` | Obrigatório se `anchor_type=equipment` |
| `area_label` | `varchar(120)` | Obrigatório se `anchor_type=area` |
| `resource_code` | `varchar(20)` | Opcional — atalho TOTVS `H6_RECURSO` |
| `tool_code` | `varchar(20)` | Opcional — `H8_FERRAM` |
| `notes` | `text` | |
| `effective_from` / `effective_to` | `timestamptz` | Histórico de troca de âncora |

**Cardinalidade:**

- **1 dispositivo → 1 amarração vigente**
- **1 âncora → N dispositivos** (vários sensores no mesmo motor, CT ou máquina)

**Índices:** `(anchor_type)`, `(work_center_code)` partial WHERE NOT NULL, `(placement_label)` via expression ou coluna materializada para busca hub.

Histórico: fechar binding (`effective_to`) e criar novo — não UPDATE destrutivo na linha vigente.

---

### `readings`

| Coluna | Tipo | Notas |
|--------|------|-------|
| `id` | `bigserial` PK | |
| `device_id` | `uuid` FK | |
| `metrics` | `jsonb` | Normalizado pelo driver |
| `delta_metrics` | `jsonb` | Só métricas `monotonic: true` |
| `meta` | `jsonb` | `counter_reset`, qualidade, … |
| `source` | `varchar(20)` | `poll` \| `manual` \| `command` |
| `recorded_at` / `created_at` | `timestamptz` | |

---

### `device_commands`

Auditoria — só comandos expostos pelo `driver_key`.

---

## Registry de drivers (JSON na API)

Ver exemplos em [ESPECIFICACAO-PLUGIN.md §5](./ESPECIFICACAO-PLUGIN.md) — contador, gauge multi-métrica (rpm + °C), telemetria futura.

---

## Relacionamentos

```text
devices 1 ── 0..1 device_bindings (vigente)
devices 1 ── * readings
devices 1 ── * device_commands

anchor lógico (CT | máquina | equipamento | área) 1 ── * bindings
work_center TOTVS (SHB010) ── opcional ──► device_bindings (atalho)
```

**Não** há tabela local de CT/máquina — CT validado via api-delpi; máquina/equipamento são rótulos operacionais (P2: catálogo local reutilizável se necessário).

---

## `placement_label` — regra de composição (API)

Ordem de fallback ao salvar binding:

| `anchor_type` | `placement_label` |
|---------------|-------------------|
| `work_center` | `{work_center_code} · {work_center_name}` |
| `machine` | `{machine_label}` (+ sufixo CT se preenchido) |
| `equipment` | `{equipment_label}` |
| `area` | `{area_label}` |
| `standalone` | `{devices.name}` |

Usado no painel agrupado, hub operador e busca tablet.

### `placement_key` — chave estável (API)

Identificador opaco para URL e agrupamento hub/picker. Gerado no save do binding; **imutável** enquanto vigente (troca de label → novo binding + nova key se âncora mudar).

| `anchor_type` | Fórmula | Exemplo |
|---------------|---------|---------|
| `work_center` | `wc:{branch}:{work_center_code}` | `wc:01:CT-53` |
| `machine` | `m:{branch}:{slug(machine_label)}` | `m:01:torno-cnc-2` |
| `equipment` | `e:{branch}:{slug(equipment_label)}` | `e:01:ventilador-exaustao-a` |
| `area` | `a:{branch}:{slug(area_label)}` | `a:01:sala-hvac` |
| `standalone` | `s:{device_id}` | um card por device |

`slug` = lowercase, trim, NFKD, espaços → `-`, max 80 chars, colisão → sufixo `-2`, `-3`.

**Rotas operador:** `/operator/placements/{placementKey}/devices` (picker) · `/operator/devices/{deviceId}` (superfície).

**Resposta `GET /operator/placements`:**

```json
{
  "items": [{
    "placementKey": "e:01:ventilador-exaustao-a",
    "placementLabel": "Ventilador exaustão setor A",
    "anchorType": "equipment",
    "deviceCount": 1,
    "onlineCount": 1,
    "byRole": { "process_gauge": 1 },
    "primaryMetricPreview": { "key": "rpm", "value": 1180, "unit": "rpm" }
  }]
}
```
