# 21 — Adaptive Capability Routing Completion · Implementation Evidence

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-ADAPTIVE-CAPABILITY-ROUTING-COMPLETION-01`  
**BASE_HEAD:** `37c908cf1d60db8c8486f8d33ad8cf3f7fbb9082`  
**IMPLEMENTATION_SHA:** `c2ae80e364b361761bd48c0a4bfce3be11975023`  
**DEPLOYED_SHA:** `c2ae80e364b361761bd48c0a4bfce3be11975023` (`srv-api` `delpi-delia-api`)  
**AUTHORITIES:** [14](./14-i02r3-independent-diagnostic-review-and-architecture-decision.md)–[20](./20-i02r3b-independent-live-outcome-review.md); docs 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25  
**EXISTING_EQUIVALENT:** `YES` — `OperationalCapabilityOrchestrator` + `select_decision_path` + R3-B typed merge  
**REUSE_DECISION:** `EXTEND` (no second planner/engine/registry)  
**I02_ACCEPTED:** `NO` (not auto-advanced)  
**VERDICT:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Scope delivered (bounded A–D)

| Slice | Change | Safety gate |
|---|---|---|
| **A FAST** | Telemetry via existing `select_decision_path` when surface is singleton + native + no discovery + closed schema; **no** singleton auto-select of applicability (model validation preserved) | Unsafe FAST force-select reverted after metamorphic/NOT_APPLICABLE regressions |
| **B OPERATIONAL + native** | R3-B typed capability+goal preserved; native assessment skipped **only** when non-write + `comparison_requested` already declared (forces corroborate). Write targets still assess (enrichment may apply). **Prohibited** `READ ⇒ SKIP_NATIVE_ASSESSMENT` | Foreign / corroboration / multi-owner gates kept |
| **C Arguments** | `_deterministic_arguments_from_schema` before model when const/single-enum/optional-default cover material keys; opaque TEO schemas remain `MODEL_REQUIRED` | No invented ids; no parallel MCP vocabulary |
| **D K2/K3 quality** | Thin prior-continuation expands extraction lists from prior excerpts (≥3, cue match, not limitation ask); index options ranked by lexical overlap before model select; log `topic=` | Grounding preserved; limitations follow-up not expanded |

## 2. Invariants preserved

```text
MODEL_OUTPUT != FACT
MCP_METADATA != AUTHORIZATION
DISCOVERY != APPROVAL
READ != WRITE
PREPARE != ACT
MESSAGE != ACT
GLOBAL_TURN_BUDGET_SECONDS=30
STAGE_CAP_10S_PRODUCTION=OFF
ARGUMENTS_HEADROOM_PRODUCTION_DEFAULT=OFF
```

## 3. Synthetic / regression evidence

| Suite | Result |
|---|---|
| `tests/test_adaptive_capability_routing_completion.py` | PASS |
| I01 / I02 / R2 / R3 / R3A / R3B regressions | PASS |
| Full `delia-api` pytest | PASS |
| Provider rename / non-MCP / multi-owner / WRITE ambiguous / foreign / injection / missing inputs / budget 30 / ACT=0 | Covered by existing + completion suites (PASS) |

## 4. Live evaluation (authenticated, MESSAGE-only)

| Field | Value |
|---|---|
| TARGET | `operador@192.168.1.237` (`srv-api`) |
| CONTAINER | `delpi-delia-api` healthy; markers `HAS_DET_ARGS/EXPAND/RANK=True` |
| MODEL | `moonshotai/kimi-k3` via `openai_compatible` |
| BUDGET / STAGE | **30** / **30** |
| CONFIG_FINGERPRINT | `5de714a34e2f63f5` (budget\|stage\|provider\|model-env) |
| SAMPLE | K1=1, K2=1 (same conversation), K3=1 — no opportunistic retries |
| DEPLOY | git pull + `up-prod-sequential.sh --pull --build delia-api` from `origin/main` |

### K1 — TÉO methodology

**Input sha256-8:** `2a8147e1` (same historical text as doc 19)  
**Correlation:** `5816e0b8-e48b-4328-b329-fa1d1c5624d5`

```text
HTTP=200
TOTAL_TURN_MS=20199 (<=30000)
SPECIALIST=mcp:teo
CAPABILITY=get_methodology_guide
TYPED_WITH_CAPABILITY=YES (no separate turn_goal)
DECISION_PATH=OPERATIONAL
NATIVE=sufficient (model)
DISCOVERY=get_catalog
OWNER_READ=REACHED
SYNTHESIS=deterministic_guidance
GROUNDING=GROUNDED
LIMITATIONS=result_truncated
CONTENT_CHARS=2032
MATERIAL_ACT=0
MODEL_CALLS_PRE_READ=4 (group, capability+goal, native, arguments)
```

**K1_RESULT:** `PASS_WITH_LIMITATION` (useful grounded methodology; truncation residual). Latency vs doc19 baseline 21469ms → 20199ms on this sample (n=1, not causal A/B).

### K2 — continuity (same conversation)

**Correlation:** `eeb15bba-07bd-44d8-b4aa-29f3f64f2337`

```text
prior_evidence_sufficient=yes
prior_continuation=transformed excerpts=12
expand_thin_extraction=NOT_LOGGED (rendered already >=120 chars)
OWNER_REINVOCATION=NO
HTTP=200
TOTAL_TURN_MS=21066
GROUNDING=NON_GROUNDED (continuity contract)
LIMITATIONS=prior_turn_evidence_only
CONTENT_CHARS=130 (baseline doc19=48)
MATERIAL_ACT=0
```

**K2_RESULT:** `PASS_WITH_LIMITATION` — structural continuity PASS; usefulness improved vs 48 chars but still short for a full extraction checklist. Expand gate ready; this sample did not need it.

### K3 — VISTA nested guidance

**Correlation:** `10e01d5d-5bcd-45d2-92e8-fe6be93abfa8`

```text
SPECIALIST=mcp:vista
CAPABILITY=get_product_guide
TYPED_WITH_CAPABILITY=YES
DECISION_PATH=OPERATIONAL
INDEX_READ=YES (identifiers=11)
INDEX_SELECT=bound field=topic topic=display_formats
OWNER_GUIDANCE_READ=YES
SYNTHESIS=deterministic_guidance
HTTP=200
TOTAL_TURN_MS=15294
GROUNDING=GROUNDED
CONTENT_CHARS=1050
MATERIAL_ACT=0
TOPIC_RELEVANCE=PARTIAL (display_formats vs legibility/visualization ask)
```

**K3_RESULT:** `PASS_WITH_LIMITATION` — nested INDEX→topic→guide preserved; topic relevance residual remains.

## 5. Optimization dimensions (vs doc19 baseline)

| Dimension | Before (doc19) | After (this SHA) |
|---|---|---|
| K1 model calls pre-READ | 4 | 4 (typed merge preserved; TEO args still model) |
| K1 total ms | 21469 | 20199 |
| K2 content chars | 48 | 130 |
| K3 topic logged | absent | `display_formats` |
| Pre-owner latency | arguments ~10s residual | arguments still model-bound for opaque TEO |

## 6. Contract impact

```text
PUBLIC_OPENAPI=NONE
HTTP_DTO=NONE
NEW_PLANNER=NO
NEW_ENGINE=NO
NEW_REGISTRY=NO
EXPERIMENTAL_FLAGS_DEFAULT=UNCHANGED
```

## 7. Rollback

```text
git revert c2ae80e364b361761bd48c0a4bfce3be11975023
# restores orchestration.py + completion tests + R3B comparison expectation + docs
```

## 8. Decision state

```text
ALGORITHM_COMPLETION=PARTIAL
FAST_PATH=TELEMETRY_SAFE_NO_AUTO_SELECT
OPERATIONAL_PATH=R3B_PRESERVED_LIVE_OPERATIONAL
REASONING_PATH=PRESERVED_ESCALATION
NATIVE_ASSESSMENT=CONDITIONED_COMPARISON_ONLY
DETERMINISTIC_ARGUMENTS=ELIGIBLE_SCHEMAS_SYNTHETIC_PASS
CONTINUITY_QUALITY=IMPROVED_VS_48_STILL_LIMITED
K1_LIVE=PASS_WITH_LIMITATION
K2_LIVE=PASS_WITH_LIMITATION
K3_LIVE=PASS_WITH_LIMITATION
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```

**Why not `ALGORITHM_COMPLETION=PASS`:** FAST does not yet perform safe deterministic capability resolution without model (auto-select blocked by safety); K2 usefulness and K3 topic pertinence remain limited on the live sample despite structural gains.
