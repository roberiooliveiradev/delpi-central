# E1.S5 — Parameter strategy shadow + cutover parcial

**Status:** `CUTOVER_PARTIAL` (2026-09-10)  
**Onda:** B (plano 01)  
**Authority agora (cutover):** `none`, `semantic`, `sale_orders` → `PlanExternalActionsService._bind_arguments`  
**Observer (shadow):** builders legados (`{}` / `build_sale_orders`)  
**Fora do corte:** `product_code`, `date_branch`, `supplies_stock`, `department_idd`, …

## Flags

```json
"parameterStrategyShadow": {
  "enabled": true,
  "cutoverEnabled": true,
  "strategies": ["none", "semantic", "sale_orders"]
}
```

- `cutoverEnabled=false` → volta authority para strategy (só shadow vs binder).

## Aceite

```text
CUTOVER_NONE_SEMANTIC = PASS
CUTOVER_SALE_ORDERS = PASS
PRODUCT_DATE_BRANCH_UNTOUCHED = PASS
SHADOW_STILL_OBSERVES_LEGACY = PASS
FLAG_ROLLBACK = PASS (cutoverEnabled off)
FULL_STRATEGY_REMOVAL = NOT_STARTED
```

## Próximo

1. Live: taxa agree binder vs legacy em `sale_orders`.  
2. Expandir cutover para `supplier_part_number` / `supplies_stock` se prose/schema bastar.  
3. E1.S6: cleanup de fields mortos só após evidência ampla.
