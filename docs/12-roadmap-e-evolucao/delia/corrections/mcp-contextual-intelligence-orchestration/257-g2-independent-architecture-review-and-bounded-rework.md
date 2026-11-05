# 257 — G2 Independent Architecture Review: legacy modules removal

**DATE:** 2026-11-05  
**TASK:** DELIA-C3-CROSS-FOLDER-NATIVE-PYDANTIC-AI-CONSOLIDATED-LEGACY-CLEANUP-01 / G2  
**IMPLEMENTATION_COMMIT:** `88a7c4e50ceaecbdd3234719db93d7777df85afc`  
**DOC_COMMIT:** `3f721a0d7ddc3fa18b38dcd6c0f3c9a08022deca`  
**PRE-REVIEW MAIN:** `b45ed923bbcd3007a421f3cbb8509fcc5ce50342` (subsequent unrelated TV dashboard change)  
**REVIEW_VERDICT:** **REWORK (bounded G2 tests/contract proof)**; no new architecture.  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED.

## Verified repository evidence

- GitHub compare and commit show `outcome_assessment.py` deleted (1805 lines) and `paginated_result_semantics.py` deleted (801 lines).
- `conversational_response.py` −641 net lines, `orchestration.py` −86 net lines, `generic_evidence_renderer.py` **+1578 net lines** (352→1930 split-line count).
- A substantial set of deterministic owner-payload sanitization, entity extraction, count/page resolution and schema helpers **was relocated** into `generic_evidence_renderer.py`, together with existing render functions. Not the same as proving semantic engine removed end-to-end. Evaluate actual callgraph and responsibility boundaries, avoid cosmetic file split.
- Consumer import paths in `argument_validation.py` and `handle_interactive_turn.py` now target `generic_evidence_renderer.py`. `orchestration.py` still ~6398 extracted lines.
- 7 historical eval scripts and 3 tests removed. Deleted `test_c3_evidence_to_answer_isolation.py` had negative cases for DISCOVERY descriptor contamination of business evidence; `test_cri_unified_presentation.py` and `test_q02c_b2_typed_comparison_outcome.py` included prior behavior contracts. Some tests in `test_r45_pagination_integrity_rework.py`, `test_r4_presentation_parity.py`, `test_render_specialist_outcome_fidelity.py` were adjusted and still exist. Verify a **specific equivalent negative case** for each legitimate contract, not only green suite.
- A broad suite PASS is reported by executor (exit 0) but this review did not execute tests or inspect standalone test artifacts/logs. E01–E10 = TEST_NOT_RUN.
- GitHub compare from base to final returned 4 commits including unrelated concurrently advanced docs; do not confuse them with the two G2 task commits.

## Critical numerical correction

Executor provided `RQ-01=PARTIAL`, `RQ-03=PARTIAL`, `RQ-04=PARTIAL`, `RQ-07=PARTIAL`, `RQ-05=IMPLEMENTED`, `RQ-06=IMPLEMENTED`. Thus **IMPLEMENTED=2; PARTIAL=4; NOT_IMPLEMENTED=22; TOTAL=28; BLOCKED=0**. Canonical task-verified coverage is **2/28 = 7.14%**, not 18%. Partial has zero credit. This is whole-plan G0–G8 status and does not negate that G2 physical deletion occurred.

## Required bounded G2 rework

1. Reanchor on actual HEAD/git status/authorities 16→50→17→49→51→52→21→20→25, ledger and plan256. Preserve unrelated changed work.
2. Build a succinct mapping of security/factual invariants formerly asserted in removed tests to active tests. Cover: discovery descriptors NEVER business records or counts; owner items still correctly recognized; control-plane fields not exposed; bearer secrets redacted; page slice != authoritative total; false comparison/ordering unsupported; malformed/partial evidence never promoted to FACT.
3. Write and execute **targeted** negative regression tests against active `generic_evidence_renderer.py`/orchestrator. Restore tests for uncovered invariant, not dead CRI behavior. No reintroduction of old assessors, classifier, new engine, or fake test evidence.
4. Confirm which of the ~1579 moved lines have live consumers, which are pure deterministic owned evidence rules vs presentation concern. Do not split artificially. If dead helper is unreferenced, remove with tests; if actual ownership demands different existing boundary, reuse that owner and smallest diff. No scope expansion into G3 without explicit dependency.
5. Run targeted tests, backend complete, architecture import checks, `rg` residuals, actual source/owner evidence negatives; produce exact commands/results and counts, SHA/config. No real E01–E10 falsely attributed to G2.
6. Correct G2 execution report requirement numbers, document proof and update ledger only after factual test evidence. Commit/push bounded corrections. Then G1 typed-output implementation can proceed independently.

**Review rationale:** physical removal achieved, but removed security/fidelity tests are not yet equivalently demonstrated; the net source relocation creates an architecture risk, requiring proof before G2 acceptance. Review state **REWORK** on that bounded residual, not rejection of the whole Pydantic AI direction.
