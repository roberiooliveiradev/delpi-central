# 305 — INT-1 TEO/DAVI Integrated Validation and Controlled Production Deployment

**TASK_ID:** `DELIA-C3-T2-INT1-TEO-DAVI-INTEGRATED-VALIDATION-AND-PRODUCTION-DEPLOY-01`  
**Data:** 2026-11-11  
**RELEASE_SHA / DEPLOYED_SHA / EVALUATED_SHA:** `e2b341d87785345ffcabf784bd6314c3ce0115d7`  
**DOC304_COMMIT (included):** `c4f3d6370c`  
**EVAL_ID:** `or-qwen14b-3863d58c5327`  
**PRODUCTION_DEPLOY:** EXECUTED (api-delpi → transformometro-api → delia-api)  
**ROLLBACK:** NOT_REQUIRED  

---

## 1. Release freeze

| Campo | Valor |
|---|---|
| ORIGIN_MAIN | `e2b341d877…` (sync YES) |
| PROCEDURE | `./infra/scripts/up-prod-sequential.sh --build <svc>` |
| ORDER | api-delpi → transformometro-api → delia-api |

### Images

| Serviço | BEFORE | AFTER |
|---|---|---|
| api-delpi | `sha256:7ea9dfd5…` | `sha256:c8316fe1…` |
| transformometro-api | `sha256:318a5ebc…` | `sha256:96c04e87…` |
| delia-api | `sha256:28af6035…` | `sha256:65c7a320…` |

Local artifacts (gitignored): `delia-api/.battery/int1-teo-davi-prod-deploy-01/`.

---

## 2. Predeploy validation

| Suite | Result |
|---|---|
| `test_teo_mcp_contract.py` | PASS (15) |
| TEO metadata/surface adjacent | PASS |
| `test_davi_pagination_completeness.py` + full-mode UC | PASS (45) |
| DELIA int1 projection/secure_decision_trace | PASS |

Enterprise probe `90260921` (DAVI UC in runtime after DAVI deploy):

```text
ROOT=90260921 PA MI
COMPONENTS=1 (10020003 MP qty 175 MT)
DEPTH=1
KEYS=bom_validity,items,root,total  (no null page keys)
classify=complete derive=(True,False) bounded.is_complete=True
```

TEO `tools/list` `read` description (runtime): Process WBS / processo_id / not materials BOM; no DAVI routing.

---

## 3. Isolated live eval (G1/P1 once)

Harness: `run_int1_openrouter_qwen14b_instrumented_eval.sh`  
Filter: `DELIA_EVAL_SCENARIO_IDS=G1…,P1…`  
Owners on docker network: **post-deploy** DAVI+TEO images above.  
Eval DÉLIA: process-isolated container mounting host `delia-api` @ RELEASE_SHA.  
Prod delia untouched during eval (`PROD_CONTAINER_UNTOUCHED=YES`).

| | G1 | P1 |
|---|---|---|
| FIRST_TOOL | **teo.read** (`process` search q=90260921 → then `decomposition_tree` get) | **davi.get_context** catalog |
| RECOVERY | SUCCESS → davi.get_context → davi.read `get_product_structure` | NOT_REQUIRED |
| owner_result_incomplete | **False** | **False** |
| GROUNDING | GROUNDED | GROUNDED |
| declared_answer.status | complete | complete |
| OBJECTIVE | **SATISFIED** (BOM PA→MP; residual `coverage_unknown` plan-absent) | **SATISFIED** (same) |

**G1 divergence residual:** first specialist still TEO despite WBS clarification (n=1). Registered; Agent not modified; no auto-rerun.

Config: model `qwen/qwen3-14b` / profile `openrouter_qwen` / config_fp `e4a5b706a3b3156b` / latency_ms_total≈146514 / MODEL_REQUESTS=2.

---

## 4. Postdeploy smoke

| Check | Result |
|---|---|
| api-delpi health | healthy / HTTP 200 |
| transformometro-api | running; WBS description active |
| delia-api health | healthy / HTTP 200 |
| DELIA Settings | env=production; profile=openrouter_qwen; model=qwen/qwen3-14b; fp=e4a5b706a3b3156b |
| DAVI 90260921 completeness | is_complete True |
| Rollback | NOT_REQUIRED |

No Agent/instruction changes. No full battery. No destructive migrations.

---

## 5. Outcomes

```text
DEPLOY_SUCCESS=YES
RUNTIME_HEALTH=YES
MCP_CONTRACT_ACTIVE=YES (TEO WBS prose + DAVI full-mode completeness)
BUSINESS_RESULT_CORRECT=YES (SKU flat BOM authoritative)
AGENT_OBJECTIVE_SATISFIED=SATISFIED_WITH_RESIDUAL (G1 TEO-first attractor; coverage_unknown finalize)
```

---

## 6. Residuals / next

- G1 first-tool TEO attractor persists (selection residual; not contract false incomplete).
- `coverage_unknown` on finalize without plan obligations (INT-3 ownership).
- Live statistical stability of G1 selection: UNPROVEN (n=1).

```text
INT1_STAGE_ACCEPTANCE=BLOCKED
INT1_CLOSED=NO
INT2/INT3/T3=NOT_AUTHORIZED
NEXT=COORDINATION_INT1_PRODUCTION_VALIDATION_INDEPENDENT_REVIEW
```
