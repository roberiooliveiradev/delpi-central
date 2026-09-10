# E1.S5 — Parameter strategy shadow (evidência)

**Status:** `SHADOW_ON` (2026-09-10) — **não** é cutover  
**Onda:** B (plano 01)  
**Escopo do 1º corte:** `none`, `semantic`, `sale_orders`  
**Fora do corte:** `product_code`, `date_branch`, `supplies_stock`, `department_idd`, …

## Inventário (resumo)

| Strategy | Onde | Classe |
|----------|------|--------|
| `none` / `semantic` | domains (+ binding `{}`) | DUPLICATES_OPENAPI |
| `sale_orders` | 1 rota registry | DUPLICATES_OPENAPI (parcial) |
| `product_code` / `date_branch` / … | maioria | BUSINESS_RULE / TRANSVERSAL — **não** neste PR |

Owner canônico de binding: `PlanExternalActionsService._bind_arguments` → `ValidateActionArgumentsService`.

## O que entrou

| Peça | Path |
|------|------|
| Flag | `openapi_tool_routing.json` → `parameterStrategyShadow.enabled=true` |
| Compare | `ParameterStrategyShadowService` |
| Telemetria | log `parameter_strategy_shadow` |
| Wiring | `OperationalRouteActionResolverService.resolve_route_action` → `metadata.parameterStrategyShadow` |
| Testes | `test_parameter_strategy_shadow_service.py` (7 passed) |

## Aceite parcial

```text
INVENTORY_STRATEGIES = PASS
SHADOW_NONE_SEMANTIC = PASS
SHADOW_SALE_ORDERS = PASS
NON_SHADOWABLE_SKIPPED = PASS
FLAG_OFF = PASS
PRODUCT_DATE_BRANCH_UNTOUCHED = PASS
CUTOVER_STRATEGY_REMOVAL = NOT_STARTED
```

## Próximo

1. Observar taxa `agree` em live para `sale_orders`.  
2. Se estável → delegar resolver a `_bind_arguments` para esses strategies.  
3. Depois: `supplier_part_number` / `supplies_stock` (ainda sem product/date_branch).
