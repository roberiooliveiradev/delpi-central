# DAVI Capability Expansion — Wave 3A Implementation

> Evidence artifact. Not runtime authority. Not live/deploy proof.

**TASK_ID:** `DAVI-CAPABILITY-EXPANSION-WAVE-003A`

## Summary

Promoted exactly two governed READ capabilities behind the existing three MCP broker tools:

| Capability | Operation | Governed max_depth |
|---|---|---|
| `product.routing.guide` | `get_product_guide` | 8 (default 8) |
| `product.where_used` | `get_product_parents` | 4 (default 4) |

Deferred (unchanged):

| Capability | Operation | Status |
|---|---|---|
| `product.raw_material.set_shortages` | `get_product_raw_material_set_shortages` | DEFER |

## Eligibility

- Before: **13** (allowlist v7)
- After: **15** (allowlist v8)
- MCP tools: **3** (unchanged)
- Agent Instructions: **UNCHANGED**

## Depth invariant (where-used)

```text
DAVI requested depth <= DAVI model-visible approved parents[] depth = 4
```

Canonical Product use case may still default to 999 when `max_depth` is omitted at the HTTP boundary. DAVI injects governed defaults via generic `argumentConstraints.argumentLimits` before execute.

## Routing pagination

Canonical guide returns full in-memory dump when `page`/`page_size` are omitted. DAVI always injects `page=1`, `page_size=50`, `max_depth=8` when omitted.

## AuthZ

- `DAVI_BUSINESS_AUTHZ_OWNER = NONE`
- Backend `@require_permission(API_DELPI_ACCESS)` remains final on both routes
- No DAVI-local RBAC / role / branch / object AuthZ

## Derived fields (routing)

- `standard_time_hours_piece` — canonical backend calculation based on `G2_TEMPAD`
- `standard_time_minutes_piece` — canonical backend calculation based on source conversion

DAVI explains; it does not own the formula.

## Source / runtime

| Surface | Status |
|---|---|
| SOURCE | PASS (this task) |
| LOCAL TESTS | see pytest report |
| DEPLOY | TEST_NOT_RUN |
| LIVE | TEST_NOT_RUN |
| AGENT PREVIEW | TEST_NOT_RUN |

## Freeze authority

Preserved: `davi-capability-wave-003a-freeze.json` (+ correction `FREEZE-CORRECTION-001`).
