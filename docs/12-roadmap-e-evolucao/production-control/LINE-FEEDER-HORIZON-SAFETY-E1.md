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


## Incidente 2026-11-12: CT-00, OP de outra filial

No Alimentador da filial 02, a prévia indicou `balance_unknown` para
`CT-00 / 11301901001 / operação 01`. Consulta somente leitura ao SC2010:
a OP `11301901001` existe apenas na filial 01, com `C2_DATRF=20130520`,
`C2_QUANT=C2_QUJE=4.5 MI`. A tela de empenhos fornecida correspondia a uma
**OP diferente**, `11302401001`, da filial 02, com produto `90263782`
em MI, 0,350 planejado e ainda não produzido.

**Correção defensiva:**
- A projeção do Alimentador rejeita somente operações cuja filial de
  origem, presente em `payload_json.operations[].branch`, difere da
  filial da publicação solicitada. Não muda o payload nem o cockpit.
- Tanto o catálogo `published-queue` quanto a prévia de horizonte
  usam o mesmo filtro. A publicação contém contagem aditiva
  `foreign_branch_operations_excluded` para auditoria e alerta visual.
- A importação de uma nova Carga Máquina recusa lotes com
  `item.branch` explicitamente divergente da filial solicitada,
  interrompendo a atualização antes de gravar novo snapshot.
- Snapshot legado **sem** informação de filial continua fail-closed:
  o saldo vivo é obrigatório; não assumir que a OP foi concluída,
  não substituir por `C2_QUANT - C2_QUJE` e não ignorar saldo desconhecido.
- Uma operação legítima da filial com saldo indisponível continua
  retornando `balance_unknown` e bloqueando a coleta.

**Condição de aceite na produção:** com o cliente na filial 02,
verificar que `11301901001` não apareça na seleção da prévia; conferir
as operações e materiais reais da `11302401001` e o aviso de integridade
se a fila ainda contiver registros de outra filial. Solicitar ao PCP a
atualização e republicação para sanear o snapshot; não alterar SD4/SC2
diretamente.

**Limitação diagnóstica:** foi comprovada a divergência no SQL Server,
mas o `payload_json` da publicação atual não pôde ser lido por esta
investigação; o filtro corrige o caso quando a filial de origem estiver
gravada na linha, conforme o contrato normal da api-delpi.


### Proteção adicional: confirmação de inexistência no SC2

Como `payload_json` da publicação não foi inspecionado, o filtro por
`operations[].branch` pode não identificar uma OP obsoleta cuja filial
tenha sido registrada incorretamente ou não esteja disponível. A consulta
autoritativa de saldos `POST /production/machine-load/operation-balances`
agora devolve o campo aditivo `order_exists` por OP+operação:

- `true`: SC2010 confirmou a OP na filial informada;
- `false`: consulta SC2010 executada, mas não encontrou a OP na filial;
- `null`: adapter legado sem capacidade de consulta de existência.

O Alimentador só exclui a operação em caso de `order_exists=false`
explícito e contabiliza `missing_order_operations_excluded` para aviso
visível. Não cria quantidade produzida ou saldo fictício. `null`,
`order_exists` ausente, resposta inválida ou erro S2S continuam
respeitando o bloqueio `balance_unknown`/integração indisponível.
A filial ecoada pelo contrato de saldos também é confrontada com a filial
solicitada, e divergência gera erro controlado.

**Deploy:** esta evolução requer reconstrução coordenada de
`api-delpi`, `production-control-api` e `production-control`
após testes e revisão do PR. A proteção de leitura e a importação
continuam sem atualizar ERP, nem alterar o snapshot publicado.
