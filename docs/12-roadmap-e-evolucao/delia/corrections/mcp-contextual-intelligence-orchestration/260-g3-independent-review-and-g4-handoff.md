# 260 — DÉLIA · Review independente G3 e handoff G4

**DATA:** 2026-11-05  
**TASK_ID REVIEWED:** `DELIA-C3-G3-ORCHESTRATION-INTERACTION-LEGACY-SHRINK-01`  
**REVIEWED CODE HEAD:** `fbb8d8e9b8244a01567e019a24cecabcca22c5ad`  
**BASE:** `6f69f8ac1a1ca752e4dfe6890a4bf36efb54bb0a`  
**REVIEW VERDICT:** `ACCEPT_WITH_RESIDUAL` — physical shrink and CRI retirement verified from GitHub diff; targeted test gaps remain.  
**PRODUCTION DEPLOY:** NOT_AUTHORIZED. **E01–E10:** TEST_NOT_RUN.

## GitHub evidence

- Compare includes unrelated concurrent TV/dashboard/plugin-ui commit; G3 code commit `fbb8d8e9` itself is bounded to DÉLIA app, tests, scripts, config and docs.
- `orchestration.py` -165 net lines in GitHub compare (33 added / 198 deleted), current ~6369 lines; 9 obsolete helper functions removed. Root composer -74 net lines, handle_interactive_turn -23, obsolete CRI instruction resource deleted, toggle config and wiring removed.
- 3 scripts retired, `test_cri_e1_response_intelligence_toggle.py` retired, test fixtures updated, code paths `response_intelligence_enabled`/CRI mode removed. Legitimate vocabulary `cri_presentation.delpi.json` remains live; do not delete merely because name contains 'cri'.
- `_apply_declared_answer` clarifies on partial evidence when a declared material plan has unmet obligations, returning `CLARIFICATION_REQUIRED` and copying `terminal.outcome` + `terminal.provenance`, with `verified_evidence_preserved`. It still relies on existing `_evaluate_material_obligations`, not a second assessor.
- New tests exist, executor reports 16/16 G1, 15/15 G2 and full backend suite exit0. This review inspected sources/diff, **did not run tests or inspect independent logs**.

## Verified residuals

**R1 — Privacy/observability negative test regression.** `test_turn_observability.py::test_projection_is_bounded_and_never_carries_payload` was deleted with the CRI tests. It checked model-id bounds, provider disclosure, secret/prompt/COT exclusion from wire and safe call projection; these invariants are not CRI-specific. The deleted `test_composition_elapsed_accumulates` also pinned honest elapsed timing, potentially still relevant independently. Restore or identify equivalent existing active negative tests for these general contracts using a non-CRI composition mode. No need to restore retired CRI behavior, selector or toggle.

**R2 — Partial clarification proof gap.** `test_clarification_applies_with_partial_evidence_and_unmet_obligations` uses `_terminal()` without outcome/provenance (per fixture), then only asserts status and limitation. The production method copies `terminal.outcome` and `terminal.provenance`; copying None does not prove preservation of verified partial evidence. Add fixture with actual owner outcome + SourceRef and assert both fields survive (and interaction serializer/NDJSON retains them where contract allows). Test continuity with multiple collected attempts and a terminal composed result where relevant; avoid fabricated source refs.

**R3 — Contradiction/stale commentary.** At ~line 260 in `orchestration.py`, a comment still describes injecting a “CRI clause”/deactivated mode/resource although the resource and toggle have been retired. Remove or correct stale commentary (without altering canonical history). Only necessary docstring cleanup.

**R4 — Unverified real quality.** E01–E10 remain TEST_NOT_RUN; module shrink cannot be read as product-outcome PASS. No production deploy.

**R5 — Reporting math.** `RQ-08..RQ-11=PARTIAL` is not the same as four completed RQs; original `RQ-11` belongs to G4 by the plan 256 stage matrix. Reconcile exact RQ-08/09/10 status on G3, and keep RQ-11 in G4, unless actual criterion-specific evidence justifies status. Accepted task-verified 5/28 remains provisional from earlier review; partial counts zero.

## Review classification

`ACCEPT_WITH_RESIDUAL` applies to **G3 physical CRI retirement and dead-code removal**, not formal completion of every G3 requirement nor production readiness. No reintroduction of CRI, no duplicate runtime, no mass rearchitecture. R1 and R2 are concrete bounded regression-proof tasks to close before integrated G7 signoff, preferably as G4 prerequisites in same bounded implementation.

## G4 execution handoff

**Task candidate:** `DELIA-C3-G4-MODEL-INVOCATION-CONFIG-OBSERVABILITY-NATIVE-CONSOLIDATION-01`.

1. Reanchor git HEAD/status/origin and Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → thematic specs → ledger → doc256 and doc260. Preserve concurrent changes. Never make production deploy.
2. Resolve R1/R2 with focused RED→GREEN tests first; R3 stale comment minimal patch. No new engines, registry, provider-selection layer or semantic assessor.
3. Actual G4 scope: `application/model_invocation/{invoke_model,context_budget,governed_retries,contracts}.py`, `infrastructure/model_invocation/pydantic_ai_adapter.py`, `infrastructure/config/{pydantic_ai_runtime_config,settings}.py`, JSON `config/pydantic_ai.runtime.delpi.json`, `interaction/turn_observability.py`. `ModelInvocationPort` is KEEP while legitimate C3-T4 and conversational consumers remain.
4. Reconcile native PydanticAI output validation, retries, usage counters and context budget against existing code; remove only genuinely duplicated logic and dead config flags with all consumers and security gates proven. **No nested retry multiplication**; preserve total-turn deadline. Pre-call token estimations remain estimates and must not be reported as SDK-measured tokens.
5. Preserve secrets out of JSON/prompt/logs. Keep Keycloak/Core/MCP/STT separate. Do not confuse text runtime removal with STT adapter removal. Reuse single JSON config and effective loaded values; no second configuration surface.
6. Test invalid schema, retry counts, provider failure, cancellation, context overflow, real token usage, redaction, NDJSON and authorization. Full backend/architecture suite, isolated native SDK fixtures; real local model eval where authorized, otherwise TEST_NOT_RUN, never false PASS.
7. Produce changed/removed symbol mapping, LOC before/after, SHA/config/model, tests and actual outcome evidence, residual search and review-ready report, docs/ledger after facts. Commit/push coherent diff; no deploy.

## Status

**PROVEN**: physical G3 changes, CRI retired wiring, partial-clarification branch, new tests present.  
**TESTS**: PASS executor-reported, not independently rerun.  
**TO_INVENTORY**: full equivalent privacy coverage, composite evidence serialization under clarification, effective usage/retries budget.  
**VERDICT**: ACCEPT_WITH_RESIDUAL; G4 authorized as bounded development under existing authority, not as automatic phase advance.
