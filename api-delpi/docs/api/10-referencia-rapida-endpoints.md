# 10 — Referência rápida de endpoints

Base: `/apps/api-delpi`

Legenda de permissões:

| Sigla | Permissão |
|---|---|
| **A** | `api-delpi.access` |
| **AF** | `api-delpi.access.full` |
| **S** | `api-delpi.system` |
| **D** | `api-delpi.data` |
| **Q** | `api-delpi.quality.access` |
| **L** | `dashboard-lmps.view` |
---

## Health

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/health` | — |

---

## Produtos (`/products`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/products/search` | A |
| GET | `/products/{code}` | A |
| GET | `/products/{code}/summary` | A |
| GET | `/products/{code}/structure` | A |
| GET | `/products/{code}/structure/exclusivity` | A |
| GET | `/products/exclusive-raw-materials/catalog` | A |
| GET | `/products/{code}/structure/excel` | A |
| GET | `/products/{code}/production-status` | A |
| GET | `/products/{code}/shipping-status` | A |
| GET | `/products/{code}/factory-status` | A |
| GET | `/products/{code}/parents` | A |
| GET | `/products/{code}/suppliers` | A |
| GET | `/products/{code}/customers` | A |
| GET | `/products/{code}/inspection` | A |
| GET | `/products/{code}/guide` | A |
| GET | `/products/{code}/internal-movements` | A |
| GET | `/products/{code}/stock` | A |
| GET | `/products/{code}/inbound-invoice-items` | A |
| GET | `/products/{code}/outbound-invoice-items` | A |
| GET | `/products/{code}/purchases` | A |
| GET | `/products/{code}/sales` | A |
| GET | `/products/{code}/sales/open-orders` | A |
| GET | `/products/{code}/sales/billing` | A |
| GET | `/products/{code}/pricing` | A |
| GET | `/products/{code}/analyser` | A |

---

## Vendas

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/sales/` | A |

---

## Sistema (`/system`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/system/tables/search` | AF ou S |
| GET | `/system/tables/{tableName}` | AF ou S |
| GET | `/system/tables/{tableName}/columns` | AF ou S |
| GET | `/system/tables/{tableName}/indexes` | AF ou S |
| GET | `/system/tables/{tableName}/relations` | AF ou S |
| GET | `/system/tables/{tableName}/schema` | AF ou S |
| GET | `/system/tables/{tableName}/columns/search` | AF ou S |
| GET | `/system/columns/search` | AF ou S |

---

## Dados

| Método | Endpoint | Perm. |
|---|---|---|
| POST | `/data/sql` | AF ou D |

---

## Financeiro

> Montagem dupla em `main.py`: `/financial/*` (preferido) e `/finacial/*` (legado).

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/financial/rol` | A |
| GET | `/financial/ebitda_pct` | A |
| GET | `/financial/fixed_cost_pct` | A |
| GET | `/financial/pmr` | A |

---

## Comercial (`/commercial`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/commercial/head_office_rol_target_pct` | A |
| GET | `/commercial/branch_rol_target_pct` | A |
| GET | `/commercial/closing-rate` | A |
| GET | `/commercial/sales-order-otd` | A |
| GET | `/commercial/new-business-rol-pct` | A |
| GET | `/commercial/new-clients-average` | A |
| GET | `/commercial/new-clients-rol-pct` | A |
| GET | `/commercial/rol/series` | A |

---

## RH (`/hr`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/hr/branches` | A |
| GET | `/hr/snapshot` | A |
| GET | `/hr/active-pdi-count` | A |
| GET | `/hr/performance-reviews-completion` | A |

---

## Produção — KPIs (`/production`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/production/direct_labor_cost_pct` | A |
| GET | `/production/production_cost_pct` | A |
| GET | `/production/depreciation_pct` | A |
| GET | `/production/overall_equipment_effectiveness_pct` | A |
| GET | `/production/oee` | A |
| GET | `/production/oee/appointments/{appointment_id}` | A |
| GET | `/production/oee/series` | A |
| GET | `/production/on_time_delivery_pct` | A |
| GET | `/production/otd` | A |
| GET | `/production/otd/series` | A |

---

## Produção operacional — Playbook 15 (`/production`)

> Detalhes, parâmetros e frases para agentes: [13-producao-operacional.md](./13-producao-operacional.md)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/production/consumption/top-items` | A |
| GET | `/production/consumption/top-items-by-work-center` | A |
| GET | `/production/consumption/top-items-validated` | A |
| GET | `/production/consumption/by-item/{code}` | A |
| GET | `/production/losses/top-materials` | A |
| GET | `/production/losses/records` | A |
| GET | `/production/schedule/today` | A |
| GET | `/production/orders/open` | A |
| GET | `/production/orders/finished` | A |
| GET | `/production/orders/finished-without-consumption` | A |
| GET | `/production/work-centers/order-summary` | A |
| GET | `/production/work-centers/average-planned-time` | A |
| GET | `/production/allocation-gaps` | A |
| GET | `/production/planned-vs-real-time` | A |

---

## Compras operacionais — Playbook 15 (`/purchases`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/purchases/top-products` | A |

---

## Suprimentos (`/supplies`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/supplies/cpv` | A |
| GET | `/supplies/otd` | A |
| GET | `/supplies/stock-value` | A |
| GET | `/supplies/inventory-turnover` | A |
| GET | `/supplies/negotiation-savings/summary` | A |

---

## Engenharia (`/engineering`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/engineering/lmps` | A ou L |
| GET | `/engineering/lmps/dashboard` | A ou L |
| GET | `/engineering/lmps/dashboard/summary` | A ou L |
| GET | `/engineering/lmps/dashboard/items` | A ou L |
| GET | `/engineering/lmps/dashboard/charts` | A ou L |
| GET | `/engineering/lmps/{sale_number}` | A ou L |
| GET | `/engineering/transforma-mais/processes` | A ou L |
| GET | `/engineering/transforma-mais/processes/summary` | A ou L |

---

## Qualidade — métricas TOTVS (`/quality`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/quality/branches` | Q |
| GET | `/quality/nonconformities` | Q |
| GET | `/quality/nonconformities/series` | Q |
| GET | `/quality/kaizens/summary` | Q |
| GET | `/quality/kaizens/{kaizen_id}` | Q |
| GET | `/quality/audit-5s/summary` | Q |
| GET | `/quality/ppm/internal/summary` | Q |
| GET | `/quality/ppm/external/summary` | Q |
| GET | `/quality/ppm/internal/series` | Q |
| GET | `/quality/ppm/external/series` | Q |
| GET | `/quality/ppm/internal` | Q |
| GET | `/quality/ppm/external` | Q |

---


## Pedidos de venda em aberto (`/pedidos-venda-abertos`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/pedidos-venda-abertos/` | A ou `pedidos-venda-abertos.access` |

## Indicadores Estratégicos

Rotas do painel SI estão em **`/apps/strategic-indicators-api/strategic-indicators`** — ver [05-indicadores-estrategicos.md](./05-indicadores-estrategicos.md) e [strategic-indicators-api/docs/API.md](../../strategic-indicators-api/docs/API.md).

---

## Documentação e OpenAPI

| Recurso | Endpoint |
|---|---|
| Swagger UI | `/docs` |
| OpenAPI | `/openapi.json` |
