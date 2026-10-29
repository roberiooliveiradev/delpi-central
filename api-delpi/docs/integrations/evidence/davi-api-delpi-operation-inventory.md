# DAVI — API DELPI operation inventory (generated)

> Evidence artifact. Not runtime authority. Not semantic capability catalog.

- Task: `DAVI-INTELLIGENCE-002`
- Source: `openapi_baseline.json` version `3`
- TOTAL OPERATIONS: **784**
- TOTAL GET: **573**
- WRITE VERBS (POST/PUT/PATCH/DELETE): **211**
- DAVI_ELIGIBLE_READ (before→after): **94 → 94**
- NEWLY ELIGIBLE: **0**

## Coverage decision

```json
{
  "taskId": "DAVI-INTELLIGENCE-002",
  "decision": "EVOLVE_SPECIALIST_INTELLIGENCE_AND_CONTEXT_DELIVERY",
  "reason": "GLPI DAVI-INTELLIGENCE-002: specialist/persona task — bounded retrieval additions only: material-movement business phrases map to get_product_internal_movements (entrada/saída/movimentos de materiais) and aggregate movement-scan phrases map to execute_readonly_sql (produtos com movimentação no período). No new ops, no new MCP tools, DATA_SQL_ACCESS unchanged; persona/specialist knowledge lives in agent intelligence + MCP instructions, not in this allowlist.",
  "previousDecision": {
    "taskId": "DAVI-INTELLIGENCE-001",
    "decision": "COMPLETE_ROW_RECORD_INTENT_ROUTING",
    "reason": "GLPI DAVI-INTELLIGENCE-001: completes the two-sided record-intent contract designed in CORRECTIVE-001 — metadata ops already suppress row-access phrases via retrievalNegativePhrases; execute_readonly_sql (canonical, owner-restored Oct-19) now owns the positive side via data-intent aliases (registros/linhas/dados de tabela) so natural requests like \"10 primeiros registros da SG1010\" discover the governed SQL capability without the user naming SQL/routes. No new ops, no new MCP tools, backend DATA_SQL_ACCESS unchanged.",
    "previousDecision": {
      "taskId": "DAVI-SUPPLIER-WEB-RESEARCH-INTELLIGENCE-003",
      "decision": "EVOLVE_SUPPLIER_WEB_RESEARCH_ORCHESTRATION",
      "reason": "GLPI #530 V3: declarative supplier_web_research flow — DELPI code is the anchor: get_product_suppliers first, then manufacturer PNs drive authorized public research (provider-side navigation only, never a backend proxy). Flows A (registered suppliers only, no web), B (code→suppliers→PN→public research), C (external PN→DELPI, V2 preserved), D (new market suppliers ≠ homologated). Reference-quality rules (manufacturer vs distributor vs internal code), privacy guard (no ERP data to public services), untrusted-content rules. Aliases on get_product_suppliers only. Eligible READ 94 unchanged; MCP tools 2; zero new capabilities.",
      "previousDecision": {
        "taskId": "DAVI-PRODUCT-MATCHING-INTELLIGENCE-V2-001",
        "decision": "EVOLVE_MATCHING_INTELLIGENCE_P1_TO_P4",
        "reason": "GLPI #530 V2: PN-first search precedence (manufacturer/distributor/DELPI code distinction), detail+supplier reconciliation, bounded similar-candidate selection with governed norms, two-layer classification (cadastral identification evidence vs technical evaluation), response contract and normalization rules in agent intelligence flow. Backend total semantics documented as OR-token universe count (not a defect); no contract change. Aliases for manufacturer-site phrasing added to PN op. Eligible READ 94 unchanged. MCP tools 2.",
        "previousDecision": {
          "taskId": "DAVI-SIMILARITY-FLOW-ACCEPTANCE-002",
          "decision": "PROMOTE_SIMILARITY_DISCOVERY_AND_AGENT_ORCHESTRATION",
          "reason": "GLPI #530 acceptance: close the similarity/dedup retrieval gap — add similarity/duplicate/equivalence/check-before-register aliases to search_products (candidate discovery) and get_product_detail (reference lookup); add governed similarity_dedup_check flow to davi_agent_intelligence.json directing the agent to reformulate composite register+check requests into pure READ discovers, bound candidate fan-out, reconcile suppliers/PNs, classify POSSIBLE_DUPLICATE/POSSIBLE_TECHNICAL_SIMILARITY/INSUFFICIENT_INFORMATION/TECHNICAL_MISMATCH and never assert equivalence without Engineering authority. READ-only guard unchanged — real write verbs still return zero candidates; the agent reformulates legitimately read-only intent. Eligible READ unchanged at 94. MCP tools remain 2.",
          "previousDecision": {
            "taskId": "DAVI-PRODUCT-DETAIL-SIMILARITY-001",
            "decision": "PROMOTE_GOVERNED_PRODUCT_DETAIL_AND_PN_DISCOVERY",
            "reason": "GLPI #530 similarity: promote get_product_detail (was SEMANTICALLY_REDUNDANT vs 3-field search_products) with fail-closed technical projection — 32 approved product.* paths (identity/type/classification, units+conversion, engineering/production fields, packaging/logistics, MP/PI-PA struct, RoHS/traceability/quality-MRP flags, DELPI classification). Financial/fiscal/accounting/commercial/audit/internal-control fields remain non-approved (never projected). Approved input: code only (view/legacy not exposed). Add generic part-number aliases to existing search_products_by_supplier_part_number op. Eligible READ 93->94. MCP tools remain 2. GPT Actions unchanged. No equivalence authority — candidates only.",
            "previousDecision": {
              "taskId": "DAVI-GOVERNED-KNOWLEDGE-MP-PI-FULL-NORMS-V2-IMPLEMENTATION-01",
              "decision": "PUBLISH_GOVERNED_KNOWLEDGE_CORPUS_V2",
              "reason": "Publish corpus V2 (17 documents: V1 15 + ratified full MP/PI norms, freeze-002) via the existing canonical GET /knowledge/technical-guides/{topic} catalog action with corpus_version selection (default latest). Backend api-delpi.access AuthZ, approved projection, 3-excerpt pages unchanged. Documents remain untrusted guidance, not domain truth or authorization. No new MCP tool, RAG, vector store, SQL or proxy capability.",
              "previousDecision": {
                "taskId": "DAVI-LIVE-TECHNICAL-KNOWLEDGE-DISCOVER-EXECUTE-01",
                "decision": "PROMOTE_GOVERNED_TECHNICAL_KNOWLEDGE_READ",
                "reason": "Owner-ratified bounded READ of the 15 frozen V1 governed-knowledge documents via the canonical GET /knowledge/technical-guides/{topic} catalog action (api-delpi.access backend AuthZ, approved projection only, 3-excerpt pages). Documents are untrusted guidance, not domain truth or authorization. MP/PI standards remain unpublished pending business ratification. No new MCP tool, RAG, vector store, SQL or proxy capability.",
                "previousDecision": {
                  "taskId": "DAVI-SUPPLIES-INVENTORY-VALIDATION-001",
                  "decision": "PROMOTE_ACCURACY_AND_NON_MOVING_STOCK_READS",
                  "reason": "Expose the four existing owner GET routes for inventory accuracy and non-moving stock (summary and paged items). Backend end-user AuthZ is unchanged. Approved nested fields preserve reference periods, denominators, exclusions and valuation source; item pages are capped at 50. No SQL/proxy/write capability.",
                  "previousDecision": {
                    "taskId": "DAVI-INVENTORY-MATERIAL-FLOW-CORRECTIVE-001",
                    "decision": "DEFER_OP_MATERIALS_BATCH_AND_TIGHTEN_DAVI_PROJECTIONS",
                    "reason": "Architecture corrective over the shipped wave: (1) defer list_production_order_operation_materials_batch from DAVI (CAPABILITY_NOT_PRODUCT_FROZEN_FOR_DAVI — owner route/contract unchanged, not a defect); governed allowlist 90->89 while baseline executable stays 87 because the batch was already NEEDS_BOUNDED_EXECUTION on the baseline snapshot; (2) DAVI-bound list_supplies_inventory_adjustments page_size to 50 (owner API contract remains <=500); (3) remove raw items[].movement_type from get_product_internal_movements DAVI projection — semantic fields (movement_category/direction/label, inventory_adjustment_nature) remain; (4) SB7 inventory provenance made fail-closed: exactly one candidate B7_DOC exposes document+counted_quantity, zero/ambiguous -> null (supporting provenance, not authority). All other promoted READs and DEFER entries unchanged. MCP tools remain 2. GPT Actions unchanged. No deploy, no rollout.",
                    "previousDecision": {
                      "taskId": "DAVI-INVENTORY-MATERIAL-FLOW-IMPLEMENTATION-001",
                      "decision": "PROMOTE_INVENTORY_MATERIAL_FLOW_READS",
                      "reason": "Promote 13 Inventory & Material Flow READs: 2 new inventory-adjustment ops (list + summary over SD3 doc='INVENT', CF-owned nature RE0=surplus/DE0=shortage, SB7 provenance, 366d pair, page_size<=500), raw-material set shortages (branch required, layered BranchAccessGate preserved), production consumption by-item and top-items, allocation gaps, finished-without-consumption anomaly, OP operation materials (single + SEMANTIC_READ_POST batch bounded 300), losses records and top-materials, safety-stock item details and consumption-analysis details (composite blocks minimized: collection totals/summaries and calculation memory only). Enrich get_product_stock with committed/reserved quantities, get_supplies_stock_value with estimation.* provenance, and get_product_internal_movements with governed kind enum (4 values) plus movement classification fields. DEFER: top_items_by_work_center (REWORK_REQUIRED — allocation-side semantics), top_items_validated (SEMANTICALLY_REDUNDANT), purchase_requests_open_coverage (UNBOUNDED_LIST_NO_PAGINATION, unchanged). MCP tools remain 2. GPT Actions unchanged. No deploy, no rollout.",
                      "previousDecision": {
                        "taskId": "SYSTEM-METADATA-IMPLEMENTATION-001",
                        "decision": "PROMOTE_SYSTEM_METADATA_GOVERNED_READS",
                        "reason": "Promote 5 frozen System Metadata READs (search_tables_by_description, search_protheus_columns_by_description, search_protheus_columns_in_table, get_protheus_table, list_protheus_table_columns) via generic restrictedPathRead=BOUNDED_METADATA_READ opt-in on /system GET + explicit inputs/outputs. Exactly 3 semantic capabilities: system.protheus.table.search, system.protheus.column.search, system.protheus.table.describe. Frozen external names table_name/text bound to owner tableName/q via trusted argumentBindings; owner results[] rebound to frozen data[] via responseBindings for column search only. Governed READ 72->77. All other /system operations (indexes, relations, schema, observability, console, smoke) remain ADMIN_OUT_OF_SCOPE; execute_readonly_sql stays GENERIC_SQL_FORBIDDEN with precedence over any marker. MCP tools remain 2. GPT Actions unchanged.",
                        "previousDecision": {
                          "taskId": "PRODUCT-MASTER-EXTENSIONS-IMPLEMENTATION-001",
                          "decision": "PROMOTE_PRODUCT_MASTER_GOVERNED_READS",
                          "reason": "Promote 9 frozen Product Master READs: physical locations and inventory blocks via governed SEMANTIC_READ_POST (trusted requestBody required, product_codes 1-50), supplier part-number lookup, exclusive raw-material catalog views, internal movements, inbound/outbound invoice items (product.invoice.history directional pair), sales summary, sales open orders (PortfolioScope-owned AuthZ preserved). Eligible READ 63->72 on live OpenAPI; baseline fallback keeps semantic POSTs non-executable (NEEDS_BOUNDED_EXECUTION) since it carries no requestBody contract. get_product_sales_billing not promoted (SEMANTICALLY REDUNDANT); get_product_directives, get_product_raw_material_set_shortages and get_product_purchase_budget_history remain DEFERRED in explicitlyNotApproved. MCP tools remain 2. GPT Actions unchanged.",
                          "previousDecision": {
                            "taskId": "DAVI-CAPABILITY-EXPANSION-WAVE-006-PRODUCTION-READ",
                            "decision": "PROMOTE_PRODUCTION_OPERATIONAL_INTELLIGENCE_READ"
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## Inventory delta

```json
{
  "previous_total_operations": 784,
  "current_total_operations": 784,
  "previous_total_get": 573,
  "current_total_get": 573,
  "added_operations": 0,
  "removed_operations": 0,
  "note": "Delta vs last committed inventory artifact (HEAD)"
}
```

## Status counts

| Status | Count |
|---|---:|
| `ADMIN_OUT_OF_SCOPE` | 71 |
| `DAVI_ELIGIBLE_READ` | 94 |
| `DESTRUCTIVE_OUT_OF_SCOPE` | 19 |
| `GENERIC_SQL_FORBIDDEN` | 1 |
| `LEGACY_UNSAFE` | 2 |
| `NEEDS_BOUNDED_EXECUTION` | 3 |
| `NEEDS_MODEL_SAFE_PROJECTION` | 362 |
| `NEEDS_NESTED_PROJECTION_SUPPORT` | 54 |
| `SEMANTICALLY_REDUNDANT` | 2 |
| `STREAM_BINARY_OUT_OF_SCOPE` | 37 |
| `WRITE_OUT_OF_SCOPE` | 139 |

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
- `get_on_time_delivery_pct`
- `get_overall_equipment_effectiveness_pct`
- `get_product_customers`
- `get_product_detail`
- `get_product_drawing`
- `get_product_factory_status`
- `get_product_guide`
- `get_product_inbound_invoice_items`
- `get_product_internal_movements`
- `get_product_last_purchase`
- `get_product_outbound_invoice_items`
- `get_product_parents`
- `get_product_pricing`
- `get_product_production_status`
- `get_product_purchase_price_history`
- `get_product_purchases`
- `get_product_raw_material_set_shortages`
- `get_product_safety_stock`
- `get_product_sales_open_orders`
- `get_product_sales_summary`
- `get_product_shipping_status`
- `get_product_stock`
- `get_product_structure`
- `get_product_structure_exclusivity`
- `get_product_suppliers`
- `get_production_allocation_gaps`
- `get_production_appointments_produced_totals`
- `get_production_appointments_summary`
- `get_production_consumption_by_item`
- `get_production_consumption_top_items`
- `get_production_losses_records`
- `get_production_losses_top_materials`
- `get_production_machine_load_operations`
- `get_production_machine_load_work_centers`
- `get_production_oee`
- `get_production_oee_series`
- `get_production_orders_finished_without_consumption`
- `get_production_otd`
- `get_production_otd_series`
- `get_protheus_table`
- `get_sales_conversion_rate`
- `get_sales_conversion_rate_series`
- `get_sales_order_otd`
- `get_sales_order_otd_by_branch`
- `get_sales_order_otd_by_customer`
- `get_sales_order_otd_series`
- `get_sales_order_otd_series_by_customer`
- `get_sales_order_otd_summary`
- `get_supplies_cpv`
- `get_supplies_inventory_accuracy_items`
- `get_supplies_inventory_accuracy_summary`
- `get_supplies_inventory_adjustments_summary`
- `get_supplies_inventory_turnover`
- `get_supplies_negotiation_savings_summary`
- `get_supplies_non_moving_stock_items`
- `get_supplies_non_moving_stock_summary`
- `get_supplies_otd`
- `get_supplies_purchase_order_otd`
- `get_supplies_purchase_order_otd_series`
- `get_supplies_safety_stock_consumption_analysis_item_details`
- `get_supplies_safety_stock_consumption_analysis_items`
- `get_supplies_safety_stock_consumption_analysis_summary`
- `get_supplies_safety_stock_item_details`
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
- `list_exclusive_raw_materials_catalog`
- `list_product_drawings`
- `list_production_order_operation_materials`
- `list_protheus_table_columns`
- `list_supplies_inventory_adjustments`
- `list_supplies_purchase_request_lines`
- `read_governed_technical_knowledge`
- `search_products`
- `search_products_by_supplier_part_number`
- `search_protheus_columns_by_description`
- `search_protheus_columns_in_table`
- `search_tables_by_description`

## High-value blocked (primary blocker)

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
- `get_supplies_third_party_materials_shipment` → `SHIPMENT_DETAIL` — Single shipment detail with returns nested — defer after list shipments proves stable.
- `list_supplies_purchase_request_recent_linked_orders` → `POLLING_CURSOR_HELPER` — after_recno polling helper for BFF sync, not primary DAVI Q&A capability.
- `list_supplies_purchase_request_recent_linked_receipts` → `POLLING_CURSOR_HELPER` — after_recno polling helper for BFF sync, not primary DAVI Q&A capability.
- `list_supplies_purchase_request_requesters` → `PII_LOOKUP_HELPER` — Requester lookup for UI filters; PII/identity helper without clear standalone information need.
- `get_supplies_protheus_user_by_email` → `PII_IDENTITY_LOOKUP` — Email→Protheus user identity lookup; not a Supplies information capability for DAVI.
- `export_supplies_third_party_materials_returns` → `STREAM_BINARY_OUT_OF_SCOPE` — Binary/document export must not flow through execute_delpi_information JSON (no base64).
- `get_product_sales_billing` → `SEMANTICALLY_REDUNDANT` — Billing-broken-down sales slice overlaps product.invoice history and sales summary semantics; no distinct governed fields authorized for this promotion
- `get_product_directives` → `DEFER` — Deferred by Architecture; no governed fields or bounded contract approved in this promotion
- `get_product_purchase_budget_history` → `DEFER` — Deferred by Architecture; purchase budget history semantics not approved in this promotion
- `get_production_consumption_top_items_by_work_center` → `REWORK_REQUIRED` — Semantics reviewed: the work-center slice counts allocation-side rows, not realized consumption — answers a different question than the top-items consumption family. Needs its own bounded contract before READ promotion.
- `get_production_consumption_top_items_validated` → `SEMANTICALLY_REDUNDANT` — Same ranking as get_production_consumption_top_items narrowed to rows whose OP has an appointment — a filter variant of the promoted operation, not a distinct governed capability.
- `list_production_order_operation_materials_batch` → `CAPABILITY_NOT_PRODUCT_FROZEN_FOR_DAVI` — Deferred by DAVI-INVENTORY-MATERIAL-FLOW-CORRECTIVE-001: not explicitly frozen in the approved DAVI Product/Architecture scope and no proven DAVI consumer need justifies the batch of up to 300 OPs. Owner API route/contract unchanged; single-OP list_production_order_operation_materials remains promoted. Not a security/AuthZ/endpoint defect.
