# 31 — Stage 03 · Discovery / Guidance Implementation Report

**TASK:** `DELIA-C3-CONVERSATIONAL-INTELLIGENCE-STAGE-03-IMPLEMENTATION-01`  
**MODE:** bounded EXTEND after authorization (§6.204 / doc [30](./30-stage-03-bounded-implementation-authorization.md))  
**AUTHORITY:** Product Master bounded authorize + Architecture / Coordination; Stage02 aceite preservado  
**BASE_HEAD (auth):** `3377302b71`  
**STATUS:** `IMPLEMENTATION_EVIDENCE_RECORDED` · `STAGE_03_ACCEPTED=NO` (independent review pending)

---

## 1. Task / HEAD

| Item | Value |
|---|---|
| AUTHORIZATION_DOC | [30](./30-stage-03-bounded-implementation-authorization.md) |
| AUTHORIZATION_LEDGER | §6.204 |
| INVENTORY | [29](./29-stage-03-discovery-guidance-inventory-and-implementation-brief.md) |
| IMPLEMENTATION_LEDGER | §6.205 (this evidence) |

## 2. Authorities reanchored

16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → 02/24 → 60/69/70 → personality/02 → ledger; plus docs 02/03/18/27/28/29/30 of this track. No historical doc substituted for HEAD/ledger.

## 3. Authorization

```text
STAGE_03_AUTHORIZATION_DECISION=APPROVED_BOUNDED
STAGE_03_AUTHORIZED=YES
MATERIAL_ACT_AUTHORIZED=NO
STAGE_02_ACCEPTED=YES_WITH_RESIDUAL
```

Authorization commit preceded functional diff.

## 4. Requirements (reconciled candidates)

| RQ | Objective | Status |
|---|---|---|
| RQ-S03-01 | Guidance grounded when owner vocabulary available | IMPLEMENTED (fake/scripted) |
| RQ-S03-02 | Honest limitation when guidance/discovery peer absent | IMPLEMENTED |
| RQ-S03-03 | Provider-neutral discovery (no owner-name branch) | IMPLEMENTED |
| RQ-S03-04 | Writing-verb guidance ≠ PREPARE/ACT | IMPLEMENTED |
| RQ-S03-05 | AuthZ fail-closed | IMPLEMENTED (D3-12 + platform) |
| RQ-S03-06 | Tool rename / owner add-remove invariance | IMPLEMENTED (D3-05/06/07/09) |

```text
RQ_TOTAL=6
RQ_IMPLEMENTED=6 (pipeline/fake evidence)
RQ_PARTIAL=0
RQ_NOT_IMPLEMENTED=0
RQ_BLOCKED=0
REAL_MODEL_EVAL=TEST_NOT_RUN
```

## 5. Inventory / Reuse

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
OWNER=delia-api application/capability_provision/orchestration.py
CONTRACT=live tools/list + SpecialistOperationClass; same-group unique DISCOVERY peer
NEW_PLANNER=NO NEW_REGISTRY=NO NEW_ENGINE=NO CHAT_REUSE=NO
```

| Responsibility | Decision |
|---|---|
| HandleInteractiveTurn / Stage02 commands | REUSE |
| Semantic select / goal / native path | REUSE |
| Authenticated tools/list + projection | REUSE |
| Envelope `_is_open_vocabulary` discovery | REUSE |
| `_requires_owner_vocabulary` for required free strings on READ/ANALYSIS | **EXTEND** |
| PendingWrite / MESSAGE≠ACT | REUSE (untouched) |

## 6. Contracts preserved

- Discovery ≠ approval; MCP result ≠ FACT; guidance ≠ execution; MESSAGE ≠ ACT; PREPARE ≠ ACT.
- No new wire fields.
- Closed `enum`/`const` skip discovery; optional free strings alone do **not** trigger (avoids indiscriminate catalog calls).
- Budget/timeout/step ceilings reused (`TurnDeadline`, `MAX_OPERATIONAL_PLAN_STEPS`).

## 7. Baseline / RED → GREEN

Gap proven: READ guide with required unconstrained `topic` did not trigger owner vocabulary; model invented topic → `SOURCE_UNAVAILABLE` when DISCOVERY peer existed unused.

EXTEND: `_is_unconstrained_string` + required-property gate inside `_requires_owner_vocabulary` for READ/ANALYSIS only.

Regression fix during GREEN: initial “any free string” trigger called `get_catalog` before every TÉO `analyze` (optional `view`). Tightened to **required** free strings only — aligns with doc29 “zero discovery universal de strings”.

## 8. Functional diff

- `delia-api/app/application/capability_provision/orchestration.py` — structural EXTEND only.
- No frontend, PendingWrite, AuthZ, or provider-name branches.

## 9. Tests (D3)

Suite: `delia-api/tests/test_stage03_discovery_guidance.py` (+ baseline CI-01 vocabulary expectation update).

| Case | Result |
|---|---|
| D3-01 guidance available | PASS |
| D3-02 guidance absent / no peer | PASS |
| D3-03 free required string | PASS |
| D3-03b optional string no trigger | PASS |
| D3-04 closed enum | PASS |
| D3-05 tool rename | PASS |
| D3-06 / D3-09 owner add / fourth fake | PASS |
| D3-07 owner removed discovery | PASS |
| D3-08 reclassified PREPARE | PASS |
| D3-10 writing verb | PASS |
| D3-11 prompt injection | PASS |
| D3-12 AuthZ denied | PASS |
| D3-13 budget exhausted | PASS |
| D3-14 multi-turn continuity | PASS |
| D3-15 Stage02 regression | PASS (concurrent + specialist + provider-neutral + turn budget suites) |

## 10. Regression evidence

Recorded at implementation time (local `.venv`):

```text
SHA_AT_RUN=working-tree after EXTEND (pre-commit); AUTH_BASE=3377302b71
CONFIG=delia-api .venv / pytest.ini
COMMAND_TARGETED=pytest tests/test_stage03_discovery_guidance.py tests/test_conversational_intelligence_baseline.py tests/test_specialist_capability_orchestration.py tests/test_provider_neutral_orchestration.py tests/test_stage02_b2_concurrent_decisions.py tests/test_execution_ceiling_turn_budget.py -q
TARGETED_RESULT=PASS
COMMAND_FULL=pytest -q
FULL_SUITE_RESULT=PASS (1229 tests observed green; includes new D3 suite)
FRONTEND=TEST_NOT_RUN (no MFE impact in this slice)
TYPECHECK=TEST_NOT_RUN (no TS impact)
REAL_MODEL_EVAL=TEST_NOT_RUN
MATERIAL_ACT_COUNT=0
```

## 11. Security

| Check | Result |
|---|---|
| MESSAGE never grants ACT | PASS (D3-10/14 + Stage02) |
| Provider metadata ≠ AuthZ | PASS (unchanged path) |
| MCP discovery ≠ approval | PASS |
| Tool result ≠ Policy | PASS (D3-11) |
| Backend-first AuthZ | PASS (D3-12) |
| Domain final authority | PASS |
| Guidance ≠ material ops | PASS |
| Budget fail-closed | PASS (D3-13) |
| Secrets in prompts/logs | NOT_PROBED_HERE (platform residual) |

## 12. Provider neutrality

Fake owners `acme-wiki` / OpenAPI sibling / renamed remotes — no DAVI/TÉO/VISTA branches in the EXTEND.

## 13. Generalization

Fake/scripted only. Holdouts / live model:

```text
GENERALIZATION_EVAL=PARTIAL_FAKE_ONLY
REAL_MODEL_EVAL=TEST_NOT_RUN
```

## 14. Outcome

```text
STAGE_03_IMPLEMENTATION_STATUS=EVIDENCE_RECORDED
STAGE_03_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
PRODUCTION_READINESS=NOT_PROVEN
IMPLEMENTATION_VERDICT=READY_FOR_INDEPENDENT_STAGE_03_ARCHITECTURE_REVIEW
NEXT=INDEPENDENT_STAGE_03_ARCHITECTURE_REVIEW
```

## 15. Residuals

- R-S03-01: real-model / live guidance eval not run.
- R-S03-02: plugin-ui tsc residuals remain other-owner (untouched).
- R-S02-* Stage02 residuals preserved unchanged.
- Optional free-string READ still does not auto-discover (by design; required-field gate).

## 16. Recommendation

Independent Architecture review of this report + D3 suite + reuse gate before any `STAGE_03_ACCEPTED` or phase advance.
