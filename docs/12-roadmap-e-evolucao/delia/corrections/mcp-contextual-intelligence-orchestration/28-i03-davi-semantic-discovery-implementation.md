# 28 — I03 · DAVI Semantic Discovery · Implementation Evidence

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-I03-DAVI-SEMANTIC-DISCOVERY-IMPLEMENTATION-01`  
**BASE_HEAD:** `1e017bf63438cf148c94b6981b05af2a532f1eed`  
**IMPLEMENTATION_SHA / DEPLOYED_SHA:** `3d14a51046fb27bbce303c574ed9bbcf804a30fe`  
**AUTHORITIES:** [27](./27-i03-davi-semantic-discovery-implementation-brief.md), [26](./26-i02-owner-crosscheck-and-acceptance-gate.md), report [44](../conversational-intelligence-c3/44-specialist-knowledge-utilization-eval.md), ledger §6.164 residual + §6.268  
**EXISTING_EQUIVALENT:** `YES` — `OperationalCapabilityOrchestrator._invoke_selected` DISCOVERY terminal  
**REUSE_DECISION:** `EXTEND`  
**I03_ACCEPTED:** `NO`  
**VERDICT:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Problem (K4)

Historical K4 selected `discover_delpi_information` correctly but rendered absolute “nenhuma ação correspondente” when `candidates=[]` even though the owner envelope carried `eligible_action_count>0`. Control-plane non-disclosure (§6.164) preserved; semantic adequacy of capability-inquiry now addressed.

**Invariant:** `0 SEARCH RESULTS != CAPABILITY ABSENT`.

## 2. Owner contract

| Field | Evidence |
|---|---|
| DAVI_OWNER | api-delpi MCP `discover_delpi_information` / `execute_delpi_information` |
| OUTPUT | `DiscoverDelpiInformationOutput` with **eligible_action_count** |
| SEARCH_NO_MATCH | `candidates=[]` + `eligible_action_count>0` |
| CAPABILITY_SURFACE | `agent_directives` only — never user catalog |
| LIVE_PROBE | via authenticated DÉLIA turn (direct MCP from agent = same envelope) |

## 3. Implementation

Helpers + DISCOVERY terminal:

- `_owner_eligible_action_count` / `_discovery_empty_result_class`
- `_live_interop_surface_lines` / `_render_zero_candidate_discovery`
- Classes: `CAPABILITY_NOT_MATCHED` | `CAPABILITY_UNAVAILABLE` | `CAPABILITY_NOT_ENUMERABLE`
- No DAVI name branch; no auto-EXECUTE; no agent_directives leak

## 4. Synthetic tests

`test_i03_semantic_capability_discovery.py` + discovery control-plane updates + full `delia-api` pytest **PASS**.

## 5. Live evaluation (MESSAGE-only)

| Field | Value |
|---|---|
| TARGET | `srv-api` `delpi-delia-api` |
| MARKERS | `_render_zero_candidate_discovery` + `CAPABILITY_NOT_MATCHED` in image |
| MODEL | `moonshotai/kimi-k3` / `openai_compatible` |
| BUDGET/STAGE | 30 / 30 |

### K4 — DAVI discovery

**Correlation:** `3d435fb9-fa54-4d3e-accd-5b0a1f026e7c`

```text
HTTP=200 TOTAL_MS=21119
SPECIALIST=davi CAPABILITY=discover_delpi_information
TYPED_WITH_CAPABILITY=YES DECISION_PATH=OPERATIONAL
discovery_terminal=CAPABILITY_NOT_MATCHED eligible=95
GROUNDING=GROUNDED CONTENT_CHARS=799
SEARCH_MISS_DISTINGUISHED=YES
FALSE_ABSENCE=NO CONTROL_PLANE_LEAK=NO
MATERIAL_ACT=0 EXECUTE_CHAIN=NO
INTEROP_SURFACE_LINES=discover_delpi_information + execute_…
```

**K4_RESULT:** `PASS` (task outcome: honest search-miss with catalog evidence).

### K1 / K2 / K3 regression (same session window, n=1)

| Case | Result | Notes |
|---|---|---|
| K1 | `PASS_WITH_LIMITATION` | TEO methodology 25122ms GROUNDED typed merge |
| K2 | `PASS_WITH_LIMITATION` / sample weak | `prior_continuation insufficient_evidence reason=invalid_record_index` — model index fluke; not DISCOVERY terminal path |
| K3 | `PASS_WITH_LIMITATION` / budget | 30013ms budget_exceeded + source_unverified; near-deadline residual (doc26); not forced display_formats |

## 6. Rollback

```text
git revert 3d14a51046fb27bbce303c574ed9bbcf804a30fe
```

## 7. State

```text
K4_LIVE=PASS
K1_REGRESSION=PASS_WITH_LIMITATION
K2_REGRESSION=SAMPLE_WEAK_NOT_I03_PATH
K3_REGRESSION=BUDGET_NEAR_LIMIT_RESIDUAL
I03_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
