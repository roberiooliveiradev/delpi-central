# Plano de evolução — API e frontend para novos dispositivos

> **Status:** planejamento (set/2026)  
> **Âncora implementada:** contador `esp8266_counter_v1` + superfície `counter_pad`  
> **Segundo tipo (padrão a copiar):** gauge `esp8266_gauge_v1` + `gauge_readout`  
> **UX P2:** [OPERATOR-SURFACES-P2.md](./OPERATOR-SURFACES-P2.md) · [WIREFRAMES.md](./WIREFRAMES.md)  
> **Registry:** [DEVICE-DRIVERS.md](./DEVICE-DRIVERS.md)

Este documento transforma o que aprendemos com **golpes** (e o que o mercado faz em IoT/MES leve) em um **plano de evolução** da `production-pulse-api` e do MFE `production-pulse` — sem reinventar o pipeline a cada sensor.

---

## 1. O que o contador já provou (baseline)

```text
Firmware HTTP  →  DeviceDriver  →  Poll / Command
                      ↓
              device_drivers.json (capabilities)
                      ↓
         last_metrics + readings + audit
                      ↓
         OperatorDeviceSurface (operatorSurface)
```

| Capacidade | Onde vive hoje | Lição |
|------------|----------------|-------|
| Catálogo declarativo | `device_drivers.json` + registry | Novo tipo = JSON + driver HTTP; **sem** migration por métrica |
| Poll / live / histórico | `DevicePollService` + readings JSONB | Histórico já é genérico |
| Comandos + auditoria | `DeviceCommandService` + `device_commands` | Capability-gated; pad só se `commands` listar |
| Continuidade monotônica | `device_monotonic_counter_continuity_service` | Só métricas `monotonic: true` + provenance de comando |
| Piso zero | `counterSet.min` + floor no continuity | Limites no content JSON, não hardcoded |
| Operador tablet | hub → picker → surface por `operatorSurface` | **Nunca** ramificar MFE por `driverKey` |
| RBAC | `operator` vs `devices.*` | Operador comanda na rota operador; manage no admin |
| Conteúdo PT | `device_api_messages.json`, validation JSON | Textos/limites fora do Python/TS de regra |

**Já generalizado:** CRUD, binding/placement, scheduler, catalog HTTP, surface router, thresholds no gauge.

**Ainda counter-específico (dívida a generalizar na evolução):**

| Dívida | Hoje | Alvo |
|--------|------|------|
| Restore / offset | chaves `counter` / `counterRaw` / `counterOffset` | genérico por métrica `monotonic` (`{key}Raw` / `{key}Offset` **ou** mapa interno único) |
| Payload `set` | só `counter` | `set` por metric key do registry |
| Labels MFE | `deviceDisplay` / `detailDisplay` hardcoded | `capabilities.metrics[].labelPt` + unit da API |
| KPI painel | deltas `pulse_counter` | `period_aggregation` por `roleKey` (já parcial) |
| Default form | `esp8266_counter_v1` | último driver usado / sem default rígido |
| `preferHardwareSet` | no JSON, pouco usado no Python | honrar flag no poll |

---

## 2. Padrão de mercado (o que copiar)

| Padrão industrial | Aplicação no Pulse |
|-------------------|--------------------|
| **Device profile / capability model** (OPC UA, MQTT Sparkplug B) | `device_drivers.json` = profile; MFE só lê `capabilities` |
| **Retain no edge** + servidor como verdade lógica | Contador: API restore + (futuro) EEPROM no chip; sensores: só leitura |
| **HMI por tipo de sinal** (ISA-101) | `operatorSurface` distintos (pad / tile / anel / board) |
| **Alarm vs data** separados | `presentation.alertLevel` na API; banner no MFE — sem recalcular limiar no browser |
| **Setpoint / target no servidor** | `goals` + `progress.pct` na API |
| **Um posto, N instrumentos** | Placement board (`placement_combo`) |
| **Driver plug-in** | Classe `DeviceDriver` + register no startup |

**Anti-padrões a evitar**

- `if driver_key == "esp8266_…"` no use case ou no React  
- Presenter/UI por path de firmware  
- Meta/% calculada só no MFE  
- Novo schema SQL por cada métrica nova  

---

## 3. Arquitetura alvo (evolução)

```text
                    ┌─ device_drivers.json ─┐
                    │ role · metrics · cmds │
                    │ surface · thresholds  │
                    │ goalsPolicy · restore │
                    └──────────┬────────────┘
                               ▼
┌────────────┐   read/cmd   ┌─────────────────┐   enrich    ┌──────────────────┐
│  Firmware  │─────────────▶│  DeviceDriver   │────────────▶│ Presentation     │
│  / PLC     │              │  (HTTP/Modbus)  │             │ alertLevel       │
└────────────┘              └────────┬────────┘             │ progress / goals │
                                     │                      └────────┬─────────┘
                                     ▼                               │
                            Poll + Command                           │
                            continuity (se monotonic)                │
                                     │                               │
                                     ▼                               ▼
                            Postgres readings ◀──────────────── metadata no live/poll
                                     │
                                     ▼
                    MFE: OperatorDeviceSurface(surface)
                         + Admin: schema-driven tiles/charts
```

**Princípio:** API entrega **fato + apresentação mínima** (`metrics`, `alertLevel`, `progress`); MFE é **render-only** nas regras de negócio.

---

## 4. Evolução da API — fases

### E-API.0 — Endurecer o baseline (pré-requisito)

| # | Entrega | Arquivos / contrato |
|---|---------|---------------------|
| 0.1 | Honrar `preferHardwareSet` no poll | `device_poll_service.py` |
| 0.2 | Labels/units só do registry nas responses de device/catalog | serialization + capabilities |
| 0.3 | Documentar extensão «novo driver» com checklist CI | este doc + DEVICE-DRIVERS |
| 0.4 | Gate: teste «driver stub no JSON sem crash no registry» | pytest |

**Pronto quando:** gauge e counter usam o mesmo caminho de capabilities; nenhum label de métrica inventado no serializer.

### E-API.1 — Profiles de sensor (temperatura / rotação / pressão)

| # | Entrega | Notas |
|---|---------|-------|
| 1.1 | Entradas JSON `esp8266_temp_v1`, `esp8266_rotation_v1`, `esp8266_pressure_v1` | stubs já esboçados em DEVICE-DRIVERS |
| 1.2 | Drivers HTTP espelhando gauge (read-only) | `infrastructure/drivers/*` + `register_device_drivers` |
| 1.3 | `presentation.alertLevel` / `alertMetricKey` no poll e live | a partir de `thresholds` |
| 1.4 | Firmware de referência **só doc** (ou sketch `.ino` separado) | não misturar com contador |

**Não fazer:** continuity/restore em métricas não monotônicas.

### E-API.2 — Goals e progress

| # | Entrega |
|---|---------|
| 2.1 | Coluna/json `goals` no device (migration V00N) **ou** tabela `device_goals` |
| 2.2 | Serviço transversal `DeviceGoalProgressService` (sem nome de rota) |
| 2.3 | Enrich em live/poll/operator GET: `goals` + `progress` |
| 2.4 | `PATCH /devices/{id}/goals` (`devices.manage`) |

Contrato: ver [OPERATOR-SURFACES-P2.md § Metas](./OPERATOR-SURFACES-P2.md).

### E-API.3 — Board do posto + telemetria

| # | Entrega |
|---|---------|
| 3.1 | `GET /operator/placements/{key}/board` — preview + alert + progress por device |
| 3.2 | Ordenação danger → warn → ok → offline |
| 3.3 | Role `telemetry_bundle` + driver multi-métrica (cap 6 metrics) |

### E-API.4 — Generalizar monotônico (pós-contador)

| # | Entrega |
|---|---------|
| 4.1 | Restore/offset por `metrics[].key` com `monotonic: true` (não só `counter`) |
| 4.2 | `set` payload aceita metric key do registry |
| 4.3 | Remover ramificações `if "counter"` restantes no poll/command |

### E-API.5 — Protocolos além de HTTP ESP (P3)

| # | Entrega |
|---|---------|
| 5.1 | Port `DeviceDriver` estável; adapter Modbus TCP / MQTT |
| 5.2 | Gateway dedicado se necessário (bounded context) — **não** regra no MFE |

---

## 5. Evolução do frontend — fases

### E-MFE.0 — Render-only capabilities

| # | Entrega |
|---|---------|
| 0.1 | Labels/ícones/units de `capabilities.metrics` (eliminar hardcode de golpes/rpm onde possível) |
| 0.2 | `resolveOperatorSurface` tipado com union estável + fallback `gauge_readout` |
| 0.3 | Teste estrutural: zero `if (driverKey === 'esp8266_counter_v1')` em páginas |

### E-MFE.1 — Novas superfícies operador

| Surface | Componente | WF |
|---------|------------|-----|
| `temperature_focus` | `OperatorTemperatureStage` | WF-PP-OP-TEMP |
| `rotation_ring` | `OperatorRotationStage` | WF-PP-OP-ROTATION |
| `telemetry_stack` | `OperatorTelemetryStack` | (stack de tiles) |

Router: `OperatorDeviceSurfacePage` — **switch só em `operatorSurface`**.

Overlays compartilhados:

- `OperatorAlertBanner` (ALERT)
- `OperatorGoalStrip` (GOAL / PCT)

### E-MFE.2 — Board combinado

| # | Entrega |
|---|---------|
| 2.1 | Rota `/operator/placements/:key/board` |
| 2.2 | Atalho «Ver posto» no picker |
| 2.3 | Cards com alert chip + mini barra % |

### E-MFE.3 — Admin alinhado

| # | Entrega |
|---|---------|
| 3.1 | Detalhe: tiles/gráficos por métricas do capabilities (já parcialmente schema-ish) |
| 3.2 | Form: edição de thresholds/goals (manage) |
| 3.3 | Histórico: presets datetime (já feitos) + métrica select do capabilities |

### E-MFE.4 — Conteúdo

| # | Entrega |
|---|---------|
| 4.1 | Chaves `PP_HELP.operator.temp*` / `rotation*` / `combo*` / `goal*` / `alert*` |
| 4.2 | Sync docs `content/helpTooltips.ts` → plugin |

---

## 6. Matriz de fluxos transversal (obrigatória)

| Fluxo | API | MFE | Fase |
|-------|-----|-----|------|
| Poll automático | scheduler + continuity | — | baseline |
| Live operador | GET live + alert/progress | surface refresh | E-API.1–2 + E-MFE.1 |
| Comando pad | command + provenance | CounterPad | baseline |
| Cadastro novo tipo | catalog drivers | form select | E-API.1 |
| Alerta limiar | enrich presentation | banner/chip | E-API.1 + E-MFE.1 |
| Meta turno | goals + progress | GoalStrip | E-API.2 + E-MFE.1 |
| Board posto | `/board` | COMBO | E-API.3 + E-MFE.2 |
| Histórico admin | readings | DeviceHistoryTab | baseline (+ métricas) |
| Offline | connectivity | offlineBanner | baseline |
| Simulate/preview | N/A Pulse | — | fora |

---

## 7. Checklist «novo dispositivo» (receita)

### API

1. Entrada em `device_drivers.json` (`roleKey`, `metrics`, `commands`, `operatorSurface`, `operatorEligible`, `thresholds?`, `counterRestore?` se monotonic).
2. Classe `*Driver` em `infrastructure/drivers/` + registro em `register_device_drivers.py`.
3. Teste: registry load + read mock + (se cmds) execute mock.
4. Se monotonic: cobrir provenance/floor nos testes de continuity.
5. Se thresholds: teste `alertLevel` no enrich.
6. Se goals: teste `progress.pct`.
7. Atualizar DEVICE-DRIVERS.md + firmware ref (doc).

### MFE

1. Se `operatorSurface` **nova**: componente + case no `OperatorDeviceSurfacePage`.
2. Se surface **existente** (`gauge_readout`): só cadastrar driver — zero UI.
3. Helps `PP_HELP` + section intros se seção nova.
4. Vitest surface router + build plugin.
5. Wireframe já listado em WIREFRAMES (ou adicionar).

### Não fazer

- Branch por `driverKey` no React ou use case.
- Texto PT no driver Python.
- Migration por métrica.
- Calcular %/alerta só no browser.

---

## 8. Ordem de entrega sugerida (commits lógicos)

```text
E-API.0 / E-MFE.0   →  limpar dívida counter (capabilities-first)
E-API.1 / E-MFE.1   →  temp + rotation (+ alert banner)
E-API.2             →  goals/progress
E-MFE.1 overlays    →  GoalStrip + % no contador existente
E-API.3 / E-MFE.2   →  board do posto
E-API.4             →  monotônico genérico (quando 2º contador aparecer)
E-API.5             →  Modbus/MQTT (P3)
```

Alinhamento com ROADMAP: bloco **P2** em [ROADMAP.md](./ROADMAP.md) · UX em [OPERATOR-SURFACES-P2.md](./OPERATOR-SURFACES-P2.md).

---

## 9. Critérios de pronto do plano (doc → execução)

- [ ] Todo device novo passa pelo checklist §7 sem patch pontual.
- [ ] MFE sem `driverKey` em switch de UI.
- [ ] API: `alertLevel` / `progress` testados quando features ligadas.
- [ ] Contador atual **não regride** (provenance, floor, pad, histórico).
- [ ] Homologação: 1 posto com contador + temperatura + rotação no board.

---

## 10. Referências

| Doc | Uso |
|-----|-----|
| [OPERATOR-SURFACES-P2.md](./OPERATOR-SURFACES-P2.md) | UX surfaces, alertas, metas |
| [WIREFRAMES.md](./WIREFRAMES.md) | ASCII TEMP/ROTATION/COMBO/… |
| [DEVICE-DRIVERS.md](./DEVICE-DRIVERS.md) | Registry + stubs |
| [ADR-002](./ADR-002-poll-scheduler-and-lan.md) | Poll / LAN |
| [ADR-003](./ADR-003-rbac-mvp.md) | RBAC operador |
| [SCHEMA.md](./SCHEMA.md) | readings JSONB |
| [DESIGN-FRONTEND.md §9](./DESIGN-FRONTEND.md) | Shell operador |
