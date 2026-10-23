# MES — Monitoramento autônomo de parada por CT, independente de OP

> Estado: **implementado — merge `2794554bd` + rework pós-revisão
> (branch `fix/pc-mes-autonomous-downtime-rework`); homologação física
> pendente**.
> TASK_ID: PC-MES-CT-AUTONOMOUS-DOWNTIME. Owner canônico dos fatos MES:
> `production-control-api`. Fonte de telemetria: `production-pulse-api`
> (contrato S2S, nunca banco). Consumidor MFE: `plugins/public-hub`.
> BASE_HEAD: `c7586034f`; rework reancorado em `2e9f95b45`.

## 1. Resumo executivo

Antes desta etapa, o monitoramento automático de parada só existia com um
run MES em `running`/`paused`. A partir daqui, o Production Control passa
a observar **todos os CTs sensorizados** (vínculo `pulse_counter` no
Pulse), mesmo sem operador, sem OP e com o cockpit fechado:

- contador válido incrementando sem run → atividade autônoma
  (`run_id = NULL`, `source = 'system'`);
- contador estável além do threshold vigente → parada autônoma
  (`downtime_events.run_id = NULL`);
- retorno dos pulsos → parada encerrada e retomada registrada;
- `Play` num CT monitorado fecha os fatos autônomos na fronteira do run,
  sem duplicar estados e sem atribuir pulsos antigos à OP;
- parada autônoma aberta ou já encerrada é classificável pela identidade
  real do downtime (escopo da sessão de bancada), sem `runId` fictício.

`EXISTING_EQUIVALENT = YES` para telemetria, eventos MES, repositórios,
poller, catálogo de motivos, timelines e realtime hub →
`REUSE_DECISION = EXTEND`. `TO_INVENTORY → YES` apenas para a observação
durável do contador sem run (nova tabela de cursor, sem duplicar fatos).

## 2. Arquitetura

```
ProductionPulseGateway.fetch_branch_counter_snapshots
  GET /integrations/devices/snapshots?branch=…&roleKey=pulse_counter   (1 GET/filial — sem N+1)
        ↓
ProductionRunPollerService  (poller único — nenhuma rotina física nova)
  └─ MesAutonomousMonitorService.tick_branch
       ├─ allowlist PC_MES_CT_AUTONOMOUS_WORK_CENTERS (* = todos)
       ├─ pg_try_advisory_xact_lock("pc-mes-wc:{branch}:{ct}")   (fail-closed)
       ├─ run running/paused? → SKIP (mecanismo legado preservado)
       ├─ work_center_pulse_observers  (cursor durável por filial+CT)
       └─ domain/services/mes_autonomous_monitoring.decide_autonomous_tick
            (puro, sem IO) → OBSERVE | ACTIVITY | STOPPED | DEGRADED | NOTHING
       └─ MesRunLifecycleService.record_autonomous_*  (mesmo repositório,
          mesma tabela, mesma invariante "1 fato aberto por CT")
       └─ mes_audit_events + machine_load_realtime_hub
```

Decisões-chave:

- **Fail-closed**: sem vínculo, vínculo ambíguo, device offline, snapshot
  inválido/stale, epoch divergente ou regressão de contador ⇒ observação
  degradada persistida no cursor; **nunca** parada inventada.
- **Baseline**: a primeira observação válida só estabelece o cursor —
  nenhuma parada retroativa (AC-10). `started_at` da parada retroage a
  `last_increment_at` observado, nunca a um tempo inventado.
- **Rebaseline pós-degradação** (rework): ao retornar de um trecho
  degradado sem incremento novo, o cursor reancora `last_increment_at`
  no instante do retorno — o intervalo sem telemetria confiável nunca
  entra no cálculo de inatividade nem é imputado como perda. Só se
  aplica quando já havia baseline real; parada autônoma aberta antes da
  falha permanece intacta (observação de qualidade explícita) até a
  atividade real encerrá-la.
- **Arbitragem**: o lock advisory por CT serializa tick autônomo ×
  `start_run`; dentro do lock o monitor recheca run ativo. Handoff é
  mesmo-CT com run ativo até o commit — o tick só vê SKIP.
- **Threshold**: reusa `PC_MES_AUTO_DOWNTIME_SECONDS` — sem ciclo de OP
  inexistente (RQ-03).
- **Rollout**: `PC_MES_CT_AUTONOMOUS_ENABLED` (default **off**) +
  allowlist por CT — homologação incremental (RQ-10).

## 3. Persistência

`migrations/V021__work_center_pulse_observers.sql`
(`production_control.work_center_pulse_observers`):

| coluna | papel |
|---|---|
| `branch, work_center` (PK) | um cursor por CT monitorado |
| `device_id`, `counter_epoch`, `last_counter` | identidade do vínculo/epoch |
| `last_increment_at`, `baseline_established_at` | evidência temporal real |
| `device_online`, `degraded_reason`, `last_seen_at` | observabilidade degradada |

Nenhum fato novo: atividade/parada continuam em
`work_center_state_events`/`downtime_events`/`mes_audit_events` com
`run_id = NULL`.

## 4. Contratos novos

| Contrato | Direção | operation_id |
|---|---|---|
| `GET /integrations/devices/snapshots` | Pulse → PC (S2S) | `list_production_pulse_device_snapshots` |
| `POST /public/machine-load/{token}/mes/downtimes/{id}/classify` | cockpit → PC | classificação por identidade do downtime |
| `GET /public/machine-load/{token}/mes/work-centers` | cockpit → PC | `public_mes_work_centers_sensorized` |

O endpoint legado de classificação por run permanece intocado. O gate de
«CT publicado» dos serviços today/period/downtime-source agora aceita
também CT sensorizado, sem remover autorização de sessão.

## 5. Cobertura

- `tests/test_mes_autonomous_monitor.py` — 23 casos: SKIP com run,
  baseline, activity, stopped, resume, idempotência, epoch swap,
  regressão, offline/ambíguo/stale (degraded, sem parada), allowlist,
  concorrência do try_lock.
- PostgreSQL real (delpi-postgres-plugins): 7/7 — baseline, producing
  `run_id NULL`, downtime `run_id NULL`, idempotência, resume, contenção
  do advisory lock, audit `run_id NULL`.
- Classificação por identidade (aberta/fechada, CT errado negado),
  live WCs sem run (1 query consolidada + autônomos), resolver de fonte
  com CT sensorizado sem fila.
- Pulse: `list_counters_by_branch` (enumeração por filial, filtro de
  role, filial inválida).
- Frontend: `classifiableDowntime` com `runId null`, picker mesclando
  CT sensorizado fora da fila, restore do posto salvo sensorizado.

## 6. Pendências

- Homologação física ESP/Pulse (gate posterior — não declarável sem
  bancada).
- Ativação: `PC_MES_CT_AUTONOMOUS_ENABLED=true` + allowlist por CT.
- Fonte canônica de expediente/turno **não inventariada** — RQ-04 fica
  intencionalmente conservador: inatividade sem evidência não vira perda.
