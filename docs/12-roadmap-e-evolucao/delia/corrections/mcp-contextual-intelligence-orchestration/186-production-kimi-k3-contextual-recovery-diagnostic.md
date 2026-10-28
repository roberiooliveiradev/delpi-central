# 186 — DÉLIA · Production Kimi K3 Contextual Recovery Diagnostic

**Date:** 2026-10-28. **Task:** `DELIA-C3-PRODUCTION-KIMI-K3-CONTEXTUAL-RECOVERY-DIAGNOSTIC-01`. **Baseline:** doc 185 (local `delia-json`). **Status:** EXECUTED; 5 production turns; CHAIN_HEALTHY; OUTCOME_PARTIAL.

## 1. Reanchorage & runtime

- REPOSITORY_HEAD=`1a2c7f307c` (main). PRODUCTION checkout `srv-api:~/projetos/delpi-central` at `48afe2ba86`.
- PRODUCTION_IMAGE_DIGEST=`sha256:9947eac96f471f55b9ea4de5c67675b962261ded9d07c047e8f4e02de3fad1c8` (DAVI-only build; `DIRECT_DELPI_*=0` verified in doc 184).
- PRODUCTION_MODEL=`moonshotai/kimi-k3` (`openai_compatible`); `DELIA_ENV=production`; realm `delpi`, client `delpi-central`.
- Identity: user `user` (owner-provided, provisioned in the prod realm during this session after an initial `invalid_grant`). Password grant only; no reset, no RBAC/Keycloak changes, no writes, no tokens logged.

## 2. Results — production kimi-k3

| Test | Grounding | Ops chain (DAVI real) | Limitations | Answer | Outcome |
|---|---|---|---|---|---|
| T1 terminal bala | GROUNDED | discover → teo.get_catalog → discover → **execute** | — | "coleção vazia — não há registros" | Honest insufficiency; candidate executed was `read_governed_technical_knowledge` (knowledge guide `product_master_sb1`, 200 empty) — **not** `search_products` |
| T2 terminal ilhós | GROUNDED | discover → **execute** | — | empty collection (same knowledge action) | same residual |
| T3 terminais tipo bala | GROUNDED | discover → execute → discover → **execute** (`search_products` ×2) | `insufficient_evidence` | "registros reais, mas não correspondem — não vou apresentá-los" | Real records returned, relevance judgment correctly **rejected** non-pertinent rows; bounded recovery retried once |
| T4.1 pesquise terminais bala | GROUNDED | discover → execute → discover → **execute** (`search_products` ×2) | `insufficient_evidence` | same honest rejection | same |
| T4.2 selecione dois exemplos | GROUNDED | discover → execute → get_catalog ×2 → discover → **execute** (`search_products`) | `insufficient_evidence` | same honest rejection | **Contextual continuation worked** — new owner calls grounded in prior context, no surface-listing |

Metrics (observability projection): model_calls 7–19/turn; input_tokens 10.5k–32.3k; output 2.7k–13.1k; latency 45s–193s/turn. Token `status=partial` on multi-cycle turns (provider-reported).

## 3. Stage evidence vs doc-185 failures

| Doc-185 local failure | Production kimi-k3 |
|---|---|
| RC1 `target_selection` binds `mcp:vista.search_data_routes` | **NOT reproduced** — every owner_surface run selected `group=mcp:davi capability=discover_delpi_information` |
| RC2 `foreign_selection=invalid` | **NOT reproduced** — all selections valid |
| RC3 admission `surface_inquiry` | **NOT reproduced** — admission `owner_surface` on all product queries |
| RC4 candidate_arguments unmergeable → `no_result` | **NOT reproduced** — `candidate_arguments ok` → `execute_delpi_information ok` in every DAVI reach |
| RC5 wrong specialist (`teo.get_product_guide`) | **NOT reproduced** — enrichment picked `teo.get_catalog` (catalog, legitimate) |
| Contextual recovery absent | **Recovery PRESENT** — second discover+execute cycle on irrelevance; bounded, deduplicated, honest stop |

## 4. Residual failure — proven stage

`FAILURE_STAGE_PROVEN` = **retrieval adequacy**: `search_products` executed but returned records judged non-pertinent (T3/T4) or the candidate bound was the knowledge action `read_governed_technical_knowledge` (T1/T2). Two unresolved hypotheses:

- **H-A (argument semantics, stage C):** generated `description` argument (e.g., full phrase "terminais elétricos do tipo bala" or "terminal") returns real but non-`bala` products — owner substring semantics don't bridge "terminal bala" → stored "TERM. BALA".
- **H-B (owner coverage/scope, stage D):** the known exemplars (`10080092`, `10081004` — "TERM. BALA …") may be outside the queried scope/branch, or DAVI's `search_products` parity (code/description/group_code/page/page_size only) cannot express the needed lookup.

Arguments are not logged by design (bounded projection) and no instrumentation change is authorized — the C-vs-D split needs one bounded owner probe with an authorized identity or temporary argument logging approved as a separate step. No domain defect inferred from this observation alone.

## 5. A/B comparison (model is the isolated variable — same code SHA lineage, same DAVI surface)

delia-json failed every scenario at admission/selection/argument stages; kimi-k3 completed the full governed chain in all 5 turns. Environmental deltas (prod catalog, prod TOTVS data, DELIA_ENV) exist but the *failed stages* are model-output stages — strong evidence the doc-185 failures were **model-capacity bound**, not orchestration defects. Generalization claim is bounded to these 4 scenarios.

## 6. Verdict

`PRODUCTION_CHAIN_HEALTHY / BUSINESS_OUTCOME=PARTIAL` — semantic selection, discovery, execution, relevance judgment and bounded contextual recovery all work in production. User goal still unmet: the two expected exemplars were not returned; residual is retrieval adequacy (H-A vs H-B). **Next bounded step:** owner-side probe — `search_products(description='bala'|'TERM. BALA')` via authorized DAVI execute — to split argument-generation vs owner-search coverage; then the smallest contract fix on the losing side.

CODE_CHANGED=NO; PROMPTS_CHANGED=NO; DAVI_CHANGED=NO; MODEL_CHANGED=NO; DEPLOY_EXECUTED=NO; phase C3 not advanced.
