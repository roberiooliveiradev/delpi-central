# DAVI MCP DISCOVERY QUALITY — BASELINE EVIDENCE

TASK_ID: `DAVI-MCP-DISCOVERY-QUALITY-001`
SCOPE: measurement only — **no runtime ranking, alias, allowlist, capability, MCP, or AuthZ change.**
STATUS: `DISCOVERY_QUALITY_BASELINE_READY_FOR_ARCHITECTURE_REVIEW`

This document summarizes `davi-mcp-discovery-quality-001.json` (same directory), the machine-readable evidence produced by
`api-delpi/scripts/evaluate_davi_discovery_quality.py` against
`api-delpi/tests/fixtures/davi_discovery_quality_v1.json`.

## 1. SOURCE STATE (recomputed)

| Field | Value |
|---|---|
| allowlist_version | 19 |
| allowlist_operation_count | 89 |
| agent_intelligence_version | 2026.10.07.2 |
| mcp_tool_count | 2 (`discover_delpi_information`, `execute_delpi_information`) |
| discover_default_top_k / max_top_k | 5 / 10 |

## 2. CATALOG SOURCE PARITY — EXPLAINED_DIFFERENCE

| Source | Executable count |
|---|---|
| Allowlist governed operations | 89 |
| `openapi_baseline.json` executable | 87 |
| Current `app.openapi()` executable | 89 |
| Runtime observed eligible (live provider) | 89 |

Difference operationIds: `list_product_inventory_blocks`, `list_product_physical_locations`.

Both are `SEMANTIC_READ_POST` operations governed by the allowlist. The frozen baseline snapshot lacks their requestBody
contracts, so the baseline catalog builder fails closed and marks them non-executable. The live runtime seeds the action
index from `app.openapi()` (`refresh_davi_action_index_from_live_openapi`), which includes the trusted requestBody
contracts, restoring all 89. The benchmark therefore evaluates the live-OpenAPI-derived catalog — the same source as
production discovery.

## 3. BENCHMARK

| Field | Value |
|---|---|
| version | `davi_discovery_quality_v1` |
| fixture | `tests/fixtures/davi_discovery_quality_v1.json` |
| runner | `scripts/evaluate_davi_discovery_quality.py` |
| total cases | 217 |

Case counts: positive_precise 90 · positive_paraphrase 89 · ambiguous 10 · write_negative 8 · generic_sql_negative 6 ·
unsupported_negative 8 · quarantine_conflict 6.

Governed actions with positive coverage: 89/89.

## 4. HEADLINE METRICS

| Metric | Value |
|---|---|
| top1_accuracy (all positive cases, n=185) | 0.5351 |
| top1_required_accuracy (top1_required subset, n=90) | 0.6667 |
| top3_recall (positive, n=185) | 0.7243 |
| top5_recall | 0.8378 |
| MRR | 0.6477 |
| positive_no_candidate_rate | 0.0270 |
| hard_negative_zero_candidate_rate | 0.9286 |
| unsupported_zero_candidate_rate | 0.0000 |
| ambiguous_top3_coverage | 0.90 |
| ambiguous_top5_coverage | 0.90 |
| positive target misses | 23 |
| positive target rank > 5 | 7 |
| hard_negative_leaks | 1 |
| unrelated_family_top1 | 25 |

Family metrics (top1 / top3 / top5):

| Family | cases | top1 | top3 | top5 |
|---|---|---|---|---|
| product_master | 56 | 0.518 | 0.750 | 0.839 |
| commercial | 37 | 0.595 | 0.730 | 0.811 |
| supplies | 45 | 0.600 | 0.778 | 0.911 |
| production | 35 | 0.429 | 0.629 | 0.800 |
| system_metadata | 12 | 0.500 | 0.667 | 0.750 |

## 5. KNOWN LIVE RESIDUAL — REPRODUCED

`DQ-STOCK-001` — query `estoque atual do produto 10080034`, expected `get_product_stock`.

Observed: target rank 3 (score 0.714), outranked by `get_product_production_status` (0.716) and `search_products` (0.716).
Status: `RESIDUAL_REPRODUCED` — matches the live provider observation; no runtime change made.

## 6. HARD-NEGATIVE INTEGRITY

| Class | Result |
|---|---|
| write_negative | 7/8 zero candidates — **1 leak** (`insira um novo fornecedor` returned read candidates; write-intent guard does not recognize this phrasing) |
| generic_sql_negative | 6/6 zero candidates |
| unsupported_negative | 0/8 zero candidates — all 8 produced spurious candidates (diagnostic; plausible-but-ungoverned requests get lexical noise) |
| quarantine_conflict | legitimate owners still reachable; foreign generic-token ownership leaks observed |

Write/SQL fail-closed posture is preserved overall, but the single write-negative leak is a security-relevant residual for
Architecture review.

## 7. ROOT-CAUSE BREAKDOWN (deterministic classifier, diagnostic only — 86 failures)

| Category | Count | Evidence pattern |
|---|---|---|
| MULTIWORD_ALIAS_COLLISION | 20 | higher-ranked action matched a full multiword alias (e.g. OTD variants, structure vs where-used) |
| ALIAS_COLLISION | 19 | foreign-family or same-family competitor outranks the covered target |
| ALIAS_MISSING | 17 | target unreachable — zero candidates or no alias coverage (OTD series/monthly, `DQ-MET-003`, `DQ-QUA-004`) |
| SUMMARY_TOKEN_NOISE | 9 | target scored only via summary/description tokens |
| SINGLE_TOKEN_OVERWEIGHT | 6 | foreign-family single-token alias outranked the multiword target |
| QUARANTINE_INTERACTION | 6 | quarantine-conflict cases; covered-but-suppressed overlaps |
| TIE_BREAK_ARTIFACT | 5 | score gap ≤0.005 decided by secondary sort keys (incl. DQ-STOCK-001: 0.716 vs 0.714) |
| OTHER | 4 | none of the above signals |
| ALIAS_TOO_GENERIC / DESCRIPTION_TOKEN_NOISE / FILLER_MATCH_FALSE_POSITIVE / STEM_COMPATIBILITY_FALSE_POSITIVE / AMBIGUOUS_QUERY / CATALOG_SOURCE_DRIFT / BENCHMARK_EXPECTATION_WRONG | 0 | no evidence in this baseline |

Dominant higher-ranked actions across clusters: `get_product_production_status` and `search_products` (generic
single-token matches outranking specific multiword intent — the DQ-STOCK-001 mechanism). Unsupported negatives bind to
generic summary tokens (`estoque`, `produto`, `fornecedor`, `data de entrega`). Full per-failure evidence (query,
expected, rank, scores, higher-ranked actions, aliases, `root_cause`) is in the JSON artifact under `known_failures`.

## 8. INVARIANTS

- No production retrieval/normalization/guard/service/index/builder file changed.
- No allowlist, negativeAliases, quarantine tokens, or Agent Intelligence change.
- No MCP surface change (still exactly 2 tools), no AuthZ change, no deploy, no provider calls.
- Discover-contract check: 54/54 candidate shapes valid, ordering identical to retrieval-level ranking, no candidate
  tokens persisted in evidence.

## 9. NEXT (NOT EXECUTED)

Architecture review decides between `DAVI-MCP-DISCOVERY-QUALITY-CORRECTIVE-001` and `NO_CORRECTIVE_REQUIRED`. Any
corrective must improve benchmark quality without operationId-specific hacks, hardcoded user phrases, generic
expose-all, weakened write/SQL fail-closed behavior, AuthZ changes, or MCP expansion.
