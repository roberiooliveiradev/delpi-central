# 42 — DAVI/VISTA semantic routing diagnosis and referential detail fix

**DATA:** 2026-10-17  
**TASK_ID:** `DELIA-C3-MCP-DAVI-VISTA-SEMANTIC-ROUTING-AND-REFERENCE-FIX-01`  
**BASE_HEAD:** `445f264007e9cb62e165502ed749f080e87f9754`  
**CODE_COMMITS:** `9eeb3dd1c7` (prior_listing + ordinal bind) · `e9b2f46287` (resolver budget floor)  
**DEPLOYED_SHA_AFTER:** `e9b2f46287389f9376ee75502baa1e2369948c40`  
**PRODUCTION_TESTED_SHA (smoke histórico):** `6dd5f6d183`

## 1. Reuse gate

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
```

Extended `OperationalCapabilityOrchestrator` selection payload + same-owner resolver. No new planner, memory engine, or provider preference.

## 2. A1 — OpenAPI vs DAVI

```text
A1_VERDICT=VALID_PROVIDER_NEUTRAL_SELECTION
A1_CODE_FIX=NONE
OPENAPI_VS_DAVI_CONTRACT_DECISION=OpenAPI delpi.search_products is a legitimate provider-neutral READ for product search; the prior smoke FAIL presupposed MCP DAVI preference, which contradicts PROVIDER_NEUTRAL_ORCHESTRATOR.
```

No `if provider == "davi"`, no global MCP-over-OpenAPI ranking.

## 3. C2 — root cause chain (confirmed)

```text
USER_T2 (primeira programação → telas/blocos)
  → TURN_GOAL prior_sufficient=false (needs fresh owner)  ✓
  → SELECTION without full prior transcript (Stage05 latency)
  → HISTORICALLY selected list_playlists again (catalog without continuity hint)
  → AFTER FIX: select get_playlist_context ✓
  → ARGUMENTS projected playlist_id not in provenance → unproven_identifier ✓
  → RESOLVER list_playlists (same owner) → bind proven id ✓
  → get_playlist_context(playlist_id=…) → GROUNDED synthesis ✓
```

Intermediate live miss after selection-only fix: `resolver decision=skipped_budget remaining_ms≈11198` while floor required 15s (`0.5 * stage`). Floor lowered to `max(0.25 * stage, 3 * MIN_VIABLE)` without raising the 30s global ceiling.

## 4. Fix summary

| Change | Role |
|---|---|
| `prior_listing` compact hint in capability catalog | Continuity for selection without full history |
| CAPABILITY_SELECTION instruction | Prefer identifier-required detail over re-list when prior listing + referent ask |
| `_user_list_ordinal` + ordinal bind in resolver | Disambiguate multi-entity lists when user names a position |
| `_fill_missing_from_entity` | Deterministic proven-id fill |
| Resolver budget floor | Allow same-owner resolve on follow-ups inside 30s |

## 5. Tests

- `test_referential_detail_resolution.py` — 10 PASS (hint, ordinal GREEN, ambiguous clarify, invented id, rename sibling, MESSAGE≠ACT, budget floor).
- Full `delia-api` pytest green after CODE SHAs.

## 6. Live revalidation (`srv-api`, SHA `e9b2f46287`)

| Test | Capability | Grounding | Latency | Verdict |
|---|---|---|---|---|
| C1 | `list_playlists` | GROUNDED | 19203 ms | PASS |
| C2 | `get_playlist_context` (via resolver `list_playlists`) | GROUNDED | 22805 ms | PASS |

```text
C2_SELECTED_CAPABILITY=get_playlist_context
C2_OWNER_ARGUMENTS_VALID=YES (playlist_id from live list_playlists)
C2_USER_GOAL_ACHIEVED=YES (slides/blocks listed)
MATERIAL_ACT_COUNT=0
MAX_OBSERVED_LATENCY_MS=22805
LIVE_DAVI_VERDICT=NOT_RERUN (A1 contract decision = no defect)
```

Correlation C2: `eb5c4374-68b1-45d3-a97d-25872f0fa3ab`.

## 7. Residuals

- B2 `reject_literal_copy` conversational residual unchanged.
- List synthesis may omit technical ids from user-facing text; resolver re-lists live — acceptable; not AuthZ from prior.
- A1 DAVI MCP path accessibility not separately smoke-tested (not required when OpenAPI is legitimate).

```text
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=INDEPENDENT_ARCHITECTURE_REVIEW
```
