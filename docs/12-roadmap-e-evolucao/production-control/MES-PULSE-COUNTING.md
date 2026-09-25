# MES shadow — contagem em tempo real (Pulse → Production Control)

> **Status:** implementado (set/2026)  
> **Owner da contagem do run:** `production-control-api`  
> **Owner da telemetria IoT:** `production-pulse-api`  
> **Superfície do operador:** `plugins/public-hub` → `/p/production-control/cockpit/{token}`

Documento canônico da integração entre o contador de golpes do **Pulso de Produção** e o **cockpit do operador** do Portal PCP. Os README das APIs resumem rotas; este arquivo descreve ownership, contratos, fórmula e operação.

---

## Objetivo perceptível

No cockpit público, o operador:

1. escolhe o posto (centro de trabalho);
2. identifica-se (código Protheus);
3. dá **play** na operação da fila;
4. vê a **contagem de peças** subir em tempo real a partir do device Pulse amarrado ao CT;
5. pode **pausar / retomar / encerrar**.

O apontamento oficial no TOTVS (SH6010 / HZA) **continua no coletor**. O run MES é **shadow**: a UI mostra contado × apontado (divergência), sem gravar no Protheus.

---

## Ownership (não misturar)

| Responsabilidade | Pacote | Não fazer |
|------------------|--------|-----------|
| Poll do ESP, continuidade monotônica, `counter` + `counterEpoch` | `production-pulse-api` | Conhecer OP / run / operador |
| Binding device ↔ CT (`device_bindings`) | `production-pulse-api` | — |
| Sessão de bancada, run, segmentos, peças do run | `production-control-api` | Falar HTTP direto com o ESP |
| Fila / HZA / apontamentos (leitura) | `production-control-api` → `api-delpi` | Write SH6010/HZA neste escopo |
| UI play + readout | `plugins/public-hub` (cockpit) | Chamar Pulse direto do browser |

```text
ESP /api/contador
  ← poll  production-pulse-api  (last_metrics.counter + counterEpoch)
  ← S2S   production-control-api  GET /integrations/devices/.../snapshot
  ← HTTP  public-hub cockpit      /public/machine-load/{token}/runs*
```

---

## Decisões travadas

| Tema | Decisão |
|------|---------|
| Identidade no cockpit | Público + código Protheus digitado → sessão opaca (`X-Delpi-Bench-Session`) |
| Conversão golpe → peça | **1:1** (MVP); cavidades fora |
| Fechamento do run | Shadow only — sem write TOTVS |
| Fonte da contagem | Âncora absoluta em `counter` + `counterEpoch` (não `SUM(delta_metrics)` na janela) |
| Integração BFF↔BFF | S2S com `API_DELPI_INTERNAL_SERVICE_TOKEN` + `X-Delpi-Caller-App: production-control-api` |
| Devices no posto | Exatamente **um** `pulse_counter` elegível; caso contrário o play rejeita |

---

## Fórmula de contagem

```text
pieces_segmento = max(0, current_counter − anchor_counter)
  se current_epoch == anchor_epoch

se epoch mudou (reset / set / restore material no Pulse):
  fechar segmento aberto com peças já conhecidas
  abrir novo segmento com âncora = (current_counter, current_epoch)

pieces_total = soma(peças dos segmentos fechados) + peças do segmento aberto
```

**Por que não somar deltas de `readings`:** cada `delta_metrics.counter` é o incremento desde o poll anterior, não desde o instante do play. Somar uma janela civil contamina a borda. O `devices.last_metrics.counter` é atualizado em **todo** poll bem-sucedido (mesmo sem persistir reading).

`counterEpoch` sobe no Pulse em:

- comando `reset` / `set` (`clear_offsets`);
- restore material (power-loss / hardware set).

Consumidor MES fecha o segmento quando o epoch muda.

---

## Modelo de dados (schema `production_control`)

Migration: [`production-control-api/migrations/V008__production_runs_mes_shadow.sql`](../../../production-control-api/migrations/V008__production_runs_mes_shadow.sql)

| Tabela | Papel |
|--------|-------|
| `operator_bench_sessions` | Sessão do operador no posto (token hash + TTL) |
| `production_runs` | Run MES (`running` \| `paused` \| `completed` \| `aborted`) |
| `production_run_segments` | Âncoras `(anchor_counter, anchor_epoch)` por segmento |

Invariante: no máximo um run `running|paused` por `(branch, work_center)`.

---

## Contratos HTTP

### Pulse — S2S (somente BFF)

Auth: `X-Delpi-Service-Token` **ou** JWT com `devices.view`.

| Método | Path | Uso |
|--------|------|-----|
| GET | `/integrations/devices/snapshot?branch=&workCenter=&roleKey=pulse_counter` | Lista devices bound ao CT |
| GET | `/integrations/devices/{deviceId}/snapshot` | Tick do device do run ativo |

Campos relevantes do item: `deviceId`, `counter`, `counterEpoch`, `online`, `status`, `lastSeenAt`, `pollIntervalMs`, `workCenterCode`, `placementKey`.

Binding esperado: `anchor_type=work_center`, `placement_key=wc:{branch}:{workCenterCode}`.

### PCP — público (cockpit)

Base: `/apps/production-control-api/public/machine-load/{token}`  
Token do link: slug configurável (`content/machine_load.json` → `publicCockpit.token`, default `aberto`).  
Writes: header `X-Delpi-Bench-Session` + honeypot `website`.

| Método | Path | Função |
|--------|------|--------|
| POST | `.../bench-sessions` | Abre sessão (operatorCode, workCenter) |
| DELETE | `.../bench-sessions/current` | Encerra sessão |
| POST | `.../runs` | Play |
| POST | `.../runs/{id}/pause` | Pause |
| POST | `.../runs/{id}/resume` | Resume |
| POST | `.../runs/{id}/stop` | Stop → `completed` |
| GET | `.../runs/active?branch=&workCenter=` | Snapshot + peças + device + divergência TOTVS |

Realtime: mesmo WS da fila (`.../ws?branch=`). Evento adicional `production_run_updated` (reason: `run_started`, `pieces_updated`, …). O cliente também faz poll HTTP ~1 s enquanto o run está `running`.

Worker: `ProductionRunPollerService` no lifespan do PCP atualiza peças dos runs `running` e emite o hint WS.

---

## UI

| Peça | Onde |
|------|------|
| Controles play / pause / stop + readout | `plugins/public-hub/.../ProductionRunControls.tsx` |
| Hook sessão + poll | `useProductionRun.ts` |
| Card “Agora nesta bancada” | `CockpitPage.tsx` → `ActiveNowCard` |
| Copy / Ajuda Portal | `plugins/production-control/src/content/copy.ts`, `helpTooltips.ts` |

Sessão fica em `sessionStorage` por filial+posto (`delpi.pcp.cockpit.bench-session.*`).

---

## Runtime / env

| Variável | Quem | Dev típico | Prod típico |
|----------|------|------------|-------------|
| `PRODUCTION_PULSE_API_URL` | PCP | `http://host.docker.internal:80/apps/production-pulse-api` | `http://delpi-production-pulse-api:8000` |
| `PRODUCTION_PULSE_API_TIMEOUT` | PCP | `5` | `5` |
| `PC_PRODUCTION_RUN_POLL_MS` | PCP | `1000` | `1000` |
| `PC_BENCH_SESSION_TTL_HOURS` | PCP | `12` | `12` |
| `API_DELPI_INTERNAL_SERVICE_TOKEN` | ambos | compartilhado | compartilhado |

Em **dev**, o Pulse usa `network_mode: host`; o PCP fica em `delpi-network` — por isso a URL passa pelo gateway no host, não por DNS de container.

Compose: `infra/docker-compose.dev.yml` / `infra/docker-compose.yml` (serviço `production-control-api`).

---

## Pré-condições operacionais

1. Device Pulse habilitado, role `pulse_counter`, **binding ativo** ao CT do posto (`work_center`).
2. Poll Pulse OK (`last_metrics.counter` preenchido).
3. Fila PCP publicada para a filial (snapshot machine-load).
4. Cockpit aberto com token válido e `?branch=01|02`.

---

## Smoke de homologação

```text
1. Admin Pulse: device bound a CT do posto de teste
2. Rebuild: production-pulse-api + production-control-api + public-hub
3. Abrir /p/production-control/cockpit/aberto?branch=01
4. Selecionar o posto
5. Identificar operador → Iniciar contagem na OP do card
6. Incrementar golpes no pad / hardware
7. Ver “Peças contadas” subir; device Online
8. Pausar / Retomar / Encerrar
9. Conferir divergência vs apontado TOTVS (se houver HZA/SH6)
10. Reset no pad durante run → total não corrompe (novo segmento / epoch)
```

Negativos esperados:

- play sem device bound → 422 clara;
- play sem sessão → 401;
- segundo play no mesmo posto → 409;
- dois `pulse_counter` no mesmo CT → 422 pedindo um único device.

---

## Rebuild (dev)

```bash
./infra/scripts/up-dev-sequential.sh --build \
  production-pulse-api production-control-api public-hub
```

---

## Fora do escopo (neste documento / MVP)

- Escrita SH6010 / HZA na api-delpi
- Fator cavidades / peças por golpe ≠ 1
- Validação forte SYS_USR / crachá físico
- Multi-device no mesmo run
- MQTT / push de pulsos / telemetria high-rate no WS do Pulse
- OEE formal derivado do run

---

## Código âncora

| Tema | Path |
|------|------|
| Epoch / continuidade | `production-pulse-api/.../device_monotonic_counter_continuity_service.py` |
| Snapshot S2S | `production-pulse-api/.../integration_device_snapshot_service.py` |
| Rotas S2S | `production-pulse-api/.../routes/integration_routes.py` |
| Fórmula peças | `production-control-api/.../production_run_counting.py` |
| Ciclo de vida run | `production-control-api/.../production_run_service.py` |
| Gateway Pulse | `production-control-api/.../production_pulse_gateway.py` |
| Rotas públicas | `production-control-api/.../public_machine_load_routes.py` |
| Poller | `production-control-api/.../production_run_poller_service.py` |
| UI | `plugins/public-hub/src/apps/production-control/ProductionRunControls.tsx` |

---

## Referências

- [production-control-api/README.md](../../../production-control-api/README.md) — tabela de endpoints públicos
- [production-pulse-api/README.md](../../../production-pulse-api/README.md) — Integrações S2S
- [INTEGRATIONS-TOTVS.md](../production-pulse/INTEGRATIONS-TOTVS.md) — binding CT (Pulse ↔ TOTVS)
- [ADR-002-poll-scheduler-and-lan.md](../production-pulse/ADR-002-poll-scheduler-and-lan.md) — poll pull do device
- [infra/README-ambiente.md](../../infra/README-ambiente.md) — rede host do Pulse em dev
