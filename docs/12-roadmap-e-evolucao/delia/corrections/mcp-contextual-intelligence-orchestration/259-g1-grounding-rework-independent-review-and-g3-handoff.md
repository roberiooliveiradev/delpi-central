# 259 — DÉLIA · Revisão independente do rework G1 e handoff delimitado G3

**DATA:** 2026-11-05  
**TASK_ID REVIEWED:** `DELIA-C3-G1-NATIVE-ANSWER-GROUNDING-AND-ACCEPTOR-REWORK-01`  
**BASE:** `a034fc6934dd98061ee10b67117222a363069846`  
**REVIEWED SHA:** `6bc403183b7e121691c3569f04fc0cccda677c73`  
**IMPLEMENTATION COMMIT:** `6b07992ec5c73c649ceea242b91ffdeea9d19348`  
**REVIEW_VERDICT:** `ACCEPT_WITH_RESIDUAL` for G1 grounding remediation.  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED; **E01–E10:** TEST_NOT_RUN.

## Code facts directly verified on GitHub

- `application/capability_provision/orchestration.py::_apply_declared_answer` always retains the deterministic `terminal.content`; model-generated `InvestigationAnswer.answer` is **never** assigned as authoritative content.
- `schema_version != "1"` rejected whole, with `declared_schema_rejected`.
- `NEEDS_CLARIFICATION` is ignored for terminal `SUCCESS` with any verified business attempt; no-business-evidence cases retain the bounded clarification path.
- Every model-declared positional evidence index is tested against `collected` and `_is_business_evidence_attempt`; a mixed valid/invalid ref list causes `declared_status_overridden`. `plan=None` or empty `evidence_needed` causes `coverage_unknown` and override.
- For a declared `COMPLETE` with valid refs and a plan, `_evaluate_material_obligations` is checked before accepting declaration *consistency*, though the output remains deterministic.
- `tests/test_g1_native_structured_output.py` contains 14 test functions, including hallucinated prose with valid SourceRef, mixed refs, empty coverage, schema invalid, clarification and bounded content. Executor reports 14/14 PASS and complete backend suite exit 0, **not independently reexecuted by reviewer**.
- No new semantic assessor, planner or Agent was introduced by this bounded rework. Only `orchestration.py` and G1 test code changed alongside docs/ledger.
- Production and real-model E01–E10 not executed; do not call `FALSE_GROUNDED=0` a real-model benchmark conclusion. It is an invariant evidenced by code and isolated tests.

## Residuals before or within G3

1. The native typed `InvestigationAnswer` now functions as a *governed declaration* whose generated `answer` never reaches the final factual response. This may be the safest correct behavior today. G3 should determine whether response generation is doing useful work and avoid perpetuating a redundant semantic stage. **No authorization to substitute model prose without independent factual support.** Do not create a second assessor to solve this.
2. `NEEDS_CLARIFICATION` with terminal SUCCESS and **some** business evidence always gets ignored. Yet partial verified evidence can coexist with unmet material obligations. Characterize via RED tests: clarification may be needed for missing necessary parameters even when one observation is valid. Preserve already verified data and use existing bounded clarification path; never discard legitimate partial evidence.
3. The finalizer `_finalize_agent_collected_attempts` remains substantial; G3 should separate true owner-gates/contract outcomes from duplicate answer/CRI composition only by removing dead code and shrinking active semantics, not shuffling LOC into a new file.
4. Obligation coverage and completeness after real owner tools remain a task-outcome question. E01–E10, generalization, and impact on answer fidelity are **pending G7**; no production rollout.
5. Updated review credit is **RQ-01, RQ-02, RQ-03, RQ-05, RQ-06 IMPLEMENTED; RQ-04, RQ-07 PARTIAL; RQ-08–28 NOT_IMPLEMENTED = 5/28=17.86%** of cleanup task, not global DÉLIA phase.

## G3 handoff — concrete bounded implementation

**Task candidate:** `DELIA-C3-G3-ORCHESTRATION-INTERACTION-LEGACY-SHRINK-01`

**Mandatory authority reanchor:** git HEAD/status, Project Instructions + .cursor, docs 16→50→17→49→51→52→21→20→25, relevant thematic specs, execution ledger, doc256 and review259. Recheck existing equivalents and legitimate consumers.

**Scope:** `application/capability_provision/orchestration.py`, `conversational_response.py`, `generic_evidence_renderer.py` only where dead consumer proven; `application/interaction/handle_interactive_turn.py`, `instruction.py`, `presentation.py`, `turn_observability.py`, `infrastructure/config/cri_instruction_resource.py` only where a live duplicate path proven. `infrastructure/orchestration/pydantic_ai_investigation.py` only for associated native Agent output wiring. No new runtime, no copying large helper families to another file.

**G3 gate:** prove real callgraph, write focused RED tests for relevant use-case behavior and the partial-evidence clarification residual, implement smallest shrink, run full backend + architecture tests, compare actual LOC and dead symbol search, and execute real model local eval where environment allows (G7 formal matrix remains separate). Preserve Evidence/SourceRef/Domain, grouped obligation coverage, protected writes, NDJSON and terminal safety; never turn model prose into FACT.

**Closeout report:** BASE/FINAL SHA, exact functions physically deleted and consumers, line deltas by file, actual tests and eval status, security/grounding/Outcome, config/model SHA, residuals, ledger update, commit/push; no auto-acceptance or production deploy.

**STATUS:** Documentation/review only; no runtime source changed or tests executed by this review.
