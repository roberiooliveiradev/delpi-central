# Alimentador de Linha — Etapa 1: completude, diagnóstico e early-stop

**TASK_ID:** `LINE-FEEDER-HORIZON-SAFETY-E1`  
**Depende de:** [LINE-FEEDER-HORIZON-E2.md](./LINE-FEEDER-HORIZON-E2.md), [LINE-FEEDER-MATERIALS-E3.md](./LINE-FEEDER-MATERIALS-E3.md), [LINE-FEEDER-UI-E4.md](./LINE-FEEDER-UI-E4.md)  
**Escopo:** confiabilidade da prévia (não otimização progressiva de ST — Etapa 2)

## Problema

Consultas longas (ex.: 8 h) podiam terminar com `Horizon incomplete` / `horizon_incomplete` genérico, às vezes confundindo **fila insuficiente** (`shortfall`) com **falha de cálculo** (`incomplete`), e ainda assim disparar empenhos/estoque para uma lista já insegura.

## Decisões (Etapa 1)

| Conceito | Semântica |
|----------|-----------|
| `shortfall` | Fila PUBLISHED válida esgotada antes do orçamento de horas; dados das ops avaliadas são confiáveis. Pode alimentar materiais. |
| `incomplete` | Bloqueio técnico/dados (`balance_unknown`, `standard_time_*`, `upstream_unavailable`, `piece_conversion_unavailable`, `setup_uncertain`, `standard_time_call_limit`, …). **Não** vira shortfall. |
| `operational_list_safe` | `true` só se nenhum CT estiver `incomplete` **e** empenhos/estoque/proporção estiverem íntegros. |
| Early-stop | Se o horizonte já for inseguro, **não** consulta SD4/SB2/localizações/bloqueios só para montar coleta. |
| Diagnóstico | Payload aditivo `diagnostics[]` + `blocking_operation` / `diagnostic_message` por CT. |

## Instrumentação

Logs estruturados (`line_feeder_horizon_preview`, `line_feeder_materials_preview`) com `phases_ms`, contadores de CTs/ops/chamadas ST e flag `materials_skipped`. Sem PII/SQL/secrets. Resposta pode incluir `timing` (não obrigatório no FE).

## Fora desta etapa (histórico)

A consulta progressiva de tempo padrão foi entregue em [LINE-FEEDER-HORIZON-OPT-E2.md](./LINE-FEEDER-HORIZON-OPT-E2.md).

Ainda fora (Etapa 3 / pós-OPT):

- Paralelização / pooling HTTP / batch ST na api-delpi  
- Otimização SQL Protheus / mudança de armazéns 99/01  

## Aceite

| AC | Cobertura |
|----|-----------|
| AC-01 shortfall legítimo | `test_materials_shortfall_queue_remains_safe` |
| AC-02 ST inválido | `test_materials_missing_standard_time_is_incomplete_not_shortfall` |
| AC-03 upstream | `test_materials_upstream_unavailable_not_shortfall` |
| AC-04 conversão/setup | `test_materials_data_blocks_are_not_operationally_safe` (+ domínio `test_line_feeder_horizon`) |
| AC-05 call limit | `test_materials_call_limit_does_not_become_shortfall` |
| AC-06/07 CT bloqueado + early-stop | `test_materials_blocked_ct_skips_stock_and_commitments` |
| AC-08 FE diagnóstico | `LineFeederMaterialsPanel.test.tsx` |
| AC-09 timing | `test_materials_timing_payload_is_present_without_secrets` |
| AC-10 regressão válida | `test_service_materials_preview_end_to_end` + suite E3 existente |

## Medição

1. Disparar prévia de materiais (ou horizonte) com `hours` alto.  
2. Nos logs da `production-control-api`, filtrar `line_feeder_materials_preview` / `line_feeder_horizon_preview`.  
3. Comparar `phases_ms.*` e contadores (`work_center_count`, `standard_time_calls`, `materials_skipped`).  
4. Latência em produção só após amostragem real — testes comprovam **chamadas evitadas**, não ms de rede.
