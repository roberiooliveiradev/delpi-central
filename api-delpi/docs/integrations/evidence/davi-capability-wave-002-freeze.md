# DAVI Wave 2 capability freeze — Product Economic Intelligence

> **Normative for the next implementation task.** Evidence/governance only. Does not change runtime.

- Task: `DAVI-CAPABILITY-EXPANSION-WAVE-002-FREEZE`
- Architecture correction: `DAVI-CAPABILITY-EXPANSION-WAVE-002-FREEZE-CORRECTION-001` — `ACCEPT_WITH_RESIDUAL`
- Source freeze SHA: `b5de5122f13bb921f6e6a48a0fad2d559e97eb80`
- Future implementation task: `DAVI-CAPABILITY-EXPANSION-WAVE-002` (DO NOT implement here)
- Source HEAD: `b5de5122f13bb921f6e6a48a0fad2d559e97eb80`
- Freeze status: `FROZEN_FOR_IMPLEMENTATION`
- Theme: Product Economic Intelligence
- Current eligible: **10**
- Wave 2 READ additions: **3**
- Expected eligible after implementation: **13**
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
HTTP GET != semantic READ
PREPARE = preview/draft/simulação sem persistir — not Wave 2 READ
MCP tools remain search_products + discover_delpi_information + execute_delpi_information
```

## Primary decisions

- `product.commercial.pricing`: **FROZEN_FOR_IMPLEMENTATION**
- `product.purchase.price_history`: **FROZEN_FOR_IMPLEMENTATION**
- `product.raw_material.price_intelligence`: **DEFER**
- `product.cost.impact_simulation`: **PREPARE / DEFER_FROM_READ_WAVE**

## Secondary decisions

- `get_product_last_purchase`: **FROZEN_FOR_IMPLEMENTATION as product.purchase.last_valid**
- `get_product_summary`: **DEFER**

`get_product_summary` remains **DEFER**. Pricing freeze does not create a mega-summary.

`product.cost.impact_simulation` is **PREPARE / DEFER_FROM_READ_WAVE**. HTTP GET compute-only simulation is not Wave 2 READ. Do not add it to the READ allowlist. A future PREPARE track may reuse the preserved source/projection analysis.

Wave 1 operational capabilities are not reopened.

## product.commercial.pricing

- **CAPABILITY ID:** `product.commercial.pricing`
- **BUSINESS NAME:** Tabelas e preços comerciais do produto / Commercial product price tables
- **BUSINESS NEED:** Consultar as tabelas comerciais registradas para um produto, incluindo preço de venda, moeda armazenada, lote, vigência e indicador de ativo, sem afirmar que todas as linhas representam o preço atual. Not purchase cost and not a mega-financial dump.
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
- **TIME SEMANTICS:** prices[].valid_from is DA1_DATVIG as stored. prices[].active is DA1_ATIVO as stored. No start_date/end_date filter exists. The route does not prove that returned rows are only currently active/effective. DAVI may report the row active flag, valid_from and registered sale_price; it must not claim sale_price is the current effective price.
- **MONETARY SEMANTICS:** sale_price is DA1_PRCVEN table unit sale price. Tax inclusion/exclusion and gross/net meaning are NOT proven in source — do not freeze a net/gross claim. lot_quantity (DA1_QTDLOT) is the lot basis for that row.
- **CURRENCY SEMANTICS:** currency is DA1_MOEDA as stored (Protheus currency code). ISO 4217 mapping to BRL is NOT proven in source; do not assume BRL. Keep the raw field.
- **UNIT SEMANTICS:** product.unit is SB1 B1_UM catalog unit. sale_price is per catalog unit on the price-table row, interpreted with prices[].lot_quantity.
- **DERIVED FIELDS:** []
- **COMPLETENESS:** Complete for the DA1 rows returned in this payload after DAVI array cap. truncated=true if more than 50 tables. Do not imply complete market pricing and do not imply every row is the current effective price.
- **PROVENANCE:** Preserve canonical operation/use case, product code, reference/start/end dates or date_end_exclusive, branch filter when used, truncated/is_complete, and currency/unit fields that are approved. Do not expose SQL, hosts, tokens, repository internals, or route mechanics.
- **RETRIEVAL ALIASES PT-BR:** ['preço do produto', 'preço comercial', 'tabela de preço', 'preço de venda']
- **RETRIEVAL ALIASES EN:** ['product sale price', 'commercial price table', 'product pricing']
- **PRIVACY:** Sale-table prices are commercially sensitive but not prohibited merely for being monetary. Drop discounts, max_price, state and operation_type. No customer-specific negotiated price field is present in the proven DTO.
- **RISK:** {'databaseQueryCost': 'LOW', 'responseVolume': 'LOW', 'nesting': 'LOW', 'historicalScan': 'LOW', 'recursiveBom': 'NONE', 'downstreamUseCases': 'LOW', 'timeoutRisk': 'LOW', 'overall': 'LOW'}
- **OBSERVABILITY:** Log action_id, actor identifier when policy allows, status, latency, result_count, date window when applicable, truncated, correlation id. Never log Authorization, OAuth tokens, candidate token, raw monetary payload, full supplier/customer records, or secrets.
- **TEST PLAN:** unit projection fail-closed siblings; discover aliases positive+collision; execute bounded payload; sibling non-match (venda vs compra vs última NF); negative AuthZ 403 without API_DELPI_ACCESS.
- **LIVE ACCEPTANCE:** Agent Preview discover→candidate→execute for a real product code; verify allowlisted fields only; verify no new MCP tools; verify Wave 1 ten still work.
- **NEGATIVE AUTHZ PLAN:** Local/backend: authenticated caller without API_DELPI_ACCESS must receive backend 403. Live second-user negative AuthZ remains TEST_NOT_RUN unless genuine new evidence exists. DAVI_LOCAL_RBAC/ROLE/BRANCH/OBJECT AuthZ forbidden.
- **QUARANTINE CHANGE REQUIRED:** [{"token": "preco", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `preco` quarantine. Future implementation must add precise multiword aliases (preço do produto / preço comercial / preço de venda) so the promoted action owns the token; unrelated economic actions remain quarantined."}, {"token": "price", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `price` quarantine. Future implementation must add precise multiword aliases (product sale price / product pricing) so the promoted action owns the token; unrelated economic actions remain quarantined."}, {"token": "pricing", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `pricing` quarantine. Future implementation must add precise multiword aliases (product pricing / commercial price table) so the promoted action owns the token; unrelated economic actions remain quarantined."}]
- **OPEN GAPS:** ['ISO 4217 currency mapping for DA1_MOEDA is not proven', 'Tax inclusion/exclusion of DA1_PRCVEN is not proven', 'SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN']
- **FREEZE STATUS:** `FROZEN_FOR_IMPLEMENTATION`

## product.purchase.price_history

- **CAPABILITY ID:** `product.purchase.price_history`
- **BUSINESS NAME:** Histórico de preço de compra da matéria-prima / Raw-material purchase price history
- **BUSINESS NEED:** Bounded recent purchase-price series for one product within a resolved date window, limited to the latest N canonical inbound-NF occurrences, with consecutive variation on the returned set — not purchase-order listings, not commercial sale tables, and not a complete-period history.
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
- **TIME SEMANTICS:** Canonical HTTP filters are start_date and end_date. If omitted, backend sets start=today-365d and exclusive end=today+1 (resolve_history_date_range). Default date_basis is issue (D1_EMISSAO). Proven ordering in fetch_purchase_price_history: D1_EMISSAO DESC, D1_DTDIGIT DESC, R_E_C_N_O_ DESC (latest-first). date_start/date_end are legacy NOT_EXPOSED. Returned start_date / date_end_exclusive are provenance of the resolved window, not proof that every matching NF in that window was returned.
- **MONETARY SEMANTICS:** items[].unit_price is SD1 D1_VUNIT NF unit price; total_value is D1_TOTAL; icms_rate is D1_PICM. Gross/net of ICMS is not fully defined in source — expose unit_price + icms_rate together. summary min/max/avg and variation_percent are backend calculations over the returned items only.
- **CURRENCY SEMANTICS:** No D1_MOEDA/currency field exists on the NF history payload. Currency is UNPROVEN; do not assume BRL. Do not invent a currency field.
- **UNIT SEMANTICS:** product.unit is B1_UM. quantity is D1_QUANT in that catalog unit. unit_price is per that unit; total_value is the NF line total.
- **DERIVED FIELDS:** [{"field": "items[].previous_unit_price", "class": "CANONICAL_BACKEND_CALCULATION", "owner": "product_raw_material_price_service.enrich_price_history_with_variation"}, {"field": "items[].variation_percent", "class": "CANONICAL_BACKEND_CALCULATION", "owner": "product_raw_material_price_service.enrich_price_history_with_variation", "formula": "((unit_price - previous_unit_price) / previous_unit_price) * 100 when previous > 0"}, {"field": "summary.*", "class": "CANONICAL_BACKEND_CALCULATION", "owner": "product_raw_material_price_service.summarize_price_history", "completenessAssumption": "Aggregates the returned TOP N items only. Does not prove total matching NFs in the whole requested period."}]
- **COMPLETENESS:** dataset_scope = bounded latest-N occurrences within the resolved date window. Default N=24, DAVI max N=50, requested window max 365 days. history_limit bounds the dataset returned by the canonical backend TOP N. summary fields describe that returned bounded dataset only. summary.total_purchases does NOT prove total matching NFs in the whole period. Backend does not expose total, has_more, or a next cursor. full_period_completeness = NOT_PROVEN. DAVI is_complete/truncated describe DAVI projection/transport completeness only. is_complete=true MUST NOT be interpreted as 'there are no more matching purchases in the requested period'. truncated=true only when DAVI projection sliced the already-returned payload (e.g. execute_max_items), not when the backend TOP N quietly omitted older matching records.
- **PROVENANCE:** Preserve canonical operation/use case, product code, reference/start/end dates or date_end_exclusive, branch filter when used, truncated/is_complete, and currency/unit fields that are approved. Do not expose SQL, hosts, tokens, repository internals, or route mechanics.
- **RETRIEVAL ALIASES PT-BR:** ['histórico de preço de compra', 'evolução de preço de compra', 'preço de compra da matéria-prima']
- **RETRIEVAL ALIASES EN:** ['purchase price history', 'buying price history', 'raw material purchase price history']
- **PRIVACY:** Supplier name/code are already in eligible get_product_purchases. History has no A2_CGC. Drop registered cadastro costs and unused NF internals.
- **RISK:** {'databaseQueryCost': 'MEDIUM', 'responseVolume': 'MEDIUM', 'nesting': 'LOW', 'historicalScan': 'MEDIUM', 'recursiveBom': 'NONE', 'downstreamUseCases': 'LOW', 'timeoutRisk': 'MEDIUM', 'overall': 'MEDIUM'}
- **OBSERVABILITY:** Log action_id, actor identifier when policy allows, status, latency, result_count, date window when applicable, truncated, correlation id. Never log Authorization, OAuth tokens, candidate token, raw monetary payload, full supplier/customer records, or secrets.
- **TEST PLAN:** unit projection fail-closed siblings; discover aliases positive+collision; execute bounded payload; sibling non-match (venda vs compra vs última NF); negative AuthZ 403 without API_DELPI_ACCESS.
- **LIVE ACCEPTANCE:** Agent Preview discover→candidate→execute for a real product code; verify allowlisted fields only; verify no new MCP tools; verify Wave 1 ten still work.
- **NEGATIVE AUTHZ PLAN:** Local/backend: authenticated caller without API_DELPI_ACCESS must receive backend 403. Live second-user negative AuthZ remains TEST_NOT_RUN unless genuine new evidence exists. DAVI_LOCAL_RBAC/ROLE/BRANCH/OBJECT AuthZ forbidden.
- **QUARANTINE CHANGE REQUIRED:** [{"token": "preco", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `preco` quarantine. Future implementation must add precise multiword aliases (histórico de preço de compra / preço de compra da matéria-prima) so the promoted action owns the token; unrelated economic actions remain quarantined."}, {"token": "price", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `price` quarantine. Future implementation must add precise multiword aliases (purchase price history) so the promoted action owns the token; unrelated economic actions remain quarantined."}]
- **OPEN GAPS:** ['NF currency is absent from the payload (UNPROVEN)', 'SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN']
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
- **TEST PLAN:** unit projection fail-closed siblings; discover aliases positive+collision; execute bounded payload; sibling non-match (venda vs compra vs última NF); negative AuthZ 403 without API_DELPI_ACCESS.
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
- `product.purchase.last_valid`

Canonical operations: `get_product_pricing`, `get_product_purchase_price_history`, `get_product_last_purchase`.

Do **not** implement `get_product_cost_impact_simulation` in Wave 2 READ.

Allowlist delta: add `operations[]` entries only (catalog_action + nested projection + aliases + generic argumentConstraints).
Future removals from `explicitlyNotApproved`: `get_product_pricing`, `get_product_purchase_price_history`.
`get_product_last_purchase` is not currently in `explicitlyNotApproved` (nested-shape blocked only).
Keep blocked: `get_product_cost_impact_simulation`, `get_product_raw_material_price_intelligence`, `get_product_summary`.
Do not remove global economic quarantine tokens; READ capabilities own via precise aliases. Cost tokens stay global-only.

Expected eligible after implementation: **13**.
Expected MCP tools: **3**.
Agent instruction change: **NO**.

Must not change in this freeze/correction task (already true): MCP server tool surface, Agent Instructions, eligibility classifier semantics, executor genericity, API routes, use cases, repositories.

