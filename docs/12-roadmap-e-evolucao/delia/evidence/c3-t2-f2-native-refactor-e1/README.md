# DÉLIA C3/T2 — F2 Native Refactor — E1 RED & Equivalence Evidence

**TASK_ID:** `DELIA-C3-T2-F2-NATIVE-REFACTOR-E1-RED-AND-EQUIVALENCE-GATE-01`
**MODE:** TEST_FIRST — zero runtime changes; tests + evidence only.
**BASE_HEAD:** `f9f5fc9b26b524073933c3277953cb4ac395f14f`
**PYDANTIC_AI_VERSION:** `2.50.0` (verified in `delpi-delia-api` container)
**TEST_FILE:** `delia-api/tests/test_f2_native_refactor_e1.py` (25 tests)
**SUITE_RESULT:** 21 PASS / 4 FAIL — the 4 failures are the intended P1 REDs
**REGRESSION_CONTROLS:** 82 PASS / 0 FAIL (progress, r45 pagination, tool-description,
owner-loop, provider-boundary, g1-surface suites)

---

## 1. Native behavior matrix (RQ-1) — behaviorally proven, not signatures

| Probe | Result |
|---|---|
| `prepared()` transforms ToolDefinitions per run; `UserError` if tool added/renamed | NATIVE_API_BEHAVIOR_PROVEN |
| `run_sync(usage=usage)` mutates the passed `RunUsage` — cross-run accumulation | NATIVE_API_BEHAVIOR_PROVEN |
| `UsageLimits(tool_calls_limit=1)` → `UsageLimitExceeded` before 2nd tool call | NATIVE_API_BEHAVIOR_PROVEN |
| Tool-raised `ModelRetry` → `RetryPromptPart` to the **model** (model-mediated retry bounded by `retries`), NOT mechanical re-invocation | NATIVE_API_BEHAVIOR_PROVEN |
| Failure **as data** (normal tool return) → plain `ToolReturnPart`, framework carries no failure class, `retries` bounds nothing | NATIVE_API_BEHAVIOR_PROVEN |
| `run(usage=)` captures a completed provider request even when the run dies afterwards (output_validator exception) | NATIVE_API_BEHAVIOR_PROVEN — **the F2 gap is closed in 2.50.0** |

## 2. P1 — transient invoke retry block (RQ-2)

**P1_FIRST_DIVERGENT_BOUNDARY:** `pydantic_ai_investigation.py:2019-2032` — identical
fingerprint + prior failure → `repeated_equivalent_failure` projection; owner never re-invoked.
RED evidence (spy on `gates._governed_semantic_tool_invoke` counting real owner calls):

| Test | Expected (post-fix) | Today | Status |
|---|---|---|---|
| transient → identical retry reaches owner once | 2 calls | 1 | **RED** |
| transient ×3 → at most 2 owner calls (bounded) | 2 | 1 | **RED** |
| transient → success → 3rd call from cache | 2 | 1 | **RED** |
| retry quota per capability (A+A, B+B) | 4 | 2 | **RED** |
| terminal `arguments_schema_rejected` → no re-invocation | 1 | 1 | CONTROL ✓ |
| `authz_denied` → no re-invocation | 1 | 1 | CONTROL ✓ |
| `credential_expired` → not transient, blocked | 1 | 1 | CONTROL ✓ |
| distinct args → distinct fingerprint | 2 | 2 | CONTROL ✓ |
| `_listing_failure_is_transient` semantics | — | — | CONTROL ✓ |

**Design proof (native seam insufficient):** the governed invoke reports failure *as data*.
Native retry paths either need a raised `ModelRetry` (→ `RetryPromptPart` to model) or are
bound by `retries=` — but a raised retry would re-enter the fingerprint check that blocks
the owner call anyway. The transient classification must act at the cache-hit branch:
EXTEND_EXISTING, reusing `_listing_failure_is_transient` semantics (timeout/unavailable/
transport/connection; denied/forbidden/unauthorized/authz excluded), one-shot per
fingerprint per capability. No new retry manager.

## 3. F1 — PreparedToolset parity (RQ-3) — **CONTRACT_EQUIVALENCE_PROVEN**

`test_f1_prepared_toolset_reproduces_envelope_hints`: identical tool definitions
(name + description + parameters_json_schema) produced by `_EnvelopeHintedToolset` and by
`inner.prepared(prepare_fn)` running the same schema-derived hint logic — including
`candidate_token`, `arguments`-object and nullable-object (`anyOf`) hints.
`PreparedToolset` is a `WrapperToolset` → `for_run`/`for_run_step` rebinding preserved.
E2 destination: replace class with `toolset.prepared(...)`, keep hint logic as prepare func.

## 4. F2 — usage accounting (RQ-4) — **ACCOUNTING_EQUIVALENCE_PROVEN**

| Path | Successful runs | Completed-request-then-run-dies |
|---|---|---|
| `_TurnUsageCountingModel` | counts | counts (1) |
| `run(usage=)` shared RunUsage | accumulates (2 runs = 2) | **counts (1)** — gap closed in 2.50.0 |

BUDGET_ENFORCEMENT_EQUIVALENCE: `UsageLimits` remains per-run; the Application-level
subtractive `TurnDeadline` is policy, not replaceable — but the counting wrapper's sole
documented justification (exception-path usage loss) no longer holds in 2.50.0.
E2 destination: REMOVE `_TurnUsageCountingModel` — pass a shared `RunUsage` via `run(usage=)`
at both arm-A and arm-B call sites; keep `turn_usage` field as the accumulator.

## 5. F7 — pagination completeness (RQ-5) — **wired oracle already covers the matrix**

`_joint_collection_coverage` (semantic_capability_support.py:3886) — invoked at :4023 inside
obligation evaluation — groups by owner+capability+scope, dedups records, requires
union == declared total:

| Scenario | Result |
|---|---|
| 40+40+29, total=109, same scope (R5 control) | COMPLETE ✓ |
| missing page (40+40 of 109) | not complete ✓ |
| duplicated page (dedup → union < total) | not complete ✓ |
| inconsistent totals (109/110) | not complete ✓ |
| different governed scopes | no union ✓ |
| single attempt == total | joint oracle abstains (≥2 candidates) — per-attempt oracle covers |

**F7 conclusion:** `aggregate_paginated_pages` is REDUNDANT with the wired oracle for the
completeness verdict; its marginal value is page-sequence diagnostics only. E2 decision
refines to: REMOVE (with contract tests preserved via `_joint_collection_coverage` +
`extract_pagination_envelope`) or keep as diagnostics helper — recommendation: REMOVE_LEGACY
candidate, since "tested but unwired" is the definition of a parallel mechanism.

## 6. E2 removal table (RQ-9)

| Function | Substitute | Equivalence | Tests | E2 decision |
|---|---|---|---|---|
| `_EnvelopeHintedToolset` | `toolset.prepared(prepare_fn)` | CONTRACT_EQUIVALENCE_PROVEN | parity green | **REMOVE class** |
| `_TurnUsageCountingModel` | `run(usage=shared)` | ACCOUNTING_EQUIVALENCE_PROVEN | parity green | **REMOVE class** |
| `non_progress_calls` (invoke seam) | EXTEND: transient-class check at cache-hit + one-shot flag | native retry can't express (failure-as-data) | 4 REDs to flip | **EXTEND** |
| `aggregate_paginated_pages` | `_joint_collection_coverage` (wired) | coverage-equivalent for verdict | matrix green | **REMOVE candidate** (Coordination confirms) |
| `insufficiency_retry_used` shared flag | keep (business policy) | — | controls green | KEEP (optional per-gate flags, defer) |
| `TurnDeadline`, AuthZ, acceptor, sufficiency, scope/filters | — | governed, no equivalent | controls green | KEEP_GOVERNED |

## 7. Generalization preparation (RQ-8, holdouts for E3)

Prepared in-suite: two capabilities (`alpha.search_items`, `beta.read_guidance`), transient×2,
terminal, authz, credential-expiry, distinct-args, scope-variant pages, inconsistent totals.
Live LLM evals: not run (cost/credentials — reserved for E3 with authorization).

## 8. Verifier status

delpi-verifier engines remain unavailable this cycle (cursor quota until 12/2, devin CLI
unauthenticated) — same blocker as F2-diagnostic and E0 cycles. Recorded as INCONCLUSIVE /
engine-blocked; no acceptance claimed.

## 9. Traceability

- E0 package: `evidence/c3-t2-f2-native-refactor-e0/README.md` (17-mechanism matrix — E1
  revalidated all cited mechanisms at `f9f5fc9b26`; line anchors unchanged).
- E0 verifier INCONCLUSIVE still pending — E1 results do not retro-accept E0.
- F1 baseline: untouched (comprehension-v4, acceptor, INVALID_GOAL, 109-control green).
