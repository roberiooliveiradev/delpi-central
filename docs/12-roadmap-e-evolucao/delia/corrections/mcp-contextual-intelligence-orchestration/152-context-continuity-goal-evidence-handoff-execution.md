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

## 10. C1/C2 bounded rework — 2026-10-26

**Task:** `DELIA-C3-CONTEXT-CONTINUITY-C1-C2-CONTRACT-INTEGRITY-REWORK-01` — resolves the §9 conditions C1 (referential subject contract) and C2 (JSON envelope integrity).

### C1 — Referential Subject Contract — Caso B resolution

Canonical check: `_TurnGoal.business_subject` contract (instruction resource v20, `turn_goal` + `select_capability#with_goal`) requires the field be copied from **user words only, never invented**. The prior test derived `"terminal pino"` from CALCULATION-class `DELIA_RESULT` prose — an unauthorized source under the contract. Canonical authorities confirm prior turns are never identifier provenance (doc 16) and anaphoric follow-ups are handled semantically via the OBSERVATION-gated `prior_observation` channel (commit 590e8e28d8 deliberate design, doc 20).

Resolution (clarification, not extension):

- `business_subject` derivation boundary made explicit in v21: **copied only from words the user actually wrote — in the current message or earlier user turns — never derived from assistant answers or tool output, never invented; null when none**. User-authored words across turns remain the same untrusted trust class; assistant-derived referents stay excluded. The referential channel for assistant content remains `prior_observation` (untrusted excerpt).
- `test_warm_path_goal_subject_reaches_selection` corrected: the prior `USER_INPUT` now names `"terminal pino"` itself, so the routed `business_subject` is a lawful production; the CALCULATION prior still proves the handoff covers the observation-gated gap.
- New contract-lock test `test_business_subject_derivation_contract_lock` pins the derivation boundary in the versioned resource; `test_subject_from_assistant_result_alone_not_transport_fabrication` proves transport fabricates nothing when no lawful subject exists.
- Residual: assistant-only referents with non-OBSERVATION priors remain a documented contractual limitation — extending `business_subject` to resolved referents from assistant output would need a separate architecture decision.

### C2 — JSON Envelope Integrity — fixed

Root cause confirmed and widened: `[:MAX_SURFACE_CHARS]` severed mid-JSON when optional fields were present, **and** the bare-list path (no optionals) applied no bound at all.

Structural fix in `_group_summaries` and `_capability_payload`:

- Optional fields (`prior_observation`, `business_subject`) reserve room up-front; the serialized envelope is never cut mid-document.
- Compaction ladder: equal description reduction across groups (fairness) → structural reduction of the bounded `untrusted_excerpt` (256→0→drop) → auxiliary group metadata strip (ids/names stay) → trailing capability omission, widest group first (no provider favoured), truthfully marked via `capabilities_omitted`.
- `business_subject` is always kept whole when included.
- Output is always valid JSON; `len <= MAX_SURFACE_CHARS` in every structurally feasible case.
- Redundant `[:MAX_SURFACE_CHARS]` at the `_select_foreign_capability` call site removed (builder now bounds the envelope).
- Same defect class in non-selection `json.dumps` blocks (records/resolver/schema/synthesis payloads at other stages) remains as residual — evidence blocks need per-shape treatment, not silent trimming; flagged for separate decision.

Tests: `test_selection_envelope_integrity.py` — 12 RED→GREEN boundary cases (small/near-limit/over-limit catalogs, max subject, max observation, both, unicode/escapes, bare-list compat, fairness, truthful omission markers, identifier completeness).

### Live evaluation (frozen: delia-json, num_ctx 8192, Ollama 0.40.8, instruction v21)

| Scenario | Result |
|---|---|
| ref_user (referent in prior USER turn) | subject `"exemplos"` (user word — lawful; weak 3B extraction), transported to select_group + select_capability; AUTHZ_DENIED at arguments (fail-closed on probe token) |
| ref_assistant_only (referent in DELIA_RESULT only) | subject `"exemplos"` — assistant-derived referent correctly NOT injected; observation gated out; NON_GROUNDED honest |
| ref_observation | `prior_observation` present; subject transported; chain reached arguments + resolver; CLARIFICATION_REQUIRED honest |
| subject_change | `business_subject="cliente"` — current-turn user word; correct |
| three_records / o2 / pino (cold path) | select_group valid JSON; NON_GROUNDED / typed ISO — 3B capacity variance, not transport |
| JSON validity | 100% of observed selection payloads parsed; all under MAX_SURFACE_CHARS |

`THREE_RECORDS_OUTCOME=NON_GROUNDED`, `O2_OUTCOME=NON_GROUNDED`, `FALSE_POSITIVES=0` — transport integrity proven; business-outcome variance remains 3B semantic capacity, unchanged by this rework.


## 11. Independent coordination review of C1/C2 rework — 2026-10-26

**VERDICT=ACCEPT_WITH_RESIDUAL for bounded C1/C2, NOT RELEASE ACCEPT.** GitHub static inspection of final `49dc645b0d1078a934ac13dfbc2dd9d51ee5a465`, executable diff, `test_selection_envelope_integrity.py`, goal-handoff tests, instruction resource v21 and execution doc 152. Executor reports 436 focused PASS, full backend EXIT=0 locally, live Ollama eval with zero false positives and non-grounded three-record/O2 outcomes; **not independently rerun**. No deploy authorized.

**C1 condition closed contractually:** v21 restricts `business_subject` to user-authored words in current or prior USER turns, never assistant/tool output. Tests no longer depend on CALCULATION assistant prose as a lawful derived subject. Projection into selection stays untrusted and does not grant AuthZ or evidence provenance. Referential recovery from assistant-only non-OBSERVATION history is an *explicit product/contract limitation*, not a defect to be repaired by inferring facts from assistant output.

**C2 core defect closed for tested feasible envelopes:** Removed serialized `[:MAX_SURFACE_CHARS]` cut from selection builders and foreign selection call; serializers now compact structurally and emit valid JSON with complete identifiers; `capabilities_omitted` reports omissions. Unit tests cover small/large catalogs and both optional fields. Important residuals: (R-C2a) terminal `return payload` after exhausting omissions has no guaranteed typed over-budget outcome if immutable group metadata + oversized optional subject cannot fit; tests do not demonstrate all pathological shapes. (R-C2b) omission of real capabilities is **not reachability**: under pressure all groups can remain named but some capabilities cease to be selectable by the LLM; `capabilities_omitted` is transparency, not coverage. Claims of "all capabilities reachable" must not be made. Review catalog fairness with representative owner surfaces under near-limit, because widest-group-first may reduce useful coverage. (R-C2c) description truncation/observation removal changes semantic relevance and can degrade implicit referents; mark omissions in measurements before attributing selection failures entirely to 3B. (R-C2d) non-selection serialized-string truncations in resolver, records, schema, synthesis remain known residual requiring **separate per-shape evidence-preserving remediation**, never global string-slicing patch.

**Business Outcome:** `three_records=NON_GROUNDED`, `O2=NON_GROUNDED`; cannot ascribe sole cause to model size without controlling for omitted catalog capabilities, remaining payload cuts and authoritative owner access. No new planner/memory/provider introduced; rework scope respected.

**Coordination:** Accept C1 and structural C2 corrections with explicitly bounded residuals. Retain **DEPLOY_BLOCKED**. Next bounded task should characterize whether non-selection cuts hit **required source evidence/schema** on failing chains, and whether omission markers affect selection coverage; authorize fixes only on proven handoffs under owner contracts and token budget. No generic inventory restart, no automatic model upgrade, no session persistence.


## 12. Evidence & schema projection integrity — C3 rework execution — 2026-10-26

Task: `DELIA-C3-EVIDENCE-SCHEMA-PROJECTION-INTEGRITY-AND-COVERAGE-01`
Base: `49dc645b0d` + `origin/main` advance; reference: §11 independent review (R-C2d residual).

### Truncation site matrix (all `json.dumps(...)[:MAX_*]` on structured blocks)

| Site (stage) | Budget | Defect class | Resolution |
|---|---|---|---|
| `_select_resolver` — resolver candidates | MAX_SURFACE_CHARS | DESTRUCTIVE_PROVEN | `_fit_json_block` — candidate descriptions shrink, then truthful `candidates_omitted` |
| `_prior_continuation_attempt` — records | MAX_SURFACE_CHARS | DESTRUCTIVE_PROVEN | tail omission + `records_omitted` |
| `_synthesize_content` — records | MAX_SURFACE_CHARS | DESTRUCTIVE_PROVEN | tail omission + `records_omitted` |
| `_corroborate_attempt` — `{left,right}` | MAX_SURFACE_CHARS | DESTRUCTIVE_PROVEN | balanced tail omission from the longer side + `left_omitted`/`right_omitted` |
| `_assess_native_path` — target group | MAX_SURFACE_CHARS | DESTRUCTIVE_PROVEN | drop `relevance_feedback` → cap descriptions → `capabilities_omitted` |
| `_select_prepare_continuation` — analysis + candidates | MAX_SURFACE_CHARS | DESTRUCTIVE_PROVEN | bounded `analysis` excerpt shrinks → descriptions → `candidates_omitted` |
| `_clarification_question` — missing inputs | MAX_SURFACE_CHARS | DESTRUCTIVE_PROVEN | description shrinks → `inputs_omitted` |
| `_judge_goal_evidence` — evidence records | MAX_RELEVANCE_EVIDENCE_CHARS | DESTRUCTIVE_PROVEN | tail omission + `records_omitted` |
| `_recover_relevance` — prior_result_preview (nested JSON-in-string) | MAX_EVIDENCE_RECORD_CHARS | DESTRUCTIVE_PROVEN | preview list structurally fitted + `records_omitted` |
| `_propose_index_probe` — capability + input_schema | MAX_ARGUMENTS_BLOCK_CHARS | DESTRUCTIVE_PROVEN | description shrinks; `input_schema` **never touched** — emits whole |
| `_propose_index_identifier` — owner index options | MAX_ARGUMENTS_BLOCK_CHARS | DESTRUCTIVE_PROVEN | hints/label shrink → `options_omitted` |
| `_build_arguments` — schema + evidence | MAX_ARGUMENTS_BLOCK_CHARS | DESTRUCTIVE_PROVEN | bounded evidence excerpts shrink → auxiliary fields drop; `input_schema` whole |
| `_propose_candidate_arguments` — inner schema | MAX_SURFACE_CHARS | DESTRUCTIVE_PROVEN | schema is the contract — emits whole via `_json_block` |
| `_resolved_values_proven` — provenance search corpus | MAX_OWNER_EVIDENCE_CHARS×4 | SAFE_BOUND | unchanged — bounded opaque corpus; worst case is a fail-closed false negative, never malformed consumer JSON |

Shared mechanism: `_fit_json_block(block, budget, *steps)` beside the C2 builders — ordered structural reductions (text-field bound → optional-field drop → trailing omission with truthful `*_omitted` marker); **the serialized output is always valid JSON**. When immutable mandatory content (schema, identifiers) cannot fit the projection budget the payload emits whole — the existing typed boundary decides: `MAX_INPUT_CHARS=16384` transport bound and/or `CONTEXT_TOO_LARGE` on the adapter-declared context window. No second budget, no new context engine.

Provenance hardening (`_build_arguments`): the `evidence_blocks` verification corpus for `apply_evidence_bound_selections` is synced to the post-projection text — a declared origin can only be proven against text the model actually saw (no fail-open on unprojected evidence).

Tests: `test_evidence_schema_projection_integrity.py` — 23 cases RED→GREEN. RED evidence: the same fixture shapes under the old `[:MAX]` cut produce `JSONDecodeError: Unterminated string` in all five measured envelope shapes (resolver/synthesis/evidence/arguments/candidate).

### Local evaluation (frozen: delia-json qwen2.5:3b, num_ctx 8192, Ollama, instruction v21, real api-delpi DAVI)

Eval environment note: the chain now reaches the real owner via delegated token exchange (`mcp-api-delpi` audience, `Host: localhost:8000`) — earlier runs used a different api build.

| Scenario | Stages | Blocks | json_valid | omissions | grounding | owner calls |
|---|---|---|---|---|---|---|
| three_records | 4 | 3 | 100% | 0 | NON_GROUNDED (honest insufficiency) | 0 |
| o2 | 3 | 1 | 100% | 0 | typed `invalid_structured_output` | 0 |
| pino | 3 | 1 | 100% | 0 | NON_GROUNDED (conversational fallback; illustrative text, no owner provenance) | 0 |
| ref_user | 12 | 10 | 100% | 0 | GROUNDED path; honest insufficient-pertinence wording | 5 (davi discover+execute) |
| ref_observation | 6 | 4 | 100% | 0 | GROUNDED; honest empty-result | 2 |
| subject_change | 9 | 7 | 100% | 0 | NON_GROUNDED; honest "no record" | 1 |
| ref_assistant_only | 1 | 0 | n/a | 0 | NON_GROUNDED — assistant-derived referent correctly not injected | 0 |

Baseline comparison (same model/config, pre-fix orchestration): three_records took a clarification path (6 stages, 0 invokes, NON_GROUNDED); ref_user stopped at admission (1 stage, NON_GROUNDED). Both baselines also produced valid JSON on the small real catalog — the destructive defect requires size pressure; n=1 model variance prevents outcome attribution, so no business-outcome improvement is claimed.

Catalog coverage (WP4): the real owner surface is small (1 group, ~2–4 capabilities, ~800–900 chars) — fits the projection budget entirely; `CAPABILITIES_OMITTED=0` observed on every live run. Under synthetic pressure the C2 compaction keeps all group identifiers listed and marks per-group `capabilities_omitted` truthfully; widest-group-first is a fairness policy, not coverage — `capabilities_omitted` remains transparency, never a reachability proof. No legitimate-capability loss reproduced on the real surface.

Residuals: (a) `business_subject` transport is mechanism-ready but the 3B did not emit the field in proposals during these runs — semantic capacity, not transport loss; (b) `pino` conversational fallback produced illustrative product text with no owner provenance — correctly NON_GROUNDED, but general-knowledge content quality is a separate concern; (c) inner bounded excerpts (descriptions, `untrusted_excerpt`, `analysis`) remain `SAFE_BOUND` by contract; (d) `_resolved_values_proven` corpus cut remains SAFE_BOUND.


## 13. Independent review — evidence/schema projection integrity — 2026-10-26

**VERDICT=ACCEPT_WITH_RESIDUAL (bounded implementation), BUSINESS_OUTCOME=NOT_PROVEN, DEPLOY_AUTHORIZED=NO.** Static GitHub independent inspection of commit `859632601b474d94076f3d75e6599f13c0e7167b` and current HEAD (newer docs-only/main movement possible). Executor reports 23 RED/GREEN, full backend green locally after fixture mount repair, architecture gates clean, live 28 parsed blocks/7 scenarios all valid JSON with 0 observed omissions; these tests and runtime traces were NOT independently executed here.

**Proven in diff:** 13 structured JSON slicing sites converted to builder-based fit/whole serialization; `input_schema`/candidate schema preserved whole, record tail omissions marked, evidence source checks rebound to projected owner/foreign evidence, and catalog test says real surface fits without omission. Reuses existing ports and budgets; no planner/provider/memory added.

**R1 — terminal over-budget handoff:** `_fit_json_block` returns full valid JSON if all reductions exhausted even when `len(payload)>budget`. The later `InvokeModel` token-budget gate only rejects if an effective adapter context window is declared and estimated prompt exceeds it; it does not enforce the distinct `MAX_SURFACE_CHARS` per-block cap, and unknown window disables token enforcement. Thus 'fails closed whenever immutable content cannot fit the local block budget' is not universally proven. Require a bounded negative test under declared and unknown window for oversized mandatory schema; distinguish local block ceiling from provider context window. Do not silently cut schema.

**R2 — omission semantics and decision quality:** Truthful `records_omitted`, `options_omitted`, etc. mark projected data lost to model, not necessarily sufficient records to complete the user goal; particularly corroboration removes records from left/right independently, and clarification may omit missing required inputs. Downstream judge/synthesis/recovery must not certify completeness on omitted evidence. Verify explicit omission contract consumption, not only JSON.parse and marker integer. `prior_result_preview` changes from serialized JSON array to nested JSON object encoded as text; consumer compatibility merits test under relevance recovery.

**R3 — conservative claim on cause of outcome:** three-record and O2 outcome still negative or typed error in n=1 and cases diverged at admission/goal, but evidence does not isolate model size as exclusive root cause. No live omission was observed, which limits conclusions about pressure paths; no tokens/latency delta measured. Do not autoauthorize model switch nor further broad refactor.

**Next bounded step:** target contract validation of overflow/no-window cases, omission-aware verdicts, and recovery-preview compatibility with RED characterization (not another inventory or automatic engine), then revisit outcome trace under a frozen local configuration. Independent review and release gates remain separate; no production deploy authorized.
