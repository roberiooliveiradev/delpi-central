# Alimentador de Linha — Etapa 3: necessidade dinâmica de materiais

**TASK_ID:** `PC-LINE-FEEDER-MATERIALS-E3`  
**Status:** implementado (backend somente leitura)  
**Depende de:** E1 PUBLISHED + E2 horizonte

## Decisão de negócio

O Alimentador **não** usa marcação manual de coletado/separado/entregue.

A cada consulta:

`to_collect = max(0, necessidade_do_horizonte − saldo_disponível_no_ponto_de_uso)`

Listas anteriores e status de pick-plans **não** reduzem a demanda. Não há reserva virtual nem escrita no Protheus.

## Inventário

| Capacidade | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| Horizonte E2 | YES | REUSE (`preview_horizon` interno) |
| Empenhos SD4 | YES | REUSE (`_fetch_commitments` / batch) |
| Estoque 99/01 | YES | REUSE leitura; EXTEND regra (só 99 abate) |
| Consolidação | PARTIAL legado | NEW motor `line_feeder_materials` (sem `scheduled_*`) |
| HTTP preview | NO | NEW `POST /line-feeder/materials/preview` |
| Pick-plans legado | YES | PRESERVE, desconectado do fluxo novo |

## Contrato

```http
POST /line-feeder/materials/preview
operationId: preview_line_feeder_materials
```

Body: `{ "branch", "workCenters", "hoursPerWorkCenter" }` — sem persistência.

Resposta: publicação/revisão, completeness, `operational_list_safe`, materiais consolidados com `required_qty`, `factory_available_qty`, `to_collect_qty`, `source_available_qty` (informativo), origins por CT/OP.

## Fórmulas

1. Operações com `covered_qty > 0` do horizonte.
2. MP com `open_qty > 0`: `needed = open_qty × min(1, covered_qty/pending_qty)`.
3. Consolida por `(product_code, unit)`.
4. Desconta saldo 99 **uma vez** no total consolidado.
5. Almox 01: disponibilidade informativa (`to_pick`/`at_risk`), não reduz `to_collect`.

## Dados incompletos

| Situação | Efeito |
|---|---|
| Horizonte incomplete | `operational_list_safe=false` |
| Estoque indisponível | status `unknown`, não zero presumido |
| Paginação estourada | `stock_pagination_incomplete` |
| Revisão mudou | 409 `HorizonPreviewStale` |
| Empenho não proporcional | warning + incomplete |

## Dependência Etapa 4

A UI consome este contrato para exibir a lista dinâmica — sem reimplementar fórmulas no MFE.
