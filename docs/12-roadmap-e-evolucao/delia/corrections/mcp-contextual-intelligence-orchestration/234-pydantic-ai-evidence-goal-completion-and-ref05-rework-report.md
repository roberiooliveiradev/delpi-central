# 234 — DÉLIA · Evidence / Goal Completion / REF05 rework

**TASK_ID:** `DELIA-C3-PYDANTIC-AI-EVIDENCE-GOAL-COMPLETION-AND-REF05-REWORK-01`  
**DATE:** 2026-11-04  
**STATUS:** EXECUTED — local validation; PRODUCTION_DEPLOY NOT_AUTHORIZED  
**BASE_HEAD (reanchor):** `9d0abef0db3a314236d2654b948959af21863a16`  
**PRIOR:** docs 231–233; consolidation commit `d8fdc646fd` (review risks)

## Authorities

Reanchored to live `main` HEAD, Project Instructions / `.cursor`, docs 16→50→17→49→51→52→21→20→25, product/tech specs, thematic 220/226/228–233, execution ledger.

## EXISTING_EQUIVALENT / REUSE_DECISION

| Concern | Equivalent | Decision |
|---|---|---|
| Typed goal | `_TurnGoal` / doc 226 vocabulary | REUSE via `SemanticInvestigationPlan` |
| Structure identity | `_comparison_records` + `_flatten_evidence_records` | REUSE for REF05 root oracle |
| Multi-source compose | `_compose_multi_evidence` / `VerifiedCompositeEvidence` | REUSE |
| Obligation states | finalize labels REQUIRED/SATISFIED/… | EXTEND (no parallel Evidence model) |
| Semantic intent | Pydantic AI Agent | EXTEND (`declare_investigation_goal` tool) |
| AuthZ / schema / writes | `_governed_semantic_tool_invoke` live `_groups` | REUSE |

`EXISTING_EQUIVALENT=YES` for gates/evidence/compose.  
`REUSE_DECISION=EXTEND` finalize + Agent plan tool.  
`EXECUTION_DRIFT=NONE` vs doc 226/231 (PA remains sole semantic runtime).

## Root causes

| ID | Defect (doc 233 / d8fdc646 review) | Fix |
|---|---|---|
| R1 | REF05 matched identifiers in rendered text/Markdown | `_authoritative_structure_root` + `_bind_attempt_to_target` on owner record roots only |
| R2 | `_COMPARE_INTENT` / `_TARGET_TOKEN` regex intent | Removed; Agent declares typed plan; Application validates |
| R3 | Finalize checked “two sources” only | `_evaluate_material_obligations` over `evidence_needed` |
| R4 | Preserve PA / no legacy sequencer | Unchanged: no LangGraph, no `_governed_owner_path` on PA path |
| R5 | Weak AuthZ assertions | Behavioral rejects (schema, write surface, revoke, injection) |

## Implementation surface

- `orchestration.py` — `SemanticInvestigationPlan`, REF05 root oracle, obligation coverage, plan-aware finalize, `_accept_semantic_investigation_plan`
- `pydantic_ai_investigation.py` — `declare_investigation_goal` tool; plan passed into finalize
- `governed_stage_gates.py` — protocol extended
- `tests/test_pydantic_ai_semantic_rework.py` — REF05×10, typed formulations, obligations, AuthZ adversarial

Removed mechanisms with substitution: `_COMPARE_INTENT`, `_TARGET_TOKEN`, text-search target cover helpers.

## Acceptance

| AC | Result |
|---|---|
| AC-01…06 REF05 / obligations / discovery | PASS (unit/adversarial) |
| AC-07 PA sole semantic runtime | PASS |
| AC-08 AuthZ/Policy preserved | PASS |
| AC-09 RED→GREEN adversarial | PASS |
| AC-10 generalization (non-hardcoded codes) | PASS |
| AC-11 backend regression | PASS (`delia-api` pytest GREEN) |
| AC-12 local E2E | `TEST_NOT_RUN` / `EXTERNAL_BLOCKER` (Docker/Ollama/API absent) |
| AC-13 residual search | no new verifier/planner/engine |
| AC-14 docs/ledger | this doc + ledger entry |
| AC-15 commit/push `main` | see ledger SHA after push |

## Local E2E

```text
LOCAL_E2E=TEST_NOT_RUN
BLOCKER=docker.sock / Ollama / delia health unreachable on executor host
PRODUCTION_DEPLOY=NOT_AUTHORIZED
```

## Verdict

`ACCEPT_WITH_RESIDUAL` — REF05/goal/obligation contracts corrected under PA runtime; functional live owner comparison still requires authorized local stack (not claimed here).
