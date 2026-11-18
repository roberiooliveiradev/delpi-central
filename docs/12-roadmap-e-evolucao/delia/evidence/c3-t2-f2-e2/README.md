# C3/T2 — F2/E2 Native-First Implementation & Legacy Elimination

**TASK_ID:** `DELIA-C3-T2-F2-E2-NATIVE-PYDANTIC-AI-IMPLEMENTATION-AND-LEGACY-ELIMINATION-01`
**BASE:** `45884cc4` (re-anchored; foreign WIP preserved)
**PYDANTIC_AI:** `2.50.0`
**MODE:** IMPLEMENTATION / RED_GREEN / LEGACY_REMOVAL

## PKG-1 — P1 transient retry at the fingerprint cache-hit seam

**File:** `delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py`

- New `InvestigationDeps.transient_invoke_retries: set[str]` — per-fingerprint
  one-shot retry budget (capability + full args fingerprint), not a global flag.
- Cache-hit branch: a cached projection is short-circuited UNLESS it carries an
  `error_code` classified transient by the EXISTING `_listing_failure_is_transient`
  (timeout/unavailable/transport/connection) AND the fingerprint has not yet
  consumed its slot. On bypass the slot is consumed — second identical
  transient failure fails closed through the original path.
- Terminal, AUTHZ_DENIED, credential, unknown failures and prior SUCCESS
  (no `error_code`) can never re-invoke. Different args = different
  fingerprint = normal invoke.
- Result: 4 RED → GREEN; 5 negative controls green.

## PKG-2 — `_EnvelopeHintedToolset` → native `prepared()`

- Deleted `class _EnvelopeHintedToolset(WrapperToolset)` (~96 lines).
- New module-level `_prepare_tool_definitions_envelope_hints(ctx, tool_defs)`
  + `_tool_prop_declares_object` — identical schema-derived hint strings,
  identical nullable-`anyOf` object detection, identical 280-char bound and
  full owner-description preservation.
- Call site: `ts.visit_and_replace(lambda leaf: _EnvelopeHintedToolset(leaf))`
  → `ts.prepared(_prepare_tool_definitions_envelope_hints)`.
- `PreparedToolset` participates in `for_run`/`for_run_step` rebinding
  natively (the property the custom class had to guarantee by hand).
- Dropped `WrapperToolset` import.

## PKG-3 — `_TurnUsageCountingModel` → native `run(usage=)`

- Deleted `class _TurnUsageCountingModel(WrapperModel)` (~52 lines) and the
  `WrapperModel`/`asynccontextmanager` imports.
- `run_model = model` (unwrapped); both run sites — investigation (arm B)
  and comprehension (arm A, two-agent experimental) — now pass
  `usage=turn_usage` into `agent.run_sync`, accumulating into the same
  shared `RunUsage` the turn budget already reads.
- Atomic swap: no state where wrapper + `usage=` coexist (the E1-pinned
  double-count hazard). `TurnDeadline`/`UsageLimits` unchanged.

## PKG-4 — `aggregate_paginated_pages` removed

- Deleted `aggregate_paginated_pages` (~190 lines), `PageAggregationResult`,
  `item_stable_id`, `DEFAULT_MAX_PAGES`, `_ID_KEYS`, and the
  `aggregation:` param + dead branch of `resolve_count_semantics`
  (its only producer was the removed oracle).
- Preserved wired helpers: `extract_pagination_envelope`,
  `PaginationEnvelope`, `resolve_count_semantics` (envelope path),
  `CountResolution*`, `UNKNOWN_TOTAL_MESSAGE`, `_is_first_page`.
- Authoritative evaluator unchanged: `_joint_collection_coverage`
  (record-union == single declared total) in
  `semantic_capability_support.py`.
- Migrated `test_r45_*`, R5 negatives in
  `test_c3_t2_evidence_closure_negatives.py`, and G2 aggregation tests to
  the wired contract — same completeness guarantees asserted.

## Verification

- P1 harness (`_p1_engine`): real orchestrator + FunctionModel drives the
  full loop — goal declaration → governed invoke → transient failure →
  identical re-invocation reaches the owner again → success. 9/9 pass.
- Migrated suites: e1 (25) + closure (33) + final (18) + r45 (19) +
  int1/c3/g2 — all green.
- Full `delia-api` regression: 100% progress dots, **0 FAILED / 0 ERROR**
  (~1980 tests) on the post-change tree.
- Residual: zero executable references to any removed symbol.
- REAL_MODEL_OUTCOME: TEST_NOT_RUN (no live model/owner in this env;
  deterministic E2E used per RQ-8 fallback).
- INDEPENDENT_VERIFICATION: **INCONCLUSIVE** — verifier r1 attempted;
  engine unavailable (`devin` CLI unauthenticated). Request preserved
  at `.git/delpi-verifier/requests/f2-e2-native-implementation-r1.md`.
  No acceptance inferred; publication gate requires a later verifier
  round or explicit Coordination decision.
