# DAVI Capability Wave 3A Inventory

**taskId:** `DAVI-CAPABILITY-EXPANSION-WAVE-003A-FREEZE`
**artifact_class:** `EVIDENCE_NOT_RUNTIME_AUTHORITY`
**source_head:** `37baceb7ba20329d9ed412fc1019182317a59191`
**origin_main:** `37baceb7ba20329d9ed412fc1019182317a59191`
**current_eligible:** 13
**allowlist_version:** 7

## Candidates

### `product.routing.guide` — **FROZEN_FOR_IMPLEMENTATION**

- operation: `get_product_guide`
- READ/PREPARE/ACT: `READ`
- AuthZ: PROVEN: @require_permission(API_DELPI_ACCESS) on guide() in product_routes.py
- businessNeed: Consultar a sequência operacional / roteiro (SG2) do produto e de componentes da BOM vigente até max_depth: operações, centros de trabalho, tempos padrão e componentes de operação. Não é status de OP, carga de máquina nem progresso de produção.

### `product.where_used` — **FROZEN_FOR_IMPLEMENTATION**

- operation: `get_product_parents`
- READ/PREPARE/ACT: `READ`
- AuthZ: PROVEN: @require_permission(API_DELPI_ACCESS) on parents() in product_routes.py
- businessNeed: Identificar produtos pai que consomem o código informado via explosão reversa da BOM vigente (SG1), recursiva até max_depth. Responde onde a MP/componente é usada. Não altera estrutura e não lista BOM filha.

### `product.raw_material.set_shortages` — **DEFER**

- operation: `get_product_raw_material_set_shortages`
- READ/PREPARE/ACT: `READ`
- AuthZ: PROVEN: @require_permission(API_DELPI_ACCESS) PLUS BranchAccessGate via raw_material_set_shortage_branch_error (PRODUCTION_CONTROL_BRANCH_VIEW_PERMS / PRODUCTION_CONTROL_ACCESS). Branch is policy-aware backend AuthZ + filter — not DAVI AuthZ.
- businessNeed: Analisar se matérias-primas da BOM vigente do PA projetam saldo negativo no extrato (estoque + PCs − empenhos) para OPs mãe abertas do PA na filial concreta.

- deferReason: Backend computation and payload are HIGH risk without enforceable bounds on open mother orders, material ledger size, or a summary-only response mode. Pagination absent. DAVI projection cannot reduce SQL/fan-out cost. Require canonical Product/domain evolution before reconsideration: e.g. maxOrders, summary-only flag, or server-side TOP on ledger.

## Source validation

```json
{
  "ok": true,
  "allowlistVersion": 7,
  "eligibleCount": 13,
  "eligibleIds": [
    "search_products",
    "get_product_stock",
    "get_product_suppliers",
    "get_product_customers",
    "get_product_purchases",
    "get_product_structure",
    "get_product_production_status",
    "get_product_factory_status",
    "get_product_structure_exclusivity",
    "get_product_shipping_status",
    "get_product_pricing",
    "get_product_purchase_price_history",
    "get_product_last_purchase"
  ],
  "wave3aOpsAbsentFromAllowlist": true,
  "openapiOperationIdsPresent": {
    "get_product_guide": false,
    "get_product_parents": false,
    "get_product_raw_material_set_shortages": false
  },
  "authzDecorators": {
    "get_product_guide": "PROVEN API_DELPI_ACCESS",
    "get_product_parents": "PROVEN API_DELPI_ACCESS",
    "get_product_raw_material_set_shortages": "PROVEN API_DELPI_ACCESS + BranchAccessGate"
  },
  "notes": [
    "davi_capability_expansion_lib.py historical seeds are STALE_EVIDENCE for Wave 2 economic status; Wave 2 freeze/implementation evidence wins.",
    "Guide/parents UC default max_depth=999 is a freeze risk mitigated by argumentLimits max=8 at future implementation."
  ]
}
```

## Notes

- Historical `davi_capability_expansion_lib.py` seeds are not runtime authority (STALE_EVIDENCE for Wave 2 economic statuses).
- Wave 2 freeze/implementation evidence remains authoritative for pricing/history/last_purchase.
- This task must not mutate allowlist, eligibility, retrieval, projection, executor, MCP, or Agent Instructions.
