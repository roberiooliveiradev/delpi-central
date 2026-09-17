# DAVI — Generic Pagination Completeness Hardening

> Evidence artifact. Not runtime authority. Not live/deploy proof.

**TASK_ID:** `DAVI-DYNAMIC-READ-PAGINATION-COMPLETENESS-001`

## Summary

Corrected generic broker semantics for `is_complete` / `truncated` when canonical pagination metadata proves a multi-page (partial) dataset.

## Classification

```text
GENERIC BROKER RESPONSE COMPLETENESS BUG
```

Not a Product / where-used / Wave 3A business-rule bug.

## Live reproduction (pre-fix)

`get_product_parents` with:

| field | value |
|---|---|
| page | 1 |
| page_size | 50 |
| total | 123 |
| total_pages | 3 |

Broker incorrectly emitted `is_complete=true`, `truncated=false`.

## Root cause

`bound_response_payload` treated `len(items) <= max_items` as dataset completeness and defaulted:

```text
is_complete=true
truncated=false
```

ignoring source `total` / `total_pages`. Envelope flags used the same optimistic rule.

## Fix

Generic helpers in `projection.py`:

- `source_pagination_proves_partial`
- `derive_response_completeness`
- `bound_response_payload` consumes derived flags

No `operationId` / path / entity / capability branching.

## Invariants preserved

| Surface | Value |
|---|---|
| eligible READ | 15 |
| allowlist version | 8 |
| MCP tools | 3 |
| Agent Instructions | UNCHANGED |
| shortages | DEFER |

## Source / runtime

| Surface | Status |
|---|---|
| SOURCE | PASS (this task) |
| LOCAL TESTS | see pytest |
| DEPLOY | TEST_NOT_RUN |
| LIVE | TEST_NOT_RUN |
| AGENT PREVIEW | TEST_NOT_RUN |
