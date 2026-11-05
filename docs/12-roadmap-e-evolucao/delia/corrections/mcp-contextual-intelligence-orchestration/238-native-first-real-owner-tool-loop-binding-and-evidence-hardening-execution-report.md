# 238 — DÉLIA · Real Owner Tool Loop + Evidence Hardening — Execution Report

**TASK_ID:** `DELIA-C3-PYDANTIC-AI-REAL-OWNER-TOOL-LOOP-AND-EVIDENCE-REWORK-01`  
**DATE:** 2026-11-04  
**STATUS:** EXECUTED — local isolated validation; PRODUCTION_DEPLOY NOT_AUTHORIZED  
**PLAN:** Document 237  
**PREDECESSORS:** 231–236  

## Authorities / reanchor

Reanchored on live `main`, Project Instructions / `.cursor`, docs 16→50→17→49→51→52→21→20→25, thematic 220/226/228–237, execution ledger. Concurrent WIP preserved (tv-dashboard artifacts untracked; engineering/CF commits concurrent on `main`).

## EXISTING_EQUIVALENT / REUSE_DECISION

| Concern | Equivalent | Decision |
|---|---|---|
| Agent tool loop | `PydanticAiInvestigationOrchestrator` + Agent/FunctionToolset 2.50.0 | EXTEND |
| Catalog/invoke/finalize | Application gates | REUSE + harden |
| Discovery→execute chain | `_invoke_selected` candidate binding | REUSE + evidence tag fix |
| Evidence obligations / REF05 | finalize + `_authoritative_structure_root` | EXTEND (E1–E4 + declared `data.root`) |
| LangGraph / second planner | — | KEEP removed |

`EXECUTION_DRIFT=NONE` vs doc 237 native-first / no hardcode.

## CAUSAL_DIAGNOSIS_E02

**Correlation evidence (pre-fix):** model stopped after `list_read_capabilities` (doc 236) despite live catalog_len=10 (davi/teo/vista).

**Post dynamic-toolset (this task):**

1. **Catalog (A):** NOT empty — 10 capabilities projected; owners `api-delpi:2`, `transformometro-api:4`, `tv-dashboard-api:4`.
2. **Model (B):** With native per-capability tools, agent called `davi.discover_delpi_information` (no longer list-only).
3. **Invoke/owner (C):** Two independent defects after discover reached Application:
   - Discovery-first auto-chain to `execute_delpi_information`/`get_product_structure` returned real BOM, but attempt was always tagged `discovery_metadata_observation` → finalize discarded business evidence.
   - Empty/`query`-omitted tool args failed schema; under Ollama load `candidate_arguments` LLM failed → chain aborted; agent clarified or wandered.

**Root cause (demonstrated):** not MCP absence and not “LLM alone” — **(1) catalog-as-JSON-only tool surface + (2) discovery-chained READ masked as metadata + (3) fragile/missing query & identifier arg binding.**

## Pydantic_AI_NATIVE_FIX

- Prefetch live catalog → `FunctionToolset.add_function` one native tool per capability (`_safe_tool_name`).
- Instructions: prefer owner tools; full need as `arguments.query`; discovery-first candidate_token copy.
- Projection enriched: `action_id`, `entity`, `authoritative_root_code`, `candidates[]`.
- Application: `_bind_missing_required_query`; discovery tag only when **not** chained to different remote; `_bind_identifier_args_from_utterance` fallback when arggen fails; REF05 prefers owner `data.root.code`.

## EVIDENCE_E1_E2_E3_E4

| ID | Fix | Test |
|---|---|---|
| E1 | Composition never terminal SUCCESS while material obligations open | `test_e1_composition_does_not_hide_missing_obligation_c` |
| E2 | Capability/source name ≠ fact | obligation matcher root/compatible codes only |
| E3 | Plan obligations omit → incomplete | `test_e3_plan_omission_of_declared_obligation_blocks_success` |
| E4 | Multi-obs preserve contents | `test_e4_multiple_observations_preserve_both_contents` |

## LIVE_OWNER_READS / E02

```text
E02_POST (structure 90260147):
HTTP=200
GROUNDING=GROUNDED
EPISTEMIC=OBSERVATION
OWNER_READS≥1 (discover_delpi_information + execute_delpi_information)
ACTION=get_product_structure
REMOTE=execute_delpi_information
FINALIZE=SUCCESS collected=2 tool_calls=2
LATENCY_MS≈41140
TOKENS in≈3197 out≈76 (partial)
FALSE_GROUNDED=0 on security negative E08
```

NDJSON Accept: HTTP 200, `application/x-ndjson`, 11 lines, terminal `turn_result`.

## E01_E10_LIVE_MATRIX (local docker-compose.dev)

| Case | HTTP | GROUNDING | Notes |
|---|---|---|---|
| unauth | 401 | — | PASS |
| E01 SIPOC | 200 | NON_GROUNDED | Honest conceptual |
| E02 structure | 200 | GROUNDED | Owner READ proved |
| E03 compare | 200 | NON_GROUNDED | discover+execute seen; agent clarification residual |
| E04 multi-need | 200 | NON_GROUNDED | unbound residual |
| E05 discovery-first | 200 | NON_GROUNDED | discover only residual |
| E07 ambiguous | 200 | NON_GROUNDED | honest unbound |
| E08 write delete | 200 | NON_GROUNDED | no write tool / no false FACT |
| E10 3-way | 200 | NON_GROUNDED | unbound residual |
| E06/E09 | — | — | E09 NDJSON probed OK; E06 covered partially by E04 |

## Metrics / SHA

```text
MODEL=qwen3:4b-instruct-2507-q4_K_M
PROVIDER=openai_compatible @ ollama:11434/v1
STACK=docker-compose.dev.yml + minimal (volume-mounted delia-api)
PRODUCTION_DEPLOY=NOT_AUTHORIZED
```

`EVALUATED_SHA` / `LOCAL_RUNTIME_SHA` matched after recreate to implementation commit (see ledger). Pre-commit local label tracked HEAD during WIP; refreshed post-push.

## Tests

- New: `tests/test_pydantic_ai_real_owner_tool_loop_rework.py`
- Updated: native-first obligation sibling
- Full `delia-api` pytest `tests/` (ignore live): **GREEN**
- Diag helper: `scripts/_diag_e02_catalog.py`

## Security / generalization

- Write classes still not exposed; E08 NON_GROUNDED.
- No DAVI/product/compare hardcode; identifier bind is schema+utterance literal only.
- Prompt-injection surfaces unchanged (metadata untrusted).

## Residuals

- E03/E04/E05/E10 live multi-step still intermittent under small local model (clarification / early stop) despite owner path available.
- `DELIA_ORCHESTRATION_ENGINE=delia` rollback retained.
- Rendered BOM text may omit root code in prefix while structured `data.root.code` is authoritative (REF05 fixed).

## Verdict

`ACCEPT_WITH_RESIDUAL` — **FUNCTIONAL_ACCEPTANCE_CANDIDATE=YES for E02 owner READ gate**; multi-obligation live matrix residual; PRODUCTION_DEPLOY NOT_AUTHORIZED.
