# Alimentador de Linha — Etapa 2: motor de horizonte

**TASK_ID:** `PC-LINE-FEEDER-HORIZON-E2`  
**Status:** implementado (backend somente leitura)  
**Depende de:** [LINE-FEEDER-PUBLISHED-QUEUE-E1.md](./LINE-FEEDER-PUBLISHED-QUEUE-E1.md) (`68068fa5a1`)

## Inventário / reuso

| Capacidade | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| Fila PUBLISHED | YES | REUSE (`list_visible_published_queues` / publication repo) |
| Saldos SH6/SC2 lote | YES | REUSE (`fetch_machine_load_operation_balances`) |
| Tempo padrão | YES | REUSE (`fetch_operation_standard_time` + `normalize_standard_time_snapshot`) |
| Motor horizonte | NO | NEW (`line_feeder_horizon.allocate_work_center_horizon`) |
| HTTP preview | NO | EXTEND (`POST /line-feeder/horizon/preview`) |

**Não** reutilizar `POST /machine-load/horizon/preview` (ampliação SH8 no WORKING).

## Contrato

```http
POST /line-feeder/horizon/preview
operationId: preview_line_feeder_horizon
Auth: JWT + production-control.line-feeder.view + view.filial-{01|02}
```

Body:

```json
{
  "branch": "01",
  "workCenters": ["CT-A", "CT-B"],
  "hoursPerWorkCenter": 3
}
```

`hoursPerWorkCenter` aplica-se **a cada** CT (orçamentos independentes).

Limites (`line_feeder.json`): max 24h/CT, 40 CTs, 500 operações/request, 200 chamadas standard-time.

Erros: 403 RBAC, 404 sem publicação, 409 `HorizonPreviewStale` (revisão mudou), 422 validação, 502 saldos.

## Algoritmo

Por CT, na ordem PUBLISHED:

1. Saldo vivo `operation_pending_qty` (não o snapshot).
2. `pending <= 0` → pula (não consome horizonte).
3. Saldo desconhecido / ST inválido → **para** o CT (`incomplete`); não salta para a próxima.
4. Setup (política abaixo) + `physical = pending × pieces_conversion_factor`.
5. `max_pieces = floor(tempo_produtivo / ideal_cycle_seconds)` (conservador).
6. Parcial se `covered < pending`; encerra o CT após parcial.
7. Offsets relativos `offset_start_seconds` / `offset_end_seconds` (não horário de fábrica).

Fórmula: `remaining_seconds = physical_pieces × ideal_cycle_seconds`  
(`ideal_cycle_seconds` já é por peça física — **uma** conversão).

## Política de setup

| Condição | Ação |
|---|---|
| `operation_produced_qty > 0` | setup = 0 (`waived_produced`) |
| `operation_produced_qty == 0` | inclui `setup_seconds` (`applicable`) |
| produzido ausente | inclui setup + `setup_uncertain` / CT `incomplete` |

Base: tempo previsto TOTVS (setup fixo uma vez) + SH6 como prova de produção iniciada.

## Fontes / qualidade

- Fila: PUBLISHED (`generation_id` + `publication_revision` / xmin).
- Saldos: `balances_as_of` + lote operation-balances.
- Tempo: `get_production_operation_standard_time` (S2S via gateway com service headers).

## Dependências da Etapa 3

Prévia já traz por operação: `covered_qty`, `remaining_outside_qty`, sequência, tempos, completeness por CT. Etapa 3 consome este contrato para materiais — **não** recalcular horizonte no MFE.

## RQ → evidência

| RQ | Teste |
|---|---|
| RQ-E2-01 orçamento/CT | `test_three_work_centers_independent_budgets` |
| RQ-E2-02 ordem PUBLISHED | `test_service_follows_published_order_not_working` |
| RQ-E2-03 saldo vivo | `test_service_live_partial_balance` |
| RQ-E2-04 conversão MI | `test_mi_factor_1000_no_double_conversion` |
| RQ-E2-05 setup | `test_setup_applicable_then_waived_*`, `test_setup_uncertain_*` |
| RQ-E2-06 parcial | `test_allocate_two_hours_*`, `test_allocate_partial_*` |
| RQ-E2-07 offsets | campos `offset_*` no payload |
| RQ-E2-08 incompleto | ST/balance unknown / setup não cabe |
| RQ-E2-09 revisão | `test_service_stale_publication_conflict` |
