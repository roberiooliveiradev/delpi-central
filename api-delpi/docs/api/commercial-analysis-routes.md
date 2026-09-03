# Rotas comerciais ROL e OTD — rotas simples

> **Status:** compostas `GET /commercial/rol` e `GET /commercial/sales-order-otd/analysis` **descontinuadas**.  
> Fonte de verdade: rotas simples por necessidade de slide (KPI / série / por cliente / por filial).

## Overview

Cada bloco do slide TV usa **uma** rota, sem `group_by`:

| Necessidade | operationId | Path |
|-------------|-------------|------|
| KPI ROL + meta SI | `get_commercial_rol_summary` | `/commercial/rol/summary` |
| KPI ROL (pares SI) | `get_si_indicator_commercial_rol_realized` / `_meta` | `/dashboard/indicators/commercial-rol/*` |
| Série ROL | `get_commercial_rol_series` | `/commercial/rol/series` |
| ROL por cliente | `get_commercial_rol_by_customer` | `/commercial/rol/by-customer` |
| ROL por produto / família | `get_commercial_rol_by_product` | `/commercial/rol/by-product` |
| ROL por filial | `get_commercial_rol_by_branch` | `/commercial/rol/by-branch` |
| KPI OTD + meta SI | `get_sales_order_otd_summary` | `/commercial/sales-order-otd/summary` |
| KPI OTD | `get_sales_order_otd` | `/commercial/sales-order-otd` |
| Série OTD | `get_sales_order_otd_series` | `/commercial/sales-order-otd/series` |
| OTD série por cliente | `get_sales_order_otd_series_by_customer` | `/commercial/sales-order-otd/series-by-customer` |
| OTD por cliente | `get_sales_order_otd_by_customer` | `/commercial/sales-order-otd/by-customer` |
| OTD por filial | `get_sales_order_otd_by_branch` | `/commercial/sales-order-otd/by-branch` |
| Painel pedidos | `get_sales_order_otd_panel` | `/commercial/sales-order-otd/panel` |

## Filtros

- **`granularity`**: nas rotas `*_series*` (`day` \| `week` \| `month` \| `year`). Em `get_sales_order_otd_series` continua obrigatório; em **`get_sales_order_otd_series_by_customer`** é **opcional** (omitido → `week`).
- **Carteira** (todas as rotas comerciais acima, exceto SI): `customer_segment`, `customer_codes`, `customer_code_stores` (pares `codigo|loja`), `customer_names`, `exclude_customer_codes`, `exclude_customer_names` — omitidos = sem filtro.
- **`top_customers`** (só `series-by-customer`): default **20**, max **100**. Aplicado quando **não** há `customer_codes`, `customer_names` nem `customer_code_stores`; ranking pelo `total_qty` do intervalo completo antes de expandir os buckets.
- Em `series-by-customer`, **todos** os filtros de query são opcionais (datas, filial, carteira, granularidade, paginação, top).
- No editor TV, «Não definido aqui» omite o query param.

## Payloads (não renomear)

| Rota | Chaves principais |
|------|-------------------|
| ROL summary | `rol` (+ `gross_revenue`/`returns`/`discounts`) + tríade meta SI (`comparable_goal`, `goal_value`, `reference_goal`) + `rol_target_pct` |
| ROL série | `points[]`: `periodo`, `rol_matrix`, `rol_branch` |
| ROL cliente | `items[]`: `customer_*`, `rol`, `share_pct`, `rank` |
| ROL filial | `items[]`: `branch`, `rol`, `gross_revenue`, `returns`, `discounts` |
| OTD summary | `sales_order_otd_pct` + tríade meta SI + contagens |
| OTD KPI | `sales_order_otd_pct` |
| OTD série | `points[]`: `periodo`, `total_qty`, `fulfilled_qty`, `otd_pct`, `fulfillment_pct`, `total_lines`, `otd_filial_01`, `otd_filial_02`, `unit`, `mixed_units` |
| OTD série por cliente | `items[]` flat (cliente × período) + `pagination` + `summary`; métricas iguais à OTD por cliente (+ `unit`/`mixed_units`) |
| OTD cliente | `items[]` + `pagination` (métricas OTD/fulfillment + `unit`/`mixed_units`) |
| OTD filial | `items[]`: `branch` + métricas (+ `unit`/`mixed_units`) |

**Unidade de medida:** qty permanece na UM nativa da linha (`C6_UM` / fallback `B1_UM`). Em agregações, `unit` só aparece se o bucket for homogêneo; se houver UMs diferentes, `unit` é `null` e `mixed_units` é `true` (sem conversão MI→peça). Detalhe: `comercial-sales-order-otd.md`.

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

- `app/application/use_cases/commercial/get_commercial_rol_summary_use_case.py`
- `app/application/use_cases/commercial/get_commercial_rol_series_use_case.py`
- `app/application/use_cases/commercial/get_commercial_rol_by_customer_use_case.py`
- `app/application/use_cases/commercial/get_commercial_rol_by_branch_use_case.py`
- `app/application/use_cases/commercial/get_sales_order_otd_*_use_case.py`
- `tv-dashboard-api/.../tv_commercial_composite_binding_migration_service.py`
