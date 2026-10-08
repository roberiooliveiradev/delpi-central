# DAVI MCP DISCOVERY QUALITY — CORRECTIVE 002 EVIDENCE

TASK_ID: `DAVI-MCP-DISCOVERY-QUALITY-CORRECTIVE-002`
SCOPE: bounded command-intent / read-boundary corrective — **no MCP surface, AuthZ, business API, capability, deployment, or provider change.**
STATUS: `BENCHMARK_CORRECTION_REQUIRED` (one frozen case, `DQ-NEG-U-008`, is a mixed request whose zero-candidate expectation conflicts with the clarified command-intent architecture — see §6)

This document summarizes `davi-mcp-discovery-quality-corrective-002.json` (same directory), produced by
`api-delpi/scripts/evaluate_davi_discovery_quality_corrective_002.py` against the frozen benchmark
(`davi_discovery_quality_v1`) plus the new adversarial command-context fixture
(`davi_discovery_command_context_v1`), evaluated on the live `app.openapi()` action index — the same seed source as
production discovery.

## 1. SOURCE STATE (recomputed at `293dcfc03f`)

| Field | Value |
|---|---|
| runtime_source_sha | `293dcfc03f263e2ef29a76c4465e2b96ed24c36e` |
| allowlist_version | 20 → **21** (guard semantics + quarantine metadata only) |
| governed_operation_count | 89 (unchanged) |
| agent_intelligence_version | 2026.10.07.2 (unchanged) |
| mcp_tool_count | 2 (`discover_delpi_information`, `execute_delpi_information`) |

Drift check before commit: `origin/main` moved `55cdc297` → `293dcfc0` during execution; delta touched only
delia-api / tv-dashboard / docs — **zero api-delpi/DAVI paths → NON_CAUSAL**. Source rebased; benchmark and
command-context fixture re-run after the rebase with identical results.

## 2. SEMANTIC DEFECT CORRECTED

Architecture rejected the Corrective-001 blanket classification of
`gerar/gere/calcular/calcule/montar/monte/traduzir/traduza/emitir/emita` as unconditional zero-candidate triggers via
`nonReadCommandVerbTokens` loaded into the mutation guard.

**Before:** verb token present → `has_explicit_write_intent` → zero candidates, regardless of semantic topic.
`calcule o OTD` was rejected even though it asks for a governed READ of an authoritative KPI.

**After:** `nonReadCommandVerbTokens` removed from the guard entirely and re-scoped as top-level
`retrievalNeutralVerbTokens` — request-form words excluded from query semantic mass and overlap scoring (like function
words), so they neither reject nor inflate capability evidence. Capability classification now comes from semantic
evidence + eligibility + quarantine + admission floors.

| Guard layer | Behaviour |
|---|---|
| True mutation verbs (`insira`, `altere`, `delete`, …) | unchanged — zero candidates |
| Generic SQL / prohibited transport | unchanged — zero candidates via quarantine |
| Orchestration/content verbs (`gere`, `calcule`, `monte`, `traduza`, `emita`) | retrieval-neutral — never zero by verb form |

## 3. GUARD PROBES (evidence `guard_semantics`)

- mutation_blocked: `insira um novo fornecedor`, `altere o produto 10080055`, `delete the product 10080055`,
  `incluir um registro` → **all True (blocked)**.
- command_verbs_not_blocked: `calcule o OTD de compras`, `gere um resumo do estoque do produto 10080034`,
  `monte um resumo dos pedidos em aberto`, `traduza a descrição do produto para inglês`, `emita a nota fiscal 12345`
  → **all False (no hard block)**.
- generic_sql_zero_candidates: `execute uma query SQL no banco`, `select * from products`, `rode uma consulta SQL`
  → **all zero candidates** (retrieval-level quarantine, unchanged).

## 4. COMMAND-CONTEXT ADVERSARIAL FIXTURE

New fixture `tests/fixtures/davi_discovery_command_context_v1.json` (sha256
`f57d2d7b…a0867`), 9 cases — separate from the frozen 217-case benchmark.

Positive — `COMMAND_CONTEXT_READ_TOP3 = 100%` (6/6, all rank 1):

| Query | Expected | Rank |
|---|---|---|
| `calcule o OTD de compras` | `get_supplies_purchase_order_otd` | 1 |
| `calcule o OEE da produção` | `get_overall_equipment_effectiveness_pct` | 1 |
| `gere o resumo dos ajustes de inventário` | `get_supplies_inventory_adjustments_summary` | 1 |
| `gere um resumo do estoque do produto 10080034` | `get_product_stock` | 1 |
| `calcule a taxa de conversão comercial` | `get_sales_conversion_rate` | 1 |
| `monte um resumo dos pedidos em aberto` | `get_product_sales_open_orders` | 1 |

Unsupported — `UNSUPPORTED_COMMAND_ZERO_CANDIDATE = 100%` (3/3):

| Query | Reason |
|---|---|
| `calcule o ICMS da nota de saída` | ICMS tax computation has no governed capability (quarantine `icms`) |
| `gere o DANFE da nota fiscal 12345` | DANFE emission is an ACT outside the READ inventory (quarantine `danfe`) |
| `monte a escala de férias do time de produção` | vacation scheduling unsupported HR domain (quarantine `férias`) |

Note: `icms`, `danfe`, `imposto`, `impostos` were added to `retrievalQuarantineTokens` — genuine out-of-catalog
fiscal/emission domains with zero owning aliases; not sentence blocklists (an action could still own the token via
governed alias if a capability ever legitimately covers it).

## 5. FROZEN BENCHMARK — BEFORE / AFTER

| Metric | Corrective-001 | Corrective-002 | Floor (§24) | Result |
|---|---|---|---|---|
| top1_accuracy | 0.9676 | 0.9676 | ≥0.90 | PASS |
| top1_required_accuracy | 0.9889 | 0.9889 | ≥0.90 | PASS |
| top3_recall | 1.0000 | 1.0000 | ≥0.98 | PASS |
| top5_recall | 1.0000 | 1.0000 | ≥0.99 | PASS |
| MRR | 0.9829 | 0.9829 | ≥0.93 | PASS |
| positive_no_candidate_rate | 0.0000 | 0.0000 | ≤0.01 | PASS |
| hard_negative_zero_candidate | 1.0000 | 1.0000 | =1.00 | PASS |
| unsupported_zero_candidate | 1.0000 | 0.875 | — | see §6 |
| ambiguous_top3 / top5 | 0.90 / 0.90 | 0.90 / 0.90 | ≥0.90 | PASS |
| unrelated_family_top1 | 1 | 1 | ≤5 | PASS |
| family top5 floor | 1.00 all | 1.00 all | ≥0.95 | PASS |
| DQ-STOCK-001 | rank 1 | **rank 1** | =1 | PASS |
| hard_negative_leaks | 0 | 0 | =0 | PASS |

Only delta vs Corrective-001: `DQ-NEG-U-008` now returns `search_products` (unsupported rate 1.0 → 0.875).
All other metrics identical — the command-context semantics fix did not disturb accepted ranking.

## 6. TRANSLATION CASE — BENCHMARK_CORRECTION_REQUIRED

| Field | Value |
|---|---|
| case | `DQ-NEG-U-008` — `traduza a descrição do produto para inglês` |
| frozen classification | `UNSUPPORTED_NEGATIVE` (expects zero candidates) |
| observed | `search_products` (score 0.91, rank 1) |
| verdict | **MIXED_REQUEST** — the retrieval leg (authoritative product description) is governed: `search_products.approvedResponseFields = [product_code, description, group_category]`. Translation itself is Agent-side orchestration after retrieval — conceptually distinct from mutating DELPI state. |
| proposed expectation | `POSITIVE`/`AMBIGUOUS` with `search_products` as expected action |
| metric impact | unsupported_zero_candidate_rate 1.0 → 0.875 until fixture corrected |

Per §12/§25 the frozen fixture was **not** modified. Architecture authorization is required to reclassify this case.

## 7. PROVENANCE

| Field | Value |
|---|---|
| frozen_fixture_sha256_before | `945de11f4ab89b28f3c076134e300005310255e28aad3b6a9763947bf0248688` |
| frozen_fixture_sha256_after | `945de11f4ab89b28f3c076134e300005310255e28aad3b6a9763947bf0248688` — **unchanged** |
| command_context_fixture_sha256 | `f57d2d7b9b9f82efdaa872ec98db611a01488c683ba3f9e94299dfefacfa0867` |
| corrective_runner_sha256 | `aab1d90a95989281b44d71baadbd2b61abba11e9aa17ff944842b3cefa8430b9` |

## 8. INVARIANTS — VERIFIED

- MCP surface: exactly 2 tools — unchanged.
- No AuthZ, OAuth, business endpoint, use case, operation membership, or capability change.
- Responsibility split preserved: guard owns only clear non-READ exclusions; retrieval owns semantic matching;
  backend owns AuthZ; Agent owns composition.
- No candidate tokens or secrets in evidence.
- Frozen fixture byte-identical before/after.

## 9. TESTS

- Command-context focused: `test_davi_discovery_command_context.py` + `test_davi_read_only_intent_guard.py` —
  **63 passed** (container, baseline-seeded catalog).
- Frozen benchmark + focused DAVI suites: all pass.
- Full `pytest -k davi` (container): **1201 passed, 5 failed** — 4 known git-dependent freeze tests (env-limited,
  `git` absent in container; **21 passed** on host) + 1 transient postgres DNS failure during container restart
  (passed on isolated rerun).

## 10. LIVE STATUS

- LIVE_DEPLOY: NOT RUN — no deploy.
- LIVE_ACCEPTANCE: TEST_NOT_RUN — only Architecture may authorize live acceptance.
- This evidence proves SOURCE + LOCAL DETERMINISTIC BENCHMARK only.
