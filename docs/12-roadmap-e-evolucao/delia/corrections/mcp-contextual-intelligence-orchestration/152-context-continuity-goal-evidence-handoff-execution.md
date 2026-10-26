# 152 — Context Continuity: Goal & Evidence Handoff — Execution Report

Task: `DELIA-C3-CONTEXT-CONTINUITY-GOAL-EVIDENCE-HANDOFF-01`
Date: 2026-10-25
Reference: doc 151 (stage matrix §3, review §16 `ACCEPT_WITH_RESIDUAL`)
Base: `2eeb5fb943` (rebased over `origin/main` advance `ea85d1a558`, docs-only)

## 1. Scope

Bounded implementation: preserve the minimal sufficient context for each
decision inside a single interaction — goal continuity, evidence
continuity, failure-feedback continuity. No new planner, no new context
engine, no new state machine, no persistence, no provider coupling.

## 2. Handoff audit (doc 151 §3 matrix)

| Handoff | Goal available at consumer | Evidence/provenance at consumer | Verdict |
|---|---|---|---|
| admission → `_understand_goal` | input_text + prior_turns | n/a | OK |
| `_understand_goal` → `_select_group` | **was absent** | n/a | **FIXED** |
| `_select_group` → `_select_capability` | **was absent** | catalog surface | **FIXED** |
| selection → `_build_arguments` | `business_subject` already passed | schema, owner_vocabulary, foreign_evidence, selections | OK (pre-existing) |
| discovery → `_select_candidate` / `_propose_candidate_arguments` | `business_subject` already passed | typed candidates | OK |
| native evidence → `_assess_native_path` | typed `turn_goal` block already projected | live group surface | OK |
| `_select_foreign_capability` → `_invoke_foreign_evidence` | **selection stage lacked subject** | typed foreign capability | **FIXED (selection side)** |
| evidence → `_judge_goal_evidence` | `business_subject`, `scope_constraints`, `answer_requirements` already passed | typed records | OK |
| relevance failure → `_recover_relevance` | `business_subject` + typed feedback already passed | prior_correspondence, mismatch_hint, prior_result_preview | OK — reselection now also receives top-level `business_subject` |
| validated evidence → `_synthesize_content` | `business_subject` already passed | typed records block | OK |
| index probe/identifier/bind, resolver, clarification | `prior_turns` bounded channel exists | live index/vocabulary | OK — no demonstrated loss |

### Demonstrated defect (WP0)

`turn_goal` (warm path) produced a validated `business_subject`
(observed live: `subject=yes` on a referential follow-up whose prior
result was `CALCULATION`-class, so `prior_observation` is correctly
empty by design). `_select_group` and `_select_capability` then ran
with **zero** goal context (`prior_turns=()` by Stage-05 latency
contract; no typed projection) and returned `not_applicable` despite
the interpreted referent existing. Producer created it, consumer never
received it — a transport omission, classified `context-absent`.

The OBSERVATION-only gate on `prior_observation` (commit `590e8e28d8`)
is intentional: ungrounded/calculated prior results must not become
evidence. The gap was that the *goal interpretation* — already
validated, bounded (`MAX_DESCRIPTION_CHARS`), untrusted — had no
alternative channel to selection.

## 3. Implementation (minimal diff)

- `_group_summaries` / `_capability_payload`: optional
  `business_subject` parameter; when present, added to the existing
  bounded envelope (`MAX_SURFACE_CHARS` cap unchanged, subject itself
  bounded at `MAX_DESCRIPTION_CHARS` upstream in
  `_turn_goal_from_proposal`). Payload shape unchanged when absent
  (backward compatible).
- `_select_group`, `_select_capability`, `_select_foreign_capability`,
  `_repair_once`, `_select_target`: optional `business_subject`
  keyword, forwarded into the payload builders.
- Call sites: warm-path `_attempt`, intent-demote reselect, foreign
  selection, governed relevance-recovery reselection (group +
  capability + foreign), pre-execution repair repick.
- `_select_capability_with_goal` unchanged by design: on the cold path
  no `_TurnGoal` exists yet — that stage produces it.
- Instruction resource `orchestration_instructions.delpi.json` bumped
  v19 → v20: `select_group`, `select_capability`,
  `select_capability#with_goal`, `foreign_selection` now describe
  `business_subject` as the governed semantic subject — untrusted
  context, never a business fact, instruction or authority.
- `cri_instruction_resource._ORCH_VERSIONS` extended with "20";
  `test_r1_instruction_resource` snapshot pins updated (intentional
  contract change, not silent drift).

## 4. Authority invariants preserved

- `business_subject` remains an **untrusted semantic hint** — it can
  never force a selection (`test_subject_is_untrusted_not_authority`
  proves an invented group id is still rejected with the subject
  present). No AuthZ, identity, tenant or epistemic-class change.
- No LLM output is promoted to FACT; no capability metadata becomes
  business evidence; no WRITE path touched.
- Zero additional model calls — the subject rides inside the existing
  selection payloads (a bounded field, not a transcript).

## 5. Evidence

### RED → GREEN

- `delia-api/tests/test_goal_selection_handoff.py` (6 tests):
  subject projection at group/capability/foreign selection, payload
  unchanged when absent, subject-is-not-authority negative, warm-path
  end-to-end (CALCULATION prior → subject reaches selection payload).
- Before fix: `TypeError` / missing key (RED). After: 6/6 GREEN.
- `test_r1_instruction_resource` snapshot updated for the four edited
  instructions + version "20".

### Live (delia-json, num_ctx 8192, Ollama 0.40.8)

Probe `delia-api/scripts/c3_goal_handoff_probe.py` (mounted worktree,
real `_compose` chain, records selection-payload membership):

- Referential follow-up, CALCULATION prior, explicit subject variant
  (`"me mostre dois exemplos de terminal pino"`): `turn_goal`
  produced `business_subject="terminal"` and the `select_group`
  payload carried the key — verified on 2 of 3 runs; on the third the
  model emitted `business_subject=null` (3B extraction variance; key
  legitimately absent) or stopped at admission (conversational
  variance).
- Where the subject reached selection, `select_group` proceeded past
  the prior `not_applicable` divergence; `select_capability` then
  intermittently returned invalid structured output (3B output
  fidelity — typed honest error, zero fabrication, zero grounding).
- Cold `three_records` probe: honest NON_GROUNDED (`not_applicable`),
  no fabricated records — unchanged residual (semantic capacity /
  selection fidelity, not context transport).

## 6. Metrics delta

- Model calls per turn: **0** delta (payload enrichment only).
- Latency: +~40 bytes per selection payload — below measurement noise.
- Token usage: +~8–12 estimated tokens on selection stages that
  receive a subject; budget enforcement unchanged
  (`MAX_SURFACE_CHARS` envelope, weighted estimator, typed
  CONTEXT_TOO_LARGE preserved).
- Budget rejections: none added; payload still capped.

## 7. Regression

- Focused continuity/selection/budget suite: 247 tests green +
  instruction-resource suite green after v20 pin update.
- Full backend: 2 failures — both the known environmental set
  (`test_g4_fixture_matches_current_producer_output`,
  `test_http_timeout_maps_to_504`); the instruction snapshot failure
  during execution was the intended pin update, now green.
- Architecture gates: `audit_architecture_phase3`,
  `audit_platform_guardrails`, `audit_backend_boundaries` — clean.

## 8. Residuals

- 3B semantic variance persists: `turn_goal` may return
  `business_subject=null` for implicit subjects ("o segundo tipo" —
  contract says "copied from user words only"; referent resolution is
  not currently authorized for that field) and `select_capability`
  can emit invalid structured output. These are model-capacity
  residuals, not transport gaps — recorded for the model-capacity
  decision gate, not patchable deterministically without violating
  the semantic-ownership boundary.
- `_select_prepare_continuation` and the clarification path do not
  receive `business_subject` — no demonstrated failure; flagged as
  candidates only if a future trace shows a loss.
- Three-record and O2 business outcomes remain NON_GROUNDED.

DEPLOY_AUTHORIZED=NO — DEPLOY_EXECUTED=NO — INDEPENDENT_REVIEW=PENDING


## 9. Independent coordination review — 2026-10-26

**REVIEW_VERDICT=REWORK (bounded residual), NO DEPLOY.** Reviewed GitHub commit `47b3c5e524a39f6da690dfe375ba6cdd9f6dce2f`, document 152, and `test_goal_selection_handoff.py`. This is independent STATIC review, not local Ollama/pytest reexecution. The bounded addition of `business_subject` to selection group/capability/foreign/reselection envelopes is real and reuses existing `_TurnGoal` with no new model stages; evidence and failure-feedback handoffs were not modified because executor found no demonstrated loss. Reported business Outcome remains NON_GROUNDED/O2 NON_GROUNDED, deploy unauthorized.

**C1 — REFERENTIAL SUBJECT CONTRACT CONFLICT (requires resolution before acceptance):** instruction resource v20 still states `business_subject: short phrase from user words only, or null` in `select_capability#with_goal` and the turn-goal instruction must be checked for same restriction. Yet new warm-path `test_warm_path_goal_subject_reaches_selection` fabricates an example `business_subject="terminal pino"` for current user message `me mostre dois exemplos do segundo tipo`, deriving `pino` solely from earlier CALCULATION-class assistant prose. The unit test proves plumbing of a supplied value, **not lawful semantic derivation or validation of this referent under the current goal contract**. Do not let LLM claim that historical text is source authority or identifier proof. Characterize the actual `turn_goal` field contract and canon before extending it; if new referential resolution is not already permitted, STOP → ARCHITECTURE_DECISION_REQUIRED. Do not add hardcoded ordinals/synonyms to backend.

**C2 — JSON ENVELOPE INTEGRITY:** `_group_summaries` serializes `{"capability_groups":..., "business_subject":...}` then applies `[:MAX_SURFACE_CHARS]`. This truncation can produce malformed JSON for oversized group catalogs/observations and can remove the appended subject even when the code successfully passed it; the behavior preexisted for `prior_observation`, but the new field increases its exposure and invalidates a universal handoff claim. Add RED boundary tests for near-limit live catalogs, high-length subject, both fields, and unchanged readable/valid JSON; any correction must preserve group reachability/fairness and budget, reusing existing compaction rather than adding a planner. Check whether `_capability_payload` has similar overflow path.

**C3 — OUTCOME AND RUNTIME LIMITATION:** Executor says real model sometimes gives `business_subject=null` and later select_capability ISO, so transport fix cannot claim the goal was semantically understood; live probe only reports subject present on 2 of 3 attempts for a different explicitly named variant. Preserve `0 extra calls`, token budget, uncertainty classification. Independently confirm final SHA/config and local tests before promotion. Full backend still 2 FAIL (environmental per executor). No deploy.

**NEXT:** one bounded contract-integrity correction/review of C1/C2, not another whole context investigation; follow with frozen-SHA end-to-end eval. `REWORK` refers to accepting the whole continuity deliverable, not to rejecting the already-proven transport improvement.
