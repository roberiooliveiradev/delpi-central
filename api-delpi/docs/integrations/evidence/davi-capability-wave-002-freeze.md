# DAVI Wave 2 capability freeze — Product Economic Intelligence

> **Normative for the next implementation task.** Evidence/governance only. Does not change runtime.

- Task: `DAVI-CAPABILITY-EXPANSION-WAVE-002-FREEZE`
- Future implementation task: `DAVI-CAPABILITY-EXPANSION-WAVE-002` (DO NOT implement here)
- Source HEAD: `6e10029bcc281c4e0c3575448a1414a157cc3c44`
- Freeze status: `FROZEN_FOR_IMPLEMENTATION`
- Theme: Product Economic Intelligence
- Current eligible: **10**
- New Wave 2 capabilities: **4**
- Expected eligible after implementation: **14**
- Expected MCP tools after implementation: **3**
- Agent instructions change: **NO**

## Architecture invariants (do not reopen)

```text
DAVI capability <= authenticated user capability
DAVI_BUSINESS_AUTHZ_OWNER = NONE
CANONICAL_BACKEND_AUTHZ = REQUIRED_FINAL
DAVI_LOCAL_RBAC / BRANCH / OBJECT / ROLE AUTHZ = FORBIDDEN
FILTER != AUTHORIZATION
endpoint != capability
backend AuthZ != raw model exposure
OAuth scope != business permission
price/cost classification != independent DAVI permission
simulation != ACT, recommendation != authorization, calculation != persistence
MCP tools remain search_products + discover_delpi_information + execute_delpi_information
```

## Primary decisions

- `product.commercial.pricing`: **FROZEN_FOR_IMPLEMENTATION**
- `product.purchase.price_history`: **FROZEN_FOR_IMPLEMENTATION**
- `product.raw_material.price_intelligence`: **DEFER**
- `product.cost.impact_simulation`: **FROZEN_FOR_IMPLEMENTATION**

## Secondary decisions

- `get_product_last_purchase`: **FROZEN_FOR_IMPLEMENTATION as product.purchase.last_valid**
- `get_product_summary`: **DEFER**

`get_product_summary` remains **DEFER**. Pricing freeze does not create a mega-summary.

Wave 1 operational capabilities are not reopened.

## product.commercial.pricing

- **CAPABILITY ID:** `product.commercial.pricing`
- **BUSINESS NAME:** Preço comercial atual do produto / Current commercial product pricing
- **BUSINESS NEED:** Authorized current/commercial sale pricing for one product: which price tables apply and the table sale_price, without dumping discounts, max price, tax internals or purchase-cost concepts.
- **TECHNICAL OWNER:** api-delpi Product bounded context
- **BUSINESS OWNER:** TO_INVENTORY — no canonical named business owner proven in source; do not invent Comercial, Suprimentos, Controladoria or Financeiro
- **SOURCE OF TRUTH:** GET /products/{code}/pricing → GetProductPricingUseCase → ProductPricingRepository: SB1010 header (B1_COD/B1_DESC/B1_UM) + DA1010/DA0010 sale tables (DA1_PRCVEN, DA1_CODTAB, DA1_MOEDA, DA1_QTDLOT, DA1_DATVIG, DA1_ATIVO)
- **CANONICAL OPERATION(S):** `get_product_pricing`
- **CANONICAL USE CASE:** `GetProductPricingUseCase`
- **READ/PREPARE/ACT:** READ
- **IDENTITY:** END_USER_ACCOUNT
- **BACKEND AUTHZ:** PROVEN: @require_permission(API_DELPI_ACCESS) on product_pricing
- **APPROVED INPUT FIELDS:** ['code']
- **REQUIRED INPUTS:** ['code']
- **OPTIONAL INPUTS:** []
- **APPROVED RESPONSE FIELDS:**
  - `product.code`
  - `product.description`
  - `product.unit`
  - `prices[].table_code`
  - `prices[].table_description`
  - `prices[].sale_price`
  - `prices[].currency`
  - `prices[].lot_quantity`
  - `prices[].valid_from`
  - `prices[].active`
- **SHAPE:** scalar OpenAPI shape wrapping nested product+prices payload
- **PROJECTION MODE:** nested
- **PROJECTION FEASIBILITY:** SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR
- **PER-OPERATION PROJECTOR:** False
- **ARGUMENT CONSTRAINTS:** {}
- **PAGINATION:** none — prices[] is a table list; global execute_max_items=50 slices arrays
- **LIMITS:** {"maxModelVisibleItems": 50, "executeMaxResponseBytes": 65536, "note": "Backend returns all DA1 rows for the product; DAVI generic array slice caps at 50."}
- **TIME SEMANTICS:** prices[].valid_from is DA1_DATVIG as stored. No start_date/end_date filter exists. Capability is current table rows, not a historical commercial-price series.
- **MONETARY SEMANTICS:** sale_price is DA1_PRCVEN table unit sale price. Tax inclusion/exclusion and gross/net meaning are NOT proven in source — do not freeze a net/gross claim. lot_quantity (DA1_QTDLOT) is the lot basis for that row.
- **CURRENCY SEMANTICS:** currency is DA1_MOEDA as stored (Protheus currency code). ISO 4217 mapping to BRL is NOT proven in source; do not assume BRL. Keep the raw field.
- **UNIT SEMANTICS:** product.unit is SB1 B1_UM catalog unit. sale_price is per catalog unit on the price-table row, interpreted with prices[].lot_quantity.
- **DERIVED FIELDS:** []
- **COMPLETENESS:** Complete for returned DA1 rows of that product after DAVI array cap. truncated=true if more than 50 tables. Do not imply complete market pricing.
- **PROVENANCE:** Preserve canonical operation/use case, product code, reference/start/end dates or date_end_exclusive, branch filter when used, truncated/is_complete, and currency/unit fields that are approved. Do not expose SQL, hosts, tokens, repository internals, or route mechanics.
- **RETRIEVAL ALIASES PT-BR:** ['preço do produto', 'preço comercial', 'tabela de preço', 'preço de venda']
- **RETRIEVAL ALIASES EN:** ['product sale price', 'commercial price table', 'product pricing']
- **PRIVACY:** Sale-table prices are commercially sensitive but not prohibited merely for being monetary. Drop discounts, max_price, state and operation_type. No customer-specific negotiated price field is present in the proven DTO.
- **RISK:** {'databaseQueryCost': 'LOW', 'responseVolume': 'LOW', 'nesting': 'LOW', 'historicalScan': 'LOW', 'recursiveBom': 'NONE', 'downstreamUseCases': 'LOW', 'timeoutRisk': 'LOW', 'overall': 'LOW'}
- **OBSERVABILITY:** Log action_id, actor identifier when policy allows, status, latency, result_count, date window when applicable, truncated, correlation id. Never log Authorization, OAuth tokens, candidate token, raw monetary payload, full supplier/customer records, or secrets.
- **TEST PLAN:** unit projection fail-closed siblings; discover aliases positive+collision; execute bounded payload; sibling non-match (venda vs compra vs última NF vs simulação); negative AuthZ 403 without API_DELPI_ACCESS.
- **LIVE ACCEPTANCE:** Agent Preview discover→candidate→execute for a real product code; verify allowlisted fields only; verify no new MCP tools; verify Wave 1 ten still work.
- **NEGATIVE AUTHZ PLAN:** Local/backend: authenticated caller without API_DELPI_ACCESS must receive backend 403. Live second-user negative AuthZ remains TEST_NOT_RUN unless genuine new evidence exists. DAVI_LOCAL_RBAC/ROLE/BRANCH/OBJECT AuthZ forbidden.
- **QUARANTINE CHANGE REQUIRED:** [{"token": "preco", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `preco` quarantine. Future implementation must add precise multiword aliases (preço do produto / preço comercial / preço de venda) so the promoted action owns the token; unrelated economic actions remain quarantined."}, {"token": "price", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `price` quarantine. Future implementation must add precise multiword aliases (product sale price / product pricing) so the promoted action owns the token; unrelated economic actions remain quarantined."}, {"token": "pricing", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `pricing` quarantine. Future implementation must add precise multiword aliases (product pricing / commercial price table) so the promoted action owns the token; unrelated economic actions remain quarantined."}]
- **OPEN GAPS:** ['ISO 4217 currency mapping for DA1_MOEDA is not proven', 'Tax inclusion/exclusion of DA1_PRCVEN is not proven', 'SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN']
- **FREEZE STATUS:** `FROZEN_FOR_IMPLEMENTATION`

## product.purchase.price_history

- **CAPABILITY ID:** `product.purchase.price_history`
- **BUSINESS NAME:** Histórico de preço de compra da matéria-prima / Raw-material purchase price history
- **BUSINESS NEED:** Authorized bounded series of inbound-NF unit purchase prices for one product, with consecutive variation — not purchase-order listings and not commercial sale tables.
- **TECHNICAL OWNER:** api-delpi Product bounded context
- **BUSINESS OWNER:** TO_INVENTORY — no canonical named business owner proven in source; do not invent Comercial, Suprimentos, Controladoria or Financeiro
- **SOURCE OF TRUTH:** GET /products/{code}/purchase-price-history → GetProductPurchasePriceHistoryUseCase → ProductRawMaterialPriceRepository.fetch_purchase_price_history: SD1010 valid inbound NF (D1_VUNIT, D1_QUANT, D1_TOTAL, D1_PICM, D1_DOC, D1_EMISSAO) + SA2010 supplier name. variation_percent/previous_unit_price/summary are CANONICAL_BACKEND_CALCULATION in product_raw_material_price_service.enrich_price_history_with_variation / summarize_price_history.
- **CANONICAL OPERATION(S):** `get_product_purchase_price_history`
- **CANONICAL USE CASE:** `GetProductPurchasePriceHistoryUseCase`
- **READ/PREPARE/ACT:** READ
- **IDENTITY:** END_USER_ACCOUNT
- **BACKEND AUTHZ:** PROVEN: @require_permission(API_DELPI_ACCESS) on get_purchase_price_history
- **APPROVED INPUT FIELDS:** ['code', 'branch', 'start_date', 'end_date', 'history_limit']
- **REQUIRED INPUTS:** ['code']
- **OPTIONAL INPUTS:** ['branch', 'start_date', 'end_date', 'history_limit']
- **APPROVED RESPONSE FIELDS:**
  - `product.product_code`
  - `product.description`
  - `product.product_type`
  - `product.unit`
  - `start_date`
  - `date_end_exclusive`
  - `branch`
  - `items[].issue_date`
  - `items[].invoice_number`
  - `items[].supplier_code`
  - `items[].supplier_name`
  - `items[].quantity`
  - `items[].unit_price`
  - `items[].total_value`
  - `items[].icms_rate`
  - `items[].previous_unit_price`
  - `items[].variation_percent`
  - `summary.total_purchases`
  - `summary.min_unit_price`
  - `summary.max_unit_price`
  - `summary.avg_unit_price`
  - `summary.last_variation_percent`
- **SHAPE:** playbook_report
- **PROJECTION MODE:** nested
- **PROJECTION FEASIBILITY:** SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR
- **PER-OPERATION PROJECTOR:** False
- **ARGUMENT CONSTRAINTS:** {"dateRange": {"startField": "start_date", "endField": "end_date", "maxDays": 365}, "argumentLimits": {"history_limit": {"minimum": 1, "maximum": 50, "default": 24}}}
- **PAGINATION:** none — history_limit TOP N, not page/page_size
- **LIMITS:** {"backendDefaultLimit": 24, "backendMaxLimit": 200, "daviDefaultLimit": 24, "daviMaxLimit": 50, "backendDefaultDateWindowDays": 365, "daviMaxDateRangeDays": 365, "rationale": "Backend default 24/365 already matches the business grain of recent price evolution. DAVI tightens only the item cap 200→50 to the global execute_max_items budget. Do not silently clamp dates."}
- **TIME SEMANTICS:** Canonical HTTP filters are start_date and end_date. If omitted, backend sets start=today-365d and exclusive end=today+1 (resolve_history_date_range). Date basis is D1_EMISSAO (issue). date_start/date_end are legacy NOT_EXPOSED. Returned start_date / date_end_exclusive are provenance of the actual window.
- **MONETARY SEMANTICS:** items[].unit_price is SD1 D1_VUNIT NF unit price; total_value is D1_TOTAL; icms_rate is D1_PICM. Gross/net of ICMS is not fully defined in source — expose unit_price + icms_rate together. summary min/max/avg and variation_percent are backend calculations over the returned items only.
- **CURRENCY SEMANTICS:** No D1_MOEDA/currency field exists on the NF history payload. Currency is UNPROVEN; do not assume BRL. Do not invent a currency field.
- **UNIT SEMANTICS:** product.unit is B1_UM. quantity is D1_QUANT in that catalog unit. unit_price is per that unit; total_value is the NF line total.
- **DERIVED FIELDS:** [{"field": "items[].previous_unit_price", "class": "CANONICAL_BACKEND_CALCULATION", "owner": "product_raw_material_price_service.enrich_price_history_with_variation"}, {"field": "items[].variation_percent", "class": "CANONICAL_BACKEND_CALCULATION", "owner": "product_raw_material_price_service.enrich_price_history_with_variation", "formula": "((unit_price - previous_unit_price) / previous_unit_price) * 100 when previous > 0"}, {"field": "summary.*", "class": "CANONICAL_BACKEND_CALCULATION", "owner": "product_raw_material_price_service.summarize_price_history", "completenessAssumption": "Aggregates the returned (already limited) items, not the full NF universe."}]
- **COMPLETENESS:** Complete only for valid inbound NFs in the resolved date window up to history_limit. truncated=true when returned items hit the DAVI cap or backend TOP limit. summary.total_purchases is len(returned items), not all-time supplier history. Do not imply complete market or complete supplier history.
- **PROVENANCE:** Preserve canonical operation/use case, product code, reference/start/end dates or date_end_exclusive, branch filter when used, truncated/is_complete, and currency/unit fields that are approved. Do not expose SQL, hosts, tokens, repository internals, or route mechanics.
- **RETRIEVAL ALIASES PT-BR:** ['histórico de preço de compra', 'evolução de preço de compra', 'preço de compra da matéria-prima']
- **RETRIEVAL ALIASES EN:** ['purchase price history', 'buying price history', 'raw material purchase price history']
- **PRIVACY:** Supplier name/code are already in eligible get_product_purchases. History has no A2_CGC. Drop registered cadastro costs and unused NF internals.
- **RISK:** {'databaseQueryCost': 'MEDIUM', 'responseVolume': 'MEDIUM', 'nesting': 'LOW', 'historicalScan': 'MEDIUM', 'recursiveBom': 'NONE', 'downstreamUseCases': 'LOW', 'timeoutRisk': 'MEDIUM', 'overall': 'MEDIUM'}
- **OBSERVABILITY:** Log action_id, actor identifier when policy allows, status, latency, result_count, date window when applicable, truncated, correlation id. Never log Authorization, OAuth tokens, candidate token, raw monetary payload, full supplier/customer records, or secrets.
- **TEST PLAN:** unit projection fail-closed siblings; discover aliases positive+collision; execute bounded payload; sibling non-match (venda vs compra vs última NF vs simulação); negative AuthZ 403 without API_DELPI_ACCESS.
- **LIVE ACCEPTANCE:** Agent Preview discover→candidate→execute for a real product code; verify allowlisted fields only; verify no new MCP tools; verify Wave 1 ten still work.
- **NEGATIVE AUTHZ PLAN:** Local/backend: authenticated caller without API_DELPI_ACCESS must receive backend 403. Live second-user negative AuthZ remains TEST_NOT_RUN unless genuine new evidence exists. DAVI_LOCAL_RBAC/ROLE/BRANCH/OBJECT AuthZ forbidden.
- **QUARANTINE CHANGE REQUIRED:** [{"token": "preco", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `preco` quarantine. Future implementation must add precise multiword aliases (histórico de preço de compra / preço de compra da matéria-prima) so the promoted action owns the token; unrelated economic actions remain quarantined."}, {"token": "price", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `price` quarantine. Future implementation must add precise multiword aliases (purchase price history) so the promoted action owns the token; unrelated economic actions remain quarantined."}]
- **OPEN GAPS:** ['NF currency is absent from the payload (UNPROVEN)', 'SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN']
- **FREEZE STATUS:** `FROZEN_FOR_IMPLEMENTATION`

## product.cost.impact_simulation

- **CAPABILITY ID:** `product.cost.impact_simulation`
- **BUSINESS NAME:** Simulação de impacto de custo do PA / Finished-product cost impact simulation
- **BUSINESS NEED:** Authorized compute-only ranking of raw materials that most impact the material cost of one finished product (PA), optionally applying a percent adjustment. Result is not an approved price, persisted cost, purchasing authorization, accounting entry or business approval.
- **TECHNICAL OWNER:** api-delpi Product bounded context
- **BUSINESS OWNER:** TO_INVENTORY — no canonical named business owner proven in source; do not invent Comercial, Suprimentos, Controladoria or Financeiro
- **SOURCE OF TRUTH:** GET /products/{code}/cost-impact-simulation → GetProductCostImpactSimulationUseCase → ProductCostImpactRepository (SB1010 header B1_CUSTD/B1_UCALSTD + recursive SG1010 BOM MP aggregation OPTION MAXRECURSION 0) → build_cost_impact_simulation (in-memory only). Unit basis: ProductCostImpactUnitService + product_cost_impact_units.json (MI = 1000 pieces). PA-only (rejects non-PA).
- **CANONICAL OPERATION(S):** `get_product_cost_impact_simulation`
- **CANONICAL USE CASE:** `GetProductCostImpactSimulationUseCase`
- **READ/PREPARE/ACT:** READ
- **IDENTITY:** END_USER_ACCOUNT
- **BACKEND AUTHZ:** PROVEN: @require_permission(API_DELPI_ACCESS) on get_cost_impact_simulation
- **APPROVED INPUT FIELDS:** ['code', 'max_depth', 'price_source', 'adjustment_percent', 'top_n']
- **REQUIRED INPUTS:** ['code']
- **OPTIONAL INPUTS:** ['max_depth', 'price_source', 'adjustment_percent', 'top_n']
- **APPROVED RESPONSE FIELDS:**
  - `product.product_code`
  - `product.description`
  - `product.product_type`
  - `product.unit`
  - `product.group_code`
  - `product.standard_cost`
  - `product.standard_cost_date`
  - `pa_reference.reference_quantity`
  - `pa_reference.reference_unit`
  - `pa_reference.bom_quantity_factor`
  - `cost_basis.reference_quantity`
  - `cost_basis.reference_unit`
  - `cost_basis.standard_cost_unit`
  - `cost_basis.material_cost_unit`
  - `cost_basis.pa_standard_cost_basis`
  - `cost_basis.material_cost_basis`
  - `cost_basis.catalog_unit`
  - `cost_basis.catalog_pieces_per_unit`
  - `cost_basis.catalog_quantity_per_reference`
  - `cost_basis.pa_standard_cost_per_piece`
  - `cost_basis.total_material_cost_per_piece`
  - `price_source`
  - `adjustment_percent`
  - `materials.items[].rank`
  - `materials.items[].raw_material_code`
  - `materials.items[].raw_material_description`
  - `materials.items[].unit`
  - `materials.items[].quantity_per_pa`
  - `materials.items[].unit_cost`
  - `materials.items[].extended_cost`
  - `materials.items[].impact_on_material_cost_percent`
  - `materials.items[].impact_on_pa_cost_percent`
  - `materials.items[].simulated_unit_cost`
  - `materials.items[].simulated_extended_cost`
  - `materials.items[].simulated_impact_on_pa_cost_percent`
  - `materials.items[].cost_delta`
  - `materials.total`
  - `materials.returned`
  - `summary.total_raw_materials`
  - `summary.returned_materials`
  - `summary.total_material_cost`
  - `summary.simulated_total_material_cost`
  - `summary.projected_cost_delta`
  - `summary.top_material_impact_percent`
  - `summary.pa_standard_cost`
  - `summary.pa_cost_comparable`
  - `summary.material_to_pa_cost_ratio`
  - `simulation.adjustment_percent`
  - `simulation.projected_total_material_cost`
  - `simulation.projected_cost_delta`
  - `simulation.projected_pa_cost_delta_percent`
- **SHAPE:** composite_analysis
- **PROJECTION MODE:** nested
- **PROJECTION FEASIBILITY:** SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR
- **PER-OPERATION PROJECTOR:** False
- **ARGUMENT CONSTRAINTS:** {"argumentLimits": {"max_depth": {"minimum": 1, "maximum": 8, "default": 8}, "top_n": {"minimum": 1, "maximum": 50, "default": 50}, "adjustment_percent": {"minimum": -100, "maximum": 1000, "default": 0}}}
- **PAGINATION:** none — top_n ranking slice, not page/page_size
- **LIMITS:** {"backendDefaultMaxDepth": 50, "backendMaxDepthQuery": 100, "daviMaxDepth": 8, "backendTopNMax": 200, "daviTopNMax": 50, "adjustmentPercentBackend": {"minimum": -100, "maximum": 1000}, "priceSourceEnum": ["standard_cost", "last_purchase"]}
- **TIME SEMANTICS:** No start_date/end_date. BOM validity is ProductBomValidityFilterService for today. product.standard_cost_date is B1_UCALSTD cadastro date. Simulation is a point-in-time compute against current BOM + current costs.
- **MONETARY SEMANTICS:** unit_cost is CANONICAL_BACKEND_CALCULATION from price_source (B1_CUSTD standard_cost or B1_UPRC last_purchase, with fallback). extended_cost = quantity_per_pa * unit_cost. simulated_* apply adjustment_percent multiplier. Impact percents are backend calculations. simulation result != approved price / persisted product cost / purchasing authorization / accounting entry / business approval. GET compute-only: no INSERT/UPDATE/DELETE in use case, service or repository.
- **CURRENCY SEMANTICS:** B1_CUSTD/B1_UPRC have no currency field in this payload. Currency UNPROVEN; do not assume BRL. Do not invent a currency field.
- **UNIT SEMANTICS:** quantity_per_pa is normalized via ProductPaBomReferenceService for 1 PA. cost_basis documents MI vs piece: parentUnits.MI catalogPiecesPerUnit=1000. materials.items[].unit is the MP catalog unit. Do not expose amount without these unit fields.
- **DERIVED FIELDS:** [{"field": "unit_cost / simulated_* / extended_cost / cost_delta / impact percents", "class": "CANONICAL_BACKEND_CALCULATION", "owner": "product_cost_impact_service.build_cost_impact_simulation"}, {"field": "summary.pa_cost_comparable / material_to_pa_cost_ratio", "class": "CANONICAL_BACKEND_CALCULATION", "owner": "ProductCostImpactUnitService.resolve_comparability", "assumptions": "comparable only if ratio in [0.05, 5.0]"}, {"field": "cost_basis.*", "class": "CANONICAL_BACKEND_CALCULATION", "owner": "ProductCostImpactUnitService.build_cost_basis", "config": "app/content/product_cost_impact_units.json"}]
- **COMPLETENESS:** Ranking is complete for MP components found in the bounded BOM explosion (max_depth). materials.total is all ranked MPs; materials.returned is the top_n slice. truncated when returned < total. Not a complete cost accounting analysis and not a complete market simulation.
- **PROVENANCE:** Preserve canonical operation/use case, product code, reference/start/end dates or date_end_exclusive, branch filter when used, truncated/is_complete, and currency/unit fields that are approved. Do not expose SQL, hosts, tokens, repository internals, or route mechanics.
- **RETRIEVAL ALIASES PT-BR:** ['impacto no custo', 'simulação de custo', 'simular impacto de custo', 'matérias-primas que mais impactam o custo']
- **RETRIEVAL ALIASES EN:** ['cost impact simulation', 'simulate cost impact', 'raw materials cost impact']
- **PRIVACY:** Internal cost/margin-adjacent ranking. Minimize to ranking + simulation totals. Drop BOM path. No customer/supplier PII in this payload.
- **RISK:** {'databaseQueryCost': 'HIGH', 'responseVolume': 'MEDIUM', 'nesting': 'MEDIUM', 'historicalScan': 'LOW', 'recursiveBom': 'HIGH', 'downstreamUseCases': 'LOW', 'timeoutRisk': 'HIGH', 'overall': 'HIGH'}
- **OBSERVABILITY:** Log action_id, actor identifier when policy allows, status, latency, result_count, date window when applicable, truncated, correlation id. Never log Authorization, OAuth tokens, candidate token, raw monetary payload, full supplier/customer records, or secrets.
- **TEST PLAN:** unit projection fail-closed siblings; discover aliases positive+collision; execute bounded payload; sibling non-match (venda vs compra vs última NF vs simulação); negative AuthZ 403 without API_DELPI_ACCESS.
- **LIVE ACCEPTANCE:** Agent Preview discover→candidate→execute for a real product code; verify allowlisted fields only; verify no new MCP tools; verify Wave 1 ten still work.
- **NEGATIVE AUTHZ PLAN:** Local/backend: authenticated caller without API_DELPI_ACCESS must receive backend 403. Live second-user negative AuthZ remains TEST_NOT_RUN unless genuine new evidence exists. DAVI_LOCAL_RBAC/ROLE/BRANCH/OBJECT AuthZ forbidden.
- **QUARANTINE CHANGE REQUIRED:** [{"token": "custo", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `custo` quarantine. Future implementation must add precise multiword aliases (impacto no custo / simulação de custo) so the promoted action owns the token; unrelated economic actions remain quarantined."}, {"token": "cost", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `cost` quarantine. Future implementation must add precise multiword aliases (cost impact simulation) so the promoted action owns the token; unrelated economic actions remain quarantined."}]
- **OPEN GAPS:** ['Currency of B1_CUSTD/B1_UPRC is UNPROVEN', 'SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN', 'Recursive BOM with MAXRECURSION 0 remains HIGH cost even with DAVI max_depth=8']
- **FREEZE STATUS:** `FROZEN_FOR_IMPLEMENTATION`

## product.purchase.last_valid

- **CAPABILITY ID:** `product.purchase.last_valid`
- **BUSINESS NAME:** Última compra válida da matéria-prima / Last valid inbound purchase snapshot
- **BUSINESS NEED:** Authorized latest valid inbound NF snapshot for one product (supplier, unit price, quantity, date) without a date window and without a history series.
- **TECHNICAL OWNER:** api-delpi Product bounded context
- **BUSINESS OWNER:** TO_INVENTORY — no canonical named business owner proven in source; do not invent Comercial, Suprimentos, Controladoria or Financeiro
- **SOURCE OF TRUTH:** GET /products/{code}/last-purchase → GetProductLastPurchaseUseCase → ProductRawMaterialPriceRepository.fetch_last_purchase: SD1010 TOP 1 valid inbound NF ordered by D1_EMISSAO/D1_DTDIGIT/D1_DOC DESC + SA2010 name. No date filter. Distinct from purchase_price_history default 365-day window.
- **CANONICAL OPERATION(S):** `get_product_last_purchase`
- **CANONICAL USE CASE:** `GetProductLastPurchaseUseCase`
- **READ/PREPARE/ACT:** READ
- **IDENTITY:** END_USER_ACCOUNT
- **BACKEND AUTHZ:** PROVEN: @require_permission(API_DELPI_ACCESS) on get_last_purchase
- **APPROVED INPUT FIELDS:** ['code', 'branch']
- **REQUIRED INPUTS:** ['code']
- **OPTIONAL INPUTS:** ['branch']
- **APPROVED RESPONSE FIELDS:**
  - `product.product_code`
  - `product.description`
  - `product.product_type`
  - `product.unit`
  - `last_purchase.branch`
  - `last_purchase.invoice_number`
  - `last_purchase.issue_date`
  - `last_purchase.supplier_code`
  - `last_purchase.supplier_name`
  - `last_purchase.quantity`
  - `last_purchase.unit_price`
  - `last_purchase.total_value`
  - `last_purchase.icms_rate`
  - `last_purchase.purchase_order`
- **SHAPE:** playbook_report
- **PROJECTION MODE:** nested
- **PROJECTION FEASIBILITY:** SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR
- **PER-OPERATION PROJECTOR:** False
- **ARGUMENT CONSTRAINTS:** {}
- **PAGINATION:** none — single snapshot
- **LIMITS:** {"maxItems": 1}
- **TIME SEMANTICS:** No start_date/end_date. Returns the latest valid NF regardless of age. This is the proven distinction versus purchase price history (windowed series).
- **MONETARY SEMANTICS:** last_purchase.unit_price is D1_VUNIT; total_value is D1_TOTAL; icms_rate is D1_PICM. Same UNPROVEN gross/net caveat as history.
- **CURRENCY SEMANTICS:** No currency field on last_purchase payload. UNPROVEN; do not assume BRL.
- **UNIT SEMANTICS:** product.unit is B1_UM; quantity/unit_price follow that catalog unit.
- **DERIVED FIELDS:** []
- **COMPLETENESS:** Complete as the single latest valid inbound NF after PurchaseValidityFilterService, or last_purchase=null if none. Not a complete purchase history.
- **PROVENANCE:** Preserve canonical operation/use case, product code, reference/start/end dates or date_end_exclusive, branch filter when used, truncated/is_complete, and currency/unit fields that are approved. Do not expose SQL, hosts, tokens, repository internals, or route mechanics.
- **RETRIEVAL ALIASES PT-BR:** ['último preço de compra', 'última compra da matéria-prima', 'última NF de compra']
- **RETRIEVAL ALIASES EN:** ['last purchase price', 'last valid purchase', 'latest inbound invoice price']
- **PRIVACY:** MUST drop supplier_tax_id (SA2 A2_CGC). Keep supplier_name/code consistent with eligible purchases list.
- **RISK:** {'databaseQueryCost': 'LOW', 'responseVolume': 'LOW', 'nesting': 'LOW', 'historicalScan': 'LOW', 'recursiveBom': 'NONE', 'downstreamUseCases': 'LOW', 'timeoutRisk': 'LOW', 'overall': 'LOW'}
- **OBSERVABILITY:** Log action_id, actor identifier when policy allows, status, latency, result_count, date window when applicable, truncated, correlation id. Never log Authorization, OAuth tokens, candidate token, raw monetary payload, full supplier/customer records, or secrets.
- **TEST PLAN:** unit projection fail-closed siblings; discover aliases positive+collision; execute bounded payload; sibling non-match (venda vs compra vs última NF vs simulação); negative AuthZ 403 without API_DELPI_ACCESS.
- **LIVE ACCEPTANCE:** Agent Preview discover→candidate→execute for a real product code; verify allowlisted fields only; verify no new MCP tools; verify Wave 1 ten still work.
- **NEGATIVE AUTHZ PLAN:** Local/backend: authenticated caller without API_DELPI_ACCESS must receive backend 403. Live second-user negative AuthZ remains TEST_NOT_RUN unless genuine new evidence exists. DAVI_LOCAL_RBAC/ROLE/BRANCH/OBJECT AuthZ forbidden.
- **QUARANTINE CHANGE REQUIRED:** [{"token": "preco", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `preco` quarantine. Future implementation must add precise multiword aliases (último preço de compra / última NF de compra) so the promoted action owns the token; unrelated economic actions remain quarantined."}, {"token": "price", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `price` quarantine. Future implementation must add precise multiword aliases (last purchase price) so the promoted action owns the token; unrelated economic actions remain quarantined."}]
- **OPEN GAPS:** ['NF currency UNPROVEN', 'SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN']
- **FREEZE STATUS:** `FROZEN_FOR_IMPLEMENTATION`

## Implementation handoff (do not execute here)

Future task: `DAVI-CAPABILITY-EXPANSION-WAVE-002`

Capabilities to implement:

- `product.commercial.pricing`
- `product.purchase.price_history`
- `product.cost.impact_simulation`
- `product.purchase.last_valid`

Allowlist delta: add `operations[]` entries only (catalog_action + nested projection + aliases + generic argumentConstraints).
Remove those operationIds from `explicitlyNotApproved` when promoting.
Do not remove global economic quarantine tokens; own via aliases.

Expected eligible after implementation: **14**.
Expected MCP tools: **3**.
Agent instruction change: **NO**.

Must not change in this freeze task (already true): MCP server tool surface, Agent Instructions, eligibility classifier semantics, executor genericity, API routes, use cases, repositories.

