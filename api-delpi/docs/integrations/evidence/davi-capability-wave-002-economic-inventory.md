# DAVI Wave 2 economic capability inventory

> **SOURCE/EVIDENCE FREEZE only.** Not implemented, not deployed, not live.

- Task: `DAVI-CAPABILITY-EXPANSION-WAVE-002-FREEZE`
- Source HEAD: `b5de5122f13bb921f6e6a48a0fad2d559e97eb80`
- origin/main: `b5de5122f13bb921f6e6a48a0fad2d559e97eb80`
- Current eligible: **10**
- MCP tools: `search_products, discover_delpi_information, execute_delpi_information`
- Execution drift: `NONE`

## Architecture

```text
Workspace Agent DAVI → DAVI App/Plugin → remote MCP → governed discovery → opaque candidate token → generic governed execute → API DELPI canonical route/use case → backend AuthZ → authoritative source → fail-closed model-safe projection → DAVI explanation
```

DAVI is intelligence / orchestration / presentation. DAVI is not source of truth, RBAC, domain owner, SQL client, generic HTTP proxy, financial authority or pricing authority.

## Candidates

### product.commercial.pricing — `FROZEN_FOR_IMPLEMENTATION`

- **BUSINESS NEED:** Consultar as tabelas comerciais registradas para um produto, incluindo preço de venda, moeda armazenada, lote, vigência e indicador de ativo, sem afirmar que todas as linhas representam o preço atual. Not purchase cost and not a mega-financial dump.
- **TECHNICAL OWNER:** api-delpi Product bounded context
- **BUSINESS OWNER:** TO_INVENTORY — no canonical named business owner proven in source; do not invent Comercial, Suprimentos, Controladoria or Financeiro
- **SOURCE OF TRUTH:** GET /products/{code}/pricing → GetProductPricingUseCase → ProductPricingRepository: SB1010 header (B1_COD/B1_DESC/B1_UM) + DA1010/DA0010 sale tables (DA1_PRCVEN, DA1_CODTAB, DA1_MOEDA, DA1_QTDLOT, DA1_DATVIG, DA1_ATIVO)
- **BACKEND AUTHZ:** PROVEN: @require_permission(API_DELPI_ACCESS) on product_pricing
- **READ/PREPARE/ACT:** READ
- **CANONICAL OPERATION(S):** `get_product_pricing`
- **INPUTS:** required=['code'] optional=[]
- **OUTPUT PATH COUNT:** 10
- **PROJECTION:** SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR / mode=nested
- **MONETARY:** sale_price is DA1_PRCVEN table unit sale price. Tax inclusion/exclusion and gross/net meaning are NOT proven in source — do not freeze a net/gross claim. lot_quantity (DA1_QTDLOT) is the lot basis for that row.
- **CURRENCY:** currency is DA1_MOEDA as stored (Protheus currency code). ISO 4217 mapping to BRL is NOT proven in source; do not assume BRL. Keep the raw field.
- **UNIT:** product.unit is SB1 B1_UM catalog unit. sale_price is per catalog unit on the price-table row, interpreted with prices[].lot_quantity.
- **TIME:** prices[].valid_from is DA1_DATVIG as stored. prices[].active is DA1_ATIVO as stored. No start_date/end_date filter exists. The route does not prove that returned rows are only currently active/effective. DAVI may report the row active flag, valid_from and registered sale_price; it must not claim sale_price is the current effective price.
- **PRIVACY:** Sale-table prices are commercially sensitive but not prohibited merely for being monetary. Drop discounts, max_price, state and operation_type. No customer-specific negotiated price field is present in the proven DTO.
- **RISK:** {'databaseQueryCost': 'LOW', 'responseVolume': 'LOW', 'nesting': 'LOW', 'historicalScan': 'LOW', 'recursiveBom': 'NONE', 'downstreamUseCases': 'LOW', 'timeoutRisk': 'LOW', 'overall': 'LOW'}
- **QUARANTINE DELTA:** [{"token": "preco", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `preco` quarantine. Future implementation must add precise multiword aliases (preço do produto / preço comercial / preço de venda) so the promoted action owns the token; unrelated economic actions remain quarantined."}, {"token": "price", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `price` quarantine. Future implementation must add precise multiword aliases (product sale price / product pricing) so the promoted action owns the token; unrelated economic actions remain quarantined."}, {"token": "pricing", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `pricing` quarantine. Future implementation must add precise multiword aliases (product pricing / commercial price table) so the promoted action owns the token; unrelated economic actions remain quarantined."}]
- **OPEN GAPS:** ['ISO 4217 currency mapping for DA1_MOEDA is not proven', 'Tax inclusion/exclusion of DA1_PRCVEN is not proven', 'SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN']
- **DECISION:** `FROZEN_FOR_IMPLEMENTATION`

### product.purchase.price_history — `FROZEN_FOR_IMPLEMENTATION`

- **BUSINESS NEED:** Bounded recent purchase-price series for one product within a resolved date window, limited to the latest N canonical inbound-NF occurrences, with consecutive variation on the returned set — not purchase-order listings, not commercial sale tables, and not a complete-period history.
- **TECHNICAL OWNER:** api-delpi Product bounded context
- **BUSINESS OWNER:** TO_INVENTORY — no canonical named business owner proven in source; do not invent Comercial, Suprimentos, Controladoria or Financeiro
- **SOURCE OF TRUTH:** GET /products/{code}/purchase-price-history → GetProductPurchasePriceHistoryUseCase → ProductRawMaterialPriceRepository.fetch_purchase_price_history: SD1010 valid inbound NF (D1_VUNIT, D1_QUANT, D1_TOTAL, D1_PICM, D1_DOC, D1_EMISSAO) + SA2010 supplier name. variation_percent/previous_unit_price/summary are CANONICAL_BACKEND_CALCULATION in product_raw_material_price_service.enrich_price_history_with_variation / summarize_price_history.
- **BACKEND AUTHZ:** PROVEN: @require_permission(API_DELPI_ACCESS) on get_purchase_price_history
- **READ/PREPARE/ACT:** READ
- **CANONICAL OPERATION(S):** `get_product_purchase_price_history`
- **INPUTS:** required=['code'] optional=['branch', 'start_date', 'end_date', 'history_limit']
- **OUTPUT PATH COUNT:** 22
- **PROJECTION:** SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR / mode=nested
- **MONETARY:** items[].unit_price is SD1 D1_VUNIT NF unit price; total_value is D1_TOTAL; icms_rate is D1_PICM. Gross/net of ICMS is not fully defined in source — expose unit_price + icms_rate together. summary min/max/avg and variation_percent are backend calculations over the returned items only.
- **CURRENCY:** No D1_MOEDA/currency field exists on the NF history payload. Currency is UNPROVEN; do not assume BRL. Do not invent a currency field.
- **UNIT:** product.unit is B1_UM. quantity is D1_QUANT in that catalog unit. unit_price is per that unit; total_value is the NF line total.
- **TIME:** Canonical HTTP filters are start_date and end_date. If omitted, backend sets start=today-365d and exclusive end=today+1 (resolve_history_date_range). Default date_basis is issue (D1_EMISSAO). Proven ordering in fetch_purchase_price_history: D1_EMISSAO DESC, D1_DTDIGIT DESC, R_E_C_N_O_ DESC (latest-first). date_start/date_end are legacy NOT_EXPOSED. Returned start_date / date_end_exclusive are provenance of the resolved window, not proof that every matching NF in that window was returned.
- **PRIVACY:** Supplier name/code are already in eligible get_product_purchases. History has no A2_CGC. Drop registered cadastro costs and unused NF internals.
- **RISK:** {'databaseQueryCost': 'MEDIUM', 'responseVolume': 'MEDIUM', 'nesting': 'LOW', 'historicalScan': 'MEDIUM', 'recursiveBom': 'NONE', 'downstreamUseCases': 'LOW', 'timeoutRisk': 'MEDIUM', 'overall': 'MEDIUM'}
- **QUARANTINE DELTA:** [{"token": "preco", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `preco` quarantine. Future implementation must add precise multiword aliases (histórico de preço de compra / preço de compra da matéria-prima) so the promoted action owns the token; unrelated economic actions remain quarantined."}, {"token": "price", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `price` quarantine. Future implementation must add precise multiword aliases (purchase price history) so the promoted action owns the token; unrelated economic actions remain quarantined."}]
- **OPEN GAPS:** ['NF currency is absent from the payload (UNPROVEN)', 'SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN']
- **DECISION:** `FROZEN_FOR_IMPLEMENTATION`

### product.raw_material.price_intelligence — `DEFER`

- **BUSINESS NEED:** Classified overlay of last-purchase snapshot, price-history summary, budget-history summary and backend price_status/indicators for one MP.
- **TECHNICAL OWNER:** api-delpi Product bounded context
- **BUSINESS OWNER:** TO_INVENTORY — no canonical named business owner proven in source; do not invent Comercial, Suprimentos, Controladoria or Financeiro
- **SOURCE OF TRUTH:** GET /products/{code}/raw-material-price-intelligence → GetProductRawMaterialPriceIntelligenceUseCase composes fetch_last_purchase + fetch_purchase_price_history + fetch_purchase_budget_history (SC1010 UNION SC7010, no TOP/limit) + classify_price_status / build_indicators.
- **BACKEND AUTHZ:** PROVEN: @require_permission(API_DELPI_ACCESS) on get_raw_material_price_intelligence
- **READ/PREPARE/ACT:** READ
- **CANONICAL OPERATION(S):** `get_product_raw_material_price_intelligence`
- **INPUTS:** required=['code'] optional=['branch', 'start_date', 'end_date', 'history_limit']
- **OUTPUT PATH COUNT:** 0
- **PROJECTION:** SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR / mode=nested
- **MONETARY:** Mix of AUTHORITATIVE_RAW_FACT (NF/cadastro prices), CANONICAL_BACKEND_CALCULATION (variation, summaries, indicators) and CANONICAL_BACKEND_CLASSIFICATION (price_status ESTAVEL/ALTA DE PRECO/QUEDA DE PRECO). DAVI must not relabel model inference as source fact.
- **CURRENCY:** Same UNPROVEN NF currency gap as purchase price history.
- **UNIT:** product.unit from SB1; monetary fields inherit sibling semantics.
- **TIME:** Same resolve_history_date_range as purchase price history (default 365 days). last_purchase inside the composite is unbounded TOP 1, independent of the window.
- **PRIVACY:** Composite includes last_purchase.supplier_tax_id (A2_CGC) — must never be approved.
- **RISK:** {'databaseQueryCost': 'HIGH', 'responseVolume': 'HIGH', 'nesting': 'HIGH', 'historicalScan': 'HIGH', 'recursiveBom': 'NONE', 'downstreamUseCases': 'HIGH', 'timeoutRisk': 'HIGH', 'overall': 'HIGH'}
- **QUARANTINE DELTA:** [{"token": "preco", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `preco` quarantine. Future implementation must add precise multiword aliases (keep global; do not own via this deferred capability) so the promoted action owns the token; unrelated economic actions remain quarantined."}, {"token": "custo", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `custo` quarantine. Future implementation must add precise multiword aliases (keep global; do not own via this deferred capability) so the promoted action owns the token; unrelated economic actions remain quarantined."}, {"token": "cost", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `cost` quarantine. Future implementation must add precise multiword aliases (keep global; do not own via this deferred capability) so the promoted action owns the token; unrelated economic actions remain quarantined."}]
- **OPEN GAPS:** ['fetch_purchase_budget_history has no item limit (unbounded UNION ALL in the date window)', 'Composite dump overlaps last_purchase + purchase_price_history', 'No summaries-only backend contract exists to isolate price_status cheaply', 'supplier_tax_id present on last_purchase nested object']
- **DECISION:** `DEFER`

- **DEFER REASON:** Distinct classified overlay exists, but executing the canonical operation always scans unbounded SC+PC budget history and dumps sibling item arrays. Projection cannot reduce backend work. Freeze last_valid + price_history instead; do not promote a mega-intelligence capability in this wave.

### product.cost.impact_simulation — `DEFER_FROM_READ_WAVE`

- **BUSINESS NEED:** Authorized compute-only ranking of raw materials that most impact the material cost of one finished product (PA), optionally applying a percent adjustment. Result is not an approved price, persisted cost, purchasing authorization, accounting entry or business approval.
- **TECHNICAL OWNER:** api-delpi Product bounded context
- **BUSINESS OWNER:** TO_INVENTORY — no canonical named business owner proven in source; do not invent Comercial, Suprimentos, Controladoria or Financeiro
- **SOURCE OF TRUTH:** GET /products/{code}/cost-impact-simulation → GetProductCostImpactSimulationUseCase → ProductCostImpactRepository (SB1010 header B1_CUSTD/B1_UCALSTD + recursive SG1010 BOM MP aggregation OPTION MAXRECURSION 0) → build_cost_impact_simulation (in-memory only). Unit basis: ProductCostImpactUnitService + product_cost_impact_units.json (MI = 1000 pieces). PA-only (rejects non-PA).
- **BACKEND AUTHZ:** PROVEN: @require_permission(API_DELPI_ACCESS) on get_cost_impact_simulation
- **READ/PREPARE/ACT:** PREPARE
- **CANONICAL OPERATION(S):** `get_product_cost_impact_simulation`
- **INPUTS:** required=['code'] optional=['max_depth', 'price_source', 'adjustment_percent', 'top_n']
- **OUTPUT PATH COUNT:** 51
- **PROJECTION:** SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR / mode=nested
- **MONETARY:** unit_cost is CANONICAL_BACKEND_CALCULATION from price_source (B1_CUSTD standard_cost or B1_UPRC last_purchase, with fallback). extended_cost = quantity_per_pa * unit_cost. simulated_* apply adjustment_percent multiplier. Impact percents are backend calculations. simulation result != approved price / persisted product cost / purchasing authorization / accounting entry / business approval. GET compute-only: no INSERT/UPDATE/DELETE in use case, service or repository.
- **CURRENCY:** B1_CUSTD/B1_UPRC have no currency field in this payload. Currency UNPROVEN; do not assume BRL. Do not invent a currency field.
- **UNIT:** quantity_per_pa is normalized via ProductPaBomReferenceService for 1 PA. cost_basis documents MI vs piece: parentUnits.MI catalogPiecesPerUnit=1000. materials.items[].unit is the MP catalog unit. Do not expose amount without these unit fields.
- **TIME:** No start_date/end_date. BOM validity is ProductBomValidityFilterService for today. product.standard_cost_date is B1_UCALSTD cadastro date. Simulation is a point-in-time compute against current BOM + current costs.
- **PRIVACY:** Internal cost/margin-adjacent ranking. Minimize to ranking + simulation totals. Drop BOM path. No customer/supplier PII in this payload.
- **RISK:** {'databaseQueryCost': 'HIGH', 'responseVolume': 'MEDIUM', 'nesting': 'MEDIUM', 'historicalScan': 'LOW', 'recursiveBom': 'HIGH', 'downstreamUseCases': 'LOW', 'timeoutRisk': 'HIGH', 'overall': 'HIGH'}
- **QUARANTINE DELTA:** [{"token": "custo", "action": "KEEP_GLOBAL", "rationale": "Cost simulation is PREPARE / DEFER_FROM_READ_WAVE. Do not own `custo` in the READ broker. Keep the global token; a future PREPARE track may own precise aliases later."}, {"token": "cost", "action": "KEEP_GLOBAL", "rationale": "Cost simulation is PREPARE / DEFER_FROM_READ_WAVE. Do not own `cost` in the READ broker."}]
- **OPEN GAPS:** ['Currency of B1_CUSTD/B1_UPRC is UNPROVEN', 'SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN', 'Recursive BOM with MAXRECURSION 0 remains HIGH cost even with DAVI max_depth=8']
- **DECISION:** `DEFER_FROM_READ_WAVE`

- **DEFER REASON:** HTTP GET compute-only simulation is PREPARE, not READ, under the canonical DAVI capability model (preview/draft/simulação sem persistir). Architecture Acceptance reclassified it out of Wave 2 READ. Analysis of source, AuthZ, projection, monetary/unit/currency gaps and simulation boundary remains valid for a future PREPARE track. Do not create PREPARE runtime, MCP tools or Agent Instruction changes in Wave 2.

### product.purchase.last_valid — `FROZEN_FOR_IMPLEMENTATION`

- **BUSINESS NEED:** Authorized latest valid inbound NF snapshot for one product (supplier, unit price, quantity, date) without a date window and without a history series.
- **TECHNICAL OWNER:** api-delpi Product bounded context
- **BUSINESS OWNER:** TO_INVENTORY — no canonical named business owner proven in source; do not invent Comercial, Suprimentos, Controladoria or Financeiro
- **SOURCE OF TRUTH:** GET /products/{code}/last-purchase → GetProductLastPurchaseUseCase → ProductRawMaterialPriceRepository.fetch_last_purchase: SD1010 TOP 1 valid inbound NF ordered by D1_EMISSAO/D1_DTDIGIT/D1_DOC DESC + SA2010 name. No date filter. Distinct from purchase_price_history default 365-day window.
- **BACKEND AUTHZ:** PROVEN: @require_permission(API_DELPI_ACCESS) on get_last_purchase
- **READ/PREPARE/ACT:** READ
- **CANONICAL OPERATION(S):** `get_product_last_purchase`
- **INPUTS:** required=['code'] optional=['branch']
- **OUTPUT PATH COUNT:** 14
- **PROJECTION:** SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR / mode=nested
- **MONETARY:** last_purchase.unit_price is D1_VUNIT; total_value is D1_TOTAL; icms_rate is D1_PICM. Same UNPROVEN gross/net caveat as history.
- **CURRENCY:** No currency field on last_purchase payload. UNPROVEN; do not assume BRL.
- **UNIT:** product.unit is B1_UM; quantity/unit_price follow that catalog unit.
- **TIME:** No start_date/end_date. Returns the latest valid NF regardless of age. This is the proven distinction versus purchase price history (windowed series).
- **PRIVACY:** MUST drop supplier_tax_id (SA2 A2_CGC). Keep supplier_name/code consistent with eligible purchases list.
- **RISK:** {'databaseQueryCost': 'LOW', 'responseVolume': 'LOW', 'nesting': 'LOW', 'historicalScan': 'LOW', 'recursiveBom': 'NONE', 'downstreamUseCases': 'LOW', 'timeoutRisk': 'LOW', 'overall': 'LOW'}
- **QUARANTINE DELTA:** [{"token": "preco", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `preco` quarantine. Future implementation must add precise multiword aliases (último preço de compra / última NF de compra) so the promoted action owns the token; unrelated economic actions remain quarantined."}, {"token": "price", "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES", "rationale": "Do not remove global `price` quarantine. Future implementation must add precise multiword aliases (last purchase price) so the promoted action owns the token; unrelated economic actions remain quarantined."}]
- **OPEN GAPS:** ['NF currency UNPROVEN', 'SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN']
- **DECISION:** `FROZEN_FOR_IMPLEMENTATION`

### product.snapshot.summary — `DEFER`

- **BUSINESS NEED:** A light cadastro+estoque+preços snapshot. Revalidated after economic inventory.
- **TECHNICAL OWNER:** api-delpi Product bounded context
- **BUSINESS OWNER:** TO_INVENTORY — no canonical named business owner proven in source; do not invent Comercial, Suprimentos, Controladoria or Financeiro
- **SOURCE OF TRUTH:** GET /products/{code}/summary composes search_products + list stock[:10] + GetProductPricingUseCase. Not a distinct minimized business contract.
- **BACKEND AUTHZ:** PROVEN: @require_permission(API_DELPI_ACCESS) on get_product_summary
- **READ/PREPARE/ACT:** READ
- **CANONICAL OPERATION(S):** `get_product_summary`
- **INPUTS:** required=['code'] optional=[]
- **OUTPUT PATH COUNT:** 0
- **PROJECTION:** SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR / mode=nested
- **MONETARY:** Would duplicate product.commercial.pricing if prices were included.
- **CURRENCY:** Same DA1_MOEDA gap as pricing.
- **UNIT:** Duplicates search/stock/pricing units.
- **TIME:** No dedicated time contract; stock and prices are current slices.
- **PRIVACY:** Composite would mix stock with commercial prices.
- **RISK:** {'overall': 'MEDIUM'}
- **QUARANTINE DELTA:** []
- **OPEN GAPS:** ['No distinct minimized semantic snapshot that does not duplicate search+stock+pricing']
- **DECISION:** `DEFER`

- **DEFER REASON:** Pricing becoming governable does not promote summary. Without prices it duplicates search+stock; with prices it is a mega-summary. Remain DEFER.

## Semantic redundancies

- `RG-PRODUCT-ECONOMIC-SALE-VS-PURCHASE`: DISTINCT: DA1 sale tables vs SD1 inbound NF unit prices.
- `RG-PRODUCT-PURCHASE-ORDERS-VS-NF-PRICES`: DISTINCT: SC7010 POs (DAVI already eligible, unit_price dropped) vs SD1 NF purchase-price series.
- `RG-PRODUCT-LAST-PURCHASE-VS-HISTORY`: DISTINCT snapshot vs bounded latest-N windowed series. last_purchase has no date filter (latest valid NF ever); history is TOP N inside a date window and does not prove full-period completeness.
- `RG-PRODUCT-INTELLIGENCE-COMPOSITE`: DEFER intelligence: composite dump + unbounded budget_history scan.
- `RG-PRODUCT-COST-SIMULATION-PREPARE`: HTTP GET != semantic READ. Compute-only simulation with adjustment_percent and simulated_*/projected_* fields is PREPARE. Defer from Wave 2 READ.
- `RG-PRODUCT-SUMMARY-AFTER-PRICING`: Remain DEFER. Pricing freeze does not promote mega-summary.

## Quarantine plan

- Keep global: ['preco', 'price', 'pricing', 'custo', 'cost']
- Remove global: NONE

- **preço do produto** → `product.commercial.pricing` (not: purchase history / last purchase / intelligence / simulation)
- **preço comercial / tabela de preço / preço de venda** → `product.commercial.pricing` (not: purchase-side capabilities)
- **preço de compra** → `product.purchase.price_history` (not: commercial pricing; too broad for last_valid unless 'último' is present)
- **histórico de preço de compra / evolução de preço de compra** → `product.purchase.price_history` (not: last_valid snapshot)
- **último preço de compra / última NF de compra** → `product.purchase.last_valid` (not: history series)
- **inteligência de preço de matéria-prima / análise de preço de mp** → `NONE_THIS_WAVE (capability DEFER; remain globally quarantined)` (not: do not steal via broad preço aliases)
- **impacto no custo / simular impacto de custo** → `NONE_THIS_READ_WAVE (PREPARE / DEFER_FROM_READ_WAVE; remain globally quarantined)` (not: do not own custo/cost aliases in the READ broker)
- **preço / custo / produto (bare tokens)** → `NONE — keep global quarantine; do not freeze these as aliases` (not: all economic capabilities)

## Runtime impact of this task

ALLOWLIST / ELIGIBILITY / RETRIEVAL / PROJECTION / EXECUTOR / MCP / AGENT / API: **UNCHANGED**.

