# DAVI — API DELPI operation inventory (generated)

> Evidence artifact. Not runtime authority. Not semantic capability catalog.

- Task: `DAVI-DYNAMIC-READ-005`
- Source: `openapi_baseline.json` version `3`
- TOTAL OPERATIONS: **703**
- TOTAL GET: **506**
- WRITE VERBS (POST/PUT/PATCH/DELETE): **197**
- DAVI_ELIGIBLE_READ (before→after): **1 → 1**
- NEWLY ELIGIBLE: **0**

## Coverage decision

```json
{
  "taskId": "DAVI-DYNAMIC-READ-005",
  "decision": "PROMOTE_ZERO_NEW_OPERATIONS",
  "reason": "No additional GET passed all gates (external-processing, classification, AuthZ/branch, model-safe flat projection) without inventing human approval."
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
  "note": "Delta vs previously generated inventory artifact on disk"
}
```

## Status counts

| Status | Count |
|---|---:|
| `ADMIN_OUT_OF_SCOPE` | 76 |
| `DAVI_ELIGIBLE_READ` | 1 |
| `DESTRUCTIVE_OUT_OF_SCOPE` | 16 |
| `GENERIC_SQL_FORBIDDEN` | 2 |
| `NEEDS_BRANCH_AUTHZ_EVIDENCE` | 1 |
| `NEEDS_DATA_CLASSIFICATION` | 60 |
| `NEEDS_EXTERNAL_PROCESSING_APPROVAL` | 316 |
| `NEEDS_NESTED_PROJECTION_SUPPORT` | 70 |
| `STREAM_BINARY_OUT_OF_SCOPE` | 31 |
| `WRITE_OUT_OF_SCOPE` | 130 |

## Eligible operationIds

- `search_products`

## High-value blocked (primary blocker)

- `get_product_detail` → `NEEDS_NESTED_PROJECTION_SUPPORT` — product_snapshot nested under product; flat items[] projection cannot sanitize; search_products approval does not transfer; external-processing not independently ratified
- `get_product_summary` → `NEEDS_DATA_CLASSIFICATION` — Composite product+stock+prices; pricing/cost classification unresolved; stock branch AuthZ unresolved; most-restrictive section wins
- `get_product_stock` → `NEEDS_BRANCH_AUTHZ_EVIDENCE` — branch query is optional filter only; no proven requested-branch AuthZ
- `get_product_structure` → `NEEDS_NESTED_PROJECTION_SUPPORT` — hierarchy/BOM shape; no independent external-processing approval
- `get_product_structure_exclusivity` → `NEEDS_NESTED_PROJECTION_SUPPORT` — nested playbook/report shape; no independent external-processing approval
- `get_product_production_status` → `NEEDS_NESTED_PROJECTION_SUPPORT` — nested production report; no independent external-processing approval
- `get_product_factory_status` → `NEEDS_NESTED_PROJECTION_SUPPORT` — composite structure/raw_material_stock/production/shipping; blocked by stock/production sections
- `get_product_suppliers` → `NEEDS_EXTERNAL_PROCESSING_APPROVAL` — supplier relational data; search_products approval does not transfer
- `get_product_customers` → `NEEDS_EXTERNAL_PROCESSING_APPROVAL` — customer relational data; search_products approval does not transfer
- `get_product_pricing` → `NEEDS_DATA_CLASSIFICATION` — pricing/financial high risk; no external-processing approval
- `get_product_purchases` → `NEEDS_EXTERNAL_PROCESSING_APPROVAL` — purchases domain; no independent DAVI external approval
- `get_product_purchase_price_history` → `NEEDS_DATA_CLASSIFICATION` — price history; financial classification unresolved
- `get_product_raw_material_price_intelligence` → `NEEDS_DATA_CLASSIFICATION` — price/cost intelligence; financial classification unresolved
- `get_product_cost_impact_simulation` → `NEEDS_DATA_CLASSIFICATION` — cost simulation; financial classification unresolved
