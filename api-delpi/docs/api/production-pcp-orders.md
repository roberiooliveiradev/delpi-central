# Ordens de produção — OPs (`VW_PCP_ORDENS_PRODUCAO`)

Catálogo filtrável de ordens de produção (estilo Power BI), separado do playbook SC2 (`/production/orders/*`) e do KPI OTD.

## Rotas

| Método | Path | operationId | Shape |
|--------|------|-------------|-------|
| GET | `/production/pcp-orders/summary` | `get_production_pcp_orders_summary` | `playbook_report` |
| GET | `/production/pcp-orders/items` | `get_production_pcp_orders_items` | `paged_list` |
| GET | `/production/pcp-orders/ranking` | `get_production_pcp_orders_ranking` | `list` |

Permissão: `KPI_PRODUCTION_ACCESS`.

## Fonte

View TOTVS `dbo.VW_PCP_ORDENS_PRODUCAO` (`NOLOCK`). Flags: `FL_OP_EM_ABERTO` / `FL_OP_MAE` (0/1), `FL_ATRASADA` / `FL_TEM_SALDO` (`Sim`/`Não`). Saldo: `SALDO_OP`.

## Filtros (EN)

Comuns: `branch`, `delivery_start` / `delivery_end` (`DT_ENTREGA`; default últimos 12 meses), `actual_end_start` / `actual_end_end`, `op_key`, `product_code`, `warehouse`, `mother_only`, `open_only`, `delayed_only`.

Items: `page`, `page_size`, `sort` (`delivery_desc|asc`, `issue_*`, `delay_*`, `qty_*`, `op_*`).

Ranking: `rank_by` (`product` \| `warehouse` \| `op`), `metric` (`order_qty` \| `reported_qty` \| `balance` \| `delay_days`), `limit`.

## Contrato de item (canônico)

`production_order` / `op_key`, `product_code`, `product_description` (+ alias `description`, **só texto** — sem prefixo do código; a view `PRODUTO_DESCRICAO` «código - desc» é normalizada), `planned_qty`, `produced_qty`, `pending_qty`, datas, `days_late`, `is_open`, `is_mother`, `is_delayed`, `has_balance`, `branch`, `warehouse`, `observation`.

## Relação com outras rotas

- `/production/orders/open|finished|…` — playbook por `reference_date` em SC2010 (não substituído).
- `/production/otd` — KPI prazo/atraso.
- Esta família — listagem de OPs por entrega prevista e flags da view.
