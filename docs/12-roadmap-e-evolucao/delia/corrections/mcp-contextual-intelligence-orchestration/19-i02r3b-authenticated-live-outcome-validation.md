# 19 — I02-R3B · Authenticated Live Outcome Validation

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-MCP-I02-R3B-AUTHENTICATED-LIVE-OUTCOME-VALIDATION-01`  
**SOURCE_HEAD:** `b684264c26f0a770dc93c9e5d650e3c503286412`  
**IMPLEMENTATION_SHA (ancestor):** `cda4963e52ae5cadc66392a5f4fcf37fb3c5aa17`  
**COORDINATION_REF:** `648f83af31ad3e6b5a1e4e9b35758d2dc4c2a1fc` (ancestor of SOURCE_HEAD)  
**AUTHORITIES:** [14](./14-i02r3-independent-diagnostic-review-and-architecture-decision.md)–[18](./18-i02r3b-independent-implementation-review.md) — **not redefined**  
**I02_ACCEPTED:** `NO`  
**SAMPLE_SIZE:** K1=1, K2=1 (same conversation), K3=1 — no opportunistic retries  
**VERDICT:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Runtime gate

| Field | Value |
|---|---|
| TARGET | `operador@192.168.1.237` (`srv-api`) |
| HOST_GIT_HEAD | `b684264c26…` (= `origin/main` at eval) |
| CONTAINER | `delpi-delia-api` healthy `{"status":"available"}` |
| R3B_IN_IMAGE | `HAS_TYPED_MERGE=True` (`_select_capability_with_goal` + `CAPABILITY_AND_GOAL_INSTRUCTION`) |
| ARGS_GUARD_DEFAULT | `False` (unchanged) |
| DELIA_TURN_BUDGET_SECONDS | **30** |
| DELIA_MODEL_STAGE_TIMEOUT_SECONDS | **30** (runtime; not forced to 10) |
| MODEL_ID | `moonshotai/kimi-k3` |
| MODEL_PROVIDER | `openai_compatible` |
| MODEL_VERSION | not separately versioned in env (model id only) |
| CONFIG_FINGERPRINT | `4e1f9a8aea970e7b` (sha256-16 of model/provider/budget/stage/teo/vista flags) |
| MCP_TEO_AVAILABLE | `DELIA_MCP_TEO_ENABLED=true` |
| MCP_VISTA_AVAILABLE | `DELIA_MCP_VISTA_ENABLED=true` |
| AUTH | password-grant Portal subject via Keycloak (no PII/tokens recorded) |
| LIVE_CORE_AUTHZ | exercised (authenticated `/interaction/turns` 200) |
| DEPLOY_REQUIRED | **NO** (R3-B already present in running image) |
| DEPLOY_PERFORMED | **NO** |
| STAGE_CAP_10S | not applied |
| EXPERIMENTAL_ARGS_GUARD | not enabled |

Local regressions before live: I01/I02/R2/R3/R3A/R3B targeted PASS; full `delia-api` pytest PASS.

## 2. K1 — TÉO methodology (cold start)

**Input:** historical K1 text (sha256-8 `2a8147e1`) — *Como devo realizar uma análise de causa raiz de um problema em um processo?*

**Correlation:** `2b833e86-4662-44a6-8c03-d24e5eb12805`

| Stage | ms | Notes |
|---|---:|---|
| select_group (model) | 4831 | |
| select_capability (model, typed) | 4084 | `goal_class=read` validated |
| turn_goal (model) | **NOT INVOKED** | `decision=typed_with_capability` |
| native_assessment (model) | 1980 | `sufficient` |
| get_catalog (owner) | 91 | DISCOVERY |
| arguments (model) | 10062 | completed |
| get_methodology_guide (owner) | 54 | READ |
| synthesis | det. | `deterministic_guidance` |

```text
HTTP=200
TOTAL_TURN_MS=21469 (<=30000)
SPECIALIST=mcp:teo
CAPABILITY=get_methodology_guide
DISCOVERY=PASS
OWNER_READ=REACHED
GROUNDING=GROUNDED
LIMITATIONS=result_truncated
CONTENT_CHARS=2032
METHOD_SIGNAL=YES
MATERIAL_ACT=0
GOAL_CLASS_PRESENT=YES
GOAL_CLASS_VALID=YES (read)
LEGACY_GOAL_FALLBACK=NO
MODEL_CALL_COUNT_PRE_READ=4  (group, capability+goal, native, arguments)
TYPED_PROPOSAL_RETURNED=YES
```

**K1_RESULT:** `PASS_WITH_LIMITATION` (useful grounded methodology; truncation residual).

Versus historical fail class (~30016ms, timeout on arguments, methodology unread): this run reached READ and finished under 30s. Different SHA/config — not a controlled A/B, but task outcome on the R3-B runtime is positive.

## 3. K2 — continuity (same conversation)

**Correlation:** `95216afd-0de8-4710-bb47-358f0d713939`

```text
PRIOR_EVIDENCE_AVAILABLE=YES (K1 DELIA_RESULT OBSERVATION in context)
prior_evidence_sufficient=yes (early turn_goal)
prior_continuation=transformed excerpts=12
OWNER_REINVOCATION=NO
LITERAL_REPLAY=NO (transformed path, not reject_literal_copy)
HTTP=200
TOTAL_TURN_MS=8720
GROUNDING=NON_GROUNDED (continuity contract)
LIMITATIONS=prior_turn_evidence_only
CONTENT_CHARS=48
MATERIAL_ACT=0
```

**K2_RESULT:** `PASS_WITH_LIMITATION` — structural continuity PASS; follow-up usefulness PARTIAL (very short content despite 12 excerpts).

## 4. K3 — VISTA regression

**Correlation:** `39005a0a-63c8-4a76-888f-bbd64e316935`  
**Input:** design/legibility panel guidance question (substitute text registered; difficulty comparable to historical K3).

```text
SPECIALIST=mcp:vista
CAPABILITY=get_product_guide
TYPED_WITH_CAPABILITY=YES (goal_class=read; no separate turn_goal)
INDEX_READ=YES (empty-arg invoke; identifiers=11)
INDEX_SELECT=bound field=topic (model; topic id value not logged)
OWNER_GUIDANCE_READ=YES (arg_keys=topic)
SYNTHESIS=deterministic_guidance
NESTED_GUIDANCE_SIGNAL=YES
HTTP=200
TOTAL_TURN_MS=17028
GROUNDING=GROUNDED
LIMITATIONS=[]
CONTENT_CHARS=1345
MATERIAL_ACT=0
TOPIC_RELEVANCE=PARTIAL_HISTORICAL_RESIDUAL (exact topic id not in logs; content signals present)
```

**K3_RESULT:** `PASS_WITH_LIMITATION`.

## 5. Optimization dimensions

| Dimension | Verdict |
|---|---|
| A. MODEL_CALL_REDUCTION (cold-start) | **PASS** — K1/K3: no `turn_goal` model purpose; `typed_with_capability` logged |
| B. LIVE_LATENCY_IMPROVEMENT | **PASS_WITH_CONTEXT** vs historical fail (~30s timeout); K1=21.5s task complete. Not a controlled same-config A/B; p50/p95 **INCONCLUSIVE** (n=1) |
| C. K1_TASK_OUTCOME | **PASS_WITH_LIMITATION** |
| C. K2_CONTINUITY | **PASS_WITH_LIMITATION** (structure); usefulness PARTIAL |
| C. K3_REGRESSION | **PASS_WITH_LIMITATION** |

Combined capability stage duration (4084ms) was **less** than historical separate capability+goal (~14778+7021); net pre-owner model time improved on this sample. Arguments still ~10s — residual pressure, not a new architecture investigation in this task.

## 6. Security

```text
MESSAGE_ONLY=YES
MATERIAL_UNAUTHORIZED_ACT_COUNT=0
WRITE_NOT_EXECUTED_IN_LIVE=YES
SYNTHETIC_HOLDOUTS=prior R3B suite PASS (not re-live)
```

## 7. Answers to coordination questions

1. Methodology knowledge reached? **YES** (`get_methodology_guide`).  
2. Within 30s? **YES** (K1 21469ms).  
3. Call eliminated? **YES** (no dedicated `turn_goal` propose on cold-start).  
4. Latency reduced vs fail class? **YES on this sample** (with SHA/config caveat).  
5. Useful grounded answer? **YES** (K1), truncation residual.  
6. K2 continuity? **YES** structurally; content usefulness PARTIAL.  
7. VISTA functional? **YES** INDEX→topic→guidance.  
8. Remaining block? Arguments stage still expensive (~10s); K2 short answer; topic relevance residual; I02 not accepted.

## 8. Open gaps / next

- Independent coordination review of this live evidence.  
- K2 answer richness (48 chars) — product residual, not R3-B regression of continuity wiring.  
- Topic id logging absent — relevance classification limited.  
- No statistical p95 (n=1).  
- Do **not** enable stage-cap 10 or arguments headroom from this result alone.

```text
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=COORDINATION_LIVE_OUTCOME_REVIEW
```
