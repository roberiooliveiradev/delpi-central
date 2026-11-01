# SURI-MCP-V6-G3 — CODE + DEPLOY ACCEPTANCE

Data: 2026-10-31 · TASK: `SURI-MCP-V6-G3-DELIVERIES-INVENTORY-001`
Plano: `SURI-MCP-V6-G3-DELIVERIES-INVENTORY-END-TO-END-IMPLEMENTATION-PLAN.md` (a0338de141)

## G3.0–G3.1 Inventário + Contract Freeze (PASS)

```text
deliveries.late   → BFF GET /deliveries/late (can_use_operations)
  → LateDeliveriesCompositionService().compose(user, branches,
     status, start_date, end_date, page, page_size, sort_by, sort_dir)
  Filtros: branch[] status{late,on_time} start_date end_date
           sort_by∈12 campos sort_dir page≥1 page_size≤1000
inventory.summary → GET /inventory/stock-balances/summary
  → InventoryStockBalancesService().get_summary(user, branches, warehouse)
inventory.items   → GET /inventory/stock-balances/items
  → list_items(user, branches, warehouse, page, page_size≤500, sort∈6)
AuthZ: can_use_operations (supplies.access/Core) + unit scope 01/02
  via serviços canônicos (normalize_overview_branches) — paridade Portal.
```

## G3.2 Implementação (menor diff, supplies-api/mcp)

```text
constants.py: CATALOG_VERSION 5→6; deliveries:{late} e
  inventory:{summary,items} em READ_ACTIONS_BY_ENTITY; allowlists
  DELIVERIES_LATE_*/INVENTORY_* (vocabulário fechado do BFF).
schemas.py:   DeliveriesLateFilters, InventorySummaryFilters,
  InventoryItemsFilters — extra="forbid".
server.py:    Literals entity/action + union de filtros (3 novos).
tool_bridge:  _dispatch_deliveries/_inventory + 3 handlers reutilizando
  os serviços canônicos (zero SQL duplicada; AuthZ por chamada via
  _operations_user; ValueError→422; gateway errors honestos).
metadata:     "read-only v1" corrigido (execute suppliers existe).
Union fix:    exclude_none+exclude_unset preservado (testes dedicados).
```

## G3.3 Testes (container supplies-mcp, imagem pré-deploy)

```text
tests/interface/suri_mcp: 179 PASS (167 baseline + 6 union + 6 G3 novos)
  - cada ação alcança o serviço com kwargs corretos
  - defaults de modelo irmão não vazam (regressão do bug V5)
  - filtros desconhecidos 422 fail-closed; action inválida rejeitada
  - test_tool_bridge.py atualizado p/ catalog v6 + novas entidades
```

## G3.7 Deploy

```text
SOURCE SHA:  a4a2697058 (fix code+tests, main)
PREV_IMAGE:  d6f9d233f3c6 (tag infra-supplies-mcp:pre-v6-rollback)
NEW_IMAGE:   infra-supplies-mcp:latest (rebuild; catalog v6 in-image)
CONTAINER:   delpi-supplies-mcp recreated only, healthy, restart=0
Não tocados: supplies-api, api-delpi, PR-api, core, keycloak, gateway
```

## G3.8 Homologação autenticada (OAuth user-delegated real)

```text
get_context(catalog):          success=true · version=6
DELIVERIES_LATE   Oct/branch01  200 success=true total=0 (empty válido)
DELIVERIES_LATE   Jul–Oct       200 success=true total=47
DELIVERIES_LATE   on_time Oct   200 success=true total=192
INVENTORY_SUMMARY branch=01     200 success=true (dados reais)
INVENTORY_ITEMS   branch=01     200 success=true total=48894
NEG filtro desconhecido         validation error (fail-closed)
NEG action inválida             "Unknown read action for inventory"
NEG branch=99                   "Unknown branch: 99" (unit scope)
TOOLS = 5 (in-image + transport) · sem writes executados
CHATGPT_TOOL_SCHEMA: INCONCLUSIVE (schema no conector não revalidado —
  o servidor publica V6; a descoberta depende do refresh do conector)
```

## G3.9 Estado final

```text
R-11 deliveries.late     = AUTHENTICATED_RUNTIME_PROVEN
R-12 inventory.summary   = AUTHENTICATED_RUNTIME_PROVEN
R-12 inventory.items     = AUTHENTICATED_RUNTIME_PROVEN
G1/G2 REGRESSION         = PASS (suíte verde; sem regressão runtime)
CATALOG_VERSION=6 · TOOL_COUNT=5
COMMITS: a4a2697058 (código+testes) · este doc
UNRESOLVED: CHATGPT_SCHEMA refresh do conector (INCONCLUSIVE)
NEXT_STEP: matriz atualizada R-11/R-12; G4/safety stock não autorizado.
```
