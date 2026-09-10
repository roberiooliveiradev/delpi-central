# E1.S5 — Parameter strategy cutover completo

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** B (plano 01)

## Ordem executada (sem pular)

1. `none` / `semantic` → OpenAPI binder  
2. `sale_orders` → OpenAPI binder  
3. `supplier_part_number` → OpenAPI binder (+ resolução canônica de papel no `_bind_arguments`)  
4. `supplies_stock` → OpenAPI binder (+ defaults `top_limit`/`limit` no wrapper de cutover)  
5. `exclusive_catalog` / `lmp` / `product_search` → domain binder canônico via `ParameterStrategyShadowService`  
6. `system_metadata` / `department_idd` → domain binder canônico  
7. `product_code` / `date_branch` → OpenAPI binder + enrich (`catalog.build_product_parameters` / `_enrich_date_branch`)

**Fora do escopo E1.S5:** `sql` (policy/domains; cleanup em E1.S6+ se aplicável).

## Flags

```json
"parameterStrategyShadow": {
  "enabled": true,
  "cutoverEnabled": true,
  "strategies": [
    "none", "semantic", "sale_orders",
    "supplier_part_number", "supplies_stock",
    "exclusive_catalog", "lmp", "product_search",
    "system_metadata", "department_idd",
    "product_code", "date_branch"
  ]
}
```

## Ownership

```text
build_parameters (resolver)
→ early return se strategy ∈ cutover + cutoverEnabled
→ ParameterStrategyShadowService.bind_via_openapi
   → binder authority: none/semantic/sale_orders/supplier_pn/supplies_stock/product_code/date_branch
   → domain binder: exclusive_catalog/lmp/product_search/system_metadata/department_idd
```

O switch tipado no resolver permanece como código morto até E1.S6 (DELETE/cleanup).

## Aceite

```text
CUTOVER_NONE_SEMANTIC = PASS
CUTOVER_SALE_ORDERS = PASS
CUTOVER_SUPPLIER_PART_NUMBER = PASS
CUTOVER_SUPPLIES_STOCK = PASS
CUTOVER_EXCLUSIVE_LMP_PRODUCT_SEARCH = PASS
CUTOVER_SYSTEM_METADATA_DEPARTMENT_IDD = PASS
CUTOVER_PRODUCT_CODE_DATE_BRANCH = PASS
MISSING_SUPPLIER_PN_RETURNS_NONE = PASS
LMP_MISSING_SALE_NUMBER_RETURNS_NONE = PASS
PRODUCT_SEARCH_NON_PRODUCTS_PATH_RETURNS_NONE = PASS
ALL_RESOLVER_STRATEGIES_IN_CUTOVER = PASS
```

## Testes

`tests/unit/domain/services/test_parameter_strategy_shadow_service.py` — suite E1.S5.

## Próximo

1. **E1.S6 fatia B** — cutover de seleção (após agree E1.S4), depois DELETE fields.  
2. Binding: switch tipado do resolver já removido (E1.S6A); não reabrir cutover de binding sem regressão live.
