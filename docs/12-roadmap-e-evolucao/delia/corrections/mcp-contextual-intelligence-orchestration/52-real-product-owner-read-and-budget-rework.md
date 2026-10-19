# 52 — Real product owner READ and budget rework

**DATE:** 2026-10-19  
**TASK_ID:** `DELIA-C3-REAL-PRODUCT-OWNER-READ-AND-BUDGET-REWORK-01`  
**REFERENCE_HEAD:** `cc18410cc67541e603c4ab2b64dcd5d81de5f4db`  
**STATUS:** `IMPLEMENTATION_CANDIDATE` (live outcome after deploy)

## Reuse gate

| Need | Owner | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|---|
| Product search contract | api-delpi `GET /products/search` (`search_products`) | YES | REUSE |
| OpenAPI projection | `openapi:delpi` / `delpi.search_products` | YES | REUSE |
| DAVI discover→execute | MCP `discover_delpi_information` / `execute_delpi_information` | YES | REUSE (not required when OpenAPI selected) |
| Orchestration / deadline | `OperationalCapabilityOrchestrator`, `TurnDeadline` 30s | YES | EXTEND (budget-skip gate only) |
| Argument proposal | LLM + schema validation | YES | REUSE |
| New planner / product registry / regex intent | — | — | **FORBIDDEN** |

## Owner direct evidence (pre-fix)

| Case | Contract | Result | Latency |
|---|---|---|---|
| OWNER-P01 `description=TERM. PINO` | `search_products` | HTTP 200, n=5, total>0, AuthZ ok | ~158ms |
| OWNER-P02 `TERM. OLHAL` | same | HTTP 200, n=5, total>0 | ~107ms |
| OWNER-P03 `terminal` | same | HTTP 200, n=5, total=64 | ~40ms |
| OWNER-P04 code from P01 | same | HTTP 200, n=1 | ~33ms |
| OWNER-P05 no-match | same | HTTP 200, n=0, total=0 | ~38ms |

DAVI discover ranks `search_products` top-1 (~90–174ms). Bare in-container execute without request AuthZ context raises `PermissionError` (expected — AuthZ via HTTP/MCP credential path).

**Conclusion:** owner READ works. Defect is DÉLIA-side after selection.

## DELIA baseline (pre-fix, deployed SEMARG)

All DELIA-P01–P05 → `SOURCE_UNAVAILABLE` / `NON_GROUNDED` (~16–29s).

Representative corr `0f88e3a5-…`:

```text
interaction_admission=operational (~2.8s)
select_group (~5.3s) → openapi:delpi
select_capability (~3.9s) → delpi.search_products READ
native_assessment (~2.2s)
plan=self_index_candidate self_index_eligible=True
index_probe=skip_budget remaining_ms≈15558
arguments=built missing=0
arguments=skip_budget_identifier_unavailable fields=6
→ SOURCE_UNAVAILABLE  (owner NEVER invoked)
```

`fields=6` = optional unconstrained strings on live OpenAPI schema (`code`, `description`, `group_code`, `customer_reference`, `sort`, `direction`).

## Root cause

```text
FIRST_DIVERGENT_STAGE=arguments (post skip_budget gate)
ROOT_CAUSE=optional_index_probe_skipped_budget discarded schema-valid
  search/filter arguments even when the model had already built them;
  with DELIA_MODEL_STAGE_TIMEOUT_SECONDS=30 the optional probe headroom
  (2×stage + MIN_VIABLE×3 ≈ 66s) exceeds the 30s turn budget, so the
  probe never runs for self_index-eligible search_products.
```

Not `model_timeout` alone; not missing owner contract; not wrong owner selection.

## Fix (minimal)

In `orchestration.py`, when `optional_index_probe_skipped_budget` and index did not run:

1. Empty `{}` free-string invoke → still `SOURCE_UNAVAILABLE` / `turn_budget_exhausted` (preserves I02-R2 / SEMARG honesty for guides).
2. Filled free-string args → proceed **only if** each value is grounded in the user message (substring or overlapping alphanumeric tokens ≥3) via `_free_string_grounded_in_user_input`.
3. Pagination-only material args (no free strings) → proceed as list READ.

No regex intent, no DAVI hardcode, no planner, no timeout increase.

## Tests

`delia-api/tests/test_real_product_owner_read_and_budget_rework.py` — PROD-T01/T02/T03–T04/T07/T08/T09/T10/T12/T14–T16/T18–T23 (+ related).  
Full `delia-api` pytest: PASS.  
`test_i02r2_index_probe_headroom` invented-topic under budget skip: still SOURCE_UNAVAILABLE.

## Live post-deploy

Filled after SSH deploy + L1–L5 in ledger §6.294 / report.

## Gates

```text
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
