# 236 — DÉLIA · Pydantic AI Native-First — Execution Report

**TASK_ID:** `DELIA-C3-PYDANTIC-AI-NATIVE-FIRST-GENERALIST-INVESTIGATION-CONSOLIDATION-01`  
**DATE:** 2026-11-04  
**STATUS:** EXECUTED — local isolated validation; PRODUCTION_DEPLOY NOT_AUTHORIZED  
**PLAN:** Document 235  
**PREDECESSORS:** 231–234  

## Authorities / reanchor

Reanchored on live `main`, Project Instructions / `.cursor`, docs 16→50→17→49→51→52→21→20→25, thematic 220/226/228–235, execution ledger. Concurrent WIP preserved (tv-dashboard / CF / engineering).

## EXISTING_EQUIVALENT / REUSE_DECISION

| Concern | Equivalent | Decision |
|---|---|---|
| Agent tool loop | `PydanticAiInvestigationOrchestrator` + `Agent`/`FunctionToolset` 2.50.0 | EXTEND |
| Governed invoke/catalog | Application gates | REUSE |
| Clarification status | `CLARIFICATION_REQUIRED` + `_clarification_content` | REUSE |
| Multi-source compose | `_compose_multi_evidence` / `VerifiedCompositeEvidence` | EXTEND as optional agent tool |
| Typed goal | `SemanticInvestigationPlan` / `_TurnGoal` | EXTEND (optional declare) |
| Material obligations | finalize obligation states | EXTEND (heterogeneous bind) |
| LangGraph / second planner | — | REMOVE stays (already gone) |
| `DELIA_ORCHESTRATION_ENGINE=delia` rollback | still in settings | KEEP residual (no acceptance to delete yet) |

`EXECUTION_DRIFT=NONE` vs doc 235 native-first decision.

## Feature API matrix (pinned `pydantic-ai[openai]==2.50.0`)

| Feature | Present | Use |
|---|---|---|
| Agent + tool loop | YES | sole investigation runtime |
| FunctionToolset | YES | dynamic tools |
| Typed tool args | YES | `arguments: dict`, list identities |
| RunContext / deps | YES | `InvestigationDeps` |
| UsageLimits | YES | request + tool_calls |
| Retries | YES | Agent retries=1 |
| CallDeferred / ApprovalRequired | YES in SDK | NOT wired (HITL writes stay confirmation chain) |
| Durable execution | not required | NOT added |

## Native agent changes

- Instructions: generalist multi-step; **declare_investigation_goal OPTIONAL**
- Typed `invoke_read_capability(arguments: dict)`
- `request_user_clarification` → finalize `CLARIFICATION_REQUIRED`
- `compose_verified_observations` → optional deterministic compose (not intent router)
- Prior-turn context block for continuity (untrusted)
- Observation handles (`obs:N`) in tool projections

## Finalize / evidence

- Clarification and agent-composed attempts short-circuit finalize
- Simple READ without plan still succeeds (AC-03)
- Two READs without compose/plan do **not** auto-compare
- `_attempt_satisfies_obligation` binds root **or** provenance source/capability (heterogeneous)
- REF05 authoritative root binding preserved for structure targets

## Deletion map (residual)

| Item | Consumers | Action |
|---|---|---|
| LangGraph | none | already removed |
| `_COMPARE_INTENT` / text REF05 | none | already removed (doc 234) |
| Mandatory declare tool | — | softened (optional) |
| Hardwired compare-only as sole multi-source path | finalize still supports plan.compare | EXTEND optional compose tool; KEEP plan path |
| `delia` rollback engine | settings/composer | KEEP residual until live acceptance |
| `_governed_owner_path` | `delia` rollback only | KEEP for rollback |

## Tests

- New: `tests/test_pydantic_ai_native_first_consolidation.py`
- Updated: semantic rework / governed_attempt tool arg shapes
- Full `delia-api` pytest `tests/` (ignore live): GREEN

## Local E2E (isolated docker-compose.dev)

Stack already was `docker-compose.dev.yml` + volume mount of `delia-api` (not `up-prod-sequential`).

Authenticated password-grant turns against `http://<delia-api>:8000/interaction/turns`:

| Case | HTTP | GROUNDING | Notes |
|---|---|---|---|
| unauth | 401 | — | PASS |
| E01 conceptual SIPOC | 200 | NON_GROUNDED | Honest conceptual answer; no false FACT |
| E02 structure 90260147 | 200 | NON_GROUNDED | `owner_path_unbound`; investigation ran (`tool_calls≥1`) but no owner bind |
| E03 compare | 200 | NON_GROUNDED | intermittent `investigation_agent_error` / unbound — no false grounded |
| E07 ambiguous | 200 | NON_GROUNDED | honest unbound (clarification path unit-tested) |

MCP health from delia-api: api-delpi / transformometro-api / tv-dashboard-api **online**. Live capability binding still incomplete in this session (catalog project observed; zero collected owner READs on E02/E03).

`FALSE_GROUNDED_COUNT=0` on executed live negatives.

`DELIA_RUNTIME_SHA` env label was stale (`d8fdc646…`) relative to working tree; code served via bind-mount. Label refresh tracked in ledger after commit SHA.

## Verdict

`ACCEPT_WITH_RESIDUAL` — native-first agent surface + evidence generalization shipped and unit/regression green; live multi-owner READ/compare functional acceptance still residual (owner bind / agent RuntimeError under Ollama). PRODUCTION_DEPLOY NOT_AUTHORIZED.
