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
| **PAC-R** | Leitura PAC: `quality-action-plans.read`, `.manage`, `api-delpi.quality.action-plans.read`, `dashboard-quality.view`, … |
| **KZ-R** | Leitura cadastro Kaizen: `cadastro-kaizen.view`, `.manage`, `dashboard-quality.view`, `api-delpi.quality.access`, … |
| **KZ-W** | Escrita cadastro Kaizen: `cadastro-kaizen.manage`, `api-delpi.quality.access`, … |
| **público** | Sem JWT (prefixo `/public/...`) |
| **PAC-W** | Escrita PAC: `quality-action-plans.write`, `.manage` |
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
| GET | `/products/directives/{identifier}` | A |
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
| GET | `/products/drawings` | A |
| GET | `/products/{code}/drawing` | A |
| GET | `/products/{code}/drawing/pdf` | A (binário PDF) |

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
| GET | `/financeiro/inadimplencia/resumo` | A / `financeiro-inadimplencia.access` |
| GET | `/financeiro/inadimplencia/mensal` | A / `financeiro-inadimplencia.access` |
| GET | `/financeiro/inadimplencia/faixas-atraso` | A / `financeiro-inadimplencia.access` |
| GET | `/financeiro/inadimplencia/clientes` | A / `financeiro-inadimplencia.access` |
| GET | `/financeiro/inadimplencia/titulos` | A / `financeiro-inadimplencia.access` |

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
| GET | `/production/appointments/work-centers` | A |
| GET | `/production/appointments` | A |
| GET | `/production/appointments/summary` | A |
| GET | `/production/appointments/series` | A |
| GET | `/production/appointments/by-op` | A |
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
| GET | `/supplies/safety-stock/filters` | A |
| GET | `/supplies/safety-stock/summary` | A |
| GET | `/supplies/safety-stock/items` | A |
| GET | `/supplies/safety-stock/items/{code}/details` | A |
| GET | `/supplies/safety-stock/items/{code}/suppliers` | A |
| GET | `/supplies/safety-stock/items/{code}/suppliers/{supplier_code}/purchase-price-history` | A |
| GET | `/supplies/safety-stock/consumption-analysis/summary` | A |
| GET | `/supplies/safety-stock/consumption-analysis/items` | A |
| GET | `/supplies/safety-stock/consumption-analysis/items/{code}` | A |

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
| GET | `/quality/kaizens/records` | KZ-R |
| POST | `/quality/kaizens/records` | KZ-W |
| POST | `/quality/kaizens/records/import-from-sheet` | KZ-W |
| POST | `/public/kaizen/suggestions` | público |
| GET | `/quality/audit-5s/summary` | Q |
| GET | `/quality/ppm/internal/summary` | Q |
| GET | `/quality/ppm/external/summary` | Q |
| GET | `/quality/ppm/internal/series` | Q |
| GET | `/quality/ppm/external/series` | Q |
| GET | `/quality/ppm/internal` | Q |
| GET | `/quality/ppm/external` | Q |

---

## PAC Qualidade — planos de ação (`/quality/action-plans`)

Doc: [quality-action-plans-pac.md](./quality-action-plans-pac.md)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/quality/action-plans/dashboard` | PAC-R |
| GET | `/quality/action-plans` | PAC-R |
| GET | `/quality/action-plans/overdue` | PAC-R |
| GET | `/quality/action-plans/my-queue` | PAC-R |
| GET | `/quality/action-plans/assignable-users` | PAC-R |
| GET | `/quality/action-plans/{plan_id}` | PAC-R |
| POST | `/quality/action-plans` | PAC-W |
| PATCH | `/quality/action-plans/{plan_id}/status` | PAC-W |
| PUT | `/quality/action-plans/{plan_id}/ishikawa` | PAC-W |
| PUT | `/quality/action-plans/{plan_id}/five-whys` | PAC-W |
| POST | `/quality/action-plans/{plan_id}/actions` | PAC-W |
| PATCH | `/quality/action-plans/{plan_id}/actions/{action_id}` | PAC-W |
| POST | `/quality/action-plans/{plan_id}/effectiveness-review` | PAC-W |

---

## Inspeções de entrada (`/inspecoes-entrada`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/inspecoes-entrada/resumo` | IE |
| GET | `/inspecoes-entrada/pendentes` | IE |
| GET | `/inspecoes-entrada/pendentes-fornecedor` | IE |
| GET | `/inspecoes-entrada/rejeitadas-ensaiador` | IE |
| GET | `/inspecoes-entrada/rejeitadas-produto` | IE |
| GET | `/inspecoes-entrada/historico` | IE |
| GET | `/inspecoes-entrada/historico/detalhe` | IE |

---

## Inspeções de processo (`/inspecoes-processo`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/inspecoes-processo/resumo` | IP |
| GET | `/inspecoes-processo/ranking-ensaio` | IP |
| GET | `/inspecoes-processo/por-produto` | IP |
| GET | `/inspecoes-processo/por-operacao` | IP |
| GET | `/inspecoes-processo/por-ensaiador` | IP |
| GET | `/inspecoes-processo/historico` | IP |
| GET | `/inspecoes-processo/historico/detalhe` | IP |
| GET | `/inspecoes-processo/auditoria-apontamentos` | IP |

---

## Controle de Retrabalhos (`/retrabalhos`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/retrabalhos/health` | CR |
| GET | `/retrabalhos/filtros` | CR |
| GET | `/retrabalhos/resumo` | CR |
| GET | `/retrabalhos/mensal` | CR |
| GET | `/retrabalhos/recursos` | CR |
| GET | `/retrabalhos/colaboradores` | CR |
| GET | `/retrabalhos/detalhes` | CR |

Permissões: `controle-retrabalhos.*` ou `api-delpi.access`. Legenda: **CR** = controle-retrabalhos.

## Acompanhamento de Refugos (`/refugos`)

| Método | Endpoint | Permissão |
|---|---|---|
| GET | `/refugos/health` | SM |
| GET | `/refugos/filtros` | SM |
| GET | `/refugos/resumo` | SM |
| GET | `/refugos/rankings` | SM |
| GET | `/refugos/registros` | SM |

Permissões: `scrap-monitoring.*` ou `api-delpi.access`. Filiais SC/ES (`01`/`02`). Legenda: **SM** = scrap-monitoring. Doc: [scrap-monitoring.md](./scrap-monitoring.md).

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
