# DAVI — API DELPI operation inventory (generated)

> Evidence artifact. Not runtime authority. Not semantic capability catalog.

- Task: `DAVI-CAPABILITY-EXPANSION-WAVE-002`
- Source: `openapi_baseline.json` version `3`
- TOTAL OPERATIONS: **703**
- TOTAL GET: **506**
- WRITE VERBS (POST/PUT/PATCH/DELETE): **197**
- DAVI_ELIGIBLE_READ (before→after): **10 → 13**
- NEWLY ELIGIBLE: **3**

## Coverage decision

```json
{
  "taskId": "DAVI-CAPABILITY-EXPANSION-WAVE-002",
  "decision": "PROMOTE_PRODUCT_ECONOMIC_READ_WAVE_2",
  "reason": "Promote get_product_pricing, get_product_purchase_price_history and get_product_last_purchase as governed READ capabilities behind the existing three MCP broker tools. Eligible READ 10→13. Cost impact simulation remains PREPARE/DEFER_FROM_READ_WAVE and is not executable. AuthZ policy unchanged (DAVI-READ-AUTHZ-REBASELINE-001). Global economic quarantine tokens remain; ownership is via precise semantic aliases only. Purchase-history dateRange uses generic missing-bound policy aligned with canonical resolve_history_date_range.",
  "previousDecision": {
    "taskId": "DAVI-CAPABILITY-EXPANSION-WAVE-001",
    "decision": "PROMOTE_OPERATIONAL_PRODUCT_INTELLIGENCE_WAVE_1"
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
| `DAVI_ELIGIBLE_READ` | 13 |
| `DESTRUCTIVE_OUT_OF_SCOPE` | 16 |
| `GENERIC_SQL_FORBIDDEN` | 2 |
| `NEEDS_MODEL_SAFE_PROJECTION` | 368 |
| `NEEDS_NESTED_PROJECTION_SUPPORT` | 66 |
| `SEMANTICALLY_REDUNDANT` | 1 |
| `STREAM_BINARY_OUT_OF_SCOPE` | 31 |
| `WRITE_OUT_OF_SCOPE` | 130 |

## Eligible operationIds

- `get_product_customers`
- `get_product_factory_status`
- `get_product_last_purchase`
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
