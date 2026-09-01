# Integrações TOTVS — production-pulse-api → api-delpi

> **Regra:** MFE **nunca** chama api-delpi. TOTVS entra só via **gateway HTTP** na production-pulse-api.  
> **Princípio:** CT/recurso TOTVS são **atalhos opcionais** — dispositivo pode amarrar só a **máquina** ou **equipamento** sem SHB010.

---

## Matriz — o que vem de onde

| Dado no plugin | Origem | Obrigatório? | Notas |
|----------------|--------|--------------|-------|
| **Dispositivo IoT** (IP, driver, leituras) | Hardware LAN + Postgres | **Sim** — entidade central | Não TOTVS |
| **`anchor_type` + labels** | Supervisor no form | **Sim** para operação | `machine`, `equipment`, `work_center`, … |
| **`placement_label`** | API compõe ao salvar | Sim (derivado) | Hub operador + agrupamento painel |
| **CT (`work_center_code`)** | TOTVS `SHB010` | Só se `anchor_type=work_center` **ou** bloco TOTVS preenchido | Validado api-delpi |
| **Recurso / ferramenta** | TOTVS | Opcional | P1 |
| **Máquina / equipamento** | Cadastro operacional local | Sim quando anchor = machine/equipment | Texto livre MVP |

---

## CT TOTVS — atalho, não pré-requisito

Use quando o sensor está num **posto PCP** ou quando quiser cruzar com fila/apontamento futuro.

| Cenário | CT no binding |
|---------|---------------|
| Contador na prensa CT-53 | **Obrigatório** (`anchor_type=work_center`) |
| Rotação ventilador HVAC | **Vazio** — `anchor_type=equipment` |
| Temp motor auxiliar | **Vazio** — `equipment_label` |
| Sensor no torno + contexto PCP | `anchor_type=machine` + CT **opcional** no bloco TOTVS |

### Rota catálogo CT

`GET /production/appointments/work-centers?branch=` → proxy BFF `GET /catalog/work-centers`

Validação: **422** só se `work_center_code` **foi informado** e não existe na SHB010.

---

## Fluxo cadastro — ventilador (sem CT)

```text
1. POST /devices { name: "ESP vent A", ip, driver: esp8266_gauge_v1 }
2. PUT /binding {
     anchor_type: "equipment",
     equipment_label: "Ventilador exaustão setor A"
     // work_center_code omitido
   }
3. API → placement_label = "Ventilador exaustão setor A"
4. Poll → readings.metrics = { rpm: 1180 }
5. Operador hub → card «Ventilador exaustão setor A» → gauge readout
```

## Fluxo cadastro — prensa (com CT)

```text
PUT /binding {
  anchor_type: "work_center",
  work_center_code: "CT-53",
  work_center_name: "Usinagem CNC",
  equipment_label: "Sensor golpe principal"  // opcional, enriquece
}
```

---

## O que fica no Postgres (sempre)

```text
devices          — hardware
device_bindings  — anchor_type, placement_label, CT opcional, máquina/equipamento
readings         — rpm, °C, counter, …
```

---

## Referências

- [SCHEMA.md § anchor_type](./SCHEMA.md)
- [ESPECIFICACAO-PLUGIN.md §7.1](./ESPECIFICACAO-PLUGIN.md) — regras R27–R32
- [production-appointments.md](../../../api-delpi/docs/api/production-appointments.md) — SHB010
