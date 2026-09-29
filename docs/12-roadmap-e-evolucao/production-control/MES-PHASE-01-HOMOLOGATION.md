# MES — Fase 01: Homologação industrial

> Matriz formal de homologação manual da Fase 01 (Estados e Paradas).
> Nenhum cenário físico pode ser marcado PASS sem execução real com evidência.
> Status inicial de todos os cenários: **PENDENTE**.

**Legenda de resultado:** `PASS` · `FAIL` · `BLOQUEADO` · `N/A`

---

## Roteiro de execução

1. Provisionar bancada de teste: 1 ESP32/contador Pulse amarrado a 1 CT com fila
   publicada; operador identificado no cockpit.
2. Executar os cenários **em ordem** — vários dependem de estado deixado pelo
   anterior.
3. Coletar evidências: foto/vídeo do cockpit, linhas de `mes_audit_events`,
   `work_center_state_events`, `downtime_events`, `production_run_segments`
   e logs da API (grep por `mes_`).

Consultas de apoio (schema `production_control`):

```sql
SELECT action, actor_type, actor_ref, occurred_at, details
  FROM mes_audit_events WHERE run_id = :run ORDER BY occurred_at;

SELECT state, started_at, ended_at FROM work_center_state_events
 WHERE run_id = :run ORDER BY started_at;

SELECT reason_code, confirmed, started_at, ended_at FROM downtime_events
 WHERE run_id = :run ORDER BY started_at;

SELECT anchor_counter, anchor_epoch, pieces, started_at, ended_at, end_reason
  FROM production_run_segments WHERE run_id = :run ORDER BY started_at;
```

---

## Matriz de cenários

| # | Cenário | Pré-condição | Passo a passo | Resultado esperado | Evidência | Resultado |
|---|---------|--------------|---------------|--------------------|-----------|-----------|
| 1 | Play normal | Fila publicada, device online, operador identificado | Clicar Play na operação | Run `running`; estado `producing` aberto; audit `run_started`; contador zera a partir da âncora | Screenshot + audit + state_event | PENDENTE |
| 2 | Contagem por hardware | Run `running` | Acionar sensor do ESP32 N vezes | `piecesTotal` incrementa por hardware; `pieces_updated` chega via WS | Vídeo + payload WS | PENDENTE |
| 3 | Pause | Run `running` | Clicar Pausar | Run `paused`; `producing` fechado; `stopped` + downtime abertos; painel "Produção parada" com timer | Screenshot + audit `run_paused` | PENDENTE |
| 4 | Classificação | Run `paused` com downtime aberto | Informar motivo no modal | Downtime classificado no **mesmo** registro; audit `downtime_classified`; WS `downtime_classified` | Query downtime + audit | PENDENTE |
| 5 | Resume | Run `paused` classificado | Clicar Retomar | Downtime/`stopped` fechados; novo `producing`; nova âncora do contador; audit `run_resumed` | state_events + segmentos | PENDENTE |
| 6 | Stop | Run `running` ou `paused` classificado | Clicar Encerrar | Run `completed`; todos os fatos fechados; audit `run_stopped`; cockpit volta à fila | Query + audit | PENDENTE |
| 7 | Múltiplas paradas | Run `running` | Pause → classificar → Resume → Pause (outro motivo) → classificar → Resume → Stop | N downtimes distintos no mesmo run, cada um ligado ao seu `stopped`; timeline mostra todos | Timeline + downtimes | PENDENTE |
| 8 | Reload durante produção | Run `running` | F5 no navegador | Run reaparece contando; sem duplicar estado/downtime | Antes/depois dos fatos | PENDENTE |
| 9 | Reload durante parada | Run `paused` | F5 | Downtime aberto reaparece; timer retoma do `startedAt` original; motivo preservado | Screenshot timer | PENDENTE |
| 10 | Restart da API durante produção | Run `running` | `docker restart production-control-api` | Poller retoma o mesmo run; contagem continua; **nenhum** `producing`/run/segmento duplicado; integrity check sem CRITICAL para o run | Log startup + segmentos | PENDENTE |
| 11 | Restart da API durante parada | Run `paused` | Reiniciar API | Downtime segue aberto; timer correto após reload; Resume funciona | Fatos + Resume OK | PENDENTE |
| 12 | Perda do WebSocket | Run `running` | Derrubar WS (rede/proxy) mantendo cockpit aberto | UI segue utilizável; contagem pode ficar estática ou cair em fallback HTTP; sem erro destrutivo | Console + UI | PENDENTE |
| 13 | Retorno do WebSocket | Cenário 12 | Restaurar WS | Uma reconciliação HTTP; contagem/timeline convergem; sem GET duplicado de timeline | Network tab | PENDENTE |
| 14 | ESP32 offline durante produção | Run `running` | Desligar ESP32 | Banner "Contador sem comunicação"; run continua `running`; **sem** downtime criado; contador congela | Screenshot + downtimes | PENDENTE |
| 15 | Retorno do ESP32 | Cenário 14 | Religar ESP32 | Contagem retoma no próximo ciclo do poller sem salto artificial | pieces_total contínuo | PENDENTE |
| 16 | Pause com Pulse indisponível | Run `running`, API do Pulse derrubada | Clicar Pausar | Pause conclui em modo degradado; `stopped`+downtime criados; audit `telemetry_fallback_used`; contagem preserva último valor | Audit + pieces_total | PENDENTE |
| 17 | Stop com Pulse indisponível | Run `running`, Pulse fora | Clicar Encerrar | Run `completed`; segmento fechado com último conhecido; audit `telemetry_fallback_used` | Audit + segmentos | PENDENTE |
| 18 | Resume sem Pulse | Run `paused` classificado, Pulse fora | Clicar Retomar | Erro claro ao operador; run continua `paused`; downtime segue aberto; nenhum segmento novo | Erro UI + fatos | PENDENTE |
| 19 | Reset/counterEpoch do contador | Run `running` | Reiniciar firmware/reset do ESP32 (novo `counterEpoch`) | Segmento anterior fechado (`end_reason=epoch_change`); nova âncora; sem peças negativas/duplicadas; audit `counter_epoch_changed` | Segmentos + audit | PENDENTE |
| 20 | Sessão expirada | Run ativo; expirar `operator_bench_sessions` | Tentar ação no cockpit | 401 → formulário de identificação reaparece; run preservado | Screenshot | PENDENTE |
| 21 | Troca de operador no mesmo CT | Run ativo, sessão expirada/encerrada | Novo operador se identifica | Mesmo run continua; nenhum run novo criado; novas ações auditadas com novo `actor_ref` | Audit actor_ref | PENDENTE |
| 22 | Duas abas/cockpits no mesmo CT | Run ativo | Abrir segunda aba no mesmo CT | Ambas veem o mesmo run; ação em uma reflete na outra via WS; sem conflito | Duas telas | PENDENTE |
| 23 | Duplo clique nas ações | Run ativo | Duplo clique em Pausar/Retomar/Encerrar | Uma única transição efetiva; segundo clique = conflito/no-op, sem fatos duplicados | Fatos únicos | PENDENTE |
| 24 | Motivo obrigatório / Outro com observação | Downtime aberto | Selecionar motivo `other`/requer nota sem nota → depois com nota | Sem nota: rejeitado com mensagem; com nota: classificado | UI + downtime.note | PENDENTE |
| 25 | Alteração posterior do motivo | Downtime classificado | "Alterar motivo" para outro motivo | Mesmo downtime atualizado; audit `downtime_reason_changed` com previous/new | Audit details | PENDENTE |
| 26 | Run atravessando troca de turno | Run `running` iniciado no turno A | Manter run durante virada de turno | Contagem/estados contínuos; nenhum encerramento automático | Timeline completa | PENDENTE |
| 27 | Relógio do operador incorreto | Run `paused` | Atrasar/adiantar relógio do PC do operador | Timer usa `referenceAt` do servidor; duração não distorce | Vídeo timer | PENDENTE |
| 28 | Restart dos containers | Run `running` e outro `paused` | `docker compose restart` da stack | Ambos recuperados; sem fatos duplicados; integrity OK | Log + fatos | PENDENTE |
| 29 | Verificação da auditoria | Ciclo completo executado | Consultar `mes_audit_events` do run | Sequência `run_started→…→run_stopped` presente, actor correto, degraded sinalizado quando aplicável | Dump audit | PENDENTE |
| 30 | Verificação da timeline completa | Run encerrado com N paradas | Abrir "Linha do tempo" | Todos os trechos producing/stopped com durações coerentes; motivos e notas exibidos; totais consistentes com fatos | Screenshot + queries | PENDENTE |

---

## Verificação pós-rodada (integridade)

Após a bateria, inspecionar o banco (somente-leitura):

```sql
-- deve retornar 0 linhas: fatos abertos órfãos
SELECT 'state' src, id, run_id FROM work_center_state_events
 WHERE ended_at IS NULL
   AND run_id NOT IN (SELECT id FROM production_runs WHERE status IN ('running','paused'))
UNION ALL
SELECT 'downtime', id, run_id FROM downtime_events
 WHERE ended_at IS NULL
   AND run_id NOT IN (SELECT id FROM production_runs WHERE status IN ('running','paused'));
```

E revisar o log de startup por `mes_integrity_issue severity=CRITICAL`.

## Critério de encerramento da Fase 01

Tecnicamente: para qualquer run observado pelo MES deve ser possível afirmar
quando começou, quanto produziu, quando/por que parou, quanto tempo parou,
quando retomou, quem executou as ações, quando encerrou e se alguma transição
ocorreu sem telemetria confiável — com consistência preservada após falhas
normais de infraestrutura.

**IMPLEMENTAÇÃO concluída ≠ HOMOLOGAÇÃO concluída.** A Fase 01 só se considera
homologada quando os 30 cenários forem executados em bancada real com
evidência registrada.
