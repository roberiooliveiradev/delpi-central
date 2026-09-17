# DAVI Wave 2 implementation evidence

> Evidence of source implementation. Not live/deploy proof. Not Agent Instructions.

- Task: `DAVI-CAPABILITY-EXPANSION-WAVE-002`
- Freeze authority: `docs/integrations/evidence/davi-capability-wave-002-freeze.json`
- Architecture acceptance: `ACCEPT_WITH_RESIDUAL`
- Allowlist version: **7**
- Eligible READ: **10 → 13**
- MCP tools: **3** (unchanged)
- Agent instructions: **UNCHANGED**

## Promoted READ capabilities

| capabilityId | operationId | status |
|---|---|---|
| product.commercial.pricing | get_product_pricing | DAVI_ELIGIBLE_READ |
| product.purchase.price_history | get_product_purchase_price_history | DAVI_ELIGIBLE_READ |
| product.purchase.last_valid | get_product_last_purchase | DAVI_ELIGIBLE_READ |

## Still not executable through the READ broker

| capabilityId | operationId | disposition |
|---|---|---|
| product.cost.impact_simulation | get_product_cost_impact_simulation | PREPARE / DEFER_FROM_READ_WAVE |
| product.raw_material.price_intelligence | get_product_raw_material_price_intelligence | DEFER |
| product.snapshot.summary | get_product_summary | DEFER |

## Generic hardening

- Quarantine ownership is phrase/alias based. Bare `preço` / `price` / `custo` / `cost` do not grant retrieval.
- Purchase-history `dateRange` uses generic `absentEnd=today` + `absentStart=effectiveEndMinusDefaultWindow` aligned with canonical `resolve_history_date_range`. No operationId branch.

## Semantic constraints preserved

- Commercial pricing does not claim current/effective price.
- Purchase history full-period completeness = NOT_PROVEN.
- Currency ISO/BRL and tax gross/net remain UNPROVEN.
- `supplier_tax_id` is dropped from last-purchase projection.

## Runtime / live

```text
SOURCE = this commit
LOCAL TESTS = see pytest evidence
DEPLOY = TEST_NOT_RUN
LIVE = TEST_NOT_RUN
AGENT PREVIEW = TEST_NOT_RUN
SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN
```
