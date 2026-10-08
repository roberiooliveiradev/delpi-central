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
| top1_accuracy (top1_required cases, n=99) | 0.5351 |
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

## 7. ROOT-CAUSE CLUSTERS (diagnostic only)

- `SINGLE_TOKEN_OVERWEIGHT` / `ALIAS_TOO_GENERIC`: `get_product_production_status` and `search_products` dominate the
  higher-ranked lists across product_master and adjacent families — generic single-token matches outrank specific
  multiword intent (this is the DQ-STOCK-001 mechanism).
- `ALIAS_MISSING`: cases with zero candidates (`[]`) concentrate on monthly/series OTD variants and some quarantine-owner
  phrasings (e.g. `DQ-COM-027`, `DQ-COM-029`, `DQ-PRD-012`, `DQ-MET-003`, `DQ-QUA-004`).
- `MULTIWORD_ALIAS_COLLISION` / `ALIAS_COLLISION`: OTD variants (sales vs purchase vs production) and safety-stock vs
  stock queries cross-rank.
- `SUMMARY_TOKEN_NOISE` / `DESCRIPTION_TOKEN_NOISE`: unsupported negatives bind to generic summary tokens (`estoque`,
  `produto`, `fornecedor`, `data de entrega`).
- `TIE_BREAK_ARTIFACT`: several target-vs-competitor pairs differ by ≤0.002 (e.g. 0.714 vs 0.716) and are decided by the
  deterministic operation_id tie-break rather than semantic specificity.
- `QUARANTINE_INTERACTION`: foreign actions gain ownership of quarantine tokens via generic occurrence paths.

Full per-failure evidence (query, expected, rank, scores, higher-ranked actions, aliases) is in the JSON artifact under
`known_failures`. Root-cause labels must remain evidence-driven; counts per frozen category are recorded there.

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
