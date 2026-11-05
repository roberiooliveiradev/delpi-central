# 261 — DÉLIA · G4 fatia 1 review independente e handoff de implementação nativa

**DATA:** 2026-11-05  
**TASK_ID:** `DELIA-C3-G4-MODEL-INVOCATION-CONFIG-OBSERVABILITY-NATIVE-CONSOLIDATION-01`  
**BASE_HEAD:** `33db89196f7346edd2126d90d3299115dd45c3a0`  
**REVIEWED_SHA:** `b619dfe02f695cf53bda04c9aafcbfc40cc1cec1`  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` only for G3 R1–R3 closure; `G4_MAIN=NOT_IMPLEMENTED`; overall G4 `INCONCLUSIVE`.  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED; **E01–E10:** TEST_NOT_RUN.

## GitHub facts

- GitHub compare indicates one task commit, 4 changed files: `application/capability_provision/orchestration.py` (3 additions, 7 deletions), `tests/test_g1_native_structured_output.py` (12 additions, 2 deletions), `tests/test_turn_observability.py` (63 additions), and plan 256 update (14 additions). No main G4 code file modified.
- Current `test_turn_observability.py` has `test_projection_is_bounded_and_never_carries_payload` and `test_composition_elapsed_accumulates_honestly`; negative wire privacy, model-id bounds and elapsed breakdown again tested in source. Executor reports backend suite PASS; review did not independently rerun.
- G1 partial clarification test now asserts preservation of outcome/provenance/SourceRef via fixture as reported; tests are local deterministic fixtures, not an authoritative real owner call.
- The stale CRI comment was removed; no runtime CRI mode restored.
- Application retry policy exists `governed_retries.py` (`LLM_CALL_MAX_ATTEMPTS=3`); two real consumers: `handle_interactive_turn.py` ~1591 and `capability_provision/orchestration.py` ~5005. Native Agent `pydantic_ai_investigation.py` ~1091 has `retries=self._agent_retries`. Config loader `pydantic_ai_runtime_config.py` imports the old maximum and exposes `llm_call_max_attempts`. This proves multiple layers **exist**, not that their attempts multiply at runtime, which depends on actual callgraph. Avoid false diagnosis.
- `InvokeModel` still executes `apply_context_budget`; exact context-window enforcement may be distinct from SDK post-call usage. Do not eliminate purely because `UsageLimits` exists.

## Bounded main G4 execution (no repeated audit-only round)

**TASK_ID NEXT:** `DELIA-C3-G4-RETRY-CONTEXT-CONFIG-OBSERVABILITY-IMPLEMENTATION-01`.

Before coding: local HEAD/status/Project Instructions/.cursor → docs 16→50→17→49→51→52→21→20→25 → technical/product/thematic specs → ledger → 256/260/261. Identify live CP/RQ/owners, preserve concurrent WIP. `EXISTING_EQUIVALENT=YES` for native Agent, UsageLimits, retry, existing ports/contracts/JSON config; `REUSE_DECISION=REUSE/SHRINK` when parity verified; no speculative interface.

### Deliverable M1: retry paths

- Trace actual handlers/orchestrator to native Agent and `InvokeModel`; test whether retries nest, separate or are mutually exclusive. Count physical provider requests under timeout, invalid output, transient unavailable, cancellation and default/maximum configured attempts.
- If duplication is proven, eliminate only duplicate outer retry for the governed path; preserve legitimate policy/total budget/transport retries. No MCP/Domain material write retries, no repeated ACT. No multiplication of native/outer attempts. Ensure `llm_call_max_attempts` config and effective Agent retries reflect approved intent and hard ceilings, not silently deleted/relaxed.
- Diff must change active runtime code, tests and import/config consumers. If no duplicate exists, explicitly prove separation, mark this subtask KEEP with tests, and proceed with other M2/M3 diffs.

### Deliverable M2: context, actual token usage and observability

- Prove current Agent vs `InvokeModel` context-budget paths. Preserve pre-call admission/pruning of oversized mandatory input where no equivalent, label estimated vs measured. Do not report heuristic token count as SDK result.
- Prefer SDK actual usage for native Agent and align `ModelCallLedger`, `turn_observability.py`, NDJSON, response-mode and deadline handling. Do not allow raw prompt/credentials/COT/agent metadata to cross the wire.
- Validate timeout/cancel and no retry after deadline.

### Deliverable M3: JSON and dead code/config reduction

- One versioned non-secret config remains `delia-api/config/pydantic_ai.runtime.delpi.json`; security hard caps remain deterministic. Minimize redundant loader/validation and remove flags only after proving callers and deployment compatibility. `infrastructure/config/pydantic_ai_runtime_config.py` should not import an implementation constant from `application/model_invocation/governed_retries.py` unless legitimate explicit ownership; compare existing policy boundary.
- `ModelInvocationPort`, `InvokeModel`, C3-T4 `StructuredUnderstanding`, STT adapter and separate Core/Keycloak/MCP settings remain until consumer/contract parity proves any retirement.
- Reduce redundant code actually, do not transfer large helpers.

### Tests, gates, report

- RED→GREEN focused tests per real failure, full backend/architecture/security tests; token estimates vs SDK truth, config failure, privacy negative, pagination/owner SourceRefs, G1/G2 preservation, deadline, retries count.
- At least one real model local bounded evaluation when authorized, otherwise `TEST_NOT_RUN`; E01–E10 formally G7. Record exact SHA/model/JSON hash, source and task outcome, not HTTP200 only.
- RQ-11..15 individual statuses (`IMPLEMENTED|PARTIAL|NOT_IMPLEMENTED|BLOCKED`); partial credit=0. Source LOC before/after, removed symbols and consumers, test evidence, residual search, docs+ledger after verified outcome, commit/push, no production deploy.
- If a subtask proves no eliminable redundancy, say KEEP and move forward; avoid infinite inventory loops or false LOC target.

**Review:** G3 residuals accepted with caveat that integration/real-owner continuity remains G7. G4 main not implemented; no false claim of G4 PASS or of real-model generalization.
