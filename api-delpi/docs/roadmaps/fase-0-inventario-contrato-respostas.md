# Fase 0 — Inventário e baseline (contrato api-delpi)

**Playbook:** [`playbook-10-contrato-respostas-api-delpi.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-10-contrato-respostas-api-delpi.md)  
**Data:** jun/2026  
**Status:** baseline congelado para fases 1–7

---

## 1. Envelope atual (todos os consumidores)

```json
{
  "success": true,
  "message": "Operação realizada com sucesso",
  "data": {}
}
```

| Campo | Presente hoje | Consumidores que leem |
|-------|---------------|------------------------|
| `success` | Sim | MFEs, SI (`DelpiApiClient`), chat |
| `message` | Sim | MFEs (erro), chat |
| `data` | Sim | **Todos** — contrato legado |
| `meta` | Sim (jun/2026 — rotas envelope) | Chat, ferramentas novas |
| `error` | Não (Fase 2) | — |

Erro hoje: `{ "success": false, "message": "..." }` ou HTTP 404 com `{ "detail": "Not Found" }` (rotas de produto).

Implementação: `api-delpi/app/core/responses.py`.

---

## 2. Matriz rota × `operationId` × `meta.shape` (chat-critical)

Perfis propostos para Fase 3 (`meta.shape`). `operationId` após Fase 1 em produtos; demais conforme catálogo OpenAPI.

### Produtos (`/products`)

| Rota | `operationId` | `meta.shape` | `meta.entity` | Notas |
|------|---------------|--------------|---------------|-------|
| `GET /search` | `search_products` | `paged_list` | `product_search` | `items[]` paginado |
| `GET /{code}` | `get_product_detail` | `product_snapshot` | `product` | `data.product` |
| `GET /{code}/summary` | `get_product_summary` | `product_snapshot` | `product` | product + stock[] + prices[] |
| `GET /{code}/analyser` | `get_product_analyser` | `composite_analysis` | `product_analyser` | product, structure, guide, inspection |
| `GET /{code}/stock` | `get_product_stock` | `paged_list` | `product_stock` | Page em `data` |
| `GET /{code}/structure` | `get_product_structure` | `hierarchy` | `product_structure` | `root` + `items[]` recursivos |
| `GET /{code}/structure/exclusivity` | `get_product_structure_exclusivity` | `playbook_report` | `product_structure_exclusivity` | items + summary |
| `GET /{code}/production-status` | `get_product_production_status` | `playbook_report` | `product_production_status` | items + summary |
| `GET /{code}/shipping-status` | `get_product_shipping_status` | `playbook_report` | `product_shipping_status` | items + summary |
| `GET /{code}/factory-status` | `get_product_factory_status` | `composite_analysis` | `product_factory_status` | seções structure/production/shipping |
| `GET /{code}/parents` | `get_product_parents` | `hierarchy` | `product_parents` | árvore reversa |
| `GET /{code}/guide` | `get_product_guide` | `paged_list` | `product_guide` | roteiro paginado |
| `GET /{code}/inspection` | `get_product_inspection` | `paged_list` | `product_inspection` | ≠ shipping-status |
| `GET /{code}/pricing` | `get_product_pricing` | `scalar` | `product_pricing` | tabelas de preço |
| `GET /{code}/purchases` | `get_product_purchases` | `paged_list` | `product_purchases` | |
| `GET /{code}/sales` | `get_product_sales_summary` | `scalar` | `product_sales` | |
| `GET /{code}/sales/open-orders` | `get_product_sales_open_orders` | `paged_list` | `product_open_orders` | |
| `GET /{code}/sales/billing` | `get_product_sales_billing` | `scalar` | `product_billing` | |
| `GET /{code}/suppliers` | `get_product_suppliers` | `paged_list` | `product_suppliers` | |
| `GET /{code}/customers` | `get_product_customers` | `paged_list` | `product_customers` | |
| `GET /{code}/internal-movements` | `get_product_internal_movements` | `paged_list` | `product_internal_movements` | |

### Suprimentos (`/supplies`) — chat + SI + dashboard-supplies

| Rota | `operationId` | `meta.shape` | Consumidor direto |
|------|---------------|--------------|-------------------|
| `GET /cpv` | `get_supplies_cpv` | `scalar` | supplies MFE, SI |
| `GET /otd` | `get_supplies_otd` | `scalar` | supplies MFE, SI |
| `GET /stock-value` | `get_supplies_stock_value` | `scalar` | supplies MFE, SI |
| `GET /inventory-turnover` | `get_supplies_inventory_turnover` | `scalar` | supplies MFE, SI |
| `GET /negotiation-savings/summary` | `get_supplies_negotiation_savings_summary` | `scalar` | SI |

### Engenharia (`/engineering`) — chat + LMP MFEs

| Rota | `operationId` | `meta.shape` | Consumidor direto |
|------|---------------|--------------|-------------------|
| `GET /lmps` | `list_lmps` | `paged_list` | chat, dashboard-lmps |
| `GET /lmps/dashboard` | `list_lmps_dashboard` | `composite_analysis` | dashboard-lmps, engineering |
| `GET /lmps/dashboard/summary` | *(auto)* | `scalar` | chat, SI, dashboard-lmps |
| `GET /lmps/dashboard/items` | *(auto)* | `paged_list` | dashboard-lmps |
| `GET /lmps/dashboard/charts` | *(auto)* | `scalar` | dashboard-lmps |
| `GET /lmps/{sale_number}` | `get_lmp_by_sale_number` | `product_snapshot` | chat |
| `GET /transforma-mais/processes` | *(auto)* | `paged_list` | dashboard-engineering |
| `GET /transforma-mais/processes/summary` | *(auto)* | `scalar` | chat, engineering |

### SQL e vendas

| Rota | `operationId` | `meta.shape` |
|------|---------------|--------------|
| `POST /data/sql` | `execute_readonly_sql` | `paged_list` |
| `GET /sales/` | `list_sale_orders` | `paged_list` |

Catálogo OpenAPI completo (83 rotas): [`minha-delpi-ai-api/docs/knowledge/_generated/api-delpi-openapi-catalog.md`](../../../minha-delpi-ai-api/docs/knowledge/_generated/api-delpi-openapi-catalog.md).

---

## 3. Matriz rota × consumidor

Legenda: **D** = HTTP direto no browser/serviço; **I** = indireto (via outro backend).

### Plugins MFE (HTTP direto — `ApiSuccessResponse` → `data`)

| Plugin | Prefixo | Rotas principais | Parse |
|--------|---------|-------------------|-------|
| `dashboard-supplies` | `/supplies` | `/cpv`, `/otd`, `/stock-value`, `/inventory-turnover` | `suppliesApi.ts` |
| `dashboard-commercial` | `/commercial` | `/closing-rate`, `/proposals`, `/rol/series`, OTD, ROL novos negócios | `commercialApi.ts` |
| `dashboard-production` | `/production` | OEE, OTD, custos, séries | `productionApi.ts` |
| `dashboard-financial` | `/financial` | `/rol`, `/ebitda_pct`, `/fixed_cost_pct`, `/pmr` | `financialApi.ts` |
| `dashboard-quality` | `/quality` | `/nonconformities`, `/ppm/*`, `/kaizens/summary`, `/audit-5s/summary` | `qualityApi.ts` |
| `dashboard-engineering` | `/engineering` | `/transforma-mais/processes*` | `engineeringApi.ts` |
| `dashboard-hr` | `/hr` | `/snapshot`, `/branches` | `hrApi.ts` |
| `dashboard-lmps` | `/engineering/lmps` | list, dashboard, summary, charts, items | `lmpApi.ts` |
| `dashboard-delpi` | `/products` | `/search`, listagem paginada | `delpiApi.ts` |
| `central-agendamento` | `/scheduling` | `/resources`, `/bookings` | `schedulingApi.ts` |
| `auditoria-5s` | `/quality/audit-5s` | `/areas`, `/audits`, NC, anexos | `audit5sApi.ts` + Socket.IO |
| `eficiencia-fabril` | `/production` | `/eficiencia-fabril/dashboard`, `/appointments` | `eficienciaFabrilApi.ts` |

### Backends e shell

| Consumidor | Tipo | Rotas api-delpi | Cliente |
|------------|------|-----------------|---------|
| **strategic-indicators-api** | D (server) | `/financial/*`, `/commercial/*`, `/production/*`, `/supplies/*`, `/quality/*`, `/engineering/lmps/*` | `shared/delpi_api_client/client.py` |
| **minha-delpi-ai-api** | D (server) | OpenAPI actions (produtos, KPIs, SQL, …) | HTTP + `ExternalActionResultPresenter` |
| **portal** | D (browser) | `/health`, `/products`, `/system/status` | `portal/src/data/delpiApi.ts` |
| **plugin strategic-indicators** | I | — | `strategic-indicators-api` |
| **plugin minha-delpi-chat** | I | — | `minha-delpi-ai-api` |
| **plugin transformometro** | — | sem integração api-delpi hoje | `transformometro-api` |

### SI — mapa gateway → método `DelpiApiClient`

| Domínio SI | Métodos client | Paths api-delpi |
|------------|----------------|-----------------|
| Financial | `get_rol`, `get_ebitda_pct`, `get_fixed_cost_pct`, `get_pmr` | `/financial/rol`, `ebitda_pct`, `fixed_cost_pct`, `pmr` |
| Commercial | `get_new_business_rol_pct`, `get_sales_conversion_rate`, `get_sales_order_otd` | `/commercial/new-business-rol-pct`, `closing-rate`, `sales-order-otd` |
| Production | `get_overall_equipment_effectiveness`, `get_on_time_delivery`, custos % | `/production/overall_equipment_effectiveness_pct`, `on_time_delivery_pct`, … |
| Supplies | `get_cpv`, `get_supplies_otd`, `get_stock_value`, `get_inventory_turnover`, `get_supplies_negotiation_savings_summary` | `/supplies/*` |
| Quality | `get_ppm_summary`, `get_kaizen_summary`, `get_audit_5s_summary` | `/quality/ppm/{type}/summary`, `kaizens/summary`, `audit-5s/summary` |
| Engineering | `get_lmp`, `get_lmp_dashboard_summary`, `list_lmps` | `/engineering/lmps/*` |

---

## 4. Checklist — rotas **sem** `agent_route()` (chat-critical)

Rotas usadas pelo chat que ainda dependem de `operationId` auto-gerado ou summary genérico:

| Rota | Prioridade Fase 1 | Observação |
|------|-------------------|------------|
| `GET /engineering/lmps/dashboard/summary` | Alta | ✅ Fase 1 — `get_lmps_dashboard_summary` |
| `GET /engineering/lmps/dashboard/items` | Média | ✅ Fase 1 — `list_lmps_dashboard_items` |
| `GET /engineering/lmps/dashboard/charts` | Média | ✅ Fase 1 — `get_lmps_dashboard_charts` |
| `GET /engineering/transforma-mais/processes` | Alta | ✅ Fase 1 — `list_transforma_mais_processes` |
| `GET /engineering/transforma-mais/processes/summary` | Alta | ✅ Fase 1 — `get_transforma_mais_summary` |
| `GET /products/{code}/inbound-invoice-items` | Baixa | NF entrada |
| `GET /products/{code}/outbound-invoice-items` | Baixa | NF saída |
| `GET /products/{code}/structure/excel` | N/A | Export arquivo — fora do chat |

Rotas de **dashboard** (financial, commercial, production, quality, hr): sem `agent_route` por design — consumidas por MFE/SI, não prioridade do guia 11.

---

## 5. Fixtures de baseline

Arquivos em `minha-delpi-ai-api/tests/fixtures/api_delpi_responses/`:

| Arquivo | Rota | Código ref. |
|---------|------|-------------|
| `product_search.json` | `GET /products/search` | `90269001` (PA fictício) |
| `product_detail_90269001.json` | `GET /products/{code}` | `90269001` |
| `product_summary_90269001.json` | `GET /products/{code}/summary` | `90269001` |
| `product_stock_90269001.json` | `GET /products/{code}/stock` | `90269001` |
| `product_structure_90269001.json` | `GET /products/{code}/structure` | `90269001` + PI `50219001` + MP `10019001` |
| `product_analyser_90269001.json` | `GET /products/{code}/analyser` | `90269001` |
| `product_factory_status_90269002.json` | `GET /products/{code}/factory-status` | `90269002` |
| `supplies_cpv.json` | `GET /supplies/cpv` | filial 01 |

> Fixtures são **estruturais** (formato envelope + shape de `data`). Códigos **fictícios** com prefixos do ERP: PA `9026xxxx`, PI `502xxxxx`, MP `1001xxxx`–`1021xxxx`. Não usar códigos de itens reais da empresa.

Loader para testes: `minha-delpi-ai-api/tests/fixtures/api_delpi_responses_loader.py`.

---

## 6. Critérios de aceite Fase 0

- [x] Matriz rota × `operationId` × `meta.shape` (§ 2)
- [x] Matriz rota × consumidor (§ 3)
- [x] ≥ 8 fixtures versionadas (§ 5)
- [x] Checklist rotas sem `agent_route` (§ 4)
- [ ] Revisão formal time plugins/SI (pendente)

**Próximo passo:** Fase 2 — envelope de erro unificado + reimport OpenAPI no chat após deploy.
