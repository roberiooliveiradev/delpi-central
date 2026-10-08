# DAVI MCP DISCOVERY QUALITY — CORRECTIVE EVIDENCE

TASK_ID: `DAVI-MCP-DISCOVERY-QUALITY-CORRECTIVE-001`
SCOPE: bounded discovery/retrieval corrective — **no MCP surface, AuthZ, business API, capability, deployment, or provider change.**
STATUS: `DISCOVERY_QUALITY_CORRECTIVE_PASS` — superseded for rollout acceptance by `DAVI-MCP-DISCOVERY-QUALITY-CORRECTIVE-002`

> **Architecture review note (Corrective-002):** the `nonReadCommandVerbTokens` blanket zero-candidate rule added
> here was found over-broad — orchestration/content verbs (`gere`/`calcule`/`monte`/`traduza`/`emita`) are
> request-form words, not capability classification. Ranking metrics below remain valid evidence; the command-verb
> semantics were corrected in `davi-mcp-discovery-quality-corrective-002.{json,md}` (allowlist v21).

This document summarizes `davi-mcp-discovery-quality-corrective-001.json` (same directory), produced by
`api-delpi/scripts/evaluate_davi_discovery_quality_corrective.py`, which runs the frozen benchmark against the
corrected retrieval source (live `app.openapi()` catalog — the same seed source as production discovery) and diffs it
against the accepted baseline artifact `davi-mcp-discovery-quality-001.json`.

## 1. SOURCE STATE (recomputed at `21449834c0`)

| Field | Value |
|---|---|
| runtime_source_sha | `21449834c0a5f0804bfadb0b6a27190207b29f40` |
| allowlist_version | 19 → **20** (discovery-governance metadata only) |
| governed_operation_count | 89 (unchanged) |
| agent_intelligence_version | 2026.10.07.2 (unchanged) |
| mcp_tool_count | 2 (`discover_delpi_information`, `execute_delpi_information`) |

Drift checks before commit: `origin/main` moved twice during execution (`d09d0b32` → `5c8f39ad` → `21449834c0`);
both deltas touched only core-api / delia-api / plugin-ui / production-control-api / transformometro-api /
tv-dashboard-api — **zero api-delpi/DAVI paths → NON_CAUSAL**. Source was rebased to `21449834c0`; benchmark and
focused tests were re-run after the rebase with identical results.

## 2. CATALOG PARITY — EXPLAINED_DIFFERENCE (preserved)

| Source | Executable count |
|---|---|
| Allowlist governed operations | 89 |
| `openapi_baseline.json` executable | 87 |
| Current `app.openapi()` executable | 89 |
| Runtime observed eligible | 89 |

Difference operationIds: `list_product_inventory_blocks`, `list_product_physical_locations` — governed
`SEMANTIC_READ_POST` operations whose requestBody contracts are absent from the frozen baseline snapshot
(fail-closed there, present in live OpenAPI). Unchanged by this corrective.

## 3. PROVENANCE

| Field | Value |
|---|---|
| benchmark_version | `davi_discovery_quality_v1` (frozen) |
| fixture_sha256_before | `945de11f4ab89b28f3c076134e300005310255e28aad3b6a9763947bf0248688` |
| fixture_sha256_after | `945de11f4ab89b28f3c076134e300005310255e28aad3b6a9763947bf0248688` |
| fixture_unchanged | **true** — identical sha256 at baseline commit and at evaluation |
| runner_sha256 | `acaf42b16afc195a0d654e04a274830b2f2891376855b8ddfe10f7894f4156c6` |
| baseline_evaluated_sha | `67f6f84bcc0a41101c8dcdeda9184b43064f98b9` |

Provenance model corrected per §23: `runtime_source_sha` + `benchmark_version` + `fixture_sha256` + `runner_sha256`
replace the ambiguous `evaluated_sha`. Metric labels corrected per §24 — `top1_accuracy` (all positive cases, n=185)
and `top1_required_accuracy` (top1-required subset, n=90) are reported separately below.

## 4. P0 — WRITE-INTENT LEAK: CLOSED

Baseline leak: `insira um novo fornecedor` returned READ candidates — `inserir`/`insira` were absent from
`writeIntentVerbTokens`.

Fix (generic, token-based — not sentence matching): added `inserir`, `insira`, `incluir`, `inclua` to
`retrievalReadOnlyGuard.writeIntentVerbTokens`, and added a separate `nonReadCommandVerbTokens` group for imperative
non-READ commands (`gerar/gere`, `calcular/calcule`, `montar/monte`, `traduzir/traduza`, `emitir/emita`). Lexical
relatives (`inserção`, `inserido`, `atualização`, `alterado`, `aprovação`) remain non-commands — no prefix/stem
matching was introduced.

| Gate | Before | After |
|---|---|---|
| write_negative zero-candidate | 7/8 | **8/8** |
| generic_sql_negative zero-candidate | 6/6 | **6/6** |
| hard_negative_leaks | 1 | **0** |

## 5. DQ-STOCK-001: RESOLVED

Query `estoque atual do produto 10080034`, expected `get_product_stock`.

| | Baseline | Corrective |
|---|---|---|
| rank | 3 (score 0.714) | **1** |
| higher-ranked | `get_product_production_status` 0.716, `search_products` 0.716 | none |

Mechanism (generic, no case/operationId special-casing): bounded ordered-subsequence alias matching lets
`estoque do produto` match through the inserted modifier `atual`, and catalog-derived token specificity de-weights
generic `produto` overlap that previously inflated `search_products`/`get_product_production_status`.

## 6. METRICS — BEFORE / AFTER

| Metric | Before | After | Target | Result |
|---|---|---|---|---|
| top1_accuracy (positive, n=185) | 0.5351 | **0.9676** | ≥0.70 | PASS |
| top1_required_accuracy (n=90) | 0.6667 | **0.9889** | ≥0.80 | PASS |
| top3_recall | 0.7243 | **1.0000** | ≥0.88 | PASS |
| top5_recall | 0.8378 | **1.0000** | ≥0.95 | PASS |
| MRR | 0.6477 | **0.9829** | ≥0.78 | PASS |
| positive_no_candidate_rate | 0.0270 | **0.0000** | ≤0.01 | PASS |
| hard_negative_zero_candidate | 0.9286 | **1.0000** | =1.00 | PASS |
| unsupported_zero_candidate | 0.0000 | **1.0000** | ≥0.75 | PASS |
| ambiguous_top3_coverage | 0.90 | **0.90** | ≥0.90 | PASS |
| ambiguous_top5_coverage | 0.90 | **0.90** | ≥0.90 | PASS |
| positive_target_misses | 23 | **0** | — | — |
| positive_target_rank_gt5 | 7 | **0** | — | — |
| hard_negative_leaks | 1 | **0** | =0 | PASS |
| unrelated_family_top1 | 25 | **1** | ≤10 | PASS |

Family metrics (top1 / top3 / top5 — floor: top5 ≥ 0.90 per family):

| Family | cases | before t1/t3/t5 | after t1/t3/t5 |
|---|---|---|---|
| product_master | 56 | 0.518 / 0.750 / 0.839 | 0.964 / 1.000 / 1.000 |
| commercial | 37 | 0.595 / 0.730 / 0.811 | 1.000 / 1.000 / 1.000 |
| supplies | 45 | 0.600 / 0.778 / 0.911 | 0.956 / 1.000 / 1.000 |
| production | 35 | 0.429 / 0.629 / 0.800 | 0.943 / 1.000 / 1.000 |
| system_metadata | 12 | 0.500 / 0.667 / 0.750 | 1.000 / 1.000 / 1.000 |

All families at top5 = 1.0 — family floor satisfied.

## 7. REGRESSION MATRIX (§21)

| Signal | Count | Detail |
|---|---|---|
| previous_top1_lost | 2 | `DQ-QUA-006` (rank 3), `DQ-SUP-038` (rank 2) — both remain inside top3 |
| previous_top3_lost | 0 | — |
| previous_top5_lost | 0 | — |
| new_positive_zero_candidate | 0 | — |
| new hard-negative leakage | 0 | — |

No baseline case reachable inside top5 became a zero-candidate. The two top1 demotions are same-family near-ties
decided by deterministic ordering, not capability loss.

## 8. ROOT-CAUSE BREAKDOWN — BEFORE / AFTER

| Category | Before | After |
|---|---|---|
| MULTIWORD_ALIAS_COLLISION | 20 | 1 |
| ALIAS_COLLISION | 19 | 0 |
| ALIAS_MISSING | 17 | 0 |
| SUMMARY_TOKEN_NOISE | 9 | 1 |
| SINGLE_TOKEN_OVERWEIGHT | 6 | 0 |
| QUARANTINE_INTERACTION | 6 | 1 |
| TIE_BREAK_ARTIFACT | 5 | 1 |
| OTHER | 4 | 2 |
| **total failures** | **86** | **6** |

Residual failures (all rank 2–3, none zero-candidate): `DQ-PM-026`, `DQ-PM-054`, `DQ-SUP-024`, `DQ-SUP-038`,
`DQ-PRD-009`, `DQ-QUA-006`. One ambiguous case, `DQ-AMB-005` (`OTD do mês`), remains zero-candidate by design: bare
`otd` is quarantine-owned and the ambiguous query matches no owning alias — consistent with the frozen legacy
quarantine contract (bare `OTD`, `preço`, `pricing` must return zero candidates).

## 9. CHANGED MECHANISMS

Runtime (`retrieval.py` — governance filter still runs before ranking; deterministic ordering preserved):

- **Bounded ordered-subsequence phrase matching** (max 1 intervening content token between consecutive alias terms)
  on top of exact-window matching.
- **Catalog-derived token specificity** (`log((N+1)/(df+1))` normalized over searchable text + semantic aliases of
  eligible actions; deterministic, no manual weights; degenerate/tiny catalogs fall back to raw coverage).
- **Specificity-weighted coverage** with content-token-only mass (function words excluded from numerator and
  denominator).
- **Admission floors**: substring-partial matches below 0.5 coverage suppressed; weak-overlap fallback below 0.50
  suppressed; single-token alias candidates with <0.25 coverage suppressed.
- **Alias-claim precedence**: an action claiming a token via governed alias no longer ranks below actions that merely
  contain the token in searchable text.
- **Deterministic tie-breaking**: duplicate normalized-alias hit-count bonus removed; equal scores fall through to
  `operation_id` ordering.
- **Shared 6-char prefix token compatibility** for gerund/flexion families (e.g. `entregando`/`entrega`); no
  uncontrolled stemming.

Metadata (`davi_external_read_allowlist.json` v19→v20 — **operations, executionMode, field bindings, and permissions
untouched**):

- `retrievalReadOnlyGuard.writeIntentVerbTokens` += `inserir`, `insira`, `incluir`, `inclua`.
- New `retrievalReadOnlyGuard.nonReadCommandVerbTokens`: imperative non-READ commands (`gere`, `calcule`, `monte`,
  `traduza`, `emita`, infinitives).
- `retrievalQuarantineTokens` += out-of-catalog domains (`weather`/`clima`, `previsao`/`forecast`, payroll/HR terms,
  `e-mail`, `sql`/`select`, `hora`, cost/finance bare terms).
- `semanticAliases`: generic business phrases added/expanded (e.g. `status fabril do produto`, `conteúdo da tabela`,
  `último preço de compra`, `furos/sobras de inventário` variants) — no benchmark query strings, no operationId
  references.
- `negativeAliases`: row-access intent phrases refined (`mostre os registros`, `liste as linhas`) without suppressing
  legitimate metadata questions (`qual tabela contém …`).

`read_only_intent_guard.py`: loads `nonReadCommandVerbTokens` into the same token-exact guard — no fuzzy/prefix
matching added.

## 10. INVARIANTS — VERIFIED IN DIFF

- MCP surface: exactly 2 tools — no contract, name, or count change.
- No AuthZ, OAuth, Keycloak, scope, audience, or token-architecture change.
- No business endpoint, use case, operation membership, or capability change.
- No DAVI-local RBAC, branch ACL, permission inference, or AuthZ fallback introduced.
- No candidate tokens in evidence output; discover-contract check 54/54 (shape + ordering identical to retrieval).
- Frozen fixture sha256 unchanged before/after.

## 11. TESTS

- Focused (post-rebase, container): `test_davi_read_only_intent_guard.py`, `test_davi_dynamic_read.py`,
  `test_davi_discovery_quality_benchmark.py`, `test_davi_inventory_material_flow_corrective.py`,
  `test_davi_system_metadata.py` — **298 passed**.
- Full `pytest -k davi` (container): **1197 passed, 4 failed** — the 4 failures are freeze/source-validation tests
  that invoke `git`, which is absent from the api-delpi container image (environment limitation, not code regression).
- Git-dependent group re-run on host (`hdvenv`, `delpi_auth` importable): **40 passed**.

## 12. LIVE STATUS

This corrective proves **SOURCE + LOCAL DETERMINISTIC BENCHMARK** only.

- LIVE_DEPLOY: NOT RUN — no deploy performed.
- LIVE_ACCEPTANCE: TEST_NOT_RUN — `DAVI-MCP-LIVE-ACCEPTANCE-001` intentionally not executed.
- Provider/OAuth/HTTP/BUSINESS_AUTHZ/CROSS_USER layers: untouched and unclaimed by this evidence.

## 13. STOP CONDITION

Per the corrective directive: no deploy, no Agent Studio update, no capability expansion. Architecture must review
this evidence before any rollout or `DAVI-MCP-LIVE-ACCEPTANCE-001` execution.
