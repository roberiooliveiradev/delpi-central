# DAVI — API DELPI operation inventory (generated)

> Evidence artifact. Not runtime authority. Not semantic capability catalog.

- Task: `DAVI-CAPABILITY-EXPANSION-WAVE-001`
- Source: `openapi_baseline.json` version `3`
- TOTAL OPERATIONS: **703**
- TOTAL GET: **506**
- WRITE VERBS (POST/PUT/PATCH/DELETE): **197**
- DAVI_ELIGIBLE_READ (before→after): **7 → 10**
- NEWLY ELIGIBLE: **3**

## Coverage decision

```json
{
  "taskId": "DAVI-CAPABILITY-EXPANSION-WAVE-001",
  "decision": "PROMOTE_OPERATIONAL_PRODUCT_INTELLIGENCE_WAVE_1",
  "reason": "Promote get_product_factory_status, get_product_structure_exclusivity and get_product_shipping_status as governed READ capabilities behind the existing three MCP broker tools. AuthZ policy unchanged (DAVI-READ-AUTHZ-REBASELINE-001).",
  "previousDecision": {
    "taskId": "DAVI-READ-AUTHZ-REBASELINE-001",
    "decision": "REBASELINE_PROMOTE_SAFE_READS"
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
| `DAVI_ELIGIBLE_READ` | 10 |
| `DESTRUCTIVE_OUT_OF_SCOPE` | 16 |
| `GENERIC_SQL_FORBIDDEN` | 2 |
| `NEEDS_MODEL_SAFE_PROJECTION` | 372 |
| `NEEDS_NESTED_PROJECTION_SUPPORT` | 65 |
| `SEMANTICALLY_REDUNDANT` | 1 |
| `STREAM_BINARY_OUT_OF_SCOPE` | 31 |
| `WRITE_OUT_OF_SCOPE` | 130 |

## Eligible operationIds

- `get_product_customers`
- `get_product_factory_status`
- `get_product_production_status`
- `get_product_purchases`
- `get_product_shipping_status`
- `get_product_stock`
- `get_product_structure`
- `get_product_structure_exclusivity`
- `get_product_suppliers`
- `search_products`

## High-value blocked (primary blocker)

- `get_product_detail` → `SEMANTICALLY_REDUNDANT` — Same Product Master slice already served by search_products; no distinct governed fields
- `get_product_summary` → `NEEDS_NESTED_PROJECTION_SUPPORT` — Composite product+stock+prices; no approved section projection yet
- `get_product_pricing` → `NEEDS_MODEL_SAFE_PROJECTION` — Awaiting explicit approvedResponseFields (minimization); not blocked by taxonomy absence
- `get_product_purchase_price_history` → `NEEDS_MODEL_SAFE_PROJECTION` — Awaiting explicit approvedResponseFields
- `get_product_raw_material_price_intelligence` → `NEEDS_MODEL_SAFE_PROJECTION` — Awaiting explicit approvedResponseFields
- `get_product_cost_impact_simulation` → `NEEDS_MODEL_SAFE_PROJECTION` — Awaiting explicit approvedResponseFields
