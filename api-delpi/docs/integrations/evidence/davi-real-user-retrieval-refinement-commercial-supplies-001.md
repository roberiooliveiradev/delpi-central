# DAVI — Real User Retrieval Refinement (Commercial + Supplies)

**TASK_ID:** `DAVI-REAL-USER-RETRIEVAL-REFINEMENT-COMMERCIAL-SUPPLIES-001`  
**STATUS (source):** PASS  
**STATUS (live/deploy):** `PENDING_EXTERNAL_ACTION` / `TEST_NOT_RUN` (filled after push + prod recreate)

## Objective

Refine semantic retrieval so natural DELPI user questions resolve to the correct governed Commercial / Supplies capability, without new tools, AuthZ, routes, or operationId hardcodes.

## Bootstrap

| Field | Value |
|---|---|
| Last externally revalidated main | `eb5f961f01c14c13fe7780cc71b4a3426557aa8a` |
| Bootstrap HEAD (pre-mutation workspace) | `398196b0fdb2a746a202625a4d7740c09e915690` |
| Ancestry of `eb5f961f01…` | CONFIRMED |
| Branch | `main` |
| Unrelated dirty | preserved (plans, openapi catalog, tv-dashboard tsbuildinfo) |

## Baseline → After

| Metric | Before | After |
|---|---|---|
| Allowlist version | 13 | 14 |
| Eligible READ | 53 | 53 |
| MCP tools | 3 | 3 |
| Agent intelligence | `2026.09.24.2` | unchanged |
| External surface | READ-only | READ-only |

## Root-cause taxonomy

| Category | Material? | Notes |
|---|---|---|
| A Missing natural-language aliases | YES | Faturou/faturamos, economia, valor do estoque, série/evolução |
| B Overly generic sibling aliases | YES | Product Master/Customers/Purchases/Stock short tokens |
| C Singular/plural | YES (partial) | saldo/saldos handled via stem + aliases |
| D Stopword / filler insertion | YES | `dos`/`de`/`neste` broke contiguous phrase match |
| E Word-order variation | YES (partial) | clients novos / média … |
| F Natural verb variation | YES | faturamos↔faturamento (suffix-gated stem) |
| G Aggregate/list/series underweight | YES | series lost to base; quais vs quantos |
| H Strong short exact phrase boosts | YES | single-token cap ≤0.78 |
| I Generic Product stealing analytics | YES | search_products / get_product_* collisions |

## Implementation strategy

**Aliases + justified generic retrieval** (Abstraction Gate PASSED).

### Metadata (allowlist v14)

Durable `semanticAliases` for Commercial + Supplies intents listed in the task matrices. No verbatim test-sentence memorization for holdouts.

### Generic retrieval (`retrieval.py`) — provider/route independent

1. Portuguese filler-tolerant ordered phrase match (content tokens only; question words `qual`/`quais`/`quanto`/`quantos` kept as content).
2. Single-token phrase boost capped at **0.78**.
3. Multiword score prefers **longest** matching alias; light hit-count tie-break.
4. Conservative PT plural/stem compatibility; verb/noun stem gated by suffix family.
5. Ranking tie-break: `(-score, -best_multiword_alias_len, operation_id)`.

No `operationId` / route boosts. No new MCP tool / executor / proxy / RBAC.

## Source acceptance (TOP-1)

All mandatory Supplies + Commercial + cross-family + holdout + write-guard cases in  
`tests/test_davi_real_user_retrieval_commercial_supplies.py` — **PASS**.

Diagnostic post-fix scores (local): S1–S6 and C1–C9 all TOP-1 correct (scores ~0.90–0.99).

## Tests executed

```text
pytest tests/test_davi_real_user_retrieval_commercial_supplies.py \
  tests/test_davi_capability_wave_005_supplies.py \
  tests/test_davi_capability_wave_004_commercial.py \
  tests/test_davi_operation_inventory_sync.py \
  tests/test_davi_dynamic_read.py::test_allowlist_v5_multi_ops_rebaseline \
  tests/test_davi_capability_wave_003a_freeze.py
# → 245 passed
```

## Residual search

| Pattern | Result |
|---|---|
| query→operationId hardcode in retrieval | ABSENT |
| route-specific boost | ABSENT |
| manual intent map | ABSENT |
| new MCP tool | ABSENT |
| AuthZ / SQL / business formula change | ABSENT |
| Agent intelligence route inventory | ABSENT |

## Coverage decision

`REFINE_REAL_USER_RETRIEVAL_COMMERCIAL_SUPPLIES`  
previous: `CORRECT_STOCK_BALANCES_SUMMARY_ITEMS_RETRIEVAL`

## Next

Push → canonical prod recreate of `api-delpi` → live discover S1–S6 / C1–C9 + representative execute → return to Architecture for Wave 006 (no GPT Actions).
