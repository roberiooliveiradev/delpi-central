# DAVI Capability Wave 3A Freeze

**taskId:** `DAVI-CAPABILITY-EXPANSION-WAVE-003A-FREEZE`
**implementationTaskId:** `DAVI-CAPABILITY-EXPANSION-WAVE-003A`
**status:** `FROZEN_FOR_IMPLEMENTATION`
**sourceFreezeSha:** `37baceb7ba20329d9ed412fc1019182317a59191`
**source_head:** `37baceb7ba20329d9ed412fc1019182317a59191`
**current_eligible:** 13
**frozen_count:** 2
**expected_eligible_after_implementation:** 15
**expected_mcp_tools_after:** 3
**agent_instruction_change:** NO

## Frozen for implementation

### `product.routing.guide`

- operation: `get_product_guide`
- inputs: `['code', 'branch', 'page', 'page_size', 'max_depth']`
- output_path_count: 15
- projection: `SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR`
- aliases PT: ['roteiro do produto', 'roteiro de produção', 'operações do produto', 'sequência de operações', 'centros de trabalho do produto']

### `product.where_used`

- operation: `get_product_parents`
- inputs: `['code', 'max_depth', 'page', 'page_size']`
- output_path_count: 25
- projection: `SUPPORTED_BY_CURRENT_GENERIC_PROJECTOR`
- aliases PT: ['onde o produto é usado', 'onde a MP é usada', 'produtos pai', 'produtos que usam este componente', 'PAs que usam esta matéria-prima', 'BOM reversa']

## Deferred

### `product.raw_material.set_shortages`

- reason: Backend computation and payload are HIGH risk without enforceable bounds on open mother orders, material ledger size, or a summary-only response mode. Pagination absent. DAVI projection cannot reduce SQL/fan-out cost. Require canonical Product/domain evolution before reconsideration: e.g. maxOrders, summary-only flag, or server-side TOP on ledger.

## Retrieval plan

```json
{
  "routingOwnerIntents": [
    "roteiro do produto",
    "roteiro de produção",
    "operações do produto",
    "sequência de operações",
    "centros de trabalho do produto",
    "product routing",
    "production routing",
    "operation sequence",
    "product operations"
  ],
  "whereUsedOwnerIntents": [
    "onde o produto é usado",
    "onde a MP é usada",
    "produtos pai",
    "produtos que usam este componente",
    "PAs que usam esta matéria-prima",
    "BOM reversa",
    "where used",
    "parent products",
    "reverse BOM",
    "products using component"
  ],
  "shortagesOwnerIntents": "NONE — deferred",
  "existingStructureRegression": [
    "estrutura do produto",
    "bom do produto",
    "product structure"
  ],
  "existingProductionRegression": [
    "status de produção",
    "production status"
  ],
  "existingFactoryRegression": [
    "status fabril",
    "factory status"
  ],
  "quarantineDelta": "NONE — no new global quarantine tokens proposed"
}
```

## Runtime impact of freeze

```json
{
  "allowlist": "UNCHANGED",
  "eligibility": "UNCHANGED_AT_13",
  "retrieval": "UNCHANGED",
  "projection": "UNCHANGED",
  "executor": "UNCHANGED",
  "mcp": "UNCHANGED_AT_3",
  "agent": "UNCHANGED",
  "apiDomain": "UNCHANGED"
}
```

## Implementation handoff

Future task `DAVI-CAPABILITY-EXPANSION-WAVE-003A` may promote exactly:

- `product.routing.guide`
- `product.where_used`

Expected eligible after implementation: **15**. MCP tools remain **3**. Agent Instructions: **NO** change. Shortages remain deferred until backend bounds exist.
