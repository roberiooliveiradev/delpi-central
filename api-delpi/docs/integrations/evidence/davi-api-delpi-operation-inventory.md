# DAVI — API DELPI operation inventory (generated)

> Evidence artifact. Not runtime authority. Not semantic capability catalog.

- Task: `DAVI-PRODUCT-DRAWING-CAPABILITY-001`
- Source: `openapi_baseline.json` version `3`
- TOTAL OPERATIONS: **703**
- TOTAL GET: **506**
- WRITE VERBS (POST/PUT/PATCH/DELETE): **197**
- DAVI_ELIGIBLE_READ (before→after): **15 → 17**
- NEWLY ELIGIBLE: **2**

## Coverage decision

```json
{
  "taskId": "DAVI-PRODUCT-DRAWING-CAPABILITY-001",
  "decision": "PROMOTE_PRODUCT_DRAWING_JSON_READ_FOUNDATION",
  "reason": "Promote list_product_drawings and get_product_drawing as governed JSON READ capabilities (catalog + metadata). Eligible READ 15→17. Catalog requires product code (requireArguments) to avoid unbounded file-server scan via DAVI. get_product_drawing_pdf remains DEFER pending generic document transport (no PDF/base64 via execute_delpi_information). get_product_analyser not promoted for drawing analysis. AuthZ unchanged (API_DELPI_ACCESS). MCP tools remain 3. Agent Instructions unchanged.",
  "previousDecision": {
    "taskId": "DAVI-CAPABILITY-EXPANSION-WAVE-003A",
    "decision": "PROMOTE_PRODUCT_ENGINEERING_READ_WAVE_3A"
  }
}
```

## Inventory delta

```json
{
  "previous_total_operations": 703,
  "current_total_operations": 703,
  "previous_total_get": 506,
  "current_total_get": 506,
  "added_operations": 0,
  "removed_operations": 0,
  "note": "Delta vs last committed inventory artifact (HEAD)"
}
```

## Status counts

| Status | Count |
|---|---:|
| `ADMIN_OUT_OF_SCOPE` | 76 |
| `DAVI_ELIGIBLE_READ` | 17 |
| `DESTRUCTIVE_OUT_OF_SCOPE` | 16 |
| `GENERIC_SQL_FORBIDDEN` | 2 |
| `NEEDS_MODEL_SAFE_PROJECTION` | 365 |
| `NEEDS_NESTED_PROJECTION_SUPPORT` | 65 |
| `SEMANTICALLY_REDUNDANT` | 1 |
| `STREAM_BINARY_OUT_OF_SCOPE` | 31 |
| `WRITE_OUT_OF_SCOPE` | 130 |

## Eligible operationIds

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
- `list_product_drawings`
- `search_products`

## High-value blocked (primary blocker)

- `get_product_detail` → `SEMANTICALLY_REDUNDANT` — Same Product Master slice already served by search_products; no distinct governed fields
- `get_product_summary` → `DEFER` — Composite product snapshot remains deferred; not a Wave 2 READ capability
- `get_product_raw_material_price_intelligence` → `DEFER` — Unbounded budget scan / composite overlap / no bounded summaries-only backend contract
- `get_product_cost_impact_simulation` → `PREPARE` — Compute-only simulation is PREPARE, not READ. HTTP GET does not imply semantic READ. Not executable through the READ broker.
- `get_product_drawing_pdf` → `NEEDS_GENERIC_DOCUMENT_BOUNDARY` — Binary PDF document transport is not a JSON READ projection. Must not embed pdf_base64 in execute_delpi_information. Requires generic authorized document boundary (ARCHITECTURE_ESCALATION if new MCP tool/resource). AuthZ remains API_DELPI_ACCESS on the HTTP route.
- `get_product_analyser` → `PRODUCT_ANALYSER_DIRECT_PROMOTION_NOT_REQUIRED` — ProductAnalyserUseCase composes product/structure/guide/inspection JSON — it does not perform visual drawing analysis. Drawing analysis must reuse AI API workflow procedure + governed individual READs + document transport, not promote this composite.
- `get_product_inspection` → `DEFER` — Drawing analysis inspection cross-check deferred (DRAWING_ANALYSIS_INSPECTION_CROSSCHECK=DEFERRED). Not required for JSON drawing catalog/metadata foundation.
