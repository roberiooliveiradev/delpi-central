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
| **KZ-R** | Leitura Kaizômetro: `kaizometro.view`, `.manage`, `.branch-01`/`.branch-02` (+ legado `cadastro-kaizen.*`), `dashboard-quality.view`, `api-delpi.quality.access`, … |
| **KZ-W** | Escrita Kaizômetro: `kaizometro.manage` (+ legado `cadastro-kaizen.manage`) + escopo `branch-*`, `api-delpi.quality.access`, … |
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
| GET | `/products/by-supplier-part-number` | A |
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
| GET | `/products/{code}/raw-material-set-shortages` | A |
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
| GET | `/financial/rol/invoices` | A |
| GET | `/financial/ebitda_pct` | A |
| GET | `/financial/fixed_cost_pct` | A |
| GET | `/financial/pmr` | A |
| GET | `/financial/purchase-freight/links` | A |
| GET | `/financeiro/inadimplencia/resumo` | A / `financeiro-inadimplencia.access` |
| GET | `/financeiro/inadimplencia/mensal` | A / `financeiro-inadimplencia.access` |
| GET | `/financeiro/inadimplencia/faixas-atraso` | A / `financeiro-inadimplencia.access` |
| GET | `/financeiro/inadimplencia/clientes` | A / `financeiro-inadimplencia.access` |
| GET | `/financeiro/inadimplencia/titulos` | A / `financeiro-inadimplencia.access` |

### Lançamento de Notas Fiscais (`/lancamento-notas-fiscais`)

> Permissões do plugin `lancamento-notas-fiscais.*` — ver [lancamento-notas-fiscais.md](./lancamento-notas-fiscais.md).

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/lancamento-notas-fiscais/suppliers` | `create` |
| POST | `/lancamento-notas-fiscais/requests` | `create` |
| GET | `/lancamento-notas-fiscais/requests` | LNF read |
| GET | `/lancamento-notas-fiscais/requests/{id}` | LNF read |
| GET | `/lancamento-notas-fiscais/requests/{id}/purchase-orders` | LNF read |
| POST | `/lancamento-notas-fiscais/requests/{id}/purchase-orders/link` | LNF process/manage |
| PATCH | `/lancamento-notas-fiscais/requests/{id}` | create/process/manage |
| POST | `/lancamento-notas-fiscais/requests/{id}/start` | process/manage |
| POST | `/lancamento-notas-fiscais/requests/{id}/block` | process/manage |
| POST | `/lancamento-notas-fiscais/requests/{id}/resume` | process/manage |
| POST | `/lancamento-notas-fiscais/requests/{id}/comments` | create/process/manage |
| POST | `/lancamento-notas-fiscais/requests/{id}/cancel` | create† / manage |
| POST | `/lancamento-notas-fiscais/requests/{id}/post-manual` | process/manage |
| POST | `/lancamento-notas-fiscais/reconciliation/refresh` | LNF read |
| POST | `/lancamento-notas-fiscais/reconciliation/run` | `manage` |

† `create`: somente própria em `pending`.

### Emissão de Notas Fiscais (`/invoice-issuance`)

> Permissões do plugin `invoice-issuance.*` — ver [invoice-issuance.md](./invoice-issuance.md).

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/invoice-issuance/parties` | create |
| GET | `/invoice-issuance/products` | create |
| GET | `/invoice-issuance/products/{code}/warehouse-01-balance` | create |
| GET | `/invoice-issuance/open-sales-orders` | create |
| GET | `/invoice-issuance/carriers` | create |
| POST | `/invoice-issuance/requests` | create |
| GET | `/invoice-issuance/requests` | II read |
| GET | `/invoice-issuance/requests/{id}` | II read |
| PATCH | `/invoice-issuance/requests/{id}` | criador + returned |
| POST | `/invoice-issuance/requests/{id}/resubmit` | criador + returned |
| POST | `/invoice-issuance/requests/{id}/start` | process/manage |
| POST | `/invoice-issuance/requests/{id}/return` | process/manage |
| POST | `/invoice-issuance/requests/{id}/issue` | process/manage |
| POST | `/invoice-issuance/requests/{id}/cancel` | create† / process / manage |

---

## Comercial (`/commercial`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/commercial/rol/summary` | A |
| GET | `/commercial/weg-rol-target-pct` | A |
| GET | `/commercial/new-business-rol-target-pct` | A |
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
| GET | `/production/machine-programs/top-intermediates` | A |
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
| GET | `/supplies/purchase-order-otd` | A |
| GET | `/supplies/purchase-order-otd/series` | A |
| GET | `/supplies/purchase-order-otd/panel` | A |
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
| GET | `/supplies/purchase-requests/open-coverage` | A |
| GET | `/supplies/third-party-materials/shipments` | A |
| GET | `/supplies/third-party-materials/shipments/{shipment_recno}` | A |
| GET | `/supplies/third-party-materials/summary` | A |
| GET | `/supplies/third-party-materials/returns/export` | A |

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
| GET | `/engineering/transformometro/savings-investment/series` | A ou L |

---

## Qualidade — métricas TOTVS (`/quality`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/quality/branches` | Q |
| GET | `/quality/nonconformities` | Q |
| GET | `/quality/nonconformities/series` | Q |
| GET | `/quality/nonconformities/streak` | Q |
| GET | `/quality/kaizens/summary` | Q |
| GET | `/quality/kaizens/summary/series` | Q |
| GET | `/quality/kaizens/{kaizen_id}` | Q |
| GET | `/quality/kaizens/records` | KZ-R |
| GET | `/quality/kaizens/records/summary` | KZ-R |
| GET | `/quality/kaizens/records/savings-investment/series` | KZ-R |
| POST | `/quality/kaizens/records` | KZ-W |
| POST | `/quality/kaizens/records/import` | KZ-W |
| POST | `/public/kaizen/suggestions` | público |
| GET | `/quality/audit-5s/summary` | Q |
| GET | `/quality/audit-5s/summary/series` | Q |
| GET | `/quality/ppm/internal/summary` | Q |
| GET | `/quality/ppm/external/summary` | Q |
| GET | `/quality/ppm/internal/series` | Q |
| GET | `/quality/ppm/external/series` | Q |
| GET | `/quality/ppm/internal` | Q |
| GET | `/quality/ppm/external` | Q |
| GET | `/quality/returned-totals` | Q |
| GET | `/quality/produced-quantity` | Q |
| GET | `/quality/scrap-cost-pct` | Q |
| GET | `/quality/scrap-cost-pct/series` | Q |
| GET | `/quality/rework-cost-pct` | Q |
| GET | `/quality/rework-cost-pct/series` | Q |

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

## Process inspection plans (`/process-inspection-plans`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/process-inspection-plans/summary` | IP |
| GET | `/process-inspection-plans/orders-without-plan` | IP |
| GET | `/process-inspection-plans/products-without-plan` | IP |
| GET | `/process-inspection-plans/products` | IP |
| GET | `/process-inspection-plans/products/{code}` | IP |

---

## Controle de Retrabalhos (`/retrabalhos`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/retrabalhos/health` | CR |
| GET | `/retrabalhos/filtros` | CR |
| GET | `/retrabalhos/resumo` | CR |
| GET | `/retrabalhos/rework_cost_pct` | CR |
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
| GET | `/refugos/scrap_cost_pct` | SM |
| GET | `/refugos/rankings` | SM |
| GET | `/refugos/serie` | SM |
| GET | `/refugos/registros` | SM |

Permissões: `scrap-monitoring.*` ou `api-delpi.access`. Filiais SC/ES (`01`/`02`). Legenda: **SM** = scrap-monitoring. Doc: [scrap-monitoring.md](./scrap-monitoring.md).

---


## Pedidos de venda em aberto (`/pedidos-venda-abertos`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/pedidos-venda-abertos/` | A ou `pedidos-venda-abertos.access` |
| POST | `/pedidos-venda-abertos/customers/enrichment` | A ou `pedidos-venda-abertos.access` |
| POST | `/pedidos-venda-abertos/customers/billing-series` | A ou `pedidos-venda-abertos.access` |

A lista base retorna a carteira completa de pedidos em aberto, sem paginação na
origem. `customers/enrichment` e `customers/billing-series` aceitam no máximo
200 clientes por requisição (`customers.max_length=200`). `billing-series`
aceita `start_date`/`end_date` (`YYYY-MM-DD`) e `granularity`
(`day|week|month|year`); `months` permanece o fallback quando o intervalo
não vem no body. Consumidores com carteiras maiores devem dividir em lotes
de até 200 e preservar a semântica de cobertura parcial: falha de um lote
não transforma campos ausentes em zero nem invalida os dados cobertos pelos
demais lotes. O MFE `commercial` chama billing diretamente na `api-delpi`;
não existe schema de billing duplicado no gateway `commercial-api`.

## Delpi Reports (`/reports`)

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/reports/definitions` | `reports.view` / manage / filial-* |
| POST | `/reports/definitions` | `reports.manage` / filial-* |
| GET | `/reports/definitions/{id}` | read |
| PATCH | `/reports/definitions/{id}` | write |
| GET | `/reports/runs` | read |
| GET | `/reports/providers` | read |

Doc: [delpi-reports.md](./delpi-reports.md)

## Canal de Denúncia — `/canal-denuncia`

| Método | Endpoint | Perm. |
|---|---|---|
| POST | `/canal-denuncia/denuncias` | `canal-denuncia.access` |
| POST | `/public/canal-denuncia/denuncias` | público |

Doc: [canal-denuncia.md](./canal-denuncia.md)

## Mural de Acessos — `/mural-acessos`

| Método | Endpoint | Perm. |
|---|---|---|
| GET | `/mural-acessos/hubs` | `mural-acessos.access` |
| POST | `/mural-acessos/hubs` | `mural-acessos.manage` |
| GET | `/mural-acessos/hubs/{id}/links` | access |
| POST | `/mural-acessos/hubs/{id}/links` | manage |
| GET | `/public/mural-acessos/menu/{token}` | público |

Doc: [mural-acessos.md](./mural-acessos.md)

## Indicadores Estratégicos

Rotas do painel SI estão em **`/apps/strategic-indicators-api/strategic-indicators`** — ver [05-indicadores-estrategicos.md](./05-indicadores-estrategicos.md) e [strategic-indicators-api/docs/API.md](../../../strategic-indicators-api/docs/API.md).

---

## Documentação e OpenAPI

| Recurso | Endpoint |
|---|---|
| Swagger UI | `/docs` |
| OpenAPI | `/openapi.json` |
