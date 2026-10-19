# 35 — Coordination decision: adaptive routing reliability remediation

**DATE:** 2026-10-19. **REVIEWED_HEAD:** `500b70870d752d9c4f809ceb12ac14e1ffc0f24d`. **EVIDENCE:** [33](./33-live-orchestration-decision-and-log-validation.md), [34](./34-independent-review-live-routing-failures-and-remediation-gate.md), current `OperationalCapabilityOrchestrator` methods `_select_target`, `_select_group`, `_select_capability_with_goal`, `_propose`, `_prior_continuation_attempt`, `_synthesize_content`; ledger §6.274–275.

## Decision

Continue existing `Adaptive Capability Routing` through **bounded deterministic selection/failure gates and outcome-aware presentation**, **not** another planner/registry/engine or broad orchestration replacement. `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND` (conditional on HEAD/authority verification by executor). Explicit priority: **R1 selection-none terminal handling + R3 K2 framing**, then **R2 provider-neutral typed discovery capability investigation/fix only if contract evidence permits**; personal ticket counts are a separate owner-linked follow-up. Preserve 30s global deadline, R3B cold-start merge, owner DISCOVERY, Core/Domain gates, READ/PREPARE/ACT and model-output-not-FACT.

### Confirmed facts

- `_select_target` returns None on missing/invalid group or capability and logs it. L02 `group=none` and L06 `capability=none` later exhausted global budget; exact caller/fallback sequence to prove before editing. Not all no-match means owner absence; model rejection/timeout/no surface need distinct truthful outcome semantics.
- L01 routed to Helpdesk correctly on tested SHA but `glpi_link_required` blocked ticket count; page length is not total and assigned/requester semantics require owner/AuthZ. Historical misroute not reproduced on this SHA.
- L04 continuity is functional but record-list wording for methodology is wrong; outcome must respect evidence kind and user intent.
- L03 TÉO and L05 VISTA safe clarification should remain regression controls. I03 previous scoped accept is unchanged; no I04/Q01 auto-implementation.

### Algorithm contract (behavior, not new architecture)

```text
User request / authorized context
 -> recognize expected result kind (count, list, guidance, hypothetical example, owner fact, action) using existing goal/capability semantics
 -> choose least sufficient FAST / OPERATIONAL / REASONING path (current mechanisms)
 -> typed group/capability candidate with current eligibility validation
 -> if valid: preserve owner discovery, argument validation and read/prepare/act gates
 -> if not: distinguish no-match/invalid proposal/owner unavailability/budget exhaustion; use only legitimate remaining fallback, else honest clarification/limitation
 -> validate evidence, pagination/scope and semantic response kind
 -> grounded presentation or honest limitation; never fabricate facts or authority
```

Expected response-kind classification is a **bounded design target** subject to current contract inventory; not approval to introduce a new DTO/engine. No generic retry until 30s, no auto-select singleton, no hardcoded DAVI/TÉO/VISTA fallback, no owner-specific capability invention or model-authored factual prose.

### Acceptance gates

- RED for L02 `group=none` and L06 `capability=none`; inspect downstream caller and prove which fallback is safe, preserving alternative legitimate paths and WRITE ambiguity. GREEN must avoid timeout caused solely by a conclusively invalid selection when a truthful user-facing result is available.
- L04 checklist/methodology framing correct, with sourced extraction and no owner reinvocation.
- R2 DAVI owner surface and typed proposal semantics compared; if a public/structural contract change is needed, `ARCHITECTURE_DECISION_REQUIRED`. No forcing a capability on zero-match evidence.
- L01 count after legitimate linked session only; absent authoritative total remains unknown. K1–K4, renamed/non-MCP, multi-owner, foreign, injection, authorization and 0 ACT regressions; full backend and authenticated live on SHA/model/config.

**REVIEW:** architecture direction APPROVED for bounded implementation of existing-contract R1/R3 after caller proof; R2 remains conditional; runtime fix not yet performed. **NEXT_RELATED:** `DELIA-C3-ORCHESTRATION-NONE-SELECTION-AND-PROJECTION-REMEDIATION-01`; **NEXT_MAIN:** I04 per canonical ledger, unchanged.
