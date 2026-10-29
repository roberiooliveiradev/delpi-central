# Doc 196 — Task 04: Engine B sequencing & recovery strategy A/B experiment

**Task:** `DELIA-C3-PLUGGABLE-ORCHESTRATION-SEQUENCING-RECOVERY-AB-01`
**Base SHA:** `68b10b81dd0c758393008dcbe470e63fda3bd9b6` (HEAD == origin/main at reanchor)
**Evaluated SHA:** working tree atop `68b10b81` (final SHA in ledger/report)
**Phase:** C3 — pluggable orchestration, experimental evaluation only
**Scope:** local experimental implementation + local evaluation. **No production adoption, no deploy, no production calls.**

## 1. H5 revalidation on current HEAD

Doc 188 reported ~9 model calls per recovery round in examined production turns, with the repeated `native_assessment` as a candidate redundancy.

Revalidation on `68b10b81dd`:

- `_recover_relevance` (orchestration.py) re-runs `native_assessment` only when `len(groups) > 1`, inside the single bounded recovery round, and passes `relevance_feedback` — the second assessment is **not** identical to the first: the mismatch is now confirmed, so the premise set changed.
- Material inputs of `native_assessment`: target `descriptor` (capability_id + operation_class), capability `group` payload, turn `goal` (goal_class, comparison_requested, output_mode, business_subject), `input_text`, workspace/prior turns, and `relevance_feedback` when present.
- **Verdict:** naive H5 ("the second assessment is literally redundant") is **refuted** — inputs differ by `relevance_feedback`, which is decisional by design. Blind reuse of a `sufficient` verdict would bypass a mandatory semantic stage.
- **Refined H5:** the *decision* is monotonic-safe to reuse in exactly one direction — a prior `foreign_evidence_required` on the **same target + same goal** can only be strengthened, never reduced, by an irrelevant native result. Reusing it skips the model call but still routes through the foreign consult under fresh feedback. All other premise combinations reassess. This is the bounded experiment implemented.

## 2. Reuse & Abstraction Gate

```
RESPONSIBILITY=quality/testing (DÉLIA protocol owner) + architecture boundaries
OWNER=application/capability_provision (governed primitives)
CANONICAL_SOURCE=orchestration.py (_assess_native_path, _recover_relevance)
EXISTING_IMPLEMENTATION=_assess_native_path + recovery round exist; decision reuse mechanism: none
EXISTING_EQUIVALENT=YES (ContextVar per-attempt carriers: _RELEVANCE_RECOVERY_USED, _CANCEL_CHECK)
REUSE_DECISION=EXTEND (opt-in ambient ledger, same ContextVar pattern; no new port)
ABSTRACTION_GATE=PASS — no new port/registry/planner; one ContextVar + two pure helpers; sole consumer Engine B; Engine A untouched (unbound ledger = byte-identical)
```

## 3. Strategy design (B1)

```
admission → evidence_session → owner_path → END
```

- `evidence_session` (new node): records `assessment_reuse=<flag>` in typed graph state — the graph-level sequencing decision. B0 = flag off (`recovery_reuse_enabled=False` constructor knob, evaluation-only).
- `owner_path`: when `assessment_reuse` is set, binds a fresh `_NATIVE_ASSESSMENT_LEDGER` (`{"records": {}, "events": []}`) **in its own node context** before calling `_governed_owner_path`. Required because LangGraph executes each node in a copied context — a ContextVar bound in `evidence_session` does not propagate to `owner_path` (verified empirically).
- `_governed_owner_path`: after each round-1 `native_assessment`, `_record_native_assessment` stores `(group_key, capability_id) → {decision, goal_fp}` — only when the ledger is bound (no-op otherwise).
- `_recover_relevance`: before the second assessment, `_reusable_native_assessment` applies the **shared deterministic monotonic check**: reuse iff `decision == foreign_evidence_required` AND same `capability_id` AND identical goal fingerprint. Reuse → skips the model call, still runs `_select_foreign_capability` + `_invoke_foreign_evidence` under `relevance_feedback`. Any other case → full reassess with feedback, unchanged.
- Trace: ledger `events` are surfaced on `owner_path`'s trace (`assessment_reused` / `assessment_reassessed`) for A/B attribution; `evidence_session` appears in every B trace.

### What this is NOT

- Not a cached authorization: the record is a status string + target key + goal fingerprint. Eligibility, candidate tokens, live-surface membership, PREPARE/ACT, budgets and cancellation are untouched.
- Not a second planner/validator: the reuse rule is a pure function over already-made decisions; all semantic stages still belong to the model through `InvokeModel/_propose`.
- Not a memory store: the ledger is per-attempt, per-invocation; nothing crosses turns or resume boundaries.

## 4. RED → GREEN

RED recorded before implementation:

- `test_engine_b_recovery_reuse.py` failed at collection (`ImportError: _NATIVE_ASSESSMENT_LEDGER`) — the mechanism did not exist.
- After mechanics but pre-strategy, `langgraph` consumed 2 `native_assessment` calls (no reuse).

GREEN: **18/18** strategy tests pass, covering R1–R10:

| R | Case | Result |
|---|------|--------|
| R1 | prior foreign_required, same target → B1 = 1 assessment call; A/B0 = 2 | PASS |
| R2 | re-selected different capability → reassess (2 calls) | PASS |
| R3 | prior `sufficient` → never reused (2 calls) | PASS |
| R4 | persistent irrelevance + reuse → honest insufficiency, no fabrication | PASS |
| R5 | forged `foreign_capability_id` → fails closed, zero foreign calls, no leak | PASS |
| R5b | capability/token opacity in content | PASS |
| R6 | cancel_check → PROCESSING_TIMEOUT regardless of reuse | PASS |
| R7 | recovery ceiling still 1 round (≤2 invokes) | PASS |
| R8 | trace shows `evidence_session` + `assessment_reused`/`_reassessed` | PASS |
| R9 | Engine A unchanged — 2 calls, no trace attr | PASS |
| R10 | B1 trace carries `assessment_reused`; B0 identical run does not | PASS |

## 5. Three-way local A/B (`scripts/engine_ab_eval.py`)

Harness upgraded per task §12/§15: engines `delia` (A), `langgraph_b0` (B0 framework baseline), `langgraph` (B1 strategy); added `S11_recovery_reuse` (two-group foreign-required recovery); per-stage call metering; **exit code now nonzero on any cross-engine status/conformance divergence** (was unconditional 0).

| Scenario | A calls | B0 calls | B1 calls | assessments A/B0/B1 | owner calls | outcome (all) |
|----------|---------|----------|----------|---------------------|-------------|----------------|
| S1_read | 6 | 6 | 6 | - | 1 | SUCCESS |
| S2_two_records | 7 | 7 | 7 | - | 1 | SUCCESS |
| S3_recovery | 9 | 9 | 9 | - | 2 | SUCCESS |
| S7_owner_unavailable | 6 | 6 | 6 | - | 1 | SOURCE_UNAVAILABLE |
| S8_unauthorized | 3 | 3 | 3 | - | 0 | CLARIFICATION_REQUIRED |
| S10_prepare_act | 4 | 4 | 4 | - | 0 | WRITE_REJECTED |
| **S11_recovery_reuse** | **17** | **17** | **16** | **2/2/1** | 4 | SUCCESS |

`OUTCOME_DIVERGENCES=0`, `NONCONFORMANT_ROWS=0`, exit 0.

**Measured effect:** exactly **1 redundant `native_assessment` call eliminated** on the reuse-eligible scenario (17→16 total fake-model calls, −5.9%), identical business outcome, identical owner calls. All other scenarios: zero delta (strategy dormant outside the reuse window).

## 6. Metric honesty

- Call counts are `FAKE_MODEL_CALLS` (scripted harness): valid for structural comparison, **not** proof of real-model token savings or semantic superiority.
- Tokens: `NOT_AVAILABLE` — the fake model reports no token accounting. Estimated avoided tokens ≈ one `native_assessment` prompt+response per reuse-eligible recovery round; not measured, not claimed.
- Latency: local-fake wall time, comparative only. B1 ≈ B0 (graph overhead dominated, no regression); A remains fastest on fakes.
- Semantic eval: `INCONCLUSIVE` — no real-model (Ollama) run executed this task; scripted fakes cannot assert real-model quality.
- Expected avoided calls before execution: **1 per reuse-eligible recovery round** (multi-group, prior `foreign_evidence_required`, same target). Observed: **1** — matches.

## 7. Frozen decisions & contracts

- Engine A behavior: **unchanged** — unbound ledger → all new code paths are no-ops; same fixture produces identical calls/outcomes (R9).
- `SupportsGovernedCapabilityAttempt` / `SupportsGovernedStageGates`: **no signature changes** — the ledger is ambient per-attempt context, same ContextVar pattern as `_RELEVANCE_RECOVERY_USED`/`_CANCEL_CHECK`.
- Recovery contract: ceiling (1 round), bounded re-invocation (2), identical-argument rejection, fail-closed identifiers — all preserved (R4/R7, 43/43 conformance on both engines).
- PREPARE/ACT, cancellation, provenance, AuthZ, token opacity: preserved (S10, R5/R5b/R6, full conformance).
- Production: `requirements.txt`/`Dockerfile` untouched; LangGraph remains `requirements-eval.txt` only; adapter still the sole framework-import site (AST-enforced); no production composition wiring.

## 8. Regression & audits

- Strategy tests: 18/18 PASS.
- Conformance: 43/43 on `delia` + `langgraph` (B1 default).
- Architecture isolation: 9/9 PASS.
- Focused sweep (7 files, incl. relevance + orchestration + provider-neutral): **289 PASS**.
- Full `delia-api` suite: **2557 collected, 2552 passed, 2 failed, 3 skipped** (local venv, Python 3.12, pytest 9.0.3).
  - `test_cri_e2_outcome_assessment.py::test_cri_instruction_variant_carries_requirements_clause` — same pre-existing fixture drift as Tasks 02/03 baseline.
  - `test_openapi_capability_provider.py::test_infra_and_env_carry_no_direct_delpi_wiring` — pre-existing environment/layout issue: the test scans `_REPO_ROOT/delia-api/env.example`, whose doc comment mentions `DELIA_OPENAPI_DELPI` (present at baseline SHA `68b10b81`, commit `269d5276b0`). In the Task-03 container layout `_REPO_ROOT` did not resolve to the repo root so the file was never scanned. Not caused by this diff — the scanned file and the test are untouched.
  - `test_g4_integrated_homologation::test_fixture_matches_current_producer_output` — PASSED locally (repo-root layout makes `/docs` resolvable; it only failed in the Task-03 container for a missing mount).
  - 3 skipped = opt-in real-model tests (`DELIA_I04_REAL_MODEL=1` unset), same as baseline.
- Architecture Phase-3 gate: PASS (no new findings).
- Backend boundaries audit: PASS (0 findings).
- Residual search: `langgraph` only in `app/infrastructure/orchestration/langgraph_engine.py` (+ pycache), tests, `requirements-eval.txt`. Zero imports in `app/application` + `app/domain`; zero production composition references.

## 9. Files changed

- `app/application/capability_provision/orchestration.py` — `_NATIVE_ASSESSMENT_LEDGER` ContextVar + `_goal_fingerprint` + `_record_native_assessment` + `_reusable_native_assessment` (+~95 lines); one `_record_native_assessment` call site; reuse check in `_recover_relevance`.
- `app/infrastructure/orchestration/langgraph_engine.py` — `recovery_reuse_enabled` flag, `evidence_session` node, `assessment_reuse` state field, ledger binding + trace events in `owner_path`.
- `tests/test_engine_b_recovery_reuse.py` — NEW, 18 tests (R1–R10 + mechanics).
- `tests/test_governed_attempt_contract.py` — `langgraph_b0` engine id + `recovery_reuse_enabled` builder kwarg.
- `scripts/engine_ab_eval.py` — three-way engines, S11 scenario, stage metering, nonzero divergence gate.
- This document + execution ledger.

## 10. Verdict & recommendation

`PROMISING_LOCAL_EVIDENCE` — bounded, measurable improvement (1 model call eliminated per reuse-eligible recovery round) with contract and security preservation, a real graph-level alternative transition, and an honest negative space documented (narrow reuse window; H5's broader claim refuted).

**Limitations:** reuse fires only when (a) multi-group surface, (b) prior decision `foreign_evidence_required`, (c) recovery re-selects same target, (d) goal unchanged — a narrow window; savings = 1 call/round (recovery is capped at 1 round anyway). Token/latency benefit on real models unmeasured. B0 graph still costs ~2× local-fake latency vs A for zero call benefit on non-recovery scenarios.

**NEXT_BOUNDED_STEP (Task 05 candidates):** (a) real-model (approved Ollama) semantic A/B on the reuse scenario to confirm the foreign consult under reused decision still feeds correct designations; (b) inventory whether production-shaped surfaces commonly hit the reuse window (multi-group + foreign-required + same target) — if rare, expected production benefit stays small; (c) optional: extend the same monotonic reasoning to `corroboration_requested` if evidence shows that decision is also monotonic-safe.
