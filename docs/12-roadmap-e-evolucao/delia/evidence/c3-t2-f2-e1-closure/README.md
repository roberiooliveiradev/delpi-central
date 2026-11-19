# DÉLIA F2 — E1 Complete Verification & E2 Readiness

**TASK_ID:** `DELIA-C3-T2-F2-E1-COMPLETE-VERIFICATION-AND-NATIVE-PARITY-CLOSURE-01`
**EVALUATED_SHA / VERIFIED_SHA / FINAL_HEAD:** `ab2b2a2190826cfa71acf62fcebb6830813f2886`
**PYDANTIC_AI_VERSION:** `2.50.0` (delpi-delia-api container)
**MODE:** verification only — zero functional changes

## Test inventory

| Suite | Result |
|---|---|
| `test_f2_native_refactor_e1.py` (E1 baseline) | 21 PASS / **4 intentional RED fails** (P1 post-fix contract) |
| `test_f2_native_refactor_e1_closure.py` (new) | **33 PASS / 0 FAIL** |
| Full `delia-api/tests/` minus E1 file | **1923 PASS / 0 FAIL** (42.21s, container) |

## §15 — definitive answers

**1. Can we remove `_EnvelopeHintedToolset`? YES — `PREPARED_TOOLSET_PARITY=PASS`.**
Proofs: identical tool defs (name/description/schema, candidate_token + arguments +
anyOf hints); `prepared()` survives `for_run` rebinding (B3 defect class); inner
get_tools errors propagate (fail-closed discovery); prepare func cannot add/rename
tools (`UserError` — structural guarantee vs WRITE exposure).
E2 removal: class `:285-381`, `WrapperToolset` import if orphaned; consumers: Agent
assembly (~:1859); migrate tests `test_int1_tool_description_and_pagination_projection`,
`test_int1_g1_model_visible_surface_integrity` to assert on prepared() output.

**2. Can we remove `_TurnUsageCountingModel`? YES — `ACCOUNTING_EQUIVALENCE=PASS`,
`BUDGET_ENFORCEMENT_EQUIVALENCE=PASS` (counting path), `COUNTING_WRAPPER_REMOVABLE=YES`.**
8-case differential: single run, two shared runs, multi-request run (2 req), output
ModelRetry (2 req), exception-before-response (equal), **exception-after-response
(wrapper=1, native=1 — the documented gap is closed in 2.50.0)**, two-agent shared
turn usage, token fields. Native `run(usage=shared)` accumulates identically.
Not covered (recorded honestly): streaming usage, cancellation timing — both are
model-level request counting, orthogonal to the seam; `TurnDeadline` is Application
policy, unaffected either way.
E2 removal: class `:433-484` + `WrapperModel` import if orphaned + construction sites
(:3270 arm B, :3615 arm A) — replace with shared `RunUsage` passed via `run(usage=)`;
`deps.turn_usage` field stays as accumulator.

**3. P1 minimal fix — `P1_ROOT_CAUSE_PROVEN`, `P1_E2_FIX_CONTRACT_READY`.**
First divergent boundary: `pydantic_ai_investigation.py:2019-2032` cache-hit branch.
At cache-hit with prior failure: if `previous` error class ∈ transient set (reuse
`_listing_failure_is_transient` semantics — timeout/unavailable/transport/connection,
excluding denied/forbidden/unauthorized/authz) AND the fingerprint's retry flag is
unused → bypass cache once, set flag, reach owner. Terminal/authz/credential-expired/
unknown stay blocked; distinct args = distinct fingerprint; quota is per fingerprint
(per capability+args). ~25 LOC, one flag, no new retry manager.
Native insufficiency PROVEN behaviorally: failure-as-data → `ToolReturnPart` (no class,
`retries=` bounds nothing); raised `ModelRetry` → `RetryPromptPart` to model (model-
mediated), and a re-issued identical call would still hit the fingerprint cache —
the classification must live at the cache seam regardless.

**4. Remove `aggregate_paginated_pages`? `F7_REMOVE_LEGACY_SAFE` — `F7_CONTRACT_MATRIX` below.**

**5. What continues:** all KEEP_GOVERNED mechanisms — fingerprints/no-progress state
(the P1 extension modifies its classification, not its existence), one-shot flags,
`TurnDeadline`, `_bounded_json`, history authority filter, goal acceptor, sufficiency,
scope/filter contracts, listing transient retry, arms A/B.

**6. Legacy eliminated in E2:** `_EnvelopeHintedToolset`, `_TurnUsageCountingModel`,
`aggregate_paginated_pages` (+ its now-redundant test surface migrated to contract tests).

**7. Simplicity proofs:** 33-case closure suite + 8-case usage differential + F1 parity
test — all green against native seams; zero new abstractions introduced anywhere.

**8. Blockers to E2:** none technical. Verifier engines remain down (below).

## F7 contract matrix (18 cases — decisive)

| Case | `aggregate_paginated_pages` (legacy, unwired) | `_joint_collection_coverage` (wired :3886) | Verdict |
|---|---|---|---|
| single page == total | COMPLETE | abstains (≥2 needed; per-attempt oracle covers) | equivalent coverage |
| 2 / 3+ pages valid | COMPLETE | COMPLETE | equal |
| **109 control (40+40+29)** | COMPLETE | COMPLETE | equal ✓ |
| missing page | not complete | NOT_COMPLETE | equal |
| duplicate page/IDs | not complete | NOT_COMPLETE (dedup) | equal |
| **out-of-order pages (1,3,2, union=109)** | **NOT complete (missing_intermediate_page)** | **COMPLETE** | wired oracle *more correct*: set union==total is the authoritative question; order is not a business guarantee |
| empty intermediate / last page | complete | COMPLETE | equal |
| inconsistent totals | not complete | NOT_COMPLETE | equal |
| no-IDs records | n/a | dedup by content fingerprint, fail-closed | covered |
| scope change / capability change | n/a | no union | covered |
| failed page | n/a | excluded → NOT_COMPLETE | covered |
| unknown total / false completeness | not complete | NOT_COMPLETE | equal |
| has_more=true on last, union==total | complete | COMPLETE | equal |
| union > declared total | — | NOT_COMPLETE | covered |

Conclusion: the legacy oracle adds only **order-sensitivity + failure-reason labels** —
diagnostics no consumer reads. For the authoritative verdict (union of distinct records
== owner-declared total), the wired oracle is equivalent or stricter where it matters.
`extract_pagination_envelope`/`resolve_count_semantics` remain WIRED (orchestrator :130,
support :159, investigation :57/:1106) — only the aggregation oracle is removable.
E2 removal: function + `CountResolutionKind`/`UNKNOWN_TOTAL_MESSAGE` if orphaned by
aggregate removal (keep envelope/count resolution used by wired paths) + migrate
`test_r45_pagination_integrity_rework.py` asserts to the wired oracle or keep file
as envelope/aggregate contract tests minus removed function.

## P1 extended negatives (RQ-3) — all green

unknown failure code → blocked; success→identical → cached; 4× terminal → 1 owner call;
tool_calls_limit=2 → framework blocks before retry; plus E1's 5 controls.

## Residual search (RQ-5)

- `aggregate_paginated_pages`: zero app/ consumers (pycache only) — REMOVE candidate confirmed.
- `_EnvelopeHintedToolset`: 1 class, consumers = Agent assembly + 2 test files.
- `_TurnUsageCountingModel`: 1 class, consumers = 2 construction sites + 1 test import.
- No orphan wrappers/retry-loops/parallel counters found beyond E0's 17.
- `extract_pagination_envelope`, `resolve_count_semantics`: WIRED — keep.

## 17-function final classification (RQ-5/RQ-9)

REPLACE_NATIVE: F1 EnvelopeHintedToolset, F2 TurnUsageCountingModel.
REMOVE_LEGACY: aggregate_paginated_pages (contract-verdict redundant).
EXTEND_EXISTING: F6 P1 transient seam.
KEEP_GOVERNED: F3 fingerprints, F4 continuity flag, F5 insufficiency flag, F8 pagination
projection/hints, F9 bounded_json, F10 goal acceptor, F11 history authority, F12
TurnDeadline (+optional cancellation_token wiring — defer), F13 arms/flags, F14 listing
retry, F15 progress classifier, F16 sufficiency/eval, F17 scope/collection rules.
TO_INVENTORY: none remaining.

## E2 implementation packages

- **PKG-1 (smallest):** F6 P1 seam — `pydantic_ai_investigation.py` cache-hit branch +
  per-fingerprint retry flag; flips 4 REDs green; controls must stay green.
- **PKG-2:** `_EnvelopeHintedToolset` → `prepared()` at assembly; delete class; migrate
  hint logic to module-level `prepare_envelope_hints` func; update 2 test files.
- **PKG-3:** `_TurnUsageCountingModel` → `run(usage=deps.turn_usage)`; delete class;
  verify arm-A/arm-B accounting via u07-style test.
- **PKG-4:** remove `aggregate_paginated_pages` (+ orphans); migrate r45 asserts.

Rollback: each PKG = one pathspec-scoped commit; revert restores prior state.
STOP conditions: any control regression (authz/terminal/fingerprint distinction),
any falso-COMPLETE, parallel-path leftover.

## Verifier

Engines still unavailable (cursor quota resets 12/2; devin CLI unauthenticated) —
`INDEPENDENT_VERIFICATION=INCONCLUSIVE` recorded, never inferred as PASS.
