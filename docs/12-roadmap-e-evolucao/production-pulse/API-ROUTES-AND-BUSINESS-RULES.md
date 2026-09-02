# Rotas da API e regras de negócio — Production Pulse

> **Fonte canônica** deste contrato (rotas + regras).  
> Spec narrativa: [ESPECIFICACAO-PLUGIN.md](./ESPECIFICACAO-PLUGIN.md) · Evolução: [API-MFE-DEVICE-EVOLUTION.md](./API-MFE-DEVICE-EVOLUTION.md) · RBAC: [ADR-003](./ADR-003-rbac-mvp.md)

**Base gateway:** `/apps/production-pulse-api`  
**Envelope:** `{ success, message, data, meta? }`  
**Auth:** JWT em todas as rotas exceto `GET /health`

---

## 1. Mapa de rotas (implementado)

### 1.1 Infra

| Método | Path | Permissão | Regra / efeito |
|--------|------|-----------|----------------|
| `GET` | `/health` | público | Liveness do serviço |

### 1.2 Catálogo

| Método | Path | Permissão | Regra / efeito |
|--------|------|-----------|----------------|
| `GET` | `/catalog/drivers` | `devices.view` | Registry `device_drivers.json` (métricas, commands, `operatorSurface`, thresholds) |
| `GET` | `/catalog/work-centers` | `devices.view` + filial | Proxy BFF → api-delpi SHB010; query `branch`, `search` |

### 1.3 Resumo (painel)

| Método | Path | Permissão | Regra / efeito |
|--------|------|-----------|----------------|
| `GET` | `/summary` | `devices.view` + filial | KPIs: total, online, offline, sem amarração — R9–R12 |

### 1.4 Dispositivos — CRUD

| Método | Path | Permissão | Regra / efeito |
|--------|------|-----------|----------------|
| `GET` | `/devices` | `devices.view` + filial | Lista; query `branch`/`branches`, `anchorType`, `workCenter`, `role`, `enabled`, busca |
| `GET` | `/devices/{id}` | `devices.view` + filial do device | Device + binding vigente + `capabilities` do registry |
| `POST` | `/devices` | `devices.manage` + filial | Cria; `driver_key` → `role_key` do registry (R24); IP único na filial (R3) |
| `PUT` | `/devices/{id}` | `devices.manage` + filial | Replace; filial **imutável** (R7) |
| `PATCH` | `/devices/{id}` | `devices.manage` + filial | Partial (wifi, debounce, token, poll, …) |
| `DELETE` | `/devices/{id}` | `devices.manage` + filial | Soft delete `enabled=false` (R8) |

### 1.5 Binding (amarração)

| Método | Path | Permissão | Regra / efeito |
|--------|------|-----------|----------------|
| `GET` | `/devices/{id}/binding` | `devices.view` | Vigente ou `null` |
| `PUT` | `/devices/{id}/binding` | `devices.manage` | 1 vigente por device (R1); valida R27–R32; fecha anterior |
| `DELETE` | `/devices/{id}/binding` | `devices.manage` | Encerra vigente → device vira rascunho (R5) |
| `GET` | `/devices/{id}/bindings/history` | `devices.view` | Histórico paginado |

### 1.6 Leituras, poll e live

| Método | Path | Permissão | Regra / efeito |
|--------|------|-----------|----------------|
| `GET` | `/devices/{id}/live` | `devices.view` | Lê chip **sem** gravar reading; aplica continuity; status R9–R12 |
| `POST` | `/devices/{id}/poll` | `devices.view` | Lê + persist reading + `last_metrics` (R14) ou falha R13 |
| `POST` | `/devices/poll-all` | `devices.manage` | Poll em massa (só com binding); query `branch`, `role` |
| `GET` | `/devices/{id}/readings` | `devices.view` | Histórico; query `from`, `to`, `metric`, `page`, `pageSize` (máx 500), `sampleIntervalMs` (R45) |

**Poll OK (R14 + continuidade):**

1. Driver `read`  
2. Se métrica monotônica caiu **sem** comando recente → restore hardware/`set` ou offset software (R37)  
3. Floor ≥ `counterSet.min` (R36)  
4. `delta_metrics` para `monotonic:true` (R16)  
5. Insert `readings` + atualiza `last_seen_at` / `last_metrics`

**Live:** mesmos passos de continuity/floor **sem** insert (exceto se no futuro enrich só em memória).

### 1.7 Comandos e teste

| Método | Path | Permissão | Regra / efeito |
|--------|------|-----------|----------------|
| `POST` | `/devices/test-probe` | `devices.manage` | Probe **sem** persistir device (R33); body `branch`, `ip_address`, `driver_key` |
| `POST` | `/devices/{id}/test` | `devices.manage` | Probe device existente |
| `POST` | `/devices/{id}/commands/{commandKey}` | `devices.command` **ou** `devices.manage` (+ filial) | R17–R18, R26, R34; capability do driver |
| `GET` | `/devices/{id}/commands` | `devices.view` | Auditoria paginada |

`commandKey` típicos (capability): `increment`, `decrement`, `reset`, `set`, `configure`, `reboot`, `factory_reset`.

**Após comando OK com métricas:** reading `source=command`; `decrement`/`reset`/`set` → provenance para polls seguintes (R38).

### 1.8 Operador (tablet)

| Método | Path | Permissão | Regra / efeito |
|--------|------|-----------|----------------|
| `GET` | `/operator/placements` | `operator` + filial | Hub; query `branch`, `anchorType`, `search`; só devices elegíveis com binding (R5, R35) |
| `GET` | `/operator/work-centers` | `operator` + filial | Alias: placements com `anchorType=work_center` |
| `GET` | `/operator/placements/{placementKey}/devices` | `operator` + filial | Picker; `operatorEligible=true` |
| `GET` | `/operator/devices/{id}` | `operator` + filial do device | Metadados da superfície (capabilities + lastMetrics) |
| `POST` | `/operator/devices/{id}/commands/{commandKey}` | `operator` + filial | Comando **sem** exigir `devices.view`/`command` (R35, ADR-003) |
| `GET` | `/operator/work-centers/{code}/devices` | `operator` | **308** → placements canônico (ADR-004) |

---

## 2. Rotas planejadas (P2 — não implementadas)

| Método | Path | Permissão | Regra / efeito |
|--------|------|-----------|----------------|
| `GET` | `/operator/placements/{placementKey}/board` | `operator` + filial | Board combo: preview + `alertLevel` + `progress` por device; ordenação danger→warn→ok→offline (R42) |
| `PATCH` | `/devices/{id}/goals` | `devices.manage` + filial | Define metas; body por metric key (R40) |
| *(enrich)* | live / poll / `GET /operator/devices/{id}` | — | Passam a incluir `presentation.alertLevel` (R39) e `goals`/`progress` (R41) quando configurados |

Drivers novos (`esp8266_temp_v1`, …) **não** exigem rota nova: usam as mesmas de devices/poll/operator; só registry + `DeviceDriver`.

Detalhe: [API-MFE-DEVICE-EVOLUTION.md](./API-MFE-DEVICE-EVOLUTION.md) · [OPERATOR-SURFACES-P2.md](./OPERATOR-SURFACES-P2.md).

---

## 3. Regras de negócio

Numeração estável. Implementação deve citar o id da regra em teste quando possível.

### 3.1 Cadastro e amarração

| Id | Regra |
|----|--------|
| **R1** | 1 device → no máximo **1** binding vigente (`effective_to` null). |
| **R2** | 1 âncora → **N** devices. |
| **R3** | IP único por filial. |
| **R4** | Nome único por filial (recomendado / validado se enforced). |
| **R5** | Sem binding vigente = rascunho: fora de hub operador, board e poll-all com binding. |
| **R6** | `work_center_code` preenchido → deve existir no catálogo TOTVS (422). |
| **R7** | Filial do device **imutável** após create. |
| **R8** | Delete = soft (`enabled=false`); fora do scheduler e hub. |
| **R24** | `driver_key` deve existir no registry; API deriva `role_key`. |
| **R25** | `operatorSurface` / commands / metrics vêm do registry — não inventar no use case. |
| **R27** | `anchor_type=work_center` → `work_center_code` obrigatório. |
| **R28** | `anchor_type=machine` → `machine_label` obrigatório; CT opcional. |
| **R29** | `anchor_type=equipment` → `equipment_label` obrigatório; CT opcional. |
| **R30** | `anchor_type=area` → `area_label` obrigatório. |
| **R31** | `anchor_type=standalone` → proíbe CT/máquina/equipamento; `placement_label` = nome do device. |
| **R32** | API compõe `placement_label` / `placement_key` ao salvar binding. |

### 3.2 Polling, conectividade e leituras

| Id | Regra |
|----|--------|
| **R9** | **Online:** dentro da grace (≈ 2× `poll_interval_ms`, piso/teto content) após último poll OK. |
| **R10** | **Offline:** enabled + binding, fora da grace ou nunca poll OK. |
| **R11** | **Disabled:** `enabled=false` — fora de scheduler, hub, KPIs online/offline. |
| **R12** | **Sem amarração:** status `no_binding`; fora do hub; conta no KPI «sem amarração». |
| **R13** | Poll **falho:** `last_error` + attempt; **não** reading; **não** muda `last_seen_at` / `last_metrics`. |
| **R14** | Poll **OK:** limpa erro; atualiza `last_seen_at` + `last_metrics`; insert reading `source=poll`. |
| **R15** | Gauge/telemetria: cada poll OK gera reading mesmo com valor estável (heartbeat). |
| **R16** | `delta_metrics` só para `monotonic:true`. Queda **explicada** (comando) → delta assinado; queda **restaurada** → meta `counter_restored` (sem tratar como reset de operador). |
| **R36** | Contagem lógica/raw **nunca** &lt; `counterSet.min` (piso 0); sync `SET` no chip se raw negativo. |
| **R37** | No **poll**, queda de raw monotônico **sem** comando intencional recente = power-loss → restore (`hardware_set` ou offset software). **Não** usa limiar de magnitude. |
| **R38** | Comando bem-sucedido em `intentionalDecreaseCommands` (`decrement`/`reset`/`set`) dentro de `intentionalDecreaseCommandGraceMs` → poll **aceita** a queda (não restore). |

### 3.3 Comandos e auditoria

| Id | Regra |
|----|--------|
| **R17** | Todo comando gera linha em `device_commands`. |
| **R18** | Comando exige permissão da rota **e** `commandKey` ∈ capabilities do driver. |
| **R19** | Comando que retorna métricas → reading `source=command` quando aplicável. |
| **R26** | Comando fora da capability → **422** (código catalogado). |
| **R34** | Mesma checagem capability na rota admin e operador. |

### 3.4 Segurança e RBAC

| Id | Regra |
|----|--------|
| **R20** | JWT obrigatório exceto `/health`. |
| **R21** | Gate de filial em toda rota com escopo de branch / device.branch. |
| **R22** | MFE **não** chama api-delpi nem IP LAN do chip. |
| **R23** | HTTP LAN só na `production-pulse-api` (ADR-002). |
| **R33** | `test-probe`: só `devices.manage`; rate limit 10/min/usuário. |
| **R35** | `/operator/*`: gate `production-pulse.operator` — **não** exige `devices.view`. Comandos na rota operador bastam com `operator`. |

### 3.5 Apresentação e multi-device (P2 — planejado)

| Id | Regra |
|----|--------|
| **R39** | `alertLevel` (`ok`/`warn`/`danger`/`stale`) calculado na **API** a partir de `thresholds` + métricas; MFE não recalcula. |
| **R40** | Metas (`goals`) só via `devices.manage`; operador somente lê `progress`. |
| **R41** | `progress.pct` / `state` calculados na API (`metrics` + `goals`). |
| **R42** | Board do posto: só devices `operatorEligible` + binding; ordenação danger → warn → ok → offline. |
| **R43** | Superfície UI escolhida por `capabilities.operatorSurface` — **proibido** ramificar por `driver_key` no MFE. |
| **R44** | Novo medidor = entrada no registry + `DeviceDriver` + (se preciso) surface; **sem** rota CRUD nova. |
| **R45** | Série do gráfico de histórico: quando o período tem mais leituras que o `pageSize`, o MFE envia `sampleIntervalMs` e a API devolve **uma leitura por bucket** cobrindo o intervalo inteiro — não só o fim da janela (LIMIT DESC). Tick do eixo X segue o **span** (não o poll). |

---

## 4. Códigos HTTP (resumo)

| Situação | HTTP |
|----------|------|
| OK | 200 / 201 |
| Validação / capability / probe falho de negócio | 422 (+ `error.code` no JSON) |
| Sem permissão / filial | 403 |
| Device não encontrado | 404 |
| Conflito (IP duplicado, etc.) | 409 |
| Redirect legado operador | 308 |

Textos PT: `device_api_messages.json` / validation content — não hardcoded no domínio.

---

## 5. Matriz permissão × ação

| Ação | `operator` | `devices.view` | `devices.manage` | `devices.command` |
|------|:----------:|:--------------:|:----------------:|:-----------------:|
| Hub / picker / surface GET | ✓ | — | — | — |
| Comando na rota `/operator/.../commands` | ✓ | — | — | — |
| Painel, readings, live, poll 1 | — | ✓ | ✓ | — |
| CRUD, binding, poll-all, test-probe, goals PATCH | — | — | ✓ | — |
| Comando na rota `/devices/.../commands` | — | — | ✓ | ✓ |
| Catálogo drivers / work-centers | — | ✓ | ✓ | — |

Detalhe: [ADR-003](./ADR-003-rbac-mvp.md).

---

## 6. Diagrama de dependência (poll)

```text
POST /devices/{id}/poll
        │
        ├─ R5/R8/R11: device enabled + (para scheduler) binding
        ├─ Driver.read
        ├─ R37/R38: provenance → restore ou accept_decrease
        ├─ R36: floor
        ├─ R16: delta
        └─ R14: persist reading + last_metrics
                 └─ (P2) R39/R41 enrich alertLevel + progress
```

---

## 7. Referências de código

| Área | Path |
|------|------|
| Devices | `production_pulse_app/interface/http/routes/device_routes.py` |
| Operator | `…/routes/operator_routes.py` |
| Catalog | `…/routes/catalog_routes.py` |
| Summary | `…/routes/summary_routes.py` |
| Poll / restore | `…/application/services/device_poll_service.py` |
| Continuity | `…/domain/services/device_monotonic_counter_continuity_service.py` |
| Commands | `…/application/services/device_command_service.py` |
| Registry | `…/content/device_drivers.json` |
