# MES — estados operacionais e paradas (fundação)

> **Status:** Etapa 04 implementada — timer realtime da parada + timeline do run.
> **Owner do domínio MES:** `production-control-api`
> **Owner da telemetria:** `production-pulse-api` (apenas hardware/counter/epoch/saúde)
> **Robustez/recuperação/auditoria/integridade:** Etapa 05 implementada (§9). Homologação industrial: `MES-PHASE-01-HOMOLOGATION.md`.

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

## 9. Robustez, auditoria e integridade (Etapa 05)

### Política de falha do Production Pulse

Telemetria indisponível **não** é máquina parada e nunca cria downtime. A
validação do snapshot é centralizada em
`domain/services/pulse_snapshot.py` → `classify_pulse_snapshot`, com estados
`usable | offline | invalid | unavailable`; nenhum caminho converte
counter/counterEpoch ausentes para `0`.

- **Play**: exige snapshot `usable` (device único do CT, counter/epoch válidos,
  online e sem staleness > 3× `pollIntervalMs`). Rejeita com erro claro ao
  operador.
- **Resume**: exige snapshot `usable` — cria a nova âncora do contador. Sem
  Pulse: run permanece `paused`, downtime aberto, nenhum segmento falso.
- **Pause**: funciona degradado — usa somente o último `pieces_total`
  persistido e as peças já conhecidas do segmento aberto, fecha o segmento sem
  inventar contagem, abre `stopped` + downtime e registra
  `telemetry_fallback_used`.
- **Stop running**: mesma estratégia do Pause (consolida com snapshot
  confiável ou fecha com último valor conhecido e completa em modo degradado).
- **Stop paused**: não depende do Pulse.
- **Poller**: snapshot inválido/offline mantém a última contagem e o segmento
  aberto inalterados; não gera epoch artificial; retenta no próximo ciclo.
- **`get_active`**: falha de telemetria devolve `device.online=false` no
  payload sem derrubar a leitura do run.

`counterEpoch` alterado fecha o segmento com o último valor conhecido e abre
nova âncora — auditado como `counter_epoch_changed` com
`{previousEpoch, newEpoch}`.

### Auditoria MES (V011 `mes_audit_events`)

Tabela append-only: `id, branch, work_center, run_id, action, actor_type,
actor_ref, occurred_at, details JSONB, created_at`. Sem tokens/JWT/segredos.

Ações registradas: `run_started`, `run_paused`, `run_resumed`, `run_stopped`,
`downtime_classified`, `downtime_reason_changed` (com previous/new no
`details`), `counter_epoch_changed`, `telemetry_fallback_used`,
`automatic_downtime_started` (details: `thresholdSeconds`,
`lastCountActivityAt`, `detectedAt`, `idleSecondsAtDetection`) e
`automatic_downtime_ended` (details: `downtimeId`, `endedAt`).
`actor_type=operator` com `actor_ref` = código do operador da sessão;
`system` para eventos sem operador — incluindo as transições automáticas.

A auditoria participa da **mesma transação** da transição: se estado/downtime
faz rollback, nenhuma linha de audit "falso-sucesso" sobrevive. A
classificação (`downtime classify`) também é atômica com sua auditoria via
`conn` compartilhada.

### Integrity check (`MesRuntimeIntegrityService`)

Executado no startup: migrations → integrity check → poller. Somente-leitura;
**nunca auto-repara** (auto-repair inventaria história industrial). Saída:
issues `{severity, issue_code, run_id, branch, work_center}` logadas de forma
estruturada. A API **continua subindo** mesmo com inconsistências — o serviço
precisa estar disponível para diagnóstico/recuperação.

Regras: `running` observado pelo MES exige segmento aberto e OU
`producing` aberto sem downtime OU — desde a detecção automática — `stopped`
aberto com **exatamente uma** parada aberta `source='system'` (parada
automática por inatividade); `running + stopped` com parada de operador, sem
parada ou com `producing` simultâneo continua `CRITICAL`. `paused` exige
`stopped` + downtime aberto e nenhum segmento aberto; `completed/aborted` não podem ter segmento/estado/
downtime abertos; fatos abertos de run A em CT cujo ativo é B = `CRITICAL`
cross-run; run sem nenhum evento MES = `WARNING` legado. Anomalias detectadas
incluem `paused_with_open_producing`, `running_with_open_stopped`,
`open_downtime_of_other_run`, `finished_with_open_state`, entre outras.

### Recuperação após restart

Run/segmento/estados/downtime são fatos persistidos: restart de API,
navegador ou container não cria run novo, não duplica `producing`/`stopped`,
não duplica downtime e não move a âncora. O poller retoma os runs `running`
do banco. O timer volta pelo `startedAt` persistido; o cockpit reconcilia via
HTTP no reconnect do WebSocket (single-flight) — sem polling de timeline.

### Telemetria offline na UI

`device.online === false` exibe o banner "Contador sem comunicação — última
contagem conhecida mantida", visual e semanticamente distinto de "Produção
parada". Pausar/Encerrar seguem disponíveis; o contador congela no último
valor confiável.

## 10. O que NÃO foi feito (fica para fases seguintes)

- abertura de `idle` ao finalizar run — não necessária nesta fase;
- administração do catálogo de motivos;
- nenhum cálculo de OEE/disponibilidade/performance;
- nenhum backfill de histórico;
- nenhuma alteração no Production Pulse;
- threshold dinâmico por ciclo/OP e supervisório consolidado de máquinas
  (a detecção automática existe — ver § 11 — mas sem tuning por item);
- integração da parada MES com TOTVS.

Homologação industrial formal: `MES-PHASE-01-HOMOLOGATION.md`.

## 11. Detecção automática de parada por ausência de peças (extensão da Fase 01)

Enquanto `run.status = running` + estado operacional `producing` + telemetria
Pulse `usable`, o MES observa `last_count_activity_at` do run — o instante do
**último incremento real** de peças (ou o Play, como baseline inicial).

Configuração: `PC_MES_AUTO_DOWNTIME_SECONDS` (default `120`; `0` desabilita).
Definida em `production-control-api/config.py`, propagada pelos exemplos de
ambiente e pelos compose — nunca hardcoded.

### Detecção

A detecção roda dentro do `ProductionRunPollerService` existente (~500 ms),
sem worker extra. A cada tick:

- snapshot Pulse **não `usable`** (offline/invalid/unavailable/stale) → nada
  muda — falha de Wi-Fi/ESP32 **não** é parada de máquina;
- incremento real de peças → `update_run_pieces(..., activity_at=agora)` e, se
  houver parada automática aberta, auto-resume;
- sem incremento → compara `agora − last_count_activity_at` com o threshold.

`last_count_activity_at` é coluna persistida (`V012`), criada no Play
(`NOW()`) e atualizada **somente** quando há incremento — nunca a cada tick.
Runs legados com `NULL`: o primeiro tick com snapshot válido grava o baseline
e só então a janela começa — nenhuma parada retroativa é inventada.

### Abertura da parada automática

Quando o threshold é atingido, em transação + `lock_run()` (revalidando o
baseline depois do lock):

- `producing` fecha em `started_at = last_count_activity_at` — a parada conta
  desde o último golpe, não desde a detecção;
- `stopped` abre com `source='system'`;
- `downtime_event` abre com `source='system'`;
- auditoria `automatic_downtime_started` (`actor_type='system'`) na mesma tx;
- WS `production_run_updated` + `reason='automatic_downtime_started'` com
  `operationalState='stopped'` e o `downtime`.

**Motivo inicial** (dois casos, decididos no momento da abertura):

- `pieces_total == 0` — nenhuma peça contada desde o Play → a parada nasce
  classificada com `reason_code='setup'`, `confirmed=true`,
  `confirmed_by_type='system'` (snapshots do catálogo, como na classificação
  manual). É a hipótese "ainda em preparação": o cockpit mostra "Setup /
  preparação" e o operador pode **alterar** o motivo enquanto a parada segue
  aberta, pelo mesmo endpoint de sempre;
- `pieces_total > 0` — máquina já produziu → `reason_code=NULL`,
  `confirmed=false` (pende classificação, como antes). O audit carrega
  `initialReasonCode` para distinguir os casos.

Estado resultante: `run.status='running'` + `stopped` + parada aberta — o
cockpit mostra "Produção parada" + cronômetro desde `startedAt` e permite
Informar/alterar motivo enquanto parada segue aberta. `paused` continua
reservado ao Pause explícito.

Ticks seguintes são idempotentes: parada já aberta → nenhum fato/evento novo.

**Fatos órfãos de run encerrado**: parada/estado abertos cujo run dono já
terminou (`ended_at` preenchido) são fechados na fronteira real do run
(`ended_at` do dono) no início das transições automáticas — fato operacional
não pode sobreviver ao próprio run e, sem a cura, a parada órfã bloquearia a
detecção do posto para sempre (conflito a cada tick, invisível nas
pendências). Se o dono segue `running`/`paused` o conflito é real e a
transição aborta como antes.

### Retorno automático

Novo incremento real em `running` + `stopped` automático, com um único `at`:

- `downtime.ended_at = at`; `stopped` fecha; `producing` reabre
  (`source='system'`); `last_count_activity_at = at`;
- auditoria `automatic_downtime_ended`; WS `automatic_downtime_ended` com
  `operationalState='producing'`.

O run nunca sai de `running`; nenhum Resume manual é exigido. `paused`
**nunca** auto-resume — o poller só processa `running`.

### Interações

- **Pause durante auto-stop**: `record_run_paused` reutiliza o `stopped` +
  parada abertos (só muda `run.status`) — sem fatos duplicados.
- **Stop durante auto-stop**: exige classificação da parada aberta
  (`DowntimeClassificationRequired`); os fatos são validados **antes** de
  mutar `run.status`, dentro da mesma transação.
- **Decaimento/correção do contador** não é golpe: atualiza `pieces_total` e
  emite `pieces_updated`, mas não mexe no baseline nem auto-resume.

### Snapshot e classificação

`get_active` passa a expor `operationalState` (estado aberto do run),
`pendingDowntime` (parada mais antiga sem classificação, aberta ou já
encerrada — `list_pending_classification`, limite 5) e
`pendingDowntimeCount`. Após o auto-resume, uma parada encerrada sem motivo
reaparece como pendência — inclusive após F5/reconnect — e o cockpit abre o
modal "Por que a produção parou?" sem bloquear a produção.

Classificação: o endpoint legado `POST /runs/{id}/downtime/classify`
continua classificando a parada **aberta**. O novo
`POST /runs/{id}/downtimes/{downtime_id}/classify` classifica uma parada
específica do run — inclusive já encerrada — validando `run_id`, filial/posto
e sessão. `requires_note` e auditoria de operador se aplicam igualmente.

Timeline: os trechos `stopped` automáticos surgem naturalmente
(`source='system'` no item e na parada); durações seguem derivadas de
timestamps — nada de `duration_seconds` persistido.

### Pendências do posto (paradas encerradas sem motivo)

`pendingDowntime` cobre apenas o run ativo. Para paradas de runs já
encerrados no mesmo posto existe a listagem de pendências:

- `GET /public/machine-load/{token}/mes/downtimes/pending?branch&workCenter`
  — requer `X-Delpi-Bench-Session` da mesma filial/CT. Retorna paradas
  **encerradas** e sem classificação (`confirmed=false` ou `reason_code`
  nulo), mais recente primeiro, limite 50, com `runId`, OP, duração e fonte.
- A classificação usa o mesmo endpoint por identidade
  (`POST /runs/{run_id}/downtimes/{downtime_id}/classify`) — a sessão só
  precisa pertencer ao posto; o run não precisa estar ativo.

No cockpit (`ProductionRunControls`), o botão "Paradas sem motivo (n)"
abre a lista (`usePendingMesDowntimes`, reconciliada pelo mesmo
`runUpdatedSignal` do WS — sem polling próprio); itens da timeline do run
ativo sem motivo também são clicáveis e abrem o `DowntimeReasonModal`
mirando aquele `downtime_id`.



## 12. Hotfix — referência temporal unificada do Play

**Defeito confirmado**: create_run_with_segment persistia
last_count_activity_at/run.started_at via NOW() do PostgreSQL, mas
start_run abria o evento producing com self._clock() — um instante
estritamente posterior (lido após o INSERT). Na primeira parada automática
sem nenhuma peça contada, o detector encerrava producing em
max(last_count_activity_at, run.started_at) = o NOW() do INSERT, que
precedia producing.started_at — violando ck_pc_state_events_time_range.
A exceção era engolida pelo tick (mes_tick_run_failed no log) e o run
permanecia apresentando producing para sempre.

Paradas após produção não falhavam porque o incremento atualizava
last_count_activity_at com o relógio da app, já posterior ao início do
producing.

**Correção**: referência temporal unificada — o producing inicial e o
run_started auditável nascem no run.started_at persistido
(_canonical_run_start), mesma origem do baseline de inatividade, na mesma
transação. O relógio da aplicação não participa da origem do Play.

**Runs legados** (abertos antes do hotfix, com producing.started_at
posterior ao baseline): em record_automatic_stopped, sob lock, o instante
de fechamento faz clamp explícito para o started_at do evento aberto —
producing encerra com duração zero no seu próprio início, stopped e o
downtime nascem nesse instante. Sem intervalo negativo e sem duração
inventada; a auditoria registra effectiveStartedAt e
clampedToOpenStateStart=true quando o clamp dispara.

**Adiamento de parada futura**: se o início efetivo calculado pelo clamp
for POSTERIOR ao instante da detecção (producing legado "no futuro"), a
transição é adiada — nenhum estado, downtime ou auditoria é gravado e o
próximo tick reavalia. Sem isso, uma parada criada no futuro faria um
golpe anterior violar a cronologia ao encerrar. Observável via log
mes_auto_downtime_deferred.

**Evidências**: test_future_clamped_stop_is_deferred_and_pulse_still_counts
(parada futura adiada; pulso antes dela conta sem rollback; parada nasce
no instante do producing quando o relógio o alcança),
test_producing_start_after_persisted_play_does_not_break_auto_stop
(relogio adiantado reproduzia CheckViolation real no Postgres; PASS após o
fix) e test_legacy_open_run_with_late_producing_event_auto_stops
(divergencia legada transiciona com clamp) —
PC_TEST_MES_DB=1 no banco de plugins de dev, escopo ZZ-TEST-AUTODT.

**Preservado**: monitoramento desde o Play, run running durante a parada,
único downtime por transição, motivo inicial setup sem peça, auto-resume
no primeiro incremento, baseline não reiniciado por poll vazio, Pulse
offline/inválido não gera parada, kill switch e threshold dinâmico.


## 13. Seleção da fonte de paradas do cockpit (Etapa 1)

**Owner**: production-control-api. O Production Pulse é owner dos
dispositivos e vínculos; o PC é owner da decisão de fonte no cockpit.
Nenhum consumidor acessa o banco do Pulse nem cadastra CTs sensorizados
em paralelo.

**Contrato**: GET /public/machine-load/{token}/downtime-source?branch&workCenter
(operationId get_public_work_center_downtime_source) — somente leitura.

Resposta: data.branch, data.workCenter, data.source
(mes|totvs|unavailable), data.reason, data.referenceAt (UTC, dia civil em
America/Sao_Paulo). Não expõe deviceId, IP, serial nem dados sensíveis.
unavailable é resposta válida — nunca há fallback silencioso para TOTVS.

**Matriz de decisão** (domain/services/downtime_source_selection.py, regra
pura):

- lookup do Pulse falhou/timeout/payload inválido → unavailable
  (source_lookup_unavailable);
- mais de um pulse_counter elegível → unavailable
  (multiple_bound_counters);
- exatamente um vinculado → mes (bound_counter) — independente de
  online/stale; device.online nunca decide fonte;
- zero vínculos + fatos MES no dia civil → mes (mes_activity_today):
  vínculo removido no meio do dia não troca a fonte;
- zero vínculos + nenhum fato MES no dia → totvs (no_bound_counter):
  ausência comprovada.

**Escopo/segurança**: token público do cockpit validado, filial canônica e
CT obrigatoriamente na fila publicada — fora do escopo o lookup de
vínculo nem ocorre. Leitura sem efeitos: não consulta TOTVS, não semeia
fila, não cria run, não escreve fatos.

**Fatos MES do dia**: PostgresMesMonitoringReadRepository
.has_activity_in_period — EXISTS sobre work_center_state_events,
downtime_events e production_runs sobrepondo o dia (sem montar timeline).

**Hardendness do gateway**: ProductionPulseGateway
.fetch_work_center_snapshot agora rejeita payload sem dict/items com
PulseGatewayError — antes, resposta malformada virava items=[] e seria
lida como "sem sensores". Consumidores existentes (start_run/_pick_device,
tick) já tratam PulseGatewayError como indisponibilidade — comportamento
mais correto.

**Etapas futuras**: a timeline diária de paradas MES (Etapa seguinte)
consumirá este contrato para decidir a fonte antes de renderizar; a
interface do cockpit e a substituição dos indicadores TOTVS são etapas
posteriores — nada foi migrado ainda.

**Evidências**: tests/test_downtime_source_selection.py — 24 testes
(unidade + política pura + gateway MockTransport + contrato HTTP +
has_activity_in_period em Postgres real com PC_TEST_MES_DB=1).

**Pendência de governança**: AGENTS.md menciona push direto na main; a
governança vigente deste projeto é revisão por PR. Registrado o conflito —
integração segue o fluxo de PR.

## 14. Etapa 2 — Histórico diário MES do posto no cockpit público

GET /public/machine-load/{token}/mes/work-centers/today?branch&workCenter
(operationId get_public_mes_work_center_today) responde: quais foram os
estados e paradas MES deste CT desde 00h de hoje (civil America/Sao_Paulo)
até agora. Somente leitura; sem efeito em run, fila, contador ou fatos.

**Owner**: production-control-api — dono dos fatos e da linha do tempo.
**Consumidor**: cockpit do operador (Etapa 3 renderizará e habilitará a
classificação na experiência diária; nada foi migrado ainda).

**Reuso (sem nova fonte nem motor paralelo)**:
- PublicWorkCenterDowntimeSourceService (Etapa 1) decide a fonte ANTES da
  consulta: totvs -> resposta controlada sem items (sem lista vazia como
  sucesso); unavailable -> erro 503 explícito, sem fallback; nunca consulta
  TOTVS nesta rota.
- MesIntegrationReadService.get_work_center_timeline — mesmo repositório,
  mesma query S2S; nada de SQL novo nem N+1.
- ProductionRunService.resolve_bench_session — autentica a sessão; o
  service confere (branch, work_center) da sessão == requisitados — token
  público sozinho NÃO basta.

**Segurança (ordem)**: 1) token público (404); 2) filial + CT na fila
publicada (422); 3) X-Delpi-Bench-Session válida (401); 4) sessão do MESMO
(filial, CT) — sessão de outro posto/filial -> 401 sem vazar fatos; 5)
fonte mes. O workCenter do navegador nunca é autoridade. Operador vê a
história do posto (inclusive runs de outros operadores do mesmo CT), não
de outros postos.

**Janela temporal**: from = meia-noite civil SP do dia; to = relógio
oficial do backend (referenceAt). Fato que começou ontem aparece, com
startedAt/endedAt originais preservados; a duração diária efetiva
(effectiveDurationSeconds) é recortada à janela — parada aberta conta até
referenceAt; run encerrado não cresce após ended_at. Intervalo sem evento
MES nunca vira parada inventada.

**DTO data**: branch, workCenter, source, reason, date, timezone, from,
to, referenceAt, summary { producingSeconds, stoppedSeconds, stopCount,
pendingReasonCount }, items[] com stateEventId, runId, productionOrder,
operationCode, state, startedAt, endedAt, source, downtime { id,
reasonCode, reasonLabel, category, note, confirmed, source,
pendingReason }, effectiveDurationSeconds.

**Motivo pendente**: downtime existente com confirmed=false OU
reasonCode ausente. Setup confirmado pelo sistema não é pendência.
stopped sem downtime = fato incompleto: downtime=null, sem identidade
fictícia nem ação de classificação.

**Resumo sem inflação**: producingSeconds/stoppedSeconds somam a UNIÃO
dos intervalos recortados por estado — eventos sobrepostos anômalos não
duplicam duração (registrado via log mes_today_overlap_detected, fatos
históricos nunca corrigidos por leitura). stopCount conta eventos stopped
distintos; pendingReasonCount conta downtimes distintos pendentes.

**Erros estáveis**: 404 token; 422 filial/CT não publicado; 401 sessão
ausente/expirada/de outro posto; 503 fonte unavailable; 200 totvs sem
items (controlado); 200 mes + items=[] + resumo zero = histórico vazio
verdadeiro. Falha no Postgres propaga como erro controlado, nunca
histórico vazio.

**Não implementado aqui** (Etapa 3): renderização no cockpit, substituição
dos indicadores TOTVS somente nos CTs MES, classificação direta na linha
do tempo diária.

**Evidências**: tests/test_public_mes_work_center_today.py — 23 testes
(AC-01..AC-18: política de fonte, janela meia-noite, recorte overnight,
parada aberta, pendência, setup confirmado, identidade preservada,
sobreposição, contrato HTTP 200/401/404/503/totvs controlado, e PG real
com PC_TEST_MES_DB=1: run + pause -> API diária devolve downtime real;
run encerrado permanece no histórico).

## 15. Etapa 3 — Atividade do posto no cockpit do operador (public-hub)

**Objetivo**: expor a API diária da Etapa 2 como experiência do operador —
resumo do dia, faixa temporal e classificação de paradas direto do
histórico, inclusive de runs já encerrados. Sem segunda engine de
timeline, sem duplicar fatos MES, sem regras de negócio no frontend.

**Entrada**: cartão compacto "Atividade do posto" (PostActivityCard) na
tela da fila — visível para todo CT, inclusive sem operações pendentes.
Resume tempo parado / nº de paradas / pendências; sem sessão convida a
identificar o operador; 503 vira "histórico indisponível".

**Detalhe**: `?view=activity` (PostActivityPage), mesmo padrão de
navegação interna de `view=operation|performance`. Mostra
`summary.{producingSeconds, stoppedSeconds, stopCount,
pendingReasonCount}` — valores oficiais da API, nunca recalculados por
soma de linhas —, faixa temporal proporcional entre `from` e `to`
(segmentos por estado MES, cores + legenda; intervalos sem fato ficam
neutros, nunca viram parada) e lista cronológica com estado, horários
reais (parada overnight conserva início de ontem), duração efetiva no
dia, OP/operação, fonte (automatic/manual), motivo, observação e selo
"Sem motivo".

**Classificação**: `downtime.pendingReason` do backend é a semântica
oficial — parada pode ter reasonCode e continuar pendente
(confirmed=false); setup confirmado pelo sistema não é marcado. Botão
"Informar motivo" / "Alterar motivo" abre o DowntimeReasonModal
existente (mesmo catálogo `fetchMesDowntimeReasons`, mesma regra
requiresNote) e grava via `classifyRunDowntime(token, runId,
downtimeId, ...)` — identidade real do item, autorizado pelo backend
para runs encerrados do mesmo CT. Sucesso refaz o GET; falha mantém o
modal com mensagem. Evento `stopped` sem downtime válido aparece como
fato, sem ação que invente identidade.

**Estados**: mes com itens / mes vazio ("nenhum evento") / totvs (posto
não sensorizado, sem histórico fictício nem fallback) / 503 (retry) /
401 (sessão invalidada + convite a identificar) / token-CT inválido /
offline (fetch falha como indisponível). Dados de outro CT nunca
aparecem: estado do hook é chaveado por (token, session, branch,
workCenter) — resposta atrasada é descartada, loading do CT novo.

**Sincronização**: useWorkCenterActivity com single-flight + pending
(refresh durante voo remarca e repete no fim). Refaz o GET em: toque
"Atualizar", transição relevante de run/parada/classificação via
WebSocket existente (`pieces_updated` isolado não dispara), reconexão
WS, retorno de aba e virada do dia civil America/Sao_Paulo. Sem nova
conexão, sem polling fixo. Horários renderizados com Intl em
America/Sao_Paulo — independentes do fuso do tablet; `referenceAt` do
backend orienta os deltas do WS.

**Não implementado aqui** (Etapa 4): substituição das superfícies TOTVS
restantes do cockpit (desempenho, indicadores, históricos legados),
OEE, edição de eventos além do motivo. §14 previa essa substituição
"nos CTs MES" já na sequência da Etapa 2 — divergência registrada: o
plano aprovado a reserva para a Etapa 4.

**Evidências**: src/apps/production-control/PostActivity.test.tsx
(17 Vitest: cliente fetchMesWorkCenterToday, tipos discriminados,
stale-CT, 401 tardio de sessão substituída não invalida a vigente,
totvs/vazio/503/401, card, página, classificação, "aguardando
confirmação" para motivo preenchido-não-confirmado, timer da parada
aberta avançando com o offset ancorado) + workCenterActivity.test.ts
(8 node:test: mapa de estados, legenda, chave de dia civil SP).
Suite public-hub 43/43 Vitest + node:test dos helpers limpo; eslint
dos arquivos novos limpo; vite build verde.

**Rework pós-merge** (mesma Etapa 3): offset do relógio do servidor
passou a ser ancorado uma vez por resposta — recalcular a cada chamada
congelava o cronômetro no referenceAt; 401 de requisição de escopo
substituído (sessão/CT trocados em voo) não invalida mais a sessão
vigente; pendência com reasonCode exibe "aguardando confirmação" em vez
de "sem motivo"; modais de classificação formatam horários em
America/Sao_Paulo em vez do fuso do dispositivo.

## 16. Etapa 4 — Substituição das superfícies TOTVS por MES no cockpit

**Objetivo**: quando o centro de trabalho é sensorizado (Etapa 1 resolve
`source=mes`), todas as superfícies de paradas/atividade do cockpit
passam a usar exclusivamente fatos MES; CT sem sensoriamento preserva os
contratos e indicadores TOTVS legados; fonte indisponível mostra
indisponibilidade explícita — nunca fallback silencioso.

**Resolução de fonte**: `useDowntimeSource` (frontend) consulta
`GET .../public/machine-load/{token}/downtime-source?branch=&workCenter=`
— decisão oficial permanece no backend. Enquanto a fonte não resolve
(`source=null`), nenhuma consulta TOTVS dependente é disparada:
`useWorkCenterPerformance` e `usePublicWorkCenterDowntimeItems` só
executam quando `source==="totvs"`; os leitores MES exigem sessão de
bancada como antes.

**Indicadores do cabeçalho** (fila e detalhe da operação — mesma
política; o detalhe recebe o nó de métricas já resolvido):

- `mes` → `MesDayMetrics`: "Produzindo · hoje", "Parado · hoje",
  "Paradas · hoje" (com selo de motivos pendentes) — rótulos de **dia
  civil**, nunca de turno. Clique nas paradas abre a Atividade do posto;
  produzindo/parado abrem o painel de desempenho.
- `totvs` → `WorkCenterShiftMetrics` legado (eficiência/produzido/
  paradas de turno) e o `DowntimeItemsModal` de apontamentos TOTVS.
- `unavailable`/erro → `SourceStatusMetrics` com mensagem e retry; o
  clique em paradas fica inerte.

**Leitura diária compartilhada**: `CockpitActivityProvider` montado
DENTRO do `OperatorSessionProvider` — um único `useWorkCenterActivity`
(e um único GET `/mes/work-centers/today` por escopo) alimenta o
PostActivityCard, o MesDayMetrics e a PostActivityPage. Classificar uma
parada na página atualiza os indicadores do cabeçalho na mesma
instância. Sem segundo fetch, sem provider global novo fora do escopo.

**Painel "Desempenho do posto"** (`?view=performance`):

- `totvs` → painel legado integral (eficiência de turno/período,
  gráficos e tabela de apontamentos TOTVS).
- `mes` → `MesPeriodPanel` com o **novo contrato**
  `GET .../mes/work-centers/period?branch=&workCenter=&days=` (1–31
  dias, sessão de bancada do mesmo filial/CT): KPIs de produzindo/
  parado/paradas/motivos pendentes no período, "Paradas por motivo"
  e "Tempo parado por dia" (ConfigurableSeriesChart do kit), seletor
  7/14/30 dias, atalho para a Atividade do posto e nota de qualidade
  quando `quality.stopOverlapSeconds > 0` (paradas sobrepostas dividem
  tempo entre motivos — exposto, nunca inventado).
- Sem sessão → convite a identificar o operador (dados MES continuam
  protegidos); `totvs` na resposta → aviso controlado; fonte
  indisponível → mensagem + retry.

**Backend — `PublicMesWorkCenterPeriodService`**: reutiliza a cadeia da
Etapa 2 (token público → filial/CT publicado → sessão de bancada →
resolvedor de fonte) e o `MesIntegrationReadService` para a janela
`[hoje−(dias−1), agora]` em dias civis America/Sao_Paulo. Totais e
série diária usam a **união de intervalos** por estado (sobreposição
nunca infla); paradas que atravessam a meia-noite fatiam o trecho certo
em cada dia; `stopCount` conta eventos únicos no período;
`pendingReasonCount` segue `pendingReason`/confirmed do fato; runs
encerrados entram normalmente; dias sem evento retornam zeros reais —
nada é sintetizado. `source=totvs` responde controlado sem agregados;
indisponível → 503. Não persiste indicadores derivados nem consulta
TOTVS.

**OEE — ARCHITECTURE_DECISION_REQUIRED**: o painel MES não exibe
percentual de eficiência, disponibilidade ou OEE — tempo produzindo não
vira proporção sem denominador (tempo programado, paradas planejadas,
regras de qualidade) aprovado. `MesPerformanceCalculator` /
`MesRunPerformanceService` existem mas medem **ritmo do run**, não
eficiência de turno nem OEE; campos de classificação OEE seguem nulos
no modelo. Lacuna registrada para decisão dos owners de domínio antes
de qualquer indicador percentual.

**Contratos preservados**: `.../performance` e
`.../performance/downtime-items` continuam íntegros para CTs TOTVS e
demais consumidores; nenhum contrato legado foi alterado ou removido.

**Evidências**: `test_public_mes_work_center_period.py` (21 pytest:
contrato, sessão, escopo, sobreposição, overnight, totvs controlado,
limites de período) + suítes MES relacionadas 68 passed; PostActivity.
test.tsx 44 Vitest incluindo "um único GET alimenta cartão e página";
node:test helpers 107/107; eslint do diff = baseline (17 findings
pré-existentes, 0 novos); vite build verde; gates de arquitetura,
boundaries, AuthZ FastAPI, OpenAPI e guardrails de plataforma: 0
findings novos. Validação visual em tablet real: pendente para a
Etapa 5 (homologação industrial).

## 16. Etapa 4 — Substituição das superfícies TOTVS por MES no cockpit

**Objetivo**: quando o centro de trabalho é sensorizado (Etapa 1 resolve
`source=mes`), todas as superfícies de paradas/atividade do cockpit
passam a usar exclusivamente fatos MES; CT sem sensoriamento preserva os
contratos e indicadores TOTVS legados; fonte indisponível mostra
indisponibilidade explícita — nunca fallback silencioso.

**Resolução de fonte**: `useDowntimeSource` (frontend) consulta
`GET .../public/machine-load/{token}/downtime-source?branch=&workCenter=`
— decisão oficial permanece no backend. Enquanto a fonte não resolve
(`source=null`), nenhuma consulta TOTVS dependente é disparada:
`useWorkCenterPerformance` e `usePublicWorkCenterDowntimeItems` só
executam quando `source==="totvs"`; os leitores MES exigem sessão de
bancada como antes.

**Indicadores do cabeçalho** (fila e detalhe da operação — mesma
política; o detalhe recebe o nó de métricas já resolvido):

- `mes` → `MesDayMetrics`: "Produzindo · hoje", "Parado · hoje",
  "Paradas · hoje" (com selo de motivos pendentes) — rótulos de **dia
  civil**, nunca de turno. Clique nas paradas abre a Atividade do posto;
  produzindo/parado abrem o painel de desempenho.
- `totvs` → `WorkCenterShiftMetrics` legado (eficiência/produzido/
  paradas de turno) e o `DowntimeItemsModal` de apontamentos TOTVS.
- `unavailable`/erro → `SourceStatusMetrics` com mensagem e retry; o
  clique em paradas fica inerte.

**Leitura diária compartilhada**: `CockpitActivityProvider` montado
DENTRO do `OperatorSessionProvider` — um único `useWorkCenterActivity`
(e um único GET `/mes/work-centers/today` por escopo) alimenta o
PostActivityCard, o MesDayMetrics e a PostActivityPage. Classificar uma
parada na página atualiza os indicadores do cabeçalho na mesma
instância. Sem segundo fetch, sem provider global novo fora do escopo.

**Painel "Desempenho do posto"** (`?view=performance`):

- `totvs` → painel legado integral (eficiência de turno/período,
  gráficos e tabela de apontamentos TOTVS).
- `mes` → `MesPeriodPanel` com o **novo contrato**
  `GET .../mes/work-centers/period?branch=&workCenter=&days=` (1–31
  dias, sessão de bancada do mesmo filial/CT): KPIs de produzindo/
  parado/paradas/motivos pendentes no período, "Paradas por motivo"
  e "Tempo parado por dia" (ConfigurableSeriesChart do kit), seletor
  7/14/30 dias, atalho para a Atividade do posto e nota de qualidade
  quando `quality.stopOverlapSeconds > 0` (paradas sobrepostas dividem
  tempo entre motivos — exposto, nunca inventado).
- Sem sessão → convite a identificar o operador (dados MES continuam
  protegidos); `totvs` na resposta → aviso controlado; fonte
  indisponível → mensagem + retry.

**Backend — `PublicMesWorkCenterPeriodService`**: reutiliza a cadeia da
Etapa 2 (token público → filial/CT publicado → sessão de bancada →
resolvedor de fonte) e o `MesIntegrationReadService` para a janela
`[hoje−(dias−1), agora]` em dias civis America/Sao_Paulo. Totais e
série diária usam a **união de intervalos** por estado (sobreposição
nunca infla); paradas que atravessam a meia-noite fatiam o trecho certo
em cada dia; `stopCount` conta eventos únicos no período;
`pendingReasonCount` segue `pendingReason`/confirmed do fato; runs
encerrados entram normalmente; dias sem evento retornam zeros reais —
nada é sintetizado. `source=totvs` responde controlado sem agregados;
indisponível → 503. Não persiste indicadores derivados nem consulta
TOTVS.

**OEE — ARCHITECTURE_DECISION_REQUIRED**: o painel MES não exibe
percentual de eficiência, disponibilidade ou OEE — tempo produzindo não
vira proporção sem denominador (tempo programado, paradas planejadas,
regras de qualidade) aprovado. `MesPerformanceCalculator` /
`MesRunPerformanceService` existem mas medem **ritmo do run**, não
eficiência de turno nem OEE; campos de classificação OEE seguem nulos
no modelo. Lacuna registrada para decisão dos owners de domínio antes
de qualquer indicador percentual.

**Contratos preservados**: `.../performance` e
`.../performance/downtime-items` continuam íntegros para CTs TOTVS e
demais consumidores; nenhum contrato legado foi alterado ou removido.

**Evidências**: `test_public_mes_work_center_period.py` (21 pytest:
contrato, sessão, escopo, sobreposição, overnight, totvs controlado,
limites de período) + suítes MES relacionadas 68 passed; PostActivity.
test.tsx 44 Vitest incluindo "um único GET alimenta cartão e página";
node:test helpers 107/107; eslint do diff = baseline (17 findings
pré-existentes, 0 novos); vite build verde; gates de arquitetura,
boundaries, AuthZ FastAPI, OpenAPI e guardrails de plataforma: 0
findings novos. Validação visual em tablet real: pendente para a
Etapa 5 (homologação industrial).
