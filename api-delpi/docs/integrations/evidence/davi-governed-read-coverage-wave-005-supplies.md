# DAVI Governed READ Coverage — Wave 005 Supplies

**TASK_ID:** `DAVI-CAPABILITY-EXPANSION-WAVE-005-SUPPLIES-READ`  
**STATUS (source):** PASS  
**STATUS (live/deploy):** `PENDING_EXTERNAL_ACTION` / `TEST_NOT_RUN`

## Product direction (frozen)

- Production MCP only: `https://minhadelpi.com.br/apps/api-delpi/mcp`
- Progressive governed coverage of API DELPI READ families
- No MCP tool per family (tools remain 3)
- No generic expose-all / proxy / SQL
- GPT Actions surface = deferred until READ families close

## Inventory rebaseline

| Field | Value |
|---|---|
| Stale inventory artifact (HEAD) | **17** |
| Actual allowlist eligible before Wave 005 (v10) | **35** |
| Rebaseline method | `scripts/generate_davi_api_inventory.py` from OpenAPI baseline + allowlist |
| After Wave 005 | **53** |
| STALE_EVIDENCE resolved | YES |

## Baseline → after

| Field | Before | After |
|---|---|---|
| Allowlist | v10 | **v11** |
| Eligible READ | 35 | **53** |
| MCP tools | 3 | **3** |
| Agent intelligence | 2026.09.24.2 | unchanged |
| Document transport | OFF / outside JSON broker | unchanged |
| GPT Actions | DEFER | unchanged |

## Disposition (30 candidates)

**PROMOTE (18):**

- KPI: `get_supplies_cpv`, `get_supplies_inventory_turnover`, `get_supplies_negotiation_savings_summary`, `get_supplies_otd`, `get_supplies_stock_value`
- Purchase-order OTD: `get_supplies_purchase_order_otd`, `get_supplies_purchase_order_otd_series`
- Safety stock: summary, items, item suppliers, supplier purchase price history
- Consumption analysis: summary, items
- Stock balances: summary, items
- Third-party materials: summary, shipments
- Purchase requests: `list_supplies_purchase_request_lines`

**DEFER (11):** panel; open coverage (unbounded); single SC detail; filters; item/consumption details; shipment detail; recent linked orders/receipts; requesters lookup; protheus user-by-email

**REJECT (1):** `export_supplies_third_party_materials_returns` — binary/document export must not flow through `execute_delpi_information` JSON

## AuthZ (backend-final)

| Subfamily | Backend permission set |
|---|---|
| KPI / PO OTD / stock balances / stock value | `KPI_SUPPLIES_ACCESS` |
| Safety stock + consumption | `SAFETY_STOCK_READ_PERMISSIONS` |
| Purchase request lines | `PURCHASE_REQUESTS_READ_PERMISSIONS` |
| Third-party materials | `THIRD_PARTY_MATERIALS_READ_PERMISSIONS` |

DAVI local RBAC / branch AuthZ / service account = ABSENT.

## Architecture invariants

- Generic discover → candidate_token → execute only
- No Supplies executor / path map / operationId switch
- Nested projection declarative (purchase_orders[], product/partner nests)
- No wildcard projection
- Drawing PDF still not executable
- Commercial OTD retrieval regresses: “OTD comercial” → sales; “OTD de compras” → purchase-order OTD

## Source tests

- `tests/test_davi_capability_wave_005_supplies.py`
- `tests/test_davi_operation_inventory_sync.py`
- Prior wave regressions updated for eligible=53 / allowlist v11

## Live / deploy

Recorded as PENDING until production MCP acceptance after deploy.
