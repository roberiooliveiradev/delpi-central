# C3/T2 — Framework-first cleanup — evidence

TASK: DELIA-C3-T2-FRAMEWORK-FIRST-NATIVE-ARCHITECTURE-CLEANUP-E2E-01
BASE_HEAD: c1d904b8cc — PHASE: C3/T2 (sem avanço)
PYDANTIC_AI: 2.50.0 · MCP SDK: 2.3.0 · PYDANTIC: 2.14.1

## RQ-1/RQ-3/RQ-5 — Inventory result (bounded sweep)

| Symbol/area | Classification | Evidence |
|---|---|---|
| `pydantic_ai_investigation.py` Agent lifecycle | KEEP | native `Agent`/`run` + governed composition (doc 291 migration done) |
| `MCPToolset` + `process_tool_call` | KEEP | single dispatch path; governance intercept preserved |
| `FunctionToolset` (investigation locals) | KEEP | native |
| `_EnvelopeHintedToolset(WrapperToolset)` | KEEP | native WrapperToolset subclass; envelope-hint contract, no parallel dispatch |
| `ModelRetry` surfaces (owner_arg, insufficiency, evidence_ref, no-progress) | KEEP | all decisions raise native `ModelRetry`; Application decides admissibility (business gate), framework executes retry |
| `_TurnUsageCountingModel` | KEEP | complements `UsageLimits` on exception paths — proven complement, not duplicate enforcement |
| Top-level private defs, orchestrator | KEEP | 0 dead (grep across app/tests/scripts) |
| `governed_capability_orchestrator.py` privates | KEEP | 0 dead |
| `semantic_capability_support.py` privates | 1 REMOVE | `_presentation_source_allows_aggregation` — zero consumers; INT3 refactor leftover; docstring redirected to `_presentation_evidence_source` |
| `application/model_invocation/*` | KEEP | `call_retry_eligible` = business admissibility gate (not retry loop); `invoke_model` = port-facing invoker; real consumers |
| `application/ports/*` | KEEP | thin ports with real boundaries and consumers |

PARALLEL_ENGINE=NO · PARALLEL_PLANNER=NO · PARALLEL_TOOL_REGISTRY=NO · PARALLEL_DISPATCH=NO

## RQ-4 — Empty-container canonicalization review (flagged)

FINDING: `_drop_empty_scope_containers` (delivered c1d904b8cc) dropped ANY
empty Mapping at ANY depth — over-broad: equivalence "empty ≡ absent" was
claimed without contract for non-carrier names and nested objects.

CONTRACT BOUND: only the published filter-carrier names
(`_SCOPE_CONTAINER_ALIASES`: `params`, `arguments`) may normalize
empty ≡ absent — live-proven on TÉO (params:{} returned unfiltered
window, INT2_A/R5). Unknown containers (`meta`, `filter`, `q`,
`pagination`) and nested empties (`params.filters:{}`) keep presence
semantics → stay material → fail-closed (task matrix C04/T17/T18).

CHANGES (bounded):
- `_strip_window_args`: no longer drops emptied containers (strips only
  proven selector keys, depth<2 — unchanged).
- `_drop_empty_scope_containers`: top-level-only, carrier names only.
- `_EMPTY_EQUIVALENT_CONTAINER_KEYS`: derived from
  `_SCOPE_CONTAINER_ALIASES` (single source).
- Declared side unchanged semantics: `{params:{page:2}}` →
  `__container__=params` (exact-domain; discarding it would over-permit).
- REMOVED `_presentation_source_allows_aggregation` (dead wrapper).

## Tests

RED baseline for restriction: c03(pagination)/c05(filter)/c07(meta)
relied on over-broad drop → updated to contract expectations:
- carrier containers empty ≡ absent (c03/c05/c07 pass);
- unknown envelopes stay separate (new test_c04, test_c07c);
- declared `{params:{page:2}}` → marker + `params` domain empty proven
  via `_required_scope_state` ok/unproven (rewritten test).

GREEN: continuity suite 19/19; sufficiency/collection/anchor suites pass.
Full delia-api regression: 100% exit 0 (same deprecation warning).
Audits: Phase3 OK · platform guardrails findings 0.

## REAL_EVAL classification

Code delta vs c1d904b8cc live-proven variant: (a) dead-symbol removal —
no behavior; (b) restriction affects ONLY non-carrier empty containers —
no scenario in INT1×14/INT2×15/targeted A-E-R5-G2 exercised non-carrier
envelopes (all used `params`/top-level) → parity holds on the exercised
surface. Fresh full A/B: TEST_NOT_RUN (bounded); restriction delta
covered by unit T17/T18 equivalents (c04/c07c). Prior live evidence at
c1d904b8cc remains the authoritative live proof for carrier envelopes:
A=SATISFIED(109), R5=SATISFIED(109), G=SATISFIED, E=honest INCONCLUSIVE
(material filter divergence correctly not united).

SAFETY counters (unit + prior live): FALSE_SATISFIED=0 FALSE_COMPLETE=0
CROSS_OWNER=0 FILTER_DRIFT=0 AUTHZ_BYPASS=0 WRITES=0.
