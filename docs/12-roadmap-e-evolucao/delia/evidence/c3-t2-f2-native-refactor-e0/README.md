# DÉLIA C3/T2 — F2 Native Pydantic AI Refactor — E0 Inventory & Substitution Plan

**TASK_ID:** `DELIA-C3-T2-F2-NATIVE-PYDANTIC-AI-INVESTIGATION-REFACTOR-AND-LEGACY-ELIMINATION-01`
**MODE:** E0 only — INVENTORY → CONTRACT_GATE. E1–E4 blocked until Coordination approves this package.
**BASE_HEAD:** `970e2bd691c4d4b9448a9cdfb265ca34986fc2c0`
**ORIGIN_MAIN (at writing):** `2c6e8570669a994c8f868b7c605db37cb1173874`
**PYDANTIC_AI_VERSION:** `2.50.0` (verified inside `delpi-delia-api` container via `pydantic_ai.__version__`)
**PHASE_FROM_16:** C3/T2 — `C3_EXECUTED=NO`; `PHASE_ADVANCEMENT=NO`
**PRIOR_PACKAGE:** `docs/12-roadmap-e-evolucao/delia/evidence/c3-t2-f2-int1-diagnostic/README.md` (F2 diagnostic, P1–P5)

No runtime code is changed by this package. All classifications cite the installed-version API surface
(introspected on `pydantic_ai 2.50.0` in-container), not the latest public docs.

---

## 1. Verified native API surface (pydantic_ai 2.50.0)

| Native feature | Verified how | Relevant to |
|---|---|---|
| `Agent(retries=, tool_timeout=, end_strategy=, max_concurrency=)` | `inspect.signature(Agent.__init__)` | tool retry count, per-tool timeouts |
| `Agent.tool(retries=, timeout=, sequential=, requires_approval=, prepare=, defer_loading=)` | `inspect.signature(Agent.tool)` | per-tool retry/timeout/approval |
| `UsageLimits(request_limit, tool_calls_limit, input/output/total_tokens_limit, cost_limit, count_tokens_before_request, per_request_input_tokens_limit)` | `UsageLimits.__dataclass_fields__` | budget |
| `Agent.run(..., usage_limits=, usage=, message_history=, retries=, cancellation_token=, deferred_tool_results=)` | `inspect.signature(Agent.run)` | cross-run usage accumulation, native cancellation |
| `ModelRetry`, `RetryPromptPart`, `UsageLimitExceeded`, `AgentRetries` | `dir(pydantic_ai)` | governed feedback + retry accounting |
| `PreparedToolset` / `toolset.prepared(prepare_func)` — wraps a toolset, transforms `ToolDefinition`s per run (cannot add/rename tools; enforced by `UserError`) | `prepared.py` source in installed package | **exact functional equivalent of `_EnvelopeHintedToolset`** |
| Toolset wrappers: `filtered`, `renamed`, `prefixed`, `approval_required`, `apply`, `for_run`, `prepared`, `with_metadata` | `AbstractToolset` methods | governed tool surface |
| `_history_processor` | `dir(pydantic_ai)` | history trimming seam (not a replacement for tool-result projection) |

**Not present natively (verified):** no identical-call deduplication, no no-progress classifier,
no pagination envelope semantics, no material-obligation evaluation, no cross-run *request-budget*
ledger (UsageLimits is per-run; `usage=` param accepts accumulation, not limits).

## 2. Current architecture map (RQ-1)

```
turn (Application, TurnDeadline :turn_budget.py:31)
 └─ run_investigation (pydantic_ai_investigation.py — arm A comprehension [flag] → arm B investigation)
     └─ Pydantic AI Agent (model=openrouter_kimi, UsageLimits(12 req/8 tools) :3270)
         ├─ _TurnUsageCountingModel (WrapperModel :433)          ← intercepts model calls
         ├─ _EnvelopeHintedToolset (WrapperToolset :285)         ← intercepts tool defs
         │     └─ governed invoke_capability tool
         │           ├─ _invocation_fingerprint + non_progress_calls (:1403/:2019/:406)  ← pre-owner cache/short-circuit
         │           ├─ observed_content_fingerprints (:411/:2083)                        ← repeat-content guard
         │           ├─ continuity_model_retry_allowed + no_progress_continuity_retry_used (:500/:2132/:426)
         │           └─ governed_capability_orchestrator → provider/MCP → Domain
         │                 └─ _listing_failure_is_transient retry ONE listing only (orchestrator :1607)
         ├─ declare_investigation_goal tool (:2233) + plan acceptor
         ├─ insufficiency_retry_used shared flag — 5 ModelRetry gates (:2924-3050)
         └─ finalize: _finalize_agent_collected_attempts (semantic_capability_support.py:4508)
               └─ Sufficiency / Evidence / Outcome (aggregate_paginated_pages UNWIRED — P2)
```

Deterministic vs model-decided: all of the above except LLM output are Application-owned. The model
decides which calls to make; Application decides whether they run, count, retry or stop.

## 3. Native-equivalence decision matrix (§6)

| # | Function / mechanism | File:line | Real responsibility | Consumers | Native equivalent (2.50.0, verified) | Classification | Reuse | Destination |
|---|---|---|---|---|---|---|---|---|
| F1 | `_EnvelopeHintedToolset` | pydantic_ai_investigation.py:285 | injects envelope/pagination hints into tool defs | Agent assembly (~:1859); tests `test_int1_tool_description_and_pagination_projection`, `test_int1_g1_model_visible_surface_integrity` | `PreparedToolset` / `.prepared(prepare_func)` — same seam, same semantics, `UserError` if tools added/renamed | **REPLACE_NATIVE** | REUSE→remove | replace class with `toolset.prepared()` call; keep hint function as the prepare callback |
| F2 | `_TurnUsageCountingModel` | :433 | accumulates usage across runs in one turn (cross-leg budget) | model construction (~:3270 arm B, :3615 arm A) | `Agent.run(usage=)` accepts accumulating `Usage`; UsageLimits still per-run | **EXTEND_EXISTING → TO_INVENTORY** | verify parity: counting `requests` inside wrapper vs passing `usage` accumulator; if parity holds, REMOVE wrapper | candidate removal pending parity RED test |
| F3 | `non_progress_calls` + `_invocation_fingerprint` + `observed_content_fingerprints` | :406/:1403/:2019/:411/:2083 | deterministic no-progress / identical-call suppression (budget safety) | invoke_capability tool body; progress tests | **none** (no native dedup) | **KEEP_GOVERNED + EXTEND_EXISTING (P1)** | EXTEND | keep; add transient-failure one-shot seam (F6) |
| F4 | `continuity_model_retry_allowed` + `no_progress_continuity_retry_used` | :500/:2132/:426 | single governed continuity retry via ModelRetry | tool body | `ModelRetry` native — flag is Application budget policy, not duplicated machinery | **KEEP_GOVERNED** | REUSE | unchanged |
| F5 | `insufficiency_retry_used` shared by 5 gates | :415/:2924/:2951/:2978/:2994/:3029 | one recovery pass across sufficiency/goal gates | tool body | native `output_retries`/ModelRetry bound count — but per-class semantics are business policy | **KEEP_GOVERNED; consolidation candidate EXTEND_EXISTING** (P5 diagnostic: no proven loss) | REUSE | optional simplify: per-gate named flags or single ledger fn; not required for correctness |
| F6 | transient invoke retry (P1 from F2 diagnostic) | gap at :2019-2032 cache-hit branch | transient owner failure is permanently blocked by fingerprint cache | invoke path | tool `retries=` only fires on raised exceptions; governed invoke returns failure as data → native retry cannot express it without raising | **EXTEND_EXISTING** | EXTEND | at cache-hit: if `previous` error_class ∈ transient set (reuse `_listing_failure_is_transient` semantics) and retry flag unused → bypass cache once, then fail-closed |
| F7 | `aggregate_paginated_pages` | generic_evidence_renderer.py (~:1300s region); zero app consumers (F2 P2, PROVEN) | integrity-checked multipage merge oracle | tests only | none — Evidence contract | **EXTEND_EXISTING (wire) or REMOVE_LEGACY** | decision required: wire into `_finalize_agent_collected_attempts` (semantic_capability_support.py:4508) for multipage verdicts, OR remove if verdicts stay per-attempt | CONTRACT_DECISION_REQUIRED |
| F8 | pagination projection / `next_page` hint / `continuation_note` / `extract_pagination_envelope` | :1118/:1130 region; generic_evidence_renderer.py:1304 | contract-surface continuity guidance (page/offset only; no cursor) | tool projection; orchestrator | none (contract semantics) | **KEEP_GOVERNED** | REUSE | unchanged |
| F9 | `_bounded_json` + `_BOUNDED_ESSENTIAL_KEYS` | :530/:559 | model-facing payload budget | projections, comprehension block :823/:827 | `_history_processor` trims message history — different seam (post-hoc vs per-call projection); not a replacement | **KEEP_GOVERNED** | REUSE | unchanged |
| F10 | `declare_investigation_goal` + plan acceptor + `MaterialObligation` | :2233/:267 | governed plan declaration (F1) | Agent tool | none — DÉLIA contract | **KEEP_GOVERNED** | REUSE | unchanged (F1 baseline) |
| F11 | `_prior_message_history` + `_prior_turn_is_user_authorized` | :1444 | history selection under authority rules (multi-turn) | :3084 | `message_history=` param native; authority-filtered selection is policy | **KEEP_GOVERNED** | REUSE | unchanged (could later express via history processor — not required) |
| F12 | `TurnDeadline` + `stage_timeout` + `PROCESSING_TIMEOUT` | turn_budget.py:31; orchestrator (25+ sites) | subtractive turn budget, stage timeouts | orchestrator, investigation | `tool_timeout`, `cancellation_token` native — complements, doesn't replace Application deadline | **KEEP_GOVERNED; EXTEND candidate** to wire `cancellation_token` to TurnDeadline (parity RED test first) | REUSE | optional E2 item |
| F13 | `run_investigation` arms A/B, flag gating | :1704-1900s, :3518+ | turn orchestration, experimental two-agent OFF | composition root | none — Application policy | **KEEP_GOVERNED** | REUSE | unchanged |
| F14 | listing transient retry (one retry) | governed_capability_orchestrator.py:1607 + `_listing_failure_is_transient` support.py:5838 | bounded transient retry for capability listing | listing path | none at this seam (pre-agent) | **KEEP_GOVERNED** | REUSE | unchanged; semantics reused by F6 |
| F15 | `classify_investigation_progress` (NEW/RELATED/NONE/DISCOVERY) | semantic_capability_support.py:~2092 region | deterministic progress classification | tool body / tests | none | **KEEP_GOVERNED** | REUSE | unchanged |
| F16 | `_normalize_obligation_tuple`, `_evaluate_material_obligations`, evidence-ref gates | support.py; used :3030-3068 | deterministic Sufficiency | finalize + unmet-obligation ModelRetry | none — domain evidence contract | **KEEP_GOVERNED** | REUSE | unchanged |
| F17 | `_schema_pagination_arg_names`, scope normalization, collection integrity rules | support.py | argument/evidence contracts | orchestrator | none | **KEEP_GOVERNED** | REUSE | unchanged |

### REMOVE_LEGACY candidates (none proven yet)

- `aggregate_paginated_pages` — dead **only if** the contract decision keeps per-attempt verdicts;
  preferred direction per F2 P2 is wiring, not removal.
- `_TurnUsageCountingModel` — removable **only after** parity proof that `run(usage=)` accounting
  preserves identical counting (requests + tokens across both arms). Until proven: KEEP.
- `_EnvelopeHintedToolset` — removed as part of F1 replacement once parity tests pass.
- Residual search for unused helpers/imports is an E2 step, not asserted here.

## 4. P1 transient-retry design (RQ-2) — recommended bounded fix

Current: identical fingerprint + prior failure → `repeated_equivalent_failure` projection,
owner never re-invoked (:2019-2032). Only terminal-class failure is tested (`arguments_schema_rejected`).

Design (EXTEND_EXISTING, ~25 LOC + flag):

1. At the cache-hit branch, before short-circuit: if `previous["outcome"]` is failure and
   `previous` error class ∈ transient set (`timeout`, `unavailable`, `transport`, `connection` —
   same set as `_listing_failure_is_transient` :5838) and `transient_invoke_retry_used` is False:
   clear flag usage → set flag → proceed to owner call (do NOT return cached projection).
2. Terminal (`arguments_schema_rejected`, validation) and AUTHZ (`denied`, `forbidden`,
   `unauthorized`, `authz*`) classes remain non-retriable — unchanged.
3. Distinct args produce a distinct fingerprint — unchanged behavior.
4. Second identical call after the single retry → normal cache-hit (fail-closed).

Why not native `retries=`/`ModelRetry`: the governed invoke returns failure **as data**;
raising inside the tool would re-enter the fingerprint check which still blocks the owner call —
the fingerprint must learn the transient classification regardless. The one-flag extension is the
minimal governed change; no new retry manager (per §8 STOP conditions).

## 5. F7 contract decision (RQ-4) — question for Coordination

`aggregate_paginated_pages` is a tested oracle with zero app consumers (F2 P2). Options:

- **(a) WIRE:** `_finalize_agent_collected_attempts` calls it when a declared-collection goal has ≥2
  page attempts → multipage COMPLETE requires integrity-checked merge (continuity, dup IDs, totals).
  Preserves 40+40+29=109 proven behavior; LLM never computes completeness.
- **(b) REMOVE:** keep per-attempt verdicts; delete oracle + its 22-assert test surface, replace with
  contract tests on finalize.
- Recommendation: **(a)** — the diagnostic showed multipage verdicts currently rely on un-checked
  aggregation; the oracle is the only integrity-checked merge in the codebase.

## 6. Target architecture map (post-E2, if E0 approved)

```
turn (Application, TurnDeadline)
 └─ run_investigation — unchanged
     └─ Agent (native)
         ├─ model: plain (usage accumulated via run(usage=) — if parity proven; else wrapper stays)
         ├─ toolsets: FunctionToolset.prepared(envelope_hint_prepare) — native seam
         ├─ invoke_capability
         │     ├─ fingerprint cache + transient-retry one-shot (F6)   ← governed, extended
         │     ├─ content fingerprints — unchanged
         │     └─ governed orchestrator → provider → Domain          ← unchanged
         ├─ declare_investigation_goal — unchanged
         └─ finalize → Sufficiency/Evidence (+ aggregate_paginated_pages wired, if F7a approved)
```

Net removals if E0 approved: `_EnvelopeHintedToolset` class (~-40 LOC), `_TurnUsageCountingModel`
(if parity proven, ~-30 LOC), zero new abstractions introduced.

## 7. RED test plan (E1 — after gate)

| Test | Defect covered |
|---|---|
| transient invoke failure → identical re-invocation reaches owner once | P1 positive |
| transient ×2 → second blocked (retry exhausted) | P1 bounded |
| `arguments_schema_rejected` → zero re-invocation | P1 terminal (exists :776 — keep) |
| AUTHZ denied → zero re-invocation | AC-8 |
| distinct args → not blocked | regression |
| envelope hints present with `prepared()` toolset | F1 parity |
| usage counting parity: wrapper vs `run(usage=)` | F2 gate for removal |
| multipage merge integrity via `aggregate_paginated_pages` (if F7a) | RQ-4 |
| 1/2/3+ pages, empty page, duplicate page, inconsistent total | RQ-9 negatives |
| insufficiency one-shot still bounds all 5 gates | F5 regression |
| 109-record control scenario | baseline preservation |

## 8. Rollback plan

Each E2 item lands as a separate pathspec-scoped commit: revert-by-commit restores prior state.
F1 flag semantics, acceptor, instructions unchanged → no migration needed. If `prepared()` parity
fails, revert F1 item only (wrapper class restored from history).

## 9. E0 gate — decisions required from Coordination

1. **Approve F1** `_EnvelopeHintedToolset → prepared()`? (REPLACE_NATIVE)
2. **Approve F6** transient invoke one-shot seam? (P1 fix — EXTEND)
3. **F7:** wire (a) or remove (b) `aggregate_paginated_pages`? (contract decision)
4. **Approve F2** usage-counting parity attempt → removal on success? (conditional)
5. **F5/F11/F12** optional simplifications — include or defer?
6. Physical scope: `pydantic_ai_investigation.py`, `semantic_capability_support.py` (finalize only),
   `governed_capability_orchestrator.py` (no change expected), tests. Anything else?

## 10. Traceability

- F2 diagnostic package: `evidence/c3-t2-f2-int1-diagnostic/README.md` (P1–P5 matrix).
- F1 baseline: `comprehension-v4`, acceptor gate, 68-test prod suite — untouched.
- All line anchors verified at BASE_HEAD `970e2bd691`.
