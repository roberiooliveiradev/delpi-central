# DAVI — API DELPI operation inventory (generated)

> Evidence artifact. Not runtime authority. Not semantic capability catalog.

- Task: `DAVI-REAL-USER-RETRIEVAL-REFINEMENT-COMMERCIAL-SUPPLIES-001`
- Source: `openapi_baseline.json` version `3`
- TOTAL OPERATIONS: **720**
- TOTAL GET: **520**
- WRITE VERBS (POST/PUT/PATCH/DELETE): **200**
- DAVI_ELIGIBLE_READ (before→after): **53 → 53**
- NEWLY ELIGIBLE: **0**

## Coverage decision

```json
{
  "taskId": "DAVI-REAL-USER-RETRIEVAL-REFINEMENT-COMMERCIAL-SUPPLIES-001",
  "decision": "REFINE_REAL_USER_RETRIEVAL_COMMERCIAL_SUPPLIES",
  "reason": "Refine Commercial+Supplies real-user retrieval via durable semanticAliases plus generic filler-tolerant phrase matching and single-token phrase cap. Eligible READ remains 53; MCP tools remain 3. No AuthZ/business-logic change.",
  "previousDecision": {
    "taskId": "DAVI-WAVE005-STOCK-BALANCES-RETRIEVAL-CORRECTION-001",
    "decision": "CORRECT_STOCK_BALANCES_SUMMARY_ITEMS_RETRIEVAL"
  }
}
```

## Inventory delta

```json
{
  "previous_total_operations": 720,
  "current_total_operations": 720,
  "previous_total_get": 520,
  "current_total_get": 520,
  "added_operations": 0,
  "removed_operations": 0,
  "note": "Delta vs last committed inventory artifact (HEAD)"
}
```

## Status counts

| Status | Count |
|---|---:|
| `ADMIN_OUT_OF_SCOPE` | 76 |
| `DAVI_ELIGIBLE_READ` | 53 |
| `DESTRUCTIVE_OUT_OF_SCOPE` | 17 |
| `GENERIC_SQL_FORBIDDEN` | 2 |
| `LEGACY_UNSAFE` | 2 |
| `NEEDS_MODEL_SAFE_PROJECTION` | 338 |
| `NEEDS_NESTED_PROJECTION_SUPPORT` | 66 |
| `SEMANTICALLY_REDUNDANT` | 1 |
| `STREAM_BINARY_OUT_OF_SCOPE` | 33 |
| `WRITE_OUT_OF_SCOPE` | 132 |

## Eligible operationIds

- `get_commercial_rol_by_branch`
- `get_commercial_rol_by_customer`
- `get_commercial_rol_by_product`
- `get_commercial_rol_series`
- `get_commercial_rol_summary`
- `get_new_business_rol_pct`
- `get_new_business_rol_target_pct`
- `get_new_clients_average`
- `get_new_clients_rol_pct`
- `get_product_customers`
- `get_product_drawing`
- `get_product_factory_status`
- `get_product_guide`
- `get_product_last_purchase`
- `get_product_parents`
- `get_product_pricing`
- `get_product_production_status`
- `get_product_purchase_price_history`
- `get_product_purchases`
- `get_product_shipping_status`
- `get_product_stock`
- `get_product_structure`
- `get_product_structure_exclusivity`
- `get_product_suppliers`
- `get_sales_conversion_rate`
- `get_sales_conversion_rate_series`
- `get_sales_order_otd`
- `get_sales_order_otd_by_branch`
- `get_sales_order_otd_by_customer`
- `get_sales_order_otd_series`
- `get_sales_order_otd_series_by_customer`
- `get_sales_order_otd_summary`
- `get_supplies_cpv`
- `get_supplies_inventory_turnover`
- `get_supplies_negotiation_savings_summary`
- `get_supplies_otd`
- `get_supplies_purchase_order_otd`
- `get_supplies_purchase_order_otd_series`
- `get_supplies_safety_stock_consumption_analysis_items`
- `get_supplies_safety_stock_consumption_analysis_summary`
- `get_supplies_safety_stock_item_suppliers`
- `get_supplies_safety_stock_items`
- `get_supplies_safety_stock_summary`
- `get_supplies_safety_stock_supplier_purchase_price_history`
- `get_supplies_stock_balances_items`
- `get_supplies_stock_balances_summary`
- `get_supplies_stock_value`
- `get_supplies_third_party_materials_shipments`
- `get_supplies_third_party_materials_summary`
- `get_weg_rol_target_pct`
- `list_product_drawings`
- `list_supplies_purchase_request_lines`
- `search_products`

## High-value blocked (primary blocker)

- `get_product_detail` → `SEMANTICALLY_REDUNDANT` — Same Product Master slice already served by search_products; no distinct governed fields
- `get_product_summary` → `DEFER` — Composite product snapshot remains deferred; not a Wave 2 READ capability
- `get_product_raw_material_price_intelligence` → `DEFER` — Unbounded budget scan / composite overlap / no bounded summaries-only backend contract
- `get_product_cost_impact_simulation` → `PREPARE` — Compute-only simulation is PREPARE, not READ. HTTP GET does not imply semantic READ. Not executable through the READ broker.
- `get_product_drawing_pdf` → `NEEDS_GENERIC_DOCUMENT_BOUNDARY` — Binary PDF document transport is not a JSON READ projection. Must not embed pdf_base64 in execute_delpi_information. Requires generic authorized document boundary (ARCHITECTURE_ESCALATION if new MCP tool/resource). AuthZ remains API_DELPI_ACCESS on the HTTP route.
- `get_product_analyser` → `PRODUCT_ANALYSER_DIRECT_PROMOTION_NOT_REQUIRED` — ProductAnalyserUseCase composes product/structure/guide/inspection JSON — it does not perform visual drawing analysis. Drawing analysis must reuse AI API workflow procedure + governed individual READs + document transport, not promote this composite.
- `get_product_inspection` → `DEFER` — Drawing analysis inspection cross-check deferred (DRAWING_ANALYSIS_INSPECTION_CROSSCHECK=DEFERRED). Not required for JSON drawing catalog/metadata foundation.
- `get_sales_order_otd_panel` → `NEEDS_NESTED_LINE_DRILLDOWN_CONTRACT` — Wave 004 candidate deferred: line-level panel with insights arrays and page_size≤1000 is a drill-down sibling to get_sales_order_otd_line_detail; needs separate nested model-safe contract review before READ broker promotion.
- `get_sales_order_otd_line_detail` → `OUT_OF_WAVE_004` — Explicitly out of Wave 004 commercial analytics family — proposal/detail/drill-down surface.
- `list_commercial_proposals` → `OUT_OF_WAVE_004` — Proposal workflow family — out of Wave 004 analytics READ scope.
- `get_commercial_proposal` → `OUT_OF_WAVE_004` — Proposal detail — out of Wave 004 analytics READ scope.
- `get_commercial_proposal_history_events` → `OUT_OF_WAVE_004` — Proposal history — out of Wave 004 analytics READ scope.
- `summarize_commercial_proposals_by_collaborator` → `OUT_OF_WAVE_004` — Proposal collaborator summary — out of Wave 004 analytics READ scope.
- `get_supplies_purchase_order_otd_panel` → `NEEDS_NESTED_LINE_DRILLDOWN_CONTRACT` — Analogous to commercial OTD panel — line drill-down with large page_size; defer to detailed wave.
- `get_supplies_purchase_requests_open_coverage` → `UNBOUNDED_LIST_NO_PAGINATION` — Returns all open SC coverage items/products without page/page_size; needs owner-side bound or pagination.
- `get_supplies_purchase_request_lines` → `SINGLE_REQUEST_DETAIL` — Single SC detail by branch/request_number; promote list_supplies_purchase_request_lines first.
- `get_supplies_safety_stock_filters` → `UI_FILTER_HELPER` — UI filter options helper, not a primary information capability.
- `get_supplies_safety_stock_item_details` → `COMPOSITE_ANALYSIS` — composite_analysis detail needs separate nested contract review.
- `get_supplies_safety_stock_consumption_analysis_item_details` → `COMPOSITE_ANALYSIS` — Includes calculation_memory and monthly series — defer nested detail wave.
- `get_supplies_third_party_materials_shipment` → `SHIPMENT_DETAIL` — Single shipment detail with returns nested — defer after list shipments proves stable.
- `list_supplies_purchase_request_recent_linked_orders` → `POLLING_CURSOR_HELPER` — after_recno polling helper for BFF sync, not primary DAVI Q&A capability.
- `list_supplies_purchase_request_recent_linked_receipts` → `POLLING_CURSOR_HELPER` — after_recno polling helper for BFF sync, not primary DAVI Q&A capability.
- `list_supplies_purchase_request_requesters_route_supplies_purchase_requests_requesters_get` → `PII_LOOKUP_HELPER` — Requester lookup for UI filters; PII/identity helper without clear standalone information need.
- `get_protheus_user_by_email_route_supplies_protheus_users_by_email_get` → `PII_IDENTITY_LOOKUP` — Email→Protheus user identity lookup; not a Supplies information capability for DAVI.
- `export_supplies_third_party_materials_returns` → `STREAM_BINARY_OUT_OF_SCOPE` — Binary/document export must not flow through execute_delpi_information JSON (no base64).
