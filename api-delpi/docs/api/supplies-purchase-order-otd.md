# OTD de pedidos de compra (MP) — `/supplies/purchase-order-otd`

**Última atualização:** 2026-08-06  
**Operações OpenAPI:** `get_supplies_purchase_order_otd`, `get_supplies_purchase_order_otd_series`, `get_supplies_purchase_order_otd_panel`  
**Repositório:** `app/infrastructure/persistence/totvs/supplies_repositories/purchase_order_otd_repository.py`  
**SQL:** `purchase_order_otd_sql.py`

## Objetivo

Percentual de linhas de **pedido de compra de matéria-prima (MP)** recebidas no prazo, alinhado à pontualidade de fornecedores (`VW_PONTUALIDADE_FORNECEDORES`).

Universo fixo: `TIPO_PRODUTO = MP` (`PRODUCT_TYPE_RAW_MATERIAL` em `app/domain/totvs/protheus_product_types.py`).  
Não confundir com:

- `GET /supplies/otd` — OTD de compras **geral** (todos os tipos)
- `GET /commercial/sales-order-otd` — OTD de **pedidos de venda**
- Estoque de segurança — lista PCs **abertos** (`C7_DATPRF`), sem taxa histórica

## Endpoints

```http
GET /supplies/purchase-order-otd?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&branch=01
GET /supplies/purchase-order-otd/series?granularity=month&start_date=...&end_date=...
GET /supplies/purchase-order-otd/panel?...&status=late&page=1&page_size=20
```

| Parâmetro | Descrição |
|-----------|-----------|
| `start_date` / `end_date` | Filtra pela **data de digitação/recebimento** (`DT_DIGITACAO`). |
| `branch` | Filial TOTVS (`01`, `02`, …) ou consolidado (omitido). |
| `granularity` (series) | `day` \| `week` \| `month` \| `year` (default `month`). |
| `status` (panel) | `on_time` \| `late`. |

## Fonte TOTVS

| Objeto | Papel |
|--------|-------|
| `VW_PONTUALIDADE_FORNECEDORES` | Linhas de recebimento vs prazo prometido |
| `SA2010` (A2) | Fornecedor — `A2_NREDUZ` (nome reduzido) no painel |

Leitura analítica com `WITH (NOLOCK)`.

## Classificação

| Situação | Regra |
|----------|-------|
| **No prazo** | `DIAS >= 0` |
| **Atrasado** | `DIAS < 0` |

Interpretação alinhada ao dashboard de suprimentos: recebimento ≤ data prometida (`DT_ENTREGA` ≈ `C7_DATPRF`).

## Resposta KPI (`data`)

| Campo | Descrição |
|-------|-----------|
| `product_type` | Sempre `MP` |
| `total_lines` | Linhas elegíveis no período |
| `on_time_lines` / `late_lines` | Contagens |
| `purchase_order_otd_pct` | `on_time_lines / total_lines × 100` (2 casas) |

Painel (`/panel`) — fornecedor:

| Campo | Fonte |
|-------|--------|
| `supplier_name` | Preferência `SA2.A2_NREDUZ`; se vazio, `NOME_FORNECEDOR` da view |
| `supplier_short_name` | `SA2.A2_NREDUZ` |

## Cache

- KPI: namespace `supplies-purchase-order-otd` (`QUERY_CACHE_TTL_SECONDS`)
- Série: `supplies-purchase-order-otd-series` (chart series cache)

## Consumidores previstos

- TV Dashboard / chat (OpenAPI agent)
- Dashboard de suprimentos (evolução futura)

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-08-06 | Família KPI + series + panel só MP. |
