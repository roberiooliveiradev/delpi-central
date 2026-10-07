# DAVI capability expansion inventory

> Evidence artifact. **Not** runtime authority. **Not** the operational allowlist.

- Task: `DAVI-CAPABILITY-EXPANSION-INVENTORY-001`
- Source HEAD: `da479a85a552866d258eb765af40c6e664c801a4`
- origin/main: `3efdb7e21d007d20b3bdfda59008a13fd1da7cc2`
- OpenAPI/baseline: `3.0.3` / v3
- Generated at: `2026-10-07T12:30:12.113791+00:00`

## Executive summary

DAVI remains intelligence/orchestration over API DELPI. This inventory converts GET operations into semantic READ capabilities and freezes Wave 1 without promoting runtime eligibility.

- Technical operations: **737** (GET **536**)
- Current `DAVI_ELIGIBLE_READ`: **87**
- Current MCP tools: **2** `['discover_delpi_information', 'execute_delpi_information']`
- Proposed semantic capabilities: **39**
- Wave 1 frozen: **3** → expected eligible after implementation **90**
- Unassigned GETs (not capabilities): **471**

## Baseline

```json
{
  "TOTAL_OPERATIONS": 737,
  "TOTAL_GET": 536,
  "DAVI_ELIGIBLE_READ": 87,
  "ELIGIBLE_OPERATION_IDS": [
    "get_commercial_rol_by_branch",
    "get_commercial_rol_by_customer",
    "get_commercial_rol_by_product",
    "get_commercial_rol_series",
    "get_commercial_rol_summary",
    "get_new_business_rol_pct",
    "get_new_business_rol_target_pct",
    "get_new_clients_average",
    "get_new_clients_rol_pct",
    "get_on_time_delivery_pct",
    "get_overall_equipment_effectiveness_pct",
    "get_product_customers",
    "get_product_drawing",
    "get_product_factory_status",
    "get_product_guide",
    "get_product_inbound_invoice_items",
    "get_product_internal_movements",
    "get_product_last_purchase",
    "get_product_outbound_invoice_items",
    "get_product_parents",
    "get_product_pricing",
    "get_product_production_status",
    "get_product_purchase_price_history",
    "get_product_purchases",
    "get_product_raw_material_set_shortages",
    "get_product_sales_open_orders",
    "get_product_sales_summary",
    "get_product_shipping_status",
    "get_product_stock",
    "get_product_structure",
    "get_product_structure_exclusivity",
    "get_product_suppliers",
    "get_production_allocation_gaps",
    "get_production_appointments_produced_totals",
    "get_production_appointments_summary",
    "get_production_consumption_by_item",
    "get_production_consumption_top_items",
    "get_production_losses_records",
    "get_production_losses_top_materials",
    "get_production_machine_load_operations",
    "get_production_machine_load_work_centers",
    "get_production_oee",
    "get_production_oee_series",
    "get_production_orders_finished_without_consumption",
    "get_production_otd",
    "get_production_otd_series",
    "get_protheus_table",
    "get_sales_conversion_rate",
    "get_sales_conversion_rate_series",
    "get_sales_order_otd",
    "get_sales_order_otd_by_branch",
    "get_sales_order_otd_by_customer",
    "get_sales_order_otd_series",
    "get_sales_order_otd_series_by_customer",
    "get_sales_order_otd_summary",
    "get_supplies_cpv",
    "get_supplies_inventory_adjustments_summary",
    "get_supplies_inventory_turnover",
    "get_supplies_negotiation_savings_summary",
    "get_supplies_otd",
    "get_supplies_purchase_order_otd",
    "get_supplies_purchase_order_otd_series",
    "get_supplies_safety_stock_consumption_analysis_item_details",
    "get_supplies_safety_stock_consumption_analysis_items",
    "get_supplies_safety_stock_consumption_analysis_summary",
    "get_supplies_safety_stock_item_details",
    "get_supplies_safety_stock_item_suppliers",
    "get_supplies_safety_stock_items",
    "get_supplies_safety_stock_summary",
    "get_supplies_safety_stock_supplier_purchase_price_history",
    "get_supplies_stock_balances_items",
    "get_supplies_stock_balances_summary",
    "get_supplies_stock_value",
    "get_supplies_third_party_materials_shipments",
    "get_supplies_third_party_materials_summary",
    "get_weg_rol_target_pct",
    "list_exclusive_raw_materials_catalog",
    "list_product_drawings",
    "list_production_order_operation_materials",
    "list_protheus_table_columns",
    "list_supplies_inventory_adjustments",
    "list_supplies_purchase_request_lines",
    "search_products",
    "search_products_by_supplier_part_number",
    "search_protheus_columns_by_description",
    "search_protheus_columns_in_table",
    "search_tables_by_description"
  ],
  "STATUS_COUNTS": {
    "ADMIN_OUT_OF_SCOPE": 71,
    "DAVI_ELIGIBLE_READ": 87,
    "DESTRUCTIVE_OUT_OF_SCOPE": 17,
    "GENERIC_SQL_FORBIDDEN": 2,
    "LEGACY_UNSAFE": 2,
    "NEEDS_BOUNDED_EXECUTION": 3,
    "NEEDS_MODEL_SAFE_PROJECTION": 338,
    "NEEDS_NESTED_PROJECTION_SUPPORT": 51,
    "SEMANTICALLY_REDUNDANT": 3,
    "STREAM_BINARY_OUT_OF_SCOPE": 33,
    "WRITE_OUT_OF_SCOPE": 130
  }
}
```

## Domain coverage (GET operations)

| Domain | GET ops | Semantic capabilities | Currently eligible | Wave 1 freeze | Main technical blockers |
|---|---:|---:|---:|---:|---|
| `admin` | 29 | 0 | 5 | 0 | ADMIN_OUT_OF_SCOPE:12, NEEDS_MODEL_SAFE_PROJECTION:9, DAVI_ELIGIBLE_READ:5, LEGACY_UNSAFE:2 |
| `commercial` | 55 | 4 | 18 | 0 | NEEDS_MODEL_SAFE_PROJECTION:25, DAVI_ELIGIBLE_READ:18, NEEDS_NESTED_PROJECTION_SUPPORT:11, STREAM_BINARY_OUT_OF_SCOPE:1 |
| `dashboards` | 75 | 0 | 0 | 0 | NEEDS_MODEL_SAFE_PROJECTION:73, NEEDS_NESTED_PROJECTION_SUPPORT:2 |
| `engineering` | 36 | 1 | 0 | 0 | NEEDS_MODEL_SAFE_PROJECTION:24, ADMIN_OUT_OF_SCOPE:6, STREAM_BINARY_OUT_OF_SCOPE:4, NEEDS_NESTED_PROJECTION_SUPPORT:2 |
| `financial` | 73 | 1 | 0 | 0 | NEEDS_MODEL_SAFE_PROJECTION:61, ADMIN_OUT_OF_SCOPE:8, STREAM_BINARY_OUT_OF_SCOPE:4 |
| `hr` | 5 | 1 | 0 | 0 | NEEDS_MODEL_SAFE_PROJECTION:4, NEEDS_NESTED_PROJECTION_SUPPORT:1 |
| `inspection` | 21 | 2 | 0 | 0 | NEEDS_MODEL_SAFE_PROJECTION:19, NEEDS_NESTED_PROJECTION_SUPPORT:2 |
| `product` | 36 | 20 | 25 | 3 | DAVI_ELIGIBLE_READ:25, NEEDS_NESTED_PROJECTION_SUPPORT:6, SEMANTICALLY_REDUNDANT:2, STREAM_BINARY_OUT_OF_SCOPE:2 |
| `production` | 53 | 4 | 17 | 0 | NEEDS_MODEL_SAFE_PROJECTION:21, DAVI_ELIGIBLE_READ:17, NEEDS_NESTED_PROJECTION_SUPPORT:14, SEMANTICALLY_REDUNDANT:1 |
| `quality` | 99 | 2 | 0 | 0 | NEEDS_MODEL_SAFE_PROJECTION:75, STREAM_BINARY_OUT_OF_SCOPE:12, NEEDS_NESTED_PROJECTION_SUPPORT:10, ADMIN_OUT_OF_SCOPE:2 |
| `reports` | 11 | 0 | 0 | 0 | NEEDS_MODEL_SAFE_PROJECTION:11 |
| `scheduling` | 6 | 0 | 0 | 0 | NEEDS_MODEL_SAFE_PROJECTION:6 |
| `supplies` | 37 | 4 | 22 | 0 | DAVI_ELIGIBLE_READ:22, NEEDS_MODEL_SAFE_PROJECTION:9, NEEDS_NESTED_PROJECTION_SUPPORT:3, STREAM_BINARY_OUT_OF_SCOPE:3 |

## Semantic clusters

- `product.master.search` — Buscar cadastro de produto [CURRENTLY_ELIGIBLE] wave=— ops=`search_products`
- `product.stock.availability` — Saldo de estoque do produto [CURRENTLY_ELIGIBLE] wave=— ops=`get_product_stock`
- `product.supplier.relationship` — Fornecedores do produto [CURRENTLY_ELIGIBLE] wave=— ops=`get_product_suppliers`
- `product.customer.relationship` — Clientes do produto [CURRENTLY_ELIGIBLE] wave=— ops=`get_product_customers`
- `product.purchasing.history` — Compras do produto [CURRENTLY_ELIGIBLE] wave=— ops=`get_product_purchases`
- `product.structure.bom` — Estrutura / BOM do produto [CURRENTLY_ELIGIBLE] wave=— ops=`get_product_structure`
- `product.production.status` — Situação produtiva do produto [CURRENTLY_ELIGIBLE] wave=— ops=`get_product_production_status`
- `product.factory.status` — Status fabril consolidado do produto [READY_FOR_FREEZE] wave=WAVE_1 ops=`get_product_factory_status`
- `product.structure.exclusivity` — Exclusividade de matérias-primas na estrutura [READY_FOR_FREEZE] wave=WAVE_1 ops=`get_product_structure_exclusivity`
- `product.shipping.status` — Status de expedição do produto [READY_FOR_FREEZE] wave=WAVE_1 ops=`get_product_shipping_status`
- `product.master.detail` — Ficha cadastral detalhada do produto [SEMANTICALLY_REDUNDANT] wave=— ops=`get_product_detail`
- `product.snapshot.summary` — Resumo leve do produto [NEEDS_SEMANTIC_CONTRACT] wave=— ops=`get_product_summary`
- `product.commercial.pricing` — Preços comerciais do produto [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_2 ops=`get_product_pricing`
- `product.purchase.price_history` — Histórico de preço de compra da MP [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_2 ops=`get_product_purchase_price_history`
- `product.raw_material.price_intelligence` — Inteligência de preço de matéria-prima [NEEDS_NESTED_PROJECTION_SUPPORT] wave=WAVE_2 ops=`get_product_raw_material_price_intelligence`
- `product.cost.impact_simulation` — Simulação de impacto de custo do PA [NEEDS_NESTED_PROJECTION_SUPPORT] wave=WAVE_2 ops=`get_product_cost_impact_simulation`
- `product.where_used` — Onde o produto é usado [NEEDS_NESTED_PROJECTION_SUPPORT] wave=WAVE_3 ops=`get_product_parents`
- `product.routing.guide` — Roteiro de produção do produto [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_3 ops=`get_product_guide`
- `product.quality.inspection` — Inspeção de qualidade do produto [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_4 ops=`get_product_inspection`
- `product.raw_material.set_shortages` — Ruptura de MP no conjunto de OPs do PA [NEEDS_NESTED_PROJECTION_SUPPORT] wave=WAVE_3 ops=`get_product_raw_material_set_shortages`
- `supplies.purchase_requests.status` — Status de solicitações de compra [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_3 ops=`get_supplies_purchase_requests_open_coverage`, `get_supplies_purchase_request_lines`
- `supplies.purchase_order.otd` — OTD de pedidos de compra [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_3 ops=`get_supplies_purchase_order_otd`, `get_supplies_purchase_order_otd_panel`, `get_supplies_purchase_order_otd_series`, `get_supplies_otd`
- `supplies.stock.balances` — Saldos de estoque de suprimentos [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_3 ops=`get_supplies_stock_balances_summary`, `get_supplies_stock_balances_items`, `get_supplies_stock_value`
- `supplies.safety_stock.summary` — Resumo de estoque de segurança [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_3 ops=`get_supplies_safety_stock_summary`, `get_supplies_safety_stock_items`
- `production.oee` — OEE de produção [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_3 ops=`get_production_oee`, `get_production_oee_series`, `get_overall_equipment_effectiveness_pct`
- `production.otd` — OTD de produção [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_3 ops=`get_on_time_delivery_pct`
- `production.machine_load` — Carga de máquinas [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_3 ops=`get_production_machine_load_work_centers`, `get_production_machine_load_operations`
- `production.appointments.summary` — Resumo de apontamentos de produção [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_3 ops=`get_production_appointments_summary`, `get_production_appointments_produced_totals`
- `commercial.rol.summary` — ROL comercial resumido [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_4 ops=`get_commercial_rol_summary`, `get_commercial_rol_series`, `get_commercial_rol_by_branch`
- `commercial.sales_order.otd` — OTD de pedidos de venda [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_4 ops=`get_sales_order_otd`, `get_sales_order_otd_summary`, `get_sales_order_otd_panel`
- `commercial.conversion.rate` — Taxa de conversão comercial [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_4 ops=`get_sales_conversion_rate`, `get_sales_conversion_rate_series`
- `commercial.proposals.status` — Status de propostas comerciais [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_4 ops=`list_commercial_proposals`, `get_commercial_proposal`, `list_propostas_comerciais`, `get_proposta_comercial`
- `quality.nonconformity.summary` — Resumo de não conformidades [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_4 ops=`get_nonconformity_series`, `get_nonconformity_streak`
- `inspection.inbound.summary` — Resumo de inspeção de entrada [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_4 ops=`get_inspecoes_entrada_resumo`, `get_inspecoes_entrada_pendentes`
- `inspection.process.summary` — Resumo de inspeção de processo [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_4 ops=`get_inspecoes_processo_resumo`
- `quality.audit_5s.summary` — Resumo de auditoria 5S [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_4 ops=`get_audit_5s_summary`, `get_audit_5s_summary_series`
- `engineering.lmp.dashboard` — Painel de LMPs [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_4 ops=`get_lmps_dashboard_summary`, `list_lmps_dashboard`
- `financial.overdue.summary` — Resumo de inadimplência [NEEDS_MODEL_SAFE_PROJECTION] wave=WAVE_5 ops=`get_financeiro_inadimplencia_resumo`, `get_financeiro_inadimplencia_faixas_atraso`, `get_financeiro_inadimplencia_mensal`
- `hr.workforce.snapshot` — Snapshot de RH [NEEDS_PRIVACY_REVIEW] wave=— ops=`get_hr_snapshot`, `get_hr_active_pdi_count`

## Redundancies

- **RG-PRODUCT-MASTER**: `search_products`, `get_product_detail` → `product.master.search`. Keep search_products as the only Product Master DAVI capability. get_product_detail is SEMANTICALLY_REDUNDANT.
- **RG-PRODUCT-SUMMARY-COMPOSITE**: `get_product_summary`, `search_products`, `get_product_stock`, `get_product_pricing` → `product.snapshot.summary`. DEFER summary. Without prices it duplicates search+stock; with prices it belongs to Wave 2.
- **RG-PRODUCT-STRUCTURE**: `get_product_structure`, `get_product_structure_excel`, `get_product_structure_exclusivity`, `list_exclusive_raw_materials_catalog` → `product.structure.bom + product.structure.exclusivity`. BOM and exclusivity are distinct. Excel export remains STREAM_BINARY_OUT_OF_SCOPE. Global exclusive catalog is a later sibling, not Wave 1.
- **RG-PRODUCT-FACTORY-SLICES**: `get_product_factory_status`, `get_product_production_status`, `get_product_shipping_status`, `get_product_structure` → `product.factory.status (classified snapshot)`. Factory capability exposes summaries/indicators only. Do not dump sibling item arrays.
- **RG-PRODUCT-ECONOMIC**: `get_product_pricing`, `get_product_purchase_price_history`, `get_product_raw_material_price_intelligence`, `get_product_cost_impact_simulation`, `get_product_last_purchase` → `Wave 2 economic cluster`. DEFER as a governed economic wave. Not confidentiality-blocked merely because monetary.
- **RG-STOCK-GRAIN**: `get_product_stock`, `get_supplies_stock_balances_summary`, `get_supplies_stock_balances_items`, `get_supplies_stock_value` → `product.stock.availability vs supplies.stock.balances`. Different grain (one code vs company/warehouse). Keep separate capabilities.
- **RG-OTD-SURFACES**: `get_on_time_delivery_pct`, `get_supplies_purchase_order_otd`, `get_sales_order_otd` → `domain-specific OTD capabilities`. Do not merge production/supplies/commercial OTD into one alias set.
- **RG-COMMERCIAL-PROPOSALS-DUAL-PATH**: `list_commercial_proposals`, `get_commercial_proposal`, `list_propostas_comerciais`, `get_proposta_comercial` → `commercial.proposals.status`. English and Portuguese technical routes are one commercial proposal capability. PDF export remains binary/out of scope.
- **RG-PURCHASE-LANGUAGE**: `get_product_purchases`, `get_supplies_purchase_request_lines`, `get_supplies_purchase_requests_open_coverage` → `product.purchasing.history vs supplies.purchase_requests.status`. Disambiguate aliases: compras do produto vs solicitação/requisição de compra.

## High-value / seeded candidates

- `get_product_detail` → **REDUNDANT**
- `get_product_summary` → **DEFER**
- `get_product_factory_status` → **PROMOTE**
- `get_product_structure_exclusivity` → **PROMOTE**
- `get_product_pricing` → **DEFER**
- `get_product_purchase_price_history` → **DEFER**
- `get_product_raw_material_price_intelligence` → **DEFER**
- `get_product_cost_impact_simulation` → **DEFER**

## Wave plan

### WAVE_1 — Operational Product Intelligence (classified factory snapshot + MP exclusivity + shipping)

`product.factory.status`, `product.structure.exclusivity`, `product.shipping.status`

Evidence-driven alternative to seeding product.snapshot.summary. These three expand distinct operational questions, reuse generic nested projection, keep MCP tools=3, and avoid promoting prices or redundant master/stock slices. Size 3 is enough to validate composite summaries, playbook_report lists, and sibling disambiguation.

### WAVE_2 — Product Economic Intelligence

`product.commercial.pricing`, `product.purchase.price_history`, `product.raw_material.price_intelligence`, `product.cost.impact_simulation`

High business value and proven backend AuthZ; blocked only by model-safe nested/flat projection + quarantine narrowing for price/cost tokens.

### WAVE_3 — Supplies / Production Operational Intelligence

`supplies.purchase_requests.status`, `supplies.purchase_order.otd`, `supplies.stock.balances`, `supplies.safety_stock.summary`, `production.oee`, `production.otd`, `production.machine_load`, `production.appointments.summary`, `product.raw_material.set_shortages`, `product.routing.guide`, `product.where_used`

Canonical routes exist; owner/AuthZ still TO_INVENTORY for several Supplies/Production handlers; projection and volume bounds required.

### WAVE_4 — Commercial / Quality / Inspection / Engineering

`commercial.rol.summary`, `commercial.sales_order.otd`, `commercial.conversion.rate`, `commercial.proposals.status`, `quality.nonconformity.summary`, `inspection.inbound.summary`, `inspection.process.summary`, `quality.audit_5s.summary`, `engineering.lmp.dashboard`, `product.quality.inspection`

Aggregated business questions are evident from route semantics; privacy/attachment exclusions remain.

### WAVE_5 — Financial aggregates (not title-level PII dumps)

`financial.overdue.summary`

Financial READ is not forbidden; start from aggregates. HR remains privacy-blocked.

## Wave 1 freeze

Status: **FROZEN_FOR_IMPLEMENTATION**

Capabilities: `product.factory.status`, `product.structure.exclusivity`, `product.shipping.status`

Normative freeze contract: `davi-capability-wave-001-freeze.md`.

## Gaps

- Unassigned GET operations: 471
- Second-user negative AuthZ: `TEST_NOT_RUN`
- MCP rate policy: TO_INVENTORY — overall rollout decision remains separate
- HR: REQUIRED before any HR capability promotion

## Next step

Architecture Acceptance → `DAVI-CAPABILITY-EXPANSION-WAVE-001` implementation. Do not implement in this evidence task.
