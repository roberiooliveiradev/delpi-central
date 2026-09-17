# DAVI Wave 2 Architecture Acceptance

- Task: `DAVI-CAPABILITY-EXPANSION-WAVE-002-FREEZE-CORRECTION-001`
- Source freeze SHA: `b5de5122f13bb921f6e6a48a0fad2d559e97eb80`
- Decision: `ACCEPT_WITH_RESIDUAL`
- Corrected freeze HEAD (generation): `b5de5122f13bb921f6e6a48a0fad2d559e97eb80`

## Corrections

1. `product.cost.impact_simulation`: READ / FROZEN_FOR_IMPLEMENTATION → **PREPARE / DEFER_FROM_READ_WAVE**.
2. `product.commercial.pricing`: remove currentness claim → registered commercial price tables.
3. `product.purchase.price_history`: bounded latest-N; `full_period_completeness = NOT_PROVEN`.

## Wave 2 READ set

- `product.commercial.pricing`
- `product.purchase.price_history`
- `product.purchase.last_valid`

Count: **3**. Expected eligible after implementation: **13**. MCP tools: **3**. Agent Instructions: **UNCHANGED**.

Canonical freeze authority after this correction remains `davi-capability-wave-002-freeze.json`.

