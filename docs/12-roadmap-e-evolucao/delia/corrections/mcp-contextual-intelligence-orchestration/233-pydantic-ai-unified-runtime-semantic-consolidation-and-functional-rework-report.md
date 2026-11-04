# 233 — DÉLIA · Rework funcional do runtime Pydantic AI (R1–R4)

**TASK_ID:** `DELIA-C3-PYDANTIC-AI-UNIFIED-RUNTIME-SEMANTIC-CONSOLIDATION-AND-FUNCTIONAL-REWORK-01`  
**DATE:** 2026-11-04  
**STATUS:** EXECUTED — local validation; PRODUCTION_DEPLOY NOT_AUTHORIZED  
**BASELINE:** commit `d989ab3716` / doc 232  
**PLAN AUTHORITY:** docs 231–232 + user rework brief

## Decision revalidated

Pydantic AI remains the sole production investigation runtime. Application
`OperationalCapabilityOrchestrator` remains gates owner + explicit `delia`
rollback sequencer. LangGraph stays removed.

## Root causes addressed

| ID | Defect | Fix |
|---|---|---|
| R1 | Agent wrapped `_governed_owner_path` via `run_governed_investigation` + silent fallthrough | Tool removed; no-tool / agent-error finalize without legacy sequencer |
| R2 | First tool `SUCCESS` treated as turn completion | `_finalize_semantic_investigation` / goal-coverage + REF05 + compose reuse |
| R3 | `del actor_user_id…` opaque | Actor/session retained for audit; AuthZ via live `_groups`; writes still rejected |
| R4 | `_bounded_json` sliced mid-JSON | Structural shrink + valid JSON + explicit `truncated` |

## EXISTING_EQUIVALENT / REUSE_DECISION

- Catalog/invoke gates → REUSE/EXTEND  
- `_compose_multi_evidence` / `_comparison_records` / `VerifiedCompositeEvidence` → REUSE  
- Admission/confirmation/surface inquiry → REUSE  
- `_governed_owner_path` semantic sequencing → REMOVE from pydantic_ai path (retained only for `delia` rollback)

## Residuals

- Live E2E owner READs: `NOT_REACHED` / `EXTERNAL_BLOCKER` — Docker socket and Ollama intermittently absent on the executor host (probed; no durable stack).  
- RC-B/RC-C functional live outcomes still depend on real owners.  
- Application `_propose` stages remain inside `delia` rollback and inside compose helpers used by finalizer when comparing two verified sources.

## Tests

- New: `tests/test_pydantic_ai_semantic_rework.py` (R1–R4)  
- Full `delia-api` pytest GREEN (`timeout=60`)  
- Owner-path contract matrix stays on `delia`; pydantic_ai covered by dedicated suites
