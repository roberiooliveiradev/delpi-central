# 43 — DAVI/VISTA · Independent correction acceptance and functional state

**DATA:** 2026-10-17. **TASK REVIEWED:** `DELIA-C3-MCP-DAVI-VISTA-SEMANTIC-ROUTING-AND-REFERENCE-FIX-01`. **VERDICT:** `ACCEPT_WITH_RESIDUAL`.

## Review boundary
Independent GitHub code/diff and report [42](./42-davi-vista-semantic-routing-and-reference-fix.md) review of commits `9eeb3dd1c7eb91a71d8202736af67447e920b430` and `e9b2f46287389f9376ee75502baa1e2369948c40`; implementation evidence commit `af7bb5dfc1d83baa0b1a1ce5ca2ef8934ae1de59`. SSH/live and full pytest evidence are **executor-reported**, not independently rerun.

`EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND`: existing provider-neutral `OperationalCapabilityOrchestrator`, capability selection and same-owner resolver extended. No new planner, MCP-first preference, DAVI/VISTA runtime branch, local tool registry or authority.

## What was corrected and current verified behavior
1. **A1 DAVI/OpenAPI classification corrected, NO CODE FIX:** original smoke selected `openapi:delpi.search_products` for a legitimate product READ and returned GROUNDED. MCP DAVI is not mandatory for every query if the OpenAPI capability legitimately fulfills the user intent under its own AuthZ and Domain rules. This is `VALID_PROVIDER_NEUTRAL_SELECTION`, **not proof of a DAVI MCP path test**.
2. **C2 VISTA contextual detail fixed:** previous live flow repeated `list_playlists` instead of choosing `get_playlist_context` after user referenced the first listed playlist. Capability selection now receives a compact `prior_listing` hint, not the entire transcript. Same-owner resolver can re-list and bind an ordinal-selected **owner-proven** ID into validated required arguments; prior conversational text alone never authorizes or establishes a fresh identifier. Synthetic holdout tests cover ordinal, ambiguity, rename, invented ID and message/write isolation.
3. **Resolver budget fixed within global ceiling:** prior `max(0.5*stage,4*MIN_VIABLE)` skipped resolver with about 11s remaining; adjusted to `max(0.25*stage,3*MIN_VIABLE)`. `GLOBAL_TURN_BUDGET_SECONDS=30`; no increase. The floor change applies generically and remains a bounded latency tradeoff, not a claim that every path succeeds.
4. **Production live evidence reported**, at deployed SHA `e9b2f46287389f9376ee75502baa1e2369948c40`: VISTA C1 `list_playlists` GROUNDED in 19,203ms; C2 `get_playlist_context` via same-owner `list_playlists` resolver GROUNDED in 22,805ms with valid playlist_id and slides/blocks delivered; `MATERIAL_ACT_COUNT=0`. Correlation C2: `eb5c4374-68b1-45d3-a97d-25872f0fa3ab`. Targeted 10 tests and full delia-api suite PASS executor-reported.

## Present state, residuals, next
- **Accepted bounded behavior:** provider-neutral OPENAPI READ for products and VISTA READ list→detail with resolved owner-bound ID and grounded answer, on the evaluated SHA/session. Existing TÉO guide READ also previously passed; no new TÉO deploy proof in this task.
- **Still open:** TÉO B2 `reject_literal_copy` → honest insufficiency instead of proportional summary; DAVI MCP discovery→execute pathway `NOT_RERUN`; broader ordinal/provenance/latency generalization across owners `NOT_PROVEN`; no unsafe write live tests.
- **Interpretation:** user-facing success on the bounded VISTA scenario is supported by executor live evidence; no general production-readiness or cross-owner reliability inference.
- **Architectural invariants:** specialist owns live tool catalog; DÉLIA selects semantic capabilities; MCP/OpenAPI adapters own provider mechanics; live owner evidence ≠ cached/prior AuthZ; `MESSAGE != ACT`; `MODEL_AUTHORED_FACTUAL_PROSE=NONE`.

```text
TASK_INDEPENDENT_REVIEW=ACCEPT_WITH_RESIDUAL
A1_PROVIDER_NEUTRAL_SELECTION=ACCEPT_NO_FIX
C2_REFERENTIAL_DETAIL=ACCEPT_FOR_EVALUATED_SCOPE
LIVE_EVIDENCE=PASS_BOUNDED_EXECUTOR_REPORTED
C3_CONVERSATIONAL_INTELLIGENCE_TRAIL=CLOSED_WITH_RESIDUAL
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
PRODUCTION_READINESS=NOT_PROVEN
NEXT=RETURN_TO_ARCHITECTURE_COORDINATION_FOR_GLOBAL_C3_GATES
```
