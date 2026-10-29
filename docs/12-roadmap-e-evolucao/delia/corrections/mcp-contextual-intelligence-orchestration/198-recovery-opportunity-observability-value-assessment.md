# 198 — Recovery-Opportunity Observability & Engine B Value Assessment

TASK_ID: `DELIA-C3-PLUGGABLE-ORCHESTRATION-RECOVERY-OBSERVABILITY-VALUE-01`
Phase: C3 (unchanged). Evaluated SHA: worktree atop
`181b238da8b7545ecbd27b3574a9307054756190` (HEAD==origin/main at
reanchor; base advanced one docs-only commit from `3016fab5ac` —
no delia-api drift). Local-only. No production deploy, no
production model/owner calls, no new productive instrumentation.

## 1. Objective

Close the telemetry gap identified in doc 197 §9: measure, from real
governed execution, how often the B1 recovery-reuse window is
*eligible* — including under Engine A, where it is observed but never
applied — and state the maximum realistically attributable saving
under current contracts.

## 2. Reuse-before-design gate

| Field | Value |
|---|---|
| RESPONSIBILITY | request-scoped per-turn telemetry |
| OWNER | `ModelCallLedger` (`app/application/interaction/turn_observability.py`) — the canonical per-turn carrier already bound by `handle_interactive_turn` via `bind/reset_turn_call_ledger` |
| CANONICAL_SOURCE | same module; eligibility predicate `_native_assessment_reuse_verdict` (orchestration) is the single contract both apply and observe evaluate |
| CONSUMERS | `build_turn_observability` → `result.observability["recovery_opportunity"]` |
| EXISTING_EQUIVALENT | YES — the ledger, its set/reset binding and the observability projection all pre-existed |
| REUSE_DECISION | EXTEND — bounded record map + counters on the existing carrier; additive projection key |
| ABSTRACTION_GATE | PASS — no new service/bus/registry; one carrier, one predicate |

## 3. Event definitions (not conflated)

| Event | Definition | Counter |
|---|---|---|
| E1 assessment executed | real `native_assessment` model invocation recorded at the authoritative point | `native_assessment_calls` |
| E2 recovery entered | bounded `_recover_relevance` round entered | `relevance_recovery_entered` |
| E3 candidate | ≥1 prior assessment record exists in THIS attempt context | `reuse_candidates` |
| E4 eligible | `_native_assessment_reuse_verdict` hits on the attempt's records | `reuse_eligible` |
| E5 reuse performed | B1 apply path consumed a verdict (model call skipped) | `reuse_performed` |
| E6 reassessment | fresh `_assess_native_path` executed in recovery | `reassessments` |

`E3 ≠ E4 ≠ E5`; a skipped model call is never equated with a better
Business Outcome.

## 4. Mechanism (minimal)

- `ModelCallLedger` gains: `_recovery_records` (attempt-scoped,
  cleared by `begin_recovery_attempt()` at each `_governed_owner_path`
  entry), `_recovery_counters` (turn-scoped, non-negative, bounded
  keys — unknown event names ignored), `record_assessment_decision`,
  `record_recovery_event`, `recovery_observation` projection.
- `_record_native_assessment` dual-writes the same
  `{decision, premise_fp}` pair to the B1 reuse ledger (if bound —
  apply) and to the call ledger (if bound — observe). One fingerprint
  computed once; records are decisions+hashes only.
- `_reusable_native_assessment` delegates the verdict to the pure
  `_native_assessment_reuse_verdict(records, …)` — the SAME predicate
  the observation path evaluates; no duplicated rule.
- Recovery block: candidate → eligible → (B1 apply: performed |
  else: reassessment). All hooks no-op when the carrier is unbound.
- Projection: additive `recovery_opportunity` key, emitted only when
  supplied — legacy shape byte-identical.

## 5. Engine A observation-only proof

Engine A never binds `_NATIVE_ASSESSMENT_LEDGER`: the apply path
cannot trigger, the model call still executes, and the opportunity
is measured via the call-ledger records. On S11 Engine A reports
`eligible=1, performed=0, reassessments=1` — opportunity observed,
optimization not applied. `ENGINE_A_BEHAVIOR_CHANGED=NO`
(17 model calls / 4 owner calls / SUCCESS identical; O13).

## 6. RED → GREEN evidence

RED recorded: `AttributeError: 'ModelCallLedger' object has no
attribute 'recovery_observation'` (collection-green, first test
failed) — mechanism absent.

GREEN: `tests/test_recovery_opportunity_observability.py` **15/15**:
O1 zero-count, O2 verbatim E1, O3 recovery entry, O4 ineligible
verdict never eligible, O5 Engine-A eligibility observed, O6 changed
premise refused, O7 reassessment counted, O8 B1 reuse counted without
phantom call, O9 cancellation invents nothing, O10 concurrent turns
isolated, sequential-turn reset, O11 fail-closed, O12 counters-only
privacy, O13 Engine-A behavior, O14 additive-only projection.

## 7. Local measurement corpus

`scripts/engine_ab_eval.py` now binds the ledger per attempt and
emits `recovery_obs` per row. Deterministic corpus (7 scenarios × 3
engines, 21 attempts):

```
S11_recovery_reuse — the only designed eligible window:
  A : calls=17 assessments=2 obs={entered:1, cand:1, elig:1, perf:0, reassess:1}
  B0: calls=17 assessments=2 obs={entered:1, cand:1, elig:1, perf:0, reassess:1}
  B1: calls=16 assessments=1 obs={entered:1, cand:1, elig:1, perf:1, reassess:0}
S1/S2/S3/S7/S8/S10: identical calls/owner/status on all engines;
  no eligible window observed (S3 recovery enters but does not reach
  the assessment stage — entered not counted, elig=0).
OUTCOME_DIVERGENCES=0  NONCONFORMANT_ROWS=0
```

Fixture prevalence (NOT production): 1/7 scenarios exhibits the
eligible window; within it, 1 avoidable call of 17 (~6% of scenario
calls) under `foreign_evidence_required` + same-target recovery +
multi-group + irrelevant-first-result — a deliberately constructed
corner of the recovery space.

## 8. Value model (measured quantities only)

| Quantity | Value | Source |
|---|---|---|
| CALLS_AVOIDED_PER_ELIGIBLE_TURN | 1 (bounded ceiling) | deterministic S11 |
| TOKENS_PER_AVOIDABLE_CALL | ~700–900 input + ~40–90 output tokens (delia-json prompt size at this stage) | Task-05 PROVIDER_REPORTED ranges |
| LATENCY_PER_AVOIDABLE_CALL | ~0.4–0.9 s at local 3.1B; provider-dependent | Task-05 measured per-call wall time |
| LOCAL_FIXTURE_PREVALENCE | 1/7 scenarios (constructed fixture, not a population) | this corpus |
| LOCAL_REAL_MODEL_PREVALENCE | 0 reuse events in 12 attempts (window never materialized) | doc 197 §8 |
| PRODUCTION_PREVALENCE | TO_INSTRUMENT — now observable per turn; needs deployment-era aggregation | §9 |

Upper bound if production frequency were f eligible-turns/N: saving
≤ 1 model call, ~700–900 in-tokens and ~0.4–0.9 s per eligible turn.
No business case is manufactured: f is unknown.

## 9. Production-frequency status

`PRODUCTION_FREQUENCY=TO_INSTRUMENT` — now *measurable*: every turn
running under a bound `ModelCallLedger` (the production path binds
one at `handle_interactive_turn`) emits `recovery_opportunity`
counters inside `result.observability`. No cross-turn aggregation
exists today; the smallest future step is summing the additive
projection fields downstream (dashboard/log aggregation) — zero new
collection. Historical data cannot establish eligibility (the
predicate needs premise fingerprints never previously recorded):
`HISTORICAL_ELIGIBILITY=INCONCLUSIVE`.

## 10. Conformance / regression / audits

- Engine A/B0/B1 contract conformance: 43/43 each (shared suite).
- Task-04 reuse 18/18; Task-05 hardening 23/23; observability
  contract suite: all PASS.
- Focused sweep (recovery|governed|relevance|observability|
  cancellation|prepare|langgraph|attempt): all PASS.
- Full `delia-api` suite: **2595 collected → 2590 passed, 2 failed,
  3 skipped** — same 2 pre-existing/environmental failures (CRI
  variant fixture drift; openapi env-scan repo-root sensitivity).
  Zero new regressions; no expectation modified.
- Architecture Phase-3: PASS. Backend boundaries: 0 findings.
- Residual search: langgraph confined to adapter/tests/
  requirements-eval; no application/domain imports; telemetry stays
  in `turn_observability` (interaction owner) — no engine internals
  in counters.

## 11. Data classification

Operational metadata only: bounded non-negative ints + a fixed
6-key dict. Records hold `decision` (enum string) and `premise_fp`
(sha256) — never input text, evidence, tokens, secrets or reasoning;
in-memory, attempt-scoped, not persisted by this change (O12/O13/O14).

## 12. Verdict

`INSTRUMENTATION_READY_FREQUENCY_UNKNOWN`

- Instrumentation correctness: PROVEN (counters reflect actual
  execution — 15 tests incl. concurrency/privacy/compat).
- Optimization safety: PROVEN (predicate identical to apply path;
  Engine A untouched; additive contract).
- Optimization value: UNRESOLVED — upper bound is small (≤1 call,
  ~6% of the eligible scenario) and production frequency unknown.

Recommendation: keep B1 as the dormant experimental variant — the
infrastructure is now correct either way. Next decision requires one
bounded aggregation read of `recovery_opportunity` across real turns
(separate authorization), not more engine work.

## 13. Unresolved / next bounded step

- Deploy-era aggregation proposal only (NOT implemented): sum
  `relevance_recovery_entered`, `reuse_eligible`, `native_assessment_calls`
  over N turns → eligibility rate + calls-avoidable ceiling.
- If a future turn-level aggregation shows eligible rate ≈ 0, retire
  B1 cleanly (the observation surface pays for itself either way).
