# Alimentador de Linha — Etapa 3: necessidade dinâmica de materiais

**TASK_ID:** `PC-LINE-FEEDER-MATERIALS-E3`  
**Rework:** `PC-LINE-FEEDER-MATERIALS-E3-REWORK`  
**Status:** implementado (backend somente leitura)  
**Depende de:** E1 PUBLISHED + E2 horizonte

## Decisão de negócio

O Alimentador **não** usa marcação manual de coletado/separado/entregue.

A cada consulta:

`to_collect = max(0, necessidade_do_horizonte − saldo_disponível_no_ponto_de_uso)`

Listas anteriores e status de pick-plans **não** reduzem a demanda. Não há reserva virtual nem escrita no Protheus.

Unidade de medida: cada produto tem UOM consistente na operação DELPI — **sem** conversões adicionais nem regras de múltiplas unidades por produto.

## Inventário

| Capacidade | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| Horizonte E2 | YES | REUSE (`preview_horizon` interno) |
| Empenhos SD4 | YES | REUSE batch api-delpi; **EXTEND** validação estrita só na prévia E3 |
| Validação envelope batch | YES (`sequencing_material_resolver`) | REUSE → `operation_materials_batch.validated_operation_materials_batch_items` |
| Estoque 99/01 | YES | REUSE leitura; EXTEND regra (só 99 abate) |
| Consolidação | PARTIAL legado | NEW motor `line_feeder_materials` (sem `scheduled_*`) |
| HTTP preview | NO | NEW `POST /line-feeder/materials/preview` |
| Pick-plans / `/requirements` | YES | PRESERVE (`_fetch_commitments` legado com `_items`) |

## Contrato

```http
POST /line-feeder/materials/preview
operationId: preview_line_feeder_materials
```

Body: `{ "branch", "workCenters", "hoursPerWorkCenter" }` — sem persistência.

Resposta: publicação/revisão, completeness, `operational_list_safe`, materiais consolidados com `required_qty`, `factory_available_qty`, `to_collect_qty`, `source_available_qty` (informativo), origins por CT/OP.

### Integração `POST /production/orders/operation-materials/batch`

Envelope canônico (api-delpi):

- `branch`, `production_orders` (eco do pedido), `items[]`, `summary`
- `summary.requested_count`, `returned_count` (= `len(items)`), `order_count`, `commitment_count`
- `items: []` com `returned_count: 0` = **ausência legítima** de empenhos ativos (não é falha)
- Sem fallback SG1

Limites de lote: BFF fatia por `commitmentBatchSize` / `maxCommitmentBatches`; falha de transporte propaga `DelpiGatewayError`.

## Fórmulas

1. Operações com `covered_qty > 0` do horizonte (total **ou** parcial).
2. MP com `open_qty > 0`: `needed = open_qty` (saldo SD4 aberto **integral** da operação contemplada).
   - Não há proporcionalidade `covered_qty / pending_qty` sobre o empenho.
   - `origins[].fraction` permanece como razão **informativa** de cobertura do horizonte.
   - `origins[].demand_basis = open_commitment`.
3. Consolida por `(product_code, unit)`.
4. Desconta saldo 99 **uma vez** no total consolidado.
5. Almox 01: disponibilidade informativa (`to_pick`/`at_risk`), não reduz `to_collect`.

> Decisão vigente (rework): a seleção das operações é determinada pelo horizonte de horas.
> Para cada operação contemplada, a necessidade de materiais considera integralmente o
> saldo aberto dos empenhos SD4.

## Ausência legítima × falha de integração (rework)

| Cenário | Critério | Efeito |
|---|---|---|
| **A** Consulta íntegra, sem SD4 | `items` é lista (pode ser `[]`); envelope/filial/eco de OPs coerentes | `operational_list_safe` segue demais regras; `no_commitments` é diagnóstico; **não** inventa MP |
| **B** Resposta inválida/incompleta | sem `items[]`, payload não-dict, `success: false`, `returned_count` incoerente, OP/filial estranha | `commitments_incomplete` + `operational_list_safe=false`; **não** tratar como ausência |
| **C** Com empenhos | validação OK + linhas SD4 | demanda = `open_qty` integral por OP contemplada |
| Transporte/lote falhou | exceção no gateway | `DelpiGatewayError` — não lista completa falsa |

`returned_count = 0` **nunca** sozinho prova falha.

## Dados incompletos

| Situação | Efeito |
|---|---|
| Horizonte incomplete | `operational_list_safe=false` |
| Empenhos inválidos/incompletos | `commitments_incomplete` |
| Estoque indisponível | status `unknown`, não zero presumido |
| Paginação estourada | `stock_pagination_incomplete` |
| Revisão mudou | 409 `HorizonPreviewStale` |
| Empenho não proporcional | warning + incomplete |

## Critérios de aceite (rework)

1. Operação sem empenhos + resposta válida → lista segura, sem demanda fictícia.
2. Sem `items[]` → não é ausência legítima.
3. Payload malformado → prévia insegura.
4. Falha de lote → erro controlado (não `operational_list_safe=true`).
5. Vários empenhos / substituído / estoque fábrica → cálculo E3 preservado.
6. `/requirements` e pick-plans legados inalterados na semântica de `_items`.

## Dependência Etapa 4

A UI consome este contrato para exibir a lista dinâmica — sem reimplementar fórmulas no MFE.


## Correção de compatibilidade (2026-11-12): unidades contínuas e SD4 sem operação

**Motivação:** OP `09564601002`, filial 02, produto `71250220` em MT,
com operações 01/02 no CT-27 e 03 no CT-99. A prévia falhava com
`piece_conversion_unavailable` porque MT não tem equivalência física
confiável para peças. Os empenhos da OP (cobre nu, PVC e pigmento, todos em
KG) aparecem no SD4 com `D4_OPERAC` vazio.

- **Horizonte:** apenas para `MT`/`KG` sem fator de peças, o motor E2 usa
  `standard_time_unit_hours` do contrato canônico de tempo padrão da
  api-delpi, em horas por unidade operacional; setup continua separado.
  Arredonda para baixo a 6 casas. Não altera a normalização por peça
  `MI/UN/PC`, nem o contrato MES/Pulse. Se faltar tempo padrão ou a unidade
  for desconhecida, permanece fail-closed.
- **Empenhos:** somente o consumidor E3 habilita `include_unassigned` na
  indexação do SD4. Cada empenho com operação em branco é associado uma
  única vez à **OP contemplada**, com `operation_code=""` e
  `operation_id="order-level:<OP>"`; nunca é rateado entre os CTs nem
  associado arbitrariamente à primeira operação. O saldo SD4 é integral.
  Permanecem intactos os demais consumidores do índice estrito.
- **Interface:** origens dessa categoria aparecem como
  "empenho sem operação definida", com CT indefinido e alerta para consultar
  o PCP antes de entregar. O saldo do 99 continua abatido uma única vez
  por material, e o almoxarifado 01 é apenas informativo.
- **Não escopo:** mudança no ERP, no catálogo `piecesFactor` da api-delpi,
  no MES/Pulse, na fila publicada e em processos de confirmação da entrega.
- **Regressões:** testes de horizonte MT/KG e da falha segura para padrões
  ausentes; material de OP sem operação contado uma vez em múltiplos CTs;
  mistura com empenhos de operação explícita; teste E3 completo e aviso UI.

**Atenção operacional:** itens com `D4_OPERAC` em branco não têm CT
autoritativo. A prévia mostra a necessidade e avisa o usuário, mas a
atribuição de posto de entrega deve ser confirmada com o PCP.
