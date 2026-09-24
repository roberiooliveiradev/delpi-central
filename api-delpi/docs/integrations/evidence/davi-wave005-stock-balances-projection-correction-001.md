# DAVI Wave 005 — Stock Balances Projection Correction

**TASK_ID:** `DAVI-WAVE005-STOCK-BALANCES-PROJECTION-CORRECTION-001`  
**STATUS (source):** PASS  
**STATUS (live/deploy):** `PENDING_EXTERNAL_ACTION` / `TEST_NOT_RUN`

## Classification

`DAVI_WAVE005_STOCK_BALANCES_GRAIN_PROJECTION` = **EXECUTION_DRIFT**

Canonical grain for `by_warehouse[]` is `branch + warehouse`. DAVI `approvedResponseFields` omitted `by_warehouse[].branch`, collapsing model-visible identity to warehouse-only.

## Fix

- Allowlist **v11 → v12**
- Add only: `by_warehouse[].branch`
- Eligible READ **53 → 53** (no new capability)
- MCP tools remain **3**
- No SQL / AuthZ / business-logic change

## Coverage decision

- `CORRECT_STOCK_BALANCES_BRANCH_GRAIN_PROJECTION`
- previous: `DAVI-CAPABILITY-EXPANSION-WAVE-005-SUPPLIES-READ`

## Tests

- Cross-branch same warehouse distinguishable after projection
- Single-branch still exposes `by_warehouse[].branch`
- Items route already preserves `items[].branch` / `items[].warehouse`
- Wave 005 / commercial / inventory-sync regressions

## Live

Production MCP acceptance after deploy: confirm every `by_warehouse` row has `branch` + `warehouse`.
