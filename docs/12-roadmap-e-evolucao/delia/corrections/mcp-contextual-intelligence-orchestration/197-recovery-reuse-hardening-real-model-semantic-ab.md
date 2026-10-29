# 197 — Recovery Reuse Hardening & Real-Model Semantic A/B

TASK_ID: `DELIA-C3-PLUGGABLE-ORCHESTRATION-RECOVERY-SAFETY-SEMANTIC-EVAL-01`
Phase: C3 (unchanged). Evaluated SHA: worktree atop `0e39cbc9a8c98ce30959c42ef243634149b9bd57`
(Task 04, HEAD==origin/main at reanchor). Environment: local Linux,
`delia-api/.venv` (pytest 9.0.3), Docker `delpi-ollama` local only.
No production model/owner calls. No deploy.

## 1. Objective

Validate and harden the Task-04 experimental recovery-decision reuse
(B1 `evidence_session` + `_NATIVE_ASSESSMENT_LEDGER`) against the two
findings raised by independent review:

- **F1 — incomplete premise equivalence**: the Task-04 fingerprint
  covered only 4 `_TurnGoal` fields; the `native_assessment` stage has
  more material inputs.
- **F2 — mutable ContextVar ledger isolation**: `set()` without a
  reset token could leak a binding on non-copying runtimes.

Then measure whether the hardened strategy yields meaningful benefit
under a real local LLM (Ollama `delia-json:latest`).

## 2. H5 — decision-dependency matrix (F1)

Traced `_assess_native_path` model input construction. The stage
proposal is assembled in `_model_stage_proposal` from the explicit
assessment block **and** ambient turn inputs.

| Input | Reaches assessment? | Stability in-turn | Classification | Disposition |
|---|---|---|---|---|
| `input_text` | yes (`_propose` arg) | fixed per turn | REQUIRED_FOR_EQUIVALENCE | in fingerprint |
| target `ProviderCapability` id | yes (block) | varies per selection | REQUIRED_FOR_EQUIVALENCE | key component |
| owner group key | yes (block) | varies per selection | REQUIRED_FOR_EQUIVALENCE | key component |
| capability contract/descriptor identity | yes (block: operation class + serialized caps) | stable per descriptor | REQUIRED_FOR_EQUIVALENCE | `capability_fp` |
| `goal.goal_class` | yes (block) | fixed per turn | REQUIRED_FOR_EQUIVALENCE | retained |
| `goal.comparison_requested` | yes (block) | fixed per turn | REQUIRED_FOR_EQUIVALENCE | retained |
| `goal.output_mode` | yes (block) | fixed per turn | REQUIRED_FOR_EQUIVALENCE | retained |
| `goal.business_subject` | yes (block) | fixed per turn | REQUIRED_FOR_EQUIVALENCE | retained |
| `goal.scope_constraints` | not serialized in block, but `_TurnGoal` is a model artifact consumed by downstream proposal text; two turns with different scope produce different goal objects | varies | MUST_INVALIDATE (conservative) | in `goal_fp` |
| `goal.answer_requirements` | same as above — requested record count/type materially scopes "sufficiency" | varies | MUST_INVALIDATE | in `goal_fp` |
| `goal.contract_subject` / `declared` / `execution_bound` / `prior_evidence_sufficient` | same class | varies | MUST_INVALIDATE | in `goal_fp` (full goal serialization) |
| `workspace_context` | yes (`_propose` ambient input — untrusted client context; can alter model request even absent from the block) | fixed per turn | REQUIRED_FOR_EQUIVALENCE | canonical hash |
| `prior_turns` (kind/content/epistemic_class) | yes (`_propose` ambient input) | fixed per turn | REQUIRED_FOR_EQUIVALENCE | canonical hash |
| `relevance_feedback` | yes (block, recovery only) | **differs by design** between rounds — it is the recovery trigger | SAFE_TO_IGNORE_WITH_PROOF | excluded; reuse permitted only in the monotonic direction (see §3) |
| evidence at decision point (foreign consult results) | not an assessment input — judged at `goal_evidence_relevance` | per round | NOT_APPLICABLE | never fingerprinted |
| correlation_id / deadline | scheduling only | per call | NOT_APPLICABLE | excluded |

**Prior fingerprint limitations (documented):**
`_goal_fingerprint` covered 4 fields. A changed `input_text`, changed
workspace context, changed prior turns, or changed scope/answer
requirements would have produced an identical fingerprint — a
`foreign_evidence_required` decision established under one user
request could have been "reused" under a materially different premise
inside the same bound context. Realized risk was low (the ledger is
bound per `owner_path` invocation, and input/goal rarely vary inside
one attempt), but the mechanism was not *proof* of equivalence.

**Hardened equivalence rules:**
`_native_assessment_premise_fp` = sha256 over canonical JSON of:
`input_text`, group key, capability id, capability fingerprint
(`capability_id`, operation class), full serialized `_TurnGoal`,
canonical `WorkspaceContext`, canonical `ConversationContextTurn`
sequence. Reuse requires: same `(group_key, capability_id)` record
key **and** identical `premise_fp` **and** prior decision ==
`foreign_evidence_required`. Any unknown/uncomparable field fails
closed to fresh assessment (H10).

## 3. Monotonic reuse proof

Reuse is restricted to a prior `foreign_evidence_required` verdict on
the identical premise. The recovery trigger — a
`goal_evidence_relevance` judgment of `irrelevant` on the foreign
evidence — can never *reduce* a foreign-evidence requirement: the
worst-case outcome of wrongly reusing is a redundant foreign consult
under fresh governance (arguments, AuthZ, provenance, budget all
re-executed), never a skipped consult. `sufficient`,
`corroboration_requested`, `inconclusive` and any absent verdict are
never reused (H9). This is a contract-level argument, not an
intuition: the reused value is a *requirement*, and recovery only
adds disconfirming evidence about the evidence, not about the
requirement. `MONOTONIC_REUSE_PROOF=YES` for this direction only;
the reverse direction (`sufficient` reuse after mismatch) remains
prohibited.

## 4. F2 — ledger lifecycle

**Before:** `owner_path` did `_NATIVE_ASSESSMENT_LEDGER.set({...})`
with no token and no reset — correct under LangGraph's copied-node
contexts but leaking the binding if the runtime ever executes the
node inline (same context) — a subsequent inline call would observe a
stale dict.

**After:** token-based `set()`/`reset(token)` pair wrapping the whole
`_governed_owner_path` call in a `try/finally` — identical lifecycle
semantics to `bind_turn_call_ledger`/`reset_turn_call_ledger`
(`turn_observability.py`, the canonical primitive this mirrors).
Fresh dict per invocation; cancellation, exceptions and retries
cannot leak state; records bounded to one group/capability per
attempt window; contents are decision statuses + premise hashes only
— no arguments, evidence payloads, tokens, or model reasoning (C8,
C10).

## 5. RED → GREEN evidence

RED (recorded before implementation):
- `test_h1_identical_premises_allow_reuse` → `TypeError:
  _record_native_assessment() takes 4 positional arguments but 8
  were given` (hardened signature absent).
- Lifecycle tests failed on missing reset semantics.

GREEN: `tests/test_engine_b_recovery_hardening.py` — **23/23 PASS**:
H1–H10 premise equivalence (identical, changed input text, scope,
answer requirements, workspace, prior turns, capability/group,
evidence, sufficient-verdict, unknown→fail-closed) + C1–C10
(concurrent turns, sequential isolation, retry, cancellation,
exception cleanup, copied-node contexts, nested invocation, no-AuthZ
leakage, bounded growth, no sensitive persistence).

## 6. Conformance & regression

- Engine A conformance: 43/43 PASS (behavior unchanged — ledger never bound).
- Engine B0 conformance: 43/43 PASS.
- Engine B1 conformance: included in the same 43-scenario contract suite — PASS.
- Task-04 reuse suite: 18/18 PASS (same-premise reuse still fires).
- Architecture isolation: 9/9 PASS.
- Focused sweep (recovery|governed|relevance|budget|cancellation|
  prepare|provenance|langgraph|attempt): **616 passed**.
- Full `delia-api` suite: **2580 collected → 2575 passed, 2 failed,
  3 skipped** — the same two pre-existing/environmental failures from
  Task 04 (CRI variant fixture drift; openapi env-scan sensitive to
  repo-root layout). Zero new regressions; no expectation modified.

## 7. Deterministic A/B (scripted fake, unchanged contract)

`scripts/engine_ab_eval.py` — identical harness as Task 04:

```
S11_recovery_reuse: A=17 calls, B0=17 calls, B1=16 calls
owner_calls=4/4/4  OUTCOME_DIVERGENCES=0  NONCONFORMANT_ROWS=0
assessments: A=2, B0=2, B1=1
```

The hardened fingerprint preserves the valid reuse window: identical
premises still reuse; the saving is exactly 1 model call in the
eligible window, as before.

## 8. Real local-model A/B (Phase C)

Model: `delia-json:latest` — digest
`7b8f4ab14fc11063fe5d577cd7cfd62bbb47f8a948ab7bb82be404705f89ac07`,
family qwen2, 3.1B, Q4_K_M, ctx 32768 — already pulled; nothing
downloaded. Endpoint: local Ollama OpenAI-compatible `/v1` via the
existing `OpenAICompatibleModelInvocationAdapter`. Token source:
`PROVIDER_REPORTED` (per-stage `ModelCallLedger` bound around each
attempt — the canonical telemetry primitive, no new instrumentation).
Fake owners with equivalent business records (`_providers()`); no
real DAVI/API DELPI. Input: `"2 exemplos de terminal bala"`.
Runs: 4 executions of the three-way matrix (12 engine-attempts).

| Run | Engine | Status | Calls | Tokens in/out | Latency | Owner | Reuse |
|---|---|---|---|---|---|---|---|
| 1 | B0 | SUCCESS | 14 | 15656/495 | — | — | n/a |
| 1 | B1 | SUCCESS | 10 | 10038/307 | 7871ms | 1 | `assessment_reassessed` (premise/verdict mismatch — no reuse) |
| 2 | A | NOT_APPLICABLE | 5 | 5447/176 | 4375ms | 0 | n/a (fail-closed `invalid_foreign_selection`) |
| 2 | B0 | SUCCESS | 12 | 13134/343 | 8234ms | 2 | n/a |
| 2 | B1 | NOT_APPLICABLE | 5 | 5445/179 | 4239ms | 0 | n/a |
| 3 | A | NOT_APPLICABLE | 5 | 5440/209 | 5321ms | 0 | n/a |
| 3 | B0 | NOT_APPLICABLE | 5 | 5444/158 | 3544ms | 0 | n/a |
| 3 | B1 | NOT_APPLICABLE | 2 | 2786/42 | 1046ms | 0 | n/a |
| 4 | A | NOT_APPLICABLE | 5 | 5442/174 | 7232ms | 0 | n/a |
| 4 | B0 | NOT_APPLICABLE | 5 | 5444/147 | 3467ms | 0 | n/a |
| 4 | B1 | NOT_APPLICABLE | 5 | 5443/163 | 3652ms | 0 | n/a |

(Run 1's A row was truncated in capture; B0/B1 rows above are verbatim.
12 measured engine-attempts total; no row edited for effect.)

Reachability: model reachable; `native_assessment` reached in 3/4
matrices; recovery reached in runs 1–2 only. `TARGET_STAGE_REACHED=
PARTIAL` across runs.

**Findings:**
- The 3.1B model's nondeterminism dominates every metric: run 4 shows
  all three engines taking byte-identical 5-call fail-closed paths,
  while runs 1–2 show 10–14 call SUCCESS paths with recovery — the
  divergence is model sampling noise, not engine behavior.
- The reuse-eligible window (same-target recovery after round-1
  `foreign_evidence_required`) **never materialized under B1** in any
  real run — when recovery occurred, the second-round target/premise
  differed or the round-1 verdict was not `foreign_evidence_required`
  → `assessment_reassessed`. The hardened fail-closed rule behaved
  exactly as designed: it declined reuse rather than forcing it.
- Token measurement is now `PROVIDER_REPORTED` — e.g. one
  `native_assessment` call ≈ 700–900 input tokens at this prompt
  size — but no reuse event exists to attribute savings to.
- `SEMANTIC_COMPARISON=INCONCLUSIVE` for benefit; safety confirmed
  (no gate bypass, no outcome divergence attributable to the
  mechanism, fail-closed paths identical to Engine A's).

## 9. Production-frequency investigation

`ModelCallLedger` already records per-stage calls (stage =
instruction id, incl. `delia.capability_orchestration.native_assessment`)
and is projected into `result.observability.calls` per turn
(`handle_interactive_turn.py`). Stage-level granularity to *detect*
an eligible turn exists; **no cross-turn aggregation** answers "how
often does the same-target recovery window occur" — the projection
is per-result, consumed by the caller, not aggregated.

`PRODUCTION_FREQUENCY=TO_INSTRUMENT`. Smallest future extension (NOT
implemented): a bounded per-turn counter in the existing
observability projection — e.g. `native_assessment_calls` plus a
`reuse_eligible` boolean computed inside the governed recovery stage
— which downstream aggregation could sum. No production logging was
added; no private prompt extraction. Prevalence was not estimated
from the S11 fixture.

## 10. Architecture audit

- `grep langgraph delia-api/app/**`: only
  `app/infrastructure/orchestration/langgraph_engine.py` (adapter) —
  zero application/domain imports.
- Phase-3 audit: PASS, no new regressions.
- Backend boundary audit: 0 findings.
- Residual search: langgraph confined to adapter/tests/
  `requirements-eval.txt`; production composition untouched; no
  DÉLIA→DELPI direct path; no duplicated governance authority (the
  reuse check lives inside the governed recovery stage; the graph
  only carries a sequencing flag).
- LangGraph node copied-context behavior now handled explicitly:
  decision carried in graph state, ledger bound+reset inside
  `owner_path` (C6).

## 11. Outcome classification & verdict

`SAFE_NO_MATERIAL_GAIN`

- Safety: PROVEN locally — 23 hardening tests, full premise
  equivalence, token-scoped ledger lifecycle, fail-closed on any
  uncomparable premise, monotonic direction only, Engine A/B0
  untouched, 0 conformance/contract divergences.
- Benefit: measured only in the deterministic harness (1 call per
  eligible window, ~6% of that scenario's calls). Under the real
  3.1B model the eligible window did not occur in 12 attempts; real-
  model benefit is UNPROVEN, not disproven.
- Frequency: production prevalence unknown (`TO_INSTRUMENT`).
- No production adoption implication. Engine A remains default;
  B1 remains local/experimental.

## 12. Residuals / unresolved

- Real-model reuse rate unmeasured — needs either a stronger local
  model, a corpus biased toward the eligible window, or the
  §9 telemetry to quantify natural prevalence.
- `relevance_feedback` handling rests on the §3 contract argument;
  a future change making assessment consume accumulated evidence
  would invalidate it — fingerprint covers assessment inputs, not
  judgment inputs.
- Two pre-existing environmental test failures unchanged.

## 13. Next bounded step

Task 06 candidate: instrument the bounded per-turn
`native_assessment`/reuse-eligibility counters in the existing
observability projection (read-only, sanitized) to answer
`PRODUCTION_FREQUENCY`, then decide whether the B1 window is worth
any further investment. Alternative: drop B1 if prevalence is
negligible — the honest default absent demand.
