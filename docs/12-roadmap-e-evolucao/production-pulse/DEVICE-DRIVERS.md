# Registry de drivers — `device_drivers.json`

> Catálogo declarativo na **production-pulse-api** (`app/content/device_drivers.json`).  
> Consumido por: cadastro (preview), poll, comandos capability-gated, hub operador (superfície UI).

---

## Schema JSON (versão 1)

```json
{
  "schemaVersion": 1,
  "drivers": {
    "<driver_key>": {
      "roleKey": "pulse_counter | process_gauge | telemetry",
      "labelPt": "string",
      "descriptionPt": "string",
      "metrics": [
        {
          "key": "counter",
          "type": "integer | number",
          "monotonic": true,
          "labelPt": "Golpes",
          "unit": "optional",
          "primary": true,
          "icon": "Hash"
        }
      ],
      "commands": ["increment", "decrement", "reset"],
      "operatorSurface": "counter_pad | gauge_readout | telemetry_dashboard",
      "operatorEligible": true,
      "poll": { "timeoutMs": 3000 },
      "thresholds": {}
    }
  }
}
```

| Campo | Obrigatório | Notas |
|-------|-------------|-------|
| `roleKey` | sim | Copiado para `devices.role_key` no save |
| `metrics[].primary` | recomendado | Métrica na tabela painel e preview card operador |
| `metrics[].monotonic` | sim | Se true → calcula `delta_metrics` no poll |
| `commands` | sim | Pode ser `[]` — gauge read-only |
| `operatorSurface` | sim | Roteador MFE `OperatorDeviceSurface` |
| `thresholds` | não | P1 — ex. `temperature_c.warnAbove: 75` para cor UI |

---

## Entradas MVP + P1

### `esp8266_counter_v1` (MVP)

```json
{
  "roleKey": "pulse_counter",
  "labelPt": "ESP8266 — contador de golpes",
  "descriptionPt": "Firmware piloto: GET /api/contador, POST incrementar/decrementar/reset/definir",
  "metrics": [
    {
      "key": "counter",
      "type": "integer",
      "monotonic": true,
      "labelPt": "Golpes",
      "primary": true,
      "icon": "Hash"
    }
  ],
  "commands": ["increment", "decrement", "reset", "set"],
  "counterRestore": { "enabled": true, "preferHardwareSet": true },
  "operatorSurface": "counter_pad",
  "operatorEligible": true,
  "poll": { "timeoutMs": 3000 }
}
```

**Firmware:** ver [README.md § Protocolo piloto](./README.md).

**HTTP:** `GET /api/sensores` → `{"rpm": <number>, "temperatura": <number>}` (aliases `rotacao`, `temperature_c`).

### `esp8266_gauge_v1` (P1 — implementado)

```json
{
  "roleKey": "process_gauge",
  "labelPt": "ESP8266 — sensores de processo",
  "descriptionPt": "Leitura rpm e temperatura; sem comandos de escrita",
  "metrics": [
    {
      "key": "rpm",
      "type": "number",
      "monotonic": false,
      "labelPt": "Rotação",
      "unit": "rpm",
      "primary": true,
      "icon": "Gauge"
    },
    {
      "key": "temperature_c",
      "type": "number",
      "monotonic": false,
      "labelPt": "Temperatura",
      "unit": "°C",
      "primary": false,
      "icon": "Thermometer"
    }
  ],
  "commands": [],
  "operatorSurface": "gauge_readout",
  "operatorEligible": true,
  "poll": { "timeoutMs": 3000 },
  "thresholds": {
    "temperature_c": { "warnAbove": 75, "dangerAbove": 90 }
  }
}
```

---

## API

| Método | Path | Resposta |
|--------|------|----------|
| `GET` | `/catalog/drivers` | `{ drivers: [{ key, ...def }] }` |

`GET /devices/{id}` embute `capabilities` derivadas do registry (commands + metrics + operatorSurface + `thresholds` quando definidos no JSON).

A superfície operador `gauge_readout` usa `capabilities.thresholds` para colorir tiles (warn/danger) conforme a leitura atual.

---

## Extensão (novo driver)

1. Entrada em `device_drivers.json`
2. Classe `DeviceDriver` em `infrastructure/drivers/`
3. Registro em `DeviceDriverRegistryService`
4. Teste unitário: registry load + mock poll
5. Wireframe operador se `operatorSurface` nova

Sem migration SQL.
