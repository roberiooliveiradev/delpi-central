# DAVI — API DELPI operation inventory (generated)

> Evidence artifact. Not runtime authority. Not semantic capability catalog.

- Task: `DAVI-CAPABILITY-EXPANSION-WAVE-003A`
- Source: `openapi_baseline.json` version `3`
- TOTAL OPERATIONS: **703**
- TOTAL GET: **506**
- WRITE VERBS (POST/PUT/PATCH/DELETE): **197**
- DAVI_ELIGIBLE_READ (before→after): **13 → 15**
- NEWLY ELIGIBLE: **2**

## Coverage decision

```json
{
  "taskId": "DAVI-CAPABILITY-EXPANSION-WAVE-003A",
  "decision": "PROMOTE_PRODUCT_ENGINEERING_READ_WAVE_3A",
  "reason": "Promote get_product_guide and get_product_parents as governed READ capabilities behind the existing three MCP broker tools. Eligible READ 13→15. Routing max_depth governed to 8; where-used max_depth governed to 4 (equals model-visible parents[] depth). get_product_raw_material_set_shortages remains DEFER (unbounded OP×MP×ledger). AuthZ policy unchanged (DAVI-READ-AUTHZ-REBASELINE-001). MCP tools remain 3. Agent Instructions unchanged.",
  "previousDecision": {
    "taskId": "DAVI-CAPABILITY-EXPANSION-WAVE-002",
    "decision": "PROMOTE_PRODUCT_ECONOMIC_READ_WAVE_2"
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
| `DAVI_ELIGIBLE_READ` | 15 |
| `DESTRUCTIVE_OUT_OF_SCOPE` | 16 |
| `GENERIC_SQL_FORBIDDEN` | 2 |
| `NEEDS_MODEL_SAFE_PROJECTION` | 367 |
| `NEEDS_NESTED_PROJECTION_SUPPORT` | 65 |
| `SEMANTICALLY_REDUNDANT` | 1 |
| `STREAM_BINARY_OUT_OF_SCOPE` | 31 |
| `WRITE_OUT_OF_SCOPE` | 130 |

## Eligible operationIds

- `get_product_customers`
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
- `search_products`

## High-value blocked (primary blocker)

- `get_product_detail` → `SEMANTICALLY_REDUNDANT` — Same Product Master slice already served by search_products; no distinct governed fields
- `get_product_summary` → `DEFER` — Composite product snapshot remains deferred; not a Wave 2 READ capability
- `get_product_raw_material_price_intelligence` → `DEFER` — Unbounded budget scan / composite overlap / no bounded summaries-only backend contract
- `get_product_cost_impact_simulation` → `PREPARE` — Compute-only simulation is PREPARE, not READ. HTTP GET does not imply semantic READ. Not executable through the READ broker.
