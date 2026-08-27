# Rotas comerciais ROL e OTD — rotas simples

> **Status:** compostas `GET /commercial/rol` e `GET /commercial/sales-order-otd/analysis` **descontinuadas**.  
> Fonte de verdade: rotas simples por necessidade de slide (KPI / série / por cliente / por filial).

## Overview

Cada bloco do slide TV usa **uma** rota, sem `group_by`:

| Necessidade | operationId | Path |
|-------------|-------------|------|
| KPI ROL | `get_si_indicator_commercial_rol_realized` / `_meta` | `/dashboard/indicators/commercial-rol/*` |
| Série ROL | `get_commercial_rol_series` | `/commercial/rol/series` |
| ROL por cliente | `get_commercial_rol_by_customer` | `/commercial/rol/by-customer` |
| ROL por filial | `get_commercial_rol_by_branch` | `/commercial/rol/by-branch` |
| KPI OTD | `get_sales_order_otd` | `/commercial/sales-order-otd` |
| Série OTD | `get_sales_order_otd_series` | `/commercial/sales-order-otd/series` |
| OTD por cliente | `get_sales_order_otd_by_customer` | `/commercial/sales-order-otd/by-customer` |
| OTD por filial | `get_sales_order_otd_by_branch` | `/commercial/sales-order-otd/by-branch` |
| Painel pedidos | `get_sales_order_otd_panel` | `/commercial/sales-order-otd/panel` |

## Filtros

- **`granularity`**: só nas rotas `*_series` (obrigatório: `day` \| `week` \| `month` \| `year`).
- **Carteira** (todas as rotas comerciais acima, exceto SI): `customer_segment`, `customer_codes`, `customer_names`, `exclude_customer_codes`, `exclude_customer_names` — omitidos = sem filtro.
- No editor TV, «Não definido aqui» omite o query param.

## Payloads (não renomear)

| Rota | Chaves principais |
|------|-------------------|
| ROL série | `points[]`: `periodo`, `rol_matrix`, `rol_branch` |
| ROL cliente | `items[]`: `customer_*`, `rol`, `share_pct`, `rank` |
| ROL filial | `items[]`: `branch`, `rol`, `gross_revenue`, `returns`, `discounts` |
| OTD KPI | `sales_order_otd_pct` |
| OTD série | `points[]`: `periodo`, `total_qty`, `fulfilled_qty`, `otd_pct`, `fulfillment_pct`, `total_lines`, `otd_filial_01`, `otd_filial_02` |
| OTD cliente | `items[]` + `pagination` (métricas OTD/fulfillment) |
| OTD filial | `items[]`: `branch` + métricas |

Slides legados com as compostas são remapeados no hydrate da tv-dashboard-api (`tv_commercial_composite_binding_migration_service`).

## Fora do escopo

- Bloco `portfolio` / carteira semanal (antes: `include=portfolio` na composta ROL).
- YoY na API.

## Consumidores

| Consumidor | Rotas |
|------------|-------|
| TV Dashboard | simples + hydrate de legado composto |
| Portal / commercial-api | séries e KPIs simples existentes |
| Chat | registry operacional nas simples (sem compostas) |

## Referências

- `app/application/use_cases/commercial/get_commercial_rol_series_use_case.py`
- `app/application/use_cases/commercial/get_commercial_rol_by_customer_use_case.py`
- `app/application/use_cases/commercial/get_commercial_rol_by_branch_use_case.py`
- `app/application/use_cases/commercial/get_sales_order_otd_*_use_case.py`
- `tv-dashboard-api/.../tv_commercial_composite_binding_migration_service.py`
