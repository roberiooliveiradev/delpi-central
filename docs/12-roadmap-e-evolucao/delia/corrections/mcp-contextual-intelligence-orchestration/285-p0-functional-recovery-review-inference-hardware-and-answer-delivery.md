# 285 — DÉLIA · Review P0: recuperação funcional não concluída

**DATA:** 2026-11-05  
**TASK_ID:** `DELIA-C3-END-TO-END-FUNCTIONAL-RECOVERY-REAL-QUESTIONS-01`  
**BASE REPORTED:** `4f56c1ce1a07bf912752866d96e76432b1bd8037`  
**REVIEWED SHA:** `27bb3d7c0211caf75e81a498204357a27bea81ca`  
**VERDICT:** `REWORK` for P0 functional objective; `ACCEPT_WITH_RESIDUAL` for reported MCP selection/READ technical evidence. **P0-1 FAIL, P0-2 PARTIAL, P0-3 FAIL; production BLOCKED.**

## Source/evidence

- Exact last commit `27bb3d7...` only changes doc256, adding P0 narrative; no demonstrated final-answer fix in that commit. GitHub comparison across base/final also shows an intervening orchestration file change; attribute changes to exact commits only, not automatically to final documentation commit.
- Executor reports three+ authenticated local runs, catalog 10, selection of `davi.discover_delpi_information`, `davi.execute_delpi_information(action=search_products)`, owner result `uncovered=50220013`. This is strong owner-tool path evidence **as reported**, but final response did not reach client. Without independent owner payload, SourceRefs, and HTTP response, grounded business outcome is not proven.
- CPU-only Ollama, ~6 tokens/s small native probe, RTX3050 6GB Docker `--gpus all` fails `no known GPU vendor found`; host NVIDIA Toolkit/CDI support is TO_INVENTORY / host-action approval needed. GPU enabling may improve throughput but does not by itself prove valid output schema under full context.
- Native `UnexpectedModelBehavior/Exceeded maximum output retries` and client 504 are distinct failure surfaces; do not prematurely conclude all defects are hardware. Full-run model-generated token metrics and native failure subtype not demonstrated. Provider/model configuration `enable_thinking=false` is executor-reported; re-check committed/runtime-effective wiring and actual observed thinking behavior, not mere parameter presence.
- Container's `DELIA_RUNTIME_SHA` stale is acknowledged EXECUTION_DRIFT; local mounted SHA and provider config must be independently checked. `PRODUCTION_DEPLOY=BLOCKED`.
- Technical tests PASS executor-reported; not independently run in this review. A green suite does not overcome P0 FAIL. RQ24/RQ28 PARTIAL.

## Bounded single-delivery recovery directive

**TASK_ID:** `DELIA-C3-P0-INFERENCE-ALTERNATIVE-AND-CLIENT-ANSWER-RECOVERY-01`.

1. Reanchor HEAD/status → Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → architecture/product/spec/ledger/docs 256,280–285 and frozen phase/release constraints. Inventory actual machine/host, existing Ollama Compose GPU support, Pydantic AI adapter/provider configs; prove `EXISTING_EQUIVALENT`/`REUSE_DECISION`.
2. **Infrastructure first (with explicit host-change authorization):** verify NVIDIA driver/toolkit/CDI requirements and existing supported deployment. Do not install system packages or alter privileged host/Docker daemon without applicable operator authorization; request exact bounded host action if lacking. If authorized, enable GPU through existing Compose boundary, test `nvidia-smi`/GPU visibility, VRAM/KV fit, partial offload, actual full DÉLIA run, memory pressure and rollback. Do not assume RTX3050 6GB can fit whole 16K context.
3. **Alternative provider/model test:** retain same Pydantic AI `Agent(output_type=InvestigationAnswer)`, same tools/gates and known-present owner question. Compare current CPU model baseline with one feasible alternative already configured/authorized (existing provider adapter/production-safe remote model or smaller locally supported model), without new provider branches, secret exposure, disabling validation or unapproved egress. Track native output validity, final client response, SourceRefs, provider actual per-turn usage (if available), 504, latency/cost. Stop if sensitive business data would leave an unauthorized boundary.
4. Confirm known-present product directly in DAVI/Domain owner; run exact query `Qual produto está cadastrado com o código 50220013?`; acceptance requires response **actually received by client**, valid InvestigationAnswer, authorized source/SourceRefs and correct content, within effective time budget. Include negative/no-data and clarification controls. MCP tool execution alone is not P0 pass.
5. If alternative produces valid output, choose smallest lawful configuration/infrastructure change, persist at legitimate owner, tests/regression, log/secret security and rollback. If all alternatives fail, prove exact native failure stage and deliver `BLOCKED` with bounded operator decision, not another open-ended plan. Do not add retries/timeouts or refactor orchestration speculatively.
6. Physical legacy removal with any replacement, consumers and tests updated, residual search, doc/ledger factual, commit/push. No production deployment until explicit release approval, user-facing READ PASS and correct production model/provider/rollback.
7. Report per-config `P0_ANSWER_DELIVERED`, `STRUCTURED_OUTPUT_VALID`, `OWNER_MATCH`, `SOURCE_REFS`, `LATENCY`, `TOKENS`, `GPU_VISIBILITY`, `CONFIG_FINGERPRINT`, `SHA`, `PRODUCTION_GATE`.

**Business acceptance remains FAIL until real user-facing answer is delivered.**
