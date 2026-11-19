# DÉLIA F2 — E1 Final Parity & Contract Closure

**TASK_ID:** `DELIA-C3-T2-F2-E1-FINAL-PARITY-CONTRACT-AND-INDEPENDENT-VERIFICATION-01`
**EVALUATED_SHA / FINAL_HEAD:** `4be7b69485556452912be0318f9a96da05579d36` (= origin/main)
**PYDANTIC_AI_VERSION:** `2.50.0`
**TEST_FILE:** `delia-api/tests/test_f2_native_refactor_e1_final.py` (18 tests, all PASS)
**COMBINED E1 SURFACE:** 76 tests — 72 PASS + 4 intentional P1 REDs; full regression 1923 PASS

## Final verdicts

| Question | Verdict | Evidence |
|---|---|---|
| `_EnvelopeHintedToolset` → `prepared()` | `ENVELOPE_WRAPPER_REMOVAL=YES` | def parity + for_run survival + error propagation + fail-closed add + **MCPToolset stub parity** (this file) |
| `_TurnUsageCountingModel` removable? | `USAGE_WRAPPER_REMOVAL=YES` | 11 differential cases incl. **streaming complete/abandoned/mid-stream-error + task cancellation** — all equal |
| P1 contract ready? | `P1_E2_CONTRACT_READY=YES` | 4 REDs stable; 9 negatives/controls green; seam = fingerprint cache-hit only |
| `aggregate_paginated_pages` removal? | `F7_REMOVE_LEGACY_SAFE` | order permutations prove verdict is set-based; has_more contradictions fail closed; order check is diagnostics-only |
| Governed controls preserved? | YES | all KEEP_GOVERNED tests green |

## New parity evidence (this package)

### Streaming & cancellation (RQ-1)

| Case | Wrapper | Native `run(usage=)` | Parity |
|---|---|---|---|
| complete stream | 1 | 1 | ✓ |
| stream abandoned early | equal | equal | ✓ |
| stream raises mid-way | equal | equal | ✓ |
| task cancelled before response | 0 | 0 | ✓ (both count nothing — request never completed) |
| late-reported tokens | 42/7 in-out | 42/7 | ✓ |
| **double-counting hazard** | — | — | wrapper+usage= together counts 2× — E2 must swap atomically |

`ACCOUNTING_PARITY=PASS` `BUDGET_ENFORCEMENT_PARITY=PASS` `CANCELLATION_BEHAVIOR=PASS` `STREAMING_BEHAVIOR=PASS`

### Pagination order contract (RQ-2)

- Permutations 1→3→2, 3→2→1, 2→1→3 with union==total → wired oracle proves COMPLETE.
  The owner contracts carry no order invariant (page/offset envelope); the set question is
  authoritative. Legacy `missing_intermediate_page` on a reordered complete set = false
  negative, diagnostics-only.
- `has_more=true` + union==total → COMPLETE (data wins over envelope flag).
- `has_more` irrelevant when union < declared total → NOT_COMPLETE.
- Source-declared wrong total → union mismatch → NOT_COMPLETE (source metadata untrusted).
- Valid pages + failed attempt → excluded → NOT_COMPLETE (fail-closed).
- Overlapping pages dedup → union < total → NOT_COMPLETE.

`PAGINATION_ORDER_CONTRACT`: set-union is the authoritative completeness criterion —
confirmed by `_joint_collection_coverage` (:3886) which is the WIRED oracle; no canonical
contract found requiring sequential arrival.

## P1 contract terms (RQ-3, locked)

One identical re-invocation after transient failure; quota per fingerprint (capability+args);
no re-call after success; terminal/authz/credential/unknown never retried; seam = existing
fingerprint cache branch (`:2019-2032`); no new retry manager. Native insufficiency proven:
failure-as-data → `ToolReturnPart` (no class); raised `ModelRetry` → `RetryPromptPart` to model
but re-issued identical call still hits the same cache.

## E2 package matrix (RQ-7 — final order)

| PKG | Scope | In | Out | Stop conditions |
|---|---|---|---|---|
| 1 | `pydantic_ai_investigation.py` cache-hit branch + per-fingerprint retry flag (~25 LOC) | 4 REDs | 4 GREEN + all controls | any authz/terminal regression |
| 2 | `_EnvelopeHintedToolset` → `prepared(prepare_envelope_hints)`; delete class + orphan imports; migrate 2 test files | parity tests | identical defs via native seam | def divergence, for_run loss |
| 3 | `run(usage=deps.turn_usage)` at :3270/:3615; delete `_TurnUsageCountingModel` | u-differential | same counts, no double-count | count drift, dead RunUsage |
| 4 | remove `aggregate_paginated_pages` + orphans; migrate `test_r45_*` asserts to wired oracle | F7 matrix | all matrix green | any NOT_COMPLETE→COMPLETE flip |

Each PKG = one pathspec-scoped commit; revert = rollback. Residual search after each.

## Verifier

Engines unavailable all session (cursor quota until 12/2, devin CLI unauthenticated) —
`INDEPENDENT_VERIFICATION=INCONCLUSIVE`. No self-acceptance claimed; `E1_ACCEPTED` NOT
declared. Technical conclusions stand on test evidence; independent review pending.
