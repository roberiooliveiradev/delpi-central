# E1.S5 — Parameter strategy shadow + cutover parcial

**Status:** `CUTOVER_PARTIAL` expandido (2026-09-10)  
**Onda:** B (plano 01)

## Ordem executada (sem pular)

1. `none` / `semantic` → binder  
2. `sale_orders` → binder  
3. `supplier_part_number` → binder (+ resolução canônica de papel no `_bind_arguments`)  
4. `supplies_stock` → binder (+ defaults `top_limit`/`limit` no wrapper de cutover)

**Ainda fora:** `product_code`, `date_branch`, `department_idd`, `lmp`, `product_search`, `exclusive_catalog`, `system_metadata`, `sql`

## Flags

```json
"parameterStrategyShadow": {
  "enabled": true,
  "cutoverEnabled": true,
  "strategies": [
    "none", "semantic", "sale_orders",
    "supplier_part_number", "supplies_stock"
  ]
}
```

## Aceite

```text
CUTOVER_NONE_SEMANTIC = PASS
CUTOVER_SALE_ORDERS = PASS
CUTOVER_SUPPLIER_PART_NUMBER = PASS
CUTOVER_SUPPLIES_STOCK = PASS
PRODUCT_DATE_BRANCH_UNTOUCHED = PASS
MISSING_SUPPLIER_PN_RETURNS_NONE = PASS
BINDER_SUPPLIER_ROLE_SCHEMA_DRIVEN = PASS
```

## Próximo (não pular)

1. Próximas strategies da fila segura (ex.: avaliar `exclusive_catalog` / `lmp` com inventário).  
2. Só então E1.S6 cleanup de fields mortos.  
3. `product_code` / `date_branch` só com plano próprio (BUSINESS_RULE / TRANSVERSAL).
