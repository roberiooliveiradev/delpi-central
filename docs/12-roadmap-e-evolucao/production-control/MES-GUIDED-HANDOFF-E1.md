# MES — Troca guiada de OP no cockpit (E1: backend e contrato)

> Estado: **implementado e validado em testes — aguardando revisão**.
> TASK_ID: PC-MES-GUIDED-HANDOFF-E1. Escopo deste documento: E1 apenas —
> a interface guiada do cockpit é a Etapa 2 e não foi iniciada.
> Base factual: main @ d114f9153.

## 1. Resumo executivo

Uma única operação de negócio, controlada pelo backend, encerra o run em
execução, consolida a contagem na fronteira Pulse e inicia exatamente um
novo run na próxima operação elegível da fila **PUBLISHED** do mesmo CT.

- EXISTING_EQUIVALENT = YES para: transação/lock (transaction(),
  lock_run FOR UPDATE), segmentos/âncoras (anchor_counter,
  anchor_epoch, pieces_from_anchor), count events append-only,
  fatos MES (MesRunLifecycleService), sessão de bancada, auditoria,
  realtime notify, taxonomia de erros e envelope HTTP.
- EXISTING_EQUIVALENT = NO para: idempotência durável por requestId
  (só equivalentes em memória/estado) e para resolução CT-scoped da
  próxima elegível na PUBLISHED (public_operation_run_context não
  restringe por CT — lacuna confirmada).
- REUSE_DECISION = EXTEND no production-control-api: novos métodos
  no ProductionRunService, novo resolver puro de domínio, FOR UPDATE
  na publicação e uma tabela mínima de idempotência (V020).

## 2. Contrato (router público existente)

| Método | Path | operation_id |
|---|---|---|
| GET | /public/machine-load/{token}/runs/{run_id}/handoff-preview?branch&workCenter | get_public_run_handoff_preview |
| POST | /public/machine-load/{token}/runs/{run_id}/handoff | confirm_public_run_handoff |

Autenticação: token do cockpit + header X-Delpi-Bench-Session válida no
escopo branch + work_center (mesma regra das rotas de run atuais).

### Prévia (leitura pura)

Retorna currentRun (mesmo envelope de GET /runs/active), nextOperation
(identidade + descrição + saldo + posição na fila, ou null), available
e block ({code, message} quando indisponível). Não muta run, contagem
nem fila. A decisão da próxima operação é sempre do backend.

### Confirmação

Body: {requestId: uuid, branch, workCenter, expectedNext: {productionOrder, operationCode}}.
O backend **recalcula** o destino sobre a linha PUBLISHED travada e confere
expectedNext — a prévia nunca é autorização.

Resposta: {requestId, replayed, transitionAt, boundary: {counter, counterEpoch}, auditId, completedRun, newRun}.

Erros: 401 sessão inválida; 404 run fora do escopo / sem publicação;
409 com data.code ∈ {no_next_operation, current_not_in_queue,
queue_changed, balance_unknown, run_not_active, device_mismatch,
epoch_conflict, request_conflict} (classificação pendente via
DowntimeClassificationRequired); 422 entrada inválida ou Pulse
indisponível; 502/503 dependências conforme política vigente.

## 3. Seleção do sucessor (RQ-02)

domain/services/machine_load_handoff.resolve_handoff_next — função pura:

- fila = operações visíveis da PUBLISHED (transfers aplicadas, retiradas
  filtradas) restritas ao mesmo CT, na ordem publicada pelo PCP;
- a operação do run precisa estar na fila — current_not_in_queue senão;
- varredura após a posição atual: saldo conhecido <= 0 ignora; saldo
  **desconhecido bloqueia** (balance_unknown — nunca autorização
  automática); primeiro saldo conhecido > 0 é o alvo; fim da fila →
  no_next_operation;
- identidade canônica branch + work_center + production_order +
  operation_code com normalização vigente (operation_identity);
- a fonte é a PUBLISHED vigente — nunca WORKING nem TOTVS.

Lacuna corrigida neste diff: public_operation_run_context e
public_operation_run_quantity agora aceitam work_center e o _queue_lookup
do composer o repassa — o contexto congelado no Play passa a ser o da
operação no CT do posto, não a primeira ocorrência da fila.

MachineLoadService.public_handoff_next_operation aplica transfers e
retiradas e aceita publication_row — na confirmação, a resolução roda
sobre a linha travada FOR UPDATE, serializando com republicação do PCP.

## 4. Fronteira de contagem (RQ-03)

Uma **única amostra Pulse** (counter, counterEpoch do device elegível)
consolida o run anterior **e** ancora o primeiro segmento do novo run. A
peça de fronteira pertence sempre ao run anterior — sem timestamps por
golpe, sem contagem dupla. Divergência de counterEpoch com o segmento
aberto (epoch_conflict) ou device trocado (device_mismatch) **bloqueia**
a troca sem fabricar peças — não há caminho degradado como no Stop manual.

## 5. Atomicidade (RQ-04)

HTTP externo (Pulse + tempo padrão) acontece antes da transação. Dentro de
uma única transaction():

    lock_run FOR UPDATE → idempotência (get) → status do run
    → PUBLISHED FOR UPDATE → re-resolução + confere expectedNext
    → consolidação (segmento aberto + baseline locked vs observado)
    → record_run_finished (classificação obrigatória) → count event
    → set_run_status(completed, segmento end_reason='handoff')
    → create_run_with_segment (âncora = amostra única)
    → record_run_started (mesmo instante at) → auditoria run_handoff +
      run_started → insert do registro idempotente → COMMIT

Qualquer exceção faz rollback integral de todos os fatos. O mesmo instante
at fecha e abre os estados MES na fronteira temporal única.

## 6. Idempotência e concorrência (RQ-05)

production_control.production_run_handoff_requests (V020): request_id
PK + request_hash (sha256 de runId+branch+CT+expectedNext) + response
JSONB, gravada na mesma transação. Replay com mesmo hash devolve a resposta
original com replayed=true; hash diferente → request_conflict. O
perdedor de duas confirmações concorrentes com o mesmo requestId recebe
o resultado gravado; requestId novo sobre run encerrado →
run_not_active, nunca segundo run. Serialização com o poller: o lock do
run + a regra de baseline (_resolve_count_observation) fazem o total
persistido prevalecer sobre observação stale.

## 7. Eventos

run_stopped + run_started notificados após o commit (mesmo hub das
rotas atuais). Replay não reemite. Auditoria: run_handoff no run
anterior (com requestId, fronteira e newRunId) + run_started no novo.

## 8. Migração

V020__production_run_handoff_requests.sql — nova tabela + end_reason
ganha 'handoff' (nova migration; V008 imutável intocada).

## 9. Riscos residuais / limitações

- Saldo elegível vem da **publicação** (não do HZA vivo) — evita HTTP
  dentro da transação; balance_unknown cobre payload incompleto.
- Stop manual continua disponível quando não há sucessora — a ausência de
  próxima OP nunca gera Stop automático.
- Homologação E2E com Pulse real e publicação viva: pendente de staging.
