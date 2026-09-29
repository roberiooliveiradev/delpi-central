# MES — estados operacionais e paradas (fundação)

> **Status:** Etapa 04 implementada — timer realtime da parada + timeline do run.
> **Owner do domínio MES:** `production-control-api`
> **Owner da telemetria:** `production-pulse-api` (apenas hardware/counter/epoch/saúde)
> **Robustez/recuperação/homologação:** Etapa 05 — *não implementada ainda*

Documento canônico do modelo MES de estados do centro de trabalho e paradas.
A contagem de peças Pulse → run permanece documentada em
[MES-PULSE-COUNTING.md](MES-PULSE-COUNTING.md) e **não depende** destas tabelas.

---

## 1. Objetivo

Persistir **fatos** que permitam reconstruir a timeline operacional de cada
centro de trabalho: quando estava livre, produzindo ou parado, por qual motivo,
vinculado a qual run/OP/operação — base auditável para Disponibilidade,
Performance, Qualidade e OEE futuros.

## 2. Três conceitos que não se confundem

| Conceito | Owner | Valores |
|---|---|---|
| Ciclo de vida do run | `production_runs.status` | `running`, `paused`, `completed`, `aborted` |
| Estado operacional do CT | `work_center_state_events.state` | `idle`, `setup`, `producing`, `stopped`, `planned_stop` |
| Saúde da telemetria | Pulse (`device.online`/`status`) | `online`, `stale`, `offline` |

**Device offline ≠ máquina parada.** Telemetria e estado produtivo são
dimensões independentes; nenhuma regra do modelo lê `device.online` para
resolver estado operacional.

## 3. Modelo

```mermaid
erDiagram
    production_runs ||--o{ work_center_state_events : "run_id"
    work_center_state_events ||--o{ downtime_events : "state_event_id"
    production_runs ||--o{ downtime_events : "run_id"
    downtime_reason_catalog ||--o{ downtime_events : "reason_code"
```

### `downtime_reason_catalog`

Catálogo governado de motivos. `code` é a identidade estável; `label` pode
mudar sem perder histórico. `active=false` desativa sem apagar (FK RESTRICT).

| Campo | Tipo | Nota |
|---|---|---|
| `code` | VARCHAR(40) PK | identidade estável |
| `label` | VARCHAR(120) | texto visual |
| `category` | VARCHAR(40) | agrupamento |
| `default_planned` | BOOLEAN NULL | NULL = classificação OEE não governada |
| `default_counts_as_availability_loss` | BOOLEAN NULL | idem |
| `requires_note` | BOOLEAN | ex.: `other` exige observação |
| `active`, `sort_order` | | catálogo ordenado, soft-delete |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

Seeds (idempotentes, `ON CONFLICT DO NOTHING`): `machine_mechanical`,
`machine_electrical`, `tool`, `raw_material`, `quality`, `setup`,
`maintenance`, `no_operator`, `logistics`, `break`, `cleaning`,
`other` (`requires_note`). Todos com classificação OEE **NULL** — nenhuma
fonte canônica do repo define ainda quais motivos são planejados ou contam
como perda de disponibilidade; inventar contaminaria indicadores futuros.

### `work_center_state_events`

Fatos temporais do estado operacional. `ended_at IS NULL` = estado aberto
(atual). `run_id` nullable — estados sem run (ex.: `idle`, `planned_stop`)
serão legítimos na Etapa 02+. `source`: `operator` | `system` | `recovery` |
`integration`.

### `downtime_events`

A parada MES. Nasce **sem motivo** (`reason_code NULL`, `confirmed=false`) —
no Pause o operador classifica depois. `planned` e
`counts_as_availability_loss` são **snapshots da classificação no momento da
aplicação**: mudança futura no catálogo não reinterpreta histórico.

`state_event_id` vincula explicitamente a parada ao evento `stopped`
(opcional; sem relacionamento circular — a parada referencia o estado).

Duração **não é persistida**: deriva-se de `ended_at − started_at`
(`NOW() − started_at` enquanto aberta). Persistir fatos, derivar indicadores.

## 4. Invariantes (banco + domínio)

| Invariante | Onde |
|---|---|
| ≤ 1 estado aberto por `(branch, work_center)` | índice parcial `UNIQUE ... WHERE ended_at IS NULL` + `MesStateConflict` |
| ≤ 1 parada aberta por `(branch, work_center)` | índice parcial `UNIQUE ... WHERE ended_at IS NULL` + `DowntimeConflict` |
| `ended_at >= started_at` | CHECK + validação de domínio |
| `confirmed` exige `reason_code` + `confirmed_at` | CHECKs + `validate_downtime_event` |
| `confirmed_at` só existe com `confirmed` | CHECK + domínio |
| FKs protegem histórico | `ON DELETE RESTRICT` (run, state event, reason) |
| Timestamps absolutos | TIMESTAMPTZ + domínio rejeita naive |

**Sem backfill inventado:** a migration cria estruturas e o catálogo, e deixa
as tabelas de eventos **vazias**. Runs históricos não viram `producing`
retroativos — a timeline MES só registra o que ela observar a partir da
Etapa 02.

## 5. Camadas

| Camada | Arquivo |
|---|---|
| Estados/origens/validações | `domain/services/mes_operational_state.py` |
| Erros | `domain/errors.py` (`InvalidMesEvent`, `MesStateConflict`, `DowntimeConflict`, `DowntimeNotFound`) |
| Ports | `domain/ports/work_center_state_repository.py`, `downtime_event_repository.py`, `downtime_reason_repository.py` |
| Orquestração | `application/services/mes_run_lifecycle_service.py` |
| Adapter | `infrastructure/persistence/postgres_mes_repository.py` |
| Migration | `migrations/V010__mes_state_and_downtime_foundation.sql` |

**Transações:** os adapters aceitam `conn` opcional; quando fornecida, não
fazem commit próprio. O `PostgresProductionRunRepository` expõe
`transaction()` (contextmanager: commit ao sair, rollback em exceção) e
`lock_run()` (`SELECT ... FOR UPDATE`). Toda transição do run abre **uma**
transação compartilhada cobrindo run + segmentos + fatos MES.

**Concorrência:** `lock_run` serializa Pause/Resume/Stop do mesmo run; os
índices únicos parciais continuam a última barreira e violações viram erros
de domínio. `update_run_pieces` só atualiza runs `running` — um tick do
poller concorrente nunca sobrescreve a contagem consolidada por uma
transição. A leitura HTTP ao Pulse acontece **antes** de abrir a transação
(nenhum I/O externo dentro dela).

## 6. Lifecycle implementado (Etapa 02)

```text
PLAY   → cria run + segmento → abre PRODUCING (source=operator, run_id)
PAUSE  → consolida peças → fecha segmento → run=paused
         → fecha PRODUCING → abre STOPPED → cria downtime (motivo NULL)
RESUME → encerra downtime → fecha STOPPED → abre PRODUCING
         → reabre segmento (nova âncora Pulse) → run=running
STOP   → consolida peças (se running) → fecha segmento → run=completed
         → encerra downtime/estado abertos do run
```

Cada transição usa um único timestamp de transição (`at`) para todos os
fatos criados juntos. Orquestração em
`application/services/mes_run_lifecycle_service.py` (`MesRunLifecycleService`),
composta no `pc_composer` junto ao `ProductionRunService`. Nenhum endpoint
novo; o contrato WS (`run_started`/`run_paused`/`run_resumed`/`run_stopped`/
`pieces_updated`) e o poller de 500 ms permanecem inalterados.

### Política para dados legados e inconsistências

- **Run criado antes da Etapa 02** (sem nenhum evento de estado observado):
  o Pause/Stop passa a gravar fatos reais a partir daquele instante
  (`stopped` + `downtime` no Pause são fatos novos, não backfill); o Resume
  de um run pausado "pré-MES" apenas abre `producing` — o que o MES não
  observou, não é inventado.
- **Inconsistência observada** (estado aberto de outro run, parada ausente
  quando o `stopped` existe, estado diferente do esperado para a transição):
  erro de domínio controlado (`InvalidMesEvent`/`MesStateConflict`/
  `DowntimeConflict`) e rollback completo. Nunca sobrescrever nem inventar.

## 7. Classificação do motivo (Etapa 03)

A parada nasce no Pause com `reason_code = NULL`, `confirmed = false` — o
`started_at` da Etapa 02 continua sendo a fonte oficial do início. A
classificação apenas confirma o motivo, **sem alterar o início**.

### Endpoints públicos do cockpit

| Rota | Descrição |
|---|---|
| `GET /public/machine-load/{token}/mes/downtime-reasons` | Catálogo ativo: `{ items: [{ code, label, category, requiresNote }] }`. Frontend usa `code` como identidade, `label` só para exibição. |
| `POST /public/machine-load/{token}/runs/{run_id}/downtime/classify` | Confirma **ou altera** o motivo da parada aberta. Body: `{ reasonCode, note }` + `X-Delpi-Bench-Session`. Nunca cria outra parada. |
| `GET /public/machine-load/{token}/runs/active` | Snapshot do run agora inclui `downtime` (view da parada aberta com `reasonCode`, `reasonLabel`, `confirmed`), cobrindo reload/navegação/reconexão sem endpoint extra. |

`MesDowntimeClassificationService` (application) valida sessão, vínculo
run↔parada, motivo existente e ativo, `requires_note`, e aplica os snapshots
`planned` / `counts_as_availability_loss` a partir do catálogo — o cliente
nunca envia esses campos nem `confirmed_at`/`confirmed_by_ref`
(`confirmed_by_ref` = `operator_code` da sessão).

Após classificar, é emitido `production_run_updated` com
`reason = "downtime_classified"` no WebSocket existente, permitindo que
outros cockpits do mesmo CT sincronizem sem polling novo.

### Guarda de qualidade do dado

Com parada MES **observada e aberta**:

- `Resume`/`Stop` exigem `reason_code != NULL` e `confirmed = true`; caso
  contrário `DowntimeClassificationRequired` (409 — "Informe o motivo da
  parada antes de continuar.");
- runs **legados** (sem downtime MES observado) não são bloqueados — a
  política de não inventar histórico da Etapa 02 é preservada.

### Distinção: parada MES × parada TOTVS

`downtime_events` = fato MES realtime desta produção (classificável aqui).
`/performance/downtime-items` = histórico/indicador de horas improdutivas do
ecossistema TOTVS — conceito diferente, **não reutilizado** para classificação.

## 8. Timer e timeline (Etapa 04)

### Princípio

```text
PERSISTIR FATOS → DERIVAR TEMPOS E INDICADORES
```

Nenhum `duration_seconds`, tempo acumulado ou OEE é persistido. Toda duração
é derivada de `started_at`/`ended_at` no momento da leitura.

### Endpoint

`GET /public/machine-load/{token}/runs/{run_id}/timeline`
(header `X-Delpi-Bench-Session`)

Contrato:

```json
{
  "runId": "...",
  "branch": "01",
  "workCenter": "CT-35",
  "status": "paused",
  "referenceAt": "2026-09-28T23:20:00+00:00",
  "summary": {
    "elapsedSeconds": 3600,
    "producingSeconds": 3200,
    "stoppedSeconds": 400,
    "stopCount": 2
  },
  "items": [
    {
      "id": "...",
      "state": "stopped",
      "startedAt": "...",
      "endedAt": null,
      "durationSeconds": 245,
      "source": "operator",
      "downtime": {
        "id": "...",
        "reasonCode": "raw_material",
        "reasonLabel": "Falta de material",
        "category": "material",
        "confirmed": true,
        "note": null
      }
    }
  ]
}
```

- `MesRunTimelineService` (application) monta: eventos de estado do run +
  downtimes associados por `state_event_id`, ordenados cronologicamente.
- `referenceAt` = relógio do backend; eventos abertos (`endedAt = null`) usam
  `referenceAt` na duração. O frontend estima o "agora" do servidor com o
  offset `referenceAt − Date.now()` — o relógio local do operador não distorce
  o timer, e a aba em background nunca perde tempo.
- `summary` deriva apenas producing/stopped/stopCount — sem OEE.
- `stopped` sem downtime (inconsistência histórica) não quebra a UI
  ("Motivo não disponível").

### Frontend

- `DowntimeElapsedTimer`: `elapsed = serverNow() − startedAt`, tick visual de
  1 s recalculando sempre do timestamp oficial; formato `HH:MM:SS` sem limite.
- `useRunTimeline`: fetch inicial + reconciliação por WS
  (`run_started`/`run_paused`/`run_resumed`/`run_stopped`/`downtime_classified`),
  single-flight com coalescing; `pieces_updated` **não** recarrega a timeline;
  reconnect faz uma única reconciliação HTTP.
- `ProductionRunTimeline`: faixa proporcional compacta + histórico legível em
  seção expansível "Linha do tempo" dentro de `ProductionRunControls` — mesmo
  componente no card e no detalhe.

Sem polling periódico de timeline; o trecho aberto evolui localmente.

## 9. O que NÃO foi feito (fica para a Etapa 05+)

- abertura de `idle` ao finalizar run — não necessária nesta fase;
- administração do catálogo de motivos;
- nenhum cálculo de OEE/disponibilidade/performance;
- nenhum backfill de histórico;
- nenhuma alteração no Production Pulse;
- detecção automática de parada / microparadas;
- integração da parada MES com TOTVS;
- robustez/recuperação/auditoria e homologação industrial (Etapa 05).
