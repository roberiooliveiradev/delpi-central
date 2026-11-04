# Alimentador de Linha — Etapa 1: fila PUBLISHED

**TASK_ID:** `PC-LINE-FEEDER-PUBLISHED-QUEUE-E1`  
**Status:** implementado (fundação de leitura)  
**Owner:** `production-control-api` (`LineFeederService` + `MachineLoadPublicationRepositoryPort`)

## Inventário (E1.S1)

| Capacidade | EXISTING_EQUIVALENT | REUSE_DECISION | Owner |
|---|---|---|---|
| Persistência PUBLISHED | YES | REUSE | `MachineLoadPublicationRepositoryPort` / Postgres |
| Visibilidade + saldo aberto do cockpit | YES | REUSE | `visible_operations` + `operation_balance_state` / `_has_open_operation_balance` |
| Leitura autenticada no Alimentador | NO | EXTEND | `LineFeederService.get_published_queue` |
| HTTP `published-queue` | NO | EXTEND (rota aditiva) | `GET /line-feeder/published-queue` |
| Tempo padrão / setup / conversão | YES (api-delpi) | REUSE na **Etapa 2** | ver dependências abaixo |

`/line-feeder/requirements` continua no snapshot **WORKING** + corte por `scheduled_*` — **sem cutover nesta etapa**.

## Contrato implementado

```http
GET /line-feeder/published-queue?branch=01&workCenter=
operationId: get_line_feeder_published_queue
Auth: JWT + production-control.line-feeder.view + view.filial-{01|02}
```

Resposta (envelope `ok`):

- `publication.generation_id`, `publication.publication_revision` (opaca, de `row_version`/xmin — detecta LIVE sem nova geração)
- `work_center_queues[]` com `operations[]` na **ordem publicada**, `sequence_position` 1-based por CT
- `operation_id` literal `branch|work_center|production_order|operation_code` (zeros à esquerda preservados)
- `pending_qty` + `balance_state` (`open`|`unknown`; `closed` omitido como no cockpit) + `balance_source`
- `queue_status`: `available` | `empty` (publicação existe sem elegíveis)
- Sem publicação: **404** — **nunca** fallback para WORKING

## Regras

1. Fonte única: `machine_load_publications` (PUBLISHED).
2. Sem refresh/publish/regeneração no caminho do Alimentador.
3. Ordem = array pós-retiradas; não usar `scheduled_date`/`scheduled_start_time` para sequenciar.
4. Mutações LIVE (`update_payload`) mudam `publication_revision` com o mesmo `generation_id`.
5. Somente leitura; RBAC do Alimentador (não token público do cockpit, não `machine-load.view` admin).

## Dependências da Etapa 2 (não implementadas aqui)

| Conceito | Fonte canônica | Lacuna E1 |
|---|---|---|
| Tempo por peça / ciclo | api-delpi `GET /production/orders/{op}/operations/{oper}/standard-time` (`get_production_operation_standard_time`); doc `api-delpi/docs/api/padroes-totvs/apontamentos-tempo-padrao.md` | Não consultado pelo Alimentador |
| Setup | mesmo contrato (`setup_seconds`) | Idem |
| Conversão peça (MI) | `pieces_conversion_factor` no payload + playbook unidades Protheus | Campo exposto quando presente; motor de horas não usa |
| Snapshot MES de tempo | `production_run_standard_time.py` | Escopo de runs MES, não do Alimentador |

## Rastreabilidade RQ

| RQ | AC | Evidência |
|---|---|---|
| RQ-E1-01 | WORKING divergente não altera leitura | `test_working_reordered_does_not_affect_published_queue` |
| RQ-E1-02 | Ordem = operador / publicação | `test_project_preserves_published_order_*`, LIVE/new publish |
| RQ-E1-03 | Identidade + saldo desconhecido | zeros à esquerda; `test_closed_balance_excluded_unknown_kept` |
| RQ-E1-04 | LIVE + nova publicação | testes LIVE/`row_version` e nova geração |
| RQ-E1-05 | RBAC filial + aditivo | HTTP 403/404; `/requirements` intacto |
| RQ-E1-06 | Doc tempos padrão | esta seção |

## Fora de escopo (confirmado)

Cálculo de horas, proporcionalização de empenhos, novas coletas, cutover de `/requirements`, UI, migrations novas.
