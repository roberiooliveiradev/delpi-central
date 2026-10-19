# 28 — I03 · DAVI Semantic Discovery · Implementation Evidence

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-I03-DAVI-SEMANTIC-DISCOVERY-IMPLEMENTATION-01`  
**BASE_HEAD:** `1e017bf63438cf148c94b6981b05af2a532f1eed`  
**AUTHORITIES:** [27](./27-i03-davi-semantic-discovery-implementation-brief.md), [26](./26-i02-owner-crosscheck-and-acceptance-gate.md), report [44](../conversational-intelligence-c3/44-specialist-knowledge-utilization-eval.md), ledger §6.164 residual + §6.268  
**EXISTING_EQUIVALENT:** `YES` — `OperationalCapabilityOrchestrator._invoke_selected` DISCOVERY terminal  
**REUSE_DECISION:** `EXTEND`  
**I03_ACCEPTED:** `NO`  
**VERDICT:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Problem (K4)

Historical K4 selected `discover_delpi_information` correctly but rendered absolute “nenhuma ação correspondente” when `candidates=[]` even though the owner envelope carried `eligible_action_count>0` (catalog exists). Control-plane fields were correctly suppressed (§6.164); semantic adequacy of capability-inquiry remained residual — now addressed.

**Invariant:** `0 SEARCH RESULTS != CAPABILITY ABSENT`.

## 2. Owner contract (repo + runtime)

| Field | Evidence |
|---|---|
| DAVI_OWNER | api-delpi MCP `discover_delpi_information` / `execute_delpi_information` |
| OUTPUT | `DiscoverDelpiInformationOutput`: query, top_k, candidate_count, **eligible_action_count**, candidates, capability_surface |
| SEARCH_NO_MATCH | `candidates=[]` with `eligible_action_count>0` |
| CAPABILITY_SURFACE | `agent_directives` only — **not** user-facing catalog |
| ENUMERATION | Count via `eligible_action_count`; full action list not in envelope |
| AUTHZ | Core/Domain; discovery ≠ approval; execute requires candidate_token |

Direct connected MCP call from this agent: see live section / `DIRECT_OWNER_PROBE`.

## 3. Implementation

Module helpers + DISCOVERY terminal in `orchestration.py`:

- `_owner_eligible_action_count` / `_discovery_empty_result_class`
- `_live_interop_surface_lines` (tools/list DISCOVERY|READ|ANALYSIS only)
- `_render_zero_candidate_discovery`

| Class | User meaning |
|---|---|
| `CAPABILITY_NOT_MATCHED` | Search miss; catalog count > 0; reformulate |
| `CAPABILITY_UNAVAILABLE` | eligible_action_count == 0 |
| `CAPABILITY_NOT_ENUMERABLE` | No count; honest gap + observed interop tools |

Never leaks `capability_surface` / `agent_directives` / telemetry keys. Never chains EXECUTE on empty candidates. Provider-neutral (no DAVI name branch).

## 4. Tests

| Suite | Result |
|---|---|
| `tests/test_i03_semantic_capability_discovery.py` | PASS |
| Discovery control-plane / zero-candidate updates | PASS |
| I01/I02/R2/R3A/R3B/ACR/K2K3 quality | PASS |
| Full `delia-api` pytest | PASS |

## 5. Live (fill after deploy)

| Field | Value |
|---|---|
| SOURCE/DEPLOYED_SHA | _pending_ |
| MODEL | kimi-k3 / openai_compatible / budget=30 |
| K4 | _pending_ |
| K1/K2/K3 regression | _pending_ |

## 6. Rollback

```text
git revert <IMPLEMENTATION_SHA>
```

## 7. State

```text
I03_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=DEPLOY_LIVE_K4_THEN_COORDINATION_REVIEW
```
