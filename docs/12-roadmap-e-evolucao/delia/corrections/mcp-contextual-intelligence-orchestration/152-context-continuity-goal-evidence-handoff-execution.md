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


## 14. Overflow / omission / recovery-preview contract rework — R1/R2/R3 closure — 2026-10-26

Bounded follow-on to the §13 independent review (`5ba117db5028de37b5fbe55ca3b5d918601815f6`), task `DELIA-C3-PROJECTION-OVERFLOW-OMISSION-RECOVERY-CONTRACT-REWORK-01`, base `859632601b`.

### R1 — overflow contract layering (pinned, no new budget)

| Layer | Bound | Enforcement | Failure |
|---|---|---|---|
| per-block `MAX_*` | compaction target | `_fit_json_block` ordered reductions | emits WHOLE valid JSON + warning; never severs |
| transport | `MAX_INPUT_CHARS=16384` | `InvokeModel` input gate, always on | `INVALID_REQUEST` before dispatch |
| model window | adapter `context_window_tokens` | `apply_context_budget` when declared | `CONTEXT_TOO_LARGE` before dispatch |

Unknown window (`context_window_tokens=None`) disables only the token layer — the transport bound still fails closed on mandatory content beyond 16384 chars. Between the compaction target and the transport bound a mandatory payload dispatches whole and valid; that is the documented residual, not silent corruption — the emitted document is never truncated mid-JSON. Tests pin all regimes: under-target, over-target/under-transport (dispatch whole), declared-window overflow (`CONTEXT_TOO_LARGE`), over-transport with unknown window (`INVALID_REQUEST`), plus exact-boundary and escaped-Unicode roundtrips. `_fit_json_block` now logs a warning on exhausted fits so the event stays traceable.

### R2 — omission-aware consumption (fail-open closed)

Proven defect class: model selections were bound to the FULL source list while the model only saw the projected prefix — an index/name matching only an omitted tail entry was treated as a valid selection (fail-open). Closed at every deterministic consumer:

| Stage | Marker | Binding now proven against |
|---|---|---|
| grounded synthesis | `records_omitted` | projected record prefix (`_render_synthesis` + select-all-replay guard) |
| prior-turn continuation | `records_omitted` | projected record prefix + `evidence_projection_partial` limitation |
| comparison | `left_omitted`/`right_omitted` | projected left/right prefixes + `evidence_projection_partial` limitation |
| capability selection (+with_goal) | `capabilities_omitted` | `_projected_capability_names(payload)` ∩ invocable |
| resolver selection | `candidates_omitted` | projected candidate names |
| prepare continuation | `candidates_omitted` | projected candidate names |
| index identifier | `options_omitted` | projected `identifier` set |
| clarification | `inputs_omitted` | marker truthful; question words only listed inputs |
| goal-evidence relevance | `records_omitted` | block carries truthful count; verdict remains semantic |

New canonical limitation code `LIMITATION_EVIDENCE_PROJECTION_PARTIAL` (interaction contracts) — surfaces when the consumed record list was truncated by projection; synthesis/comparison/prior-continuation carry it, so a partial projection can never read as a complete owner answer. v22 instruction clauses define every `*_omitted` marker and the `prior_result_preview` object shape for the semantic consumers.

### R3 — prior_result_preview compatibility (pinned)

`prior_result_preview` is a JSON **object** string `{"records": [...], "records_omitted"?: N}` nested inside the outer feedback JSON. Consumers are LLM-only (semantic re-selection/reformulation); the deterministic boundary never parses the inner preview into authority. Tests pin: object-with-records shape, `records_omitted` under pressure, empty preview, and injection-shaped record text surviving as escaped inert data. Recovery stays bounded (one governed round; identical-query re-execution still forbidden).

### Tests and runtime evidence

- `test_projection_omission_recovery_contract.py` — 25 cases. RED proven on baseline (`git stash` of the fix): baseline selected `resolve_3` never projected, rendered synthesis index 4 outside the projected prefix, and bound an omitted capability — the exact fail-open the review described. Post-fix: GREEN.
- Focused suites: continuity/selection/envelope/relevance/C3/R1-resource — all green.
- Live Ollama eval (frozen: delia-json qwen2.5:3b, num_ctx 8192, instruction v22, real api-delpi DAVI via delegated exchange): 7 scenarios, 31/31 captured blocks valid JSON; two over-compaction-target blocks (8599/7416 chars vs 6000 target) emitted whole and valid — the R1 layering operating live; `business_subject` observed propagating into `foreign_selection`; one governed recovery round executed on three_records; all outcomes honest (GROUNDED-with-insufficient-content or NON_GROUNDED); FALSE_POSITIVES=0.

Residuals: (a) unknown-window admits whole payloads up to the transport bound — documented; hardening further requires an adapter-declared window (architecture decision, not silently implemented); (b) 3B semantic capacity remains the outcome limiter — no business-outcome claim; (c) token/latency recorded from probe usage (three_records: 24351 in / 402 out / 18.0s across 12 stages incl. recovery).


## 15. Independent coordination review — f24ceddf6b — 2026-10-26

**VERDICT=ACCEPT_WITH_RESIDUAL** for bounded R1/R2/R3 implementation, **DEPLOY_AUTHORIZED=NO**. Independent STATIC GitHub code/diff review at final commit `f24ceddf6b9c99513ca6d186a998717dea16be87`, plus executor report; backend/real Ollama not independently rerun. Executor reports 25 RED/green contract tests, 126 focused PASS, CI architecture clean and full backend green in clean environment, 31/31 parsed blocks valid, 0 reported fabricated records, but three-record and O2 business outcomes not achieved. No full release acceptance.

**Verified strengths:** `_projected_capability_names` and projected-membership filters now refuse selecting capability IDs removed from model-visible catalog; resolver, prepare and index identifiers likewise bound to their projected lists. Synthesis/prior-turn render bind to `block["records"]` actually presented; comparison operates on projected left/right; `LIMITATION_EVIDENCE_PROJECTION_PARTIAL` is propagated in certain result paths. `_fit_json_block` clearly declares local budget a compaction target and logs overflow rather than slicing immutable schemas. Preview's nested JSON object-string format preserved with tests as reported.

**Residual A — hard vs soft bounds:** after exhausted fit, payload may remain above `MAX_SURFACE_CHARS`; declared-model-window budget can reject, but unknown window disables that enforcement. Transport MAX_INPUT_CHARS applies only if the assembled request passes that boundary; do not claim fail-closed for every local overflow. Operational release requires declared/effective context parity and explicit over-target observability, especially if evaluation had two blocks >6000.

**Residual B — omission semantics not universally closed:** a limitation tuple records some projected partial results, but does not itself establish that consumers block a `GROUNDED` status / agreement / requested count based on the missing records. Verify exact downstream use of `evidence_projection_partial` in authoritative Outcome/presentation gates; specifically whether synthesis returns `rendered` with limitation and any final surface still implies complete answer. The deterministic binding prevents fabricated indexes, not all false completeness. Do not equate 0 sample false positives with universal guarantee.

**Residual C — post-projection payload mutation:** in `_select_capability` the projected allowed set is computed from `cap_payload`, then `relevance_feedback` is embedded later by another serialization path. Check whether the actual dispatched block is identical for capability membership, marker and size and whether the later serialization can invalidate the `MAX_SURFACE_CHARS` target. Only modify after a RED test demonstrates a mismatch.

**Residual D — provenance/preview:** `_build_arguments` rebinding `evidence_blocks` to projected text is directionally correct; ensure no implicit fallback to unprojected owner data across validator paths. Nested `prior_result_preview` compatibility is pinned at the existing LLM consumer; not authority. Preserve injected strings as inert data.

**Outcome interpretation:** The three-record case reportedly reached 12 stages and an honest empty-owner-data answer; this is NOT success in retrieving three records. `GROUNDED` status on a sourced empty response must be explained separately from `business_outcome=FAIL`. O2 = non-grounded. Remaining failures cannot yet be attributed exclusively to 3B; admission/goal, owner availability and matching remain competing explanations.

**NEXT:** Stop broad context rewrites. One narrow evidence audit of residual B/C on HEAD with tests of final business-outcome gating and actual dispatched block (incl relevance feedback); fix only demonstrated defects. Keep deploy blocked pending review, runtime parity and owner/outcome evidence. Do not add a planner, new taxonomy, model swap or session persistence.


## 16. Residual B/C closure — outcome completeness & final payload consistency — 2026-10-26

Task `DELIA-C3-OUTCOME-COMPLETENESS-FINAL-PAYLOAD-CONSISTENCY-01`, base `f24ceddf6b`, closing the two residuals the independent review (§15) marked for a narrow evidence audit. No planner, engine, registry, memory, provider or second budget added; both fixes extend existing owners.

### B — partial evidence must not read as complete

Causal record:

- PRODUCER: `_records_payload`/`_fit_json_block` writes `records_omitted=N` into the evidence block.
- ORIGINAL_DATA: owner record set (e.g., 5 records).
- PROJECTED_DATA: fitted prefix (e.g., 3) + `records_omitted=2`.
- ACTUAL_MODEL_PAYLOAD: block with marker.
- CONSUMER: `_synthesize_content`/`_prior_continuation_attempt` → `_render_synthesis` → `_list_header`.
- VALIDATION_INPUT: `record_index` already bound to projected prefix (R2); `has_more` taken only from the owner pagination envelope.
- OUTPUT: header rendered `Encontrei N registros:` even when `records_omitted>0` — an unqualified completeness read on a partial projection.
- FIRST_DIVERGENCE: presentation gate never received the projection-omission signal.
- ROOT_CAUSE: `projected_omitted` never threaded to `_render_synthesis`/`_list_header`.

Fix (bounded): `conversational_response._render_synthesis` accepts `projected_omitted`; both call sites pass `bool(block.get("records_omitted"))`; `_list_header` qualifies the count when the projection was partial (partial-but-useful stays presentable, never as exhaustive). `LIMITATION_EVIDENCE_PROJECTION_PARTIAL` propagation through attempt→turn→result was verified end-to-end (already existed). `GROUNDED` remains a provenance state, not a business-outcome verdict: an authoritative empty/partial result stays honest.

### C — validation must bind to the dispatched payload

Causal record:

- PRODUCER: `_select_capability` built `cap_payload` via `_capability_payload`, computed `visible` names from it, then wrapped `{"capabilities": json.loads(cap_payload), "relevance_feedback": …}` without re-fitting.
- ORIGINAL_DATA: eligible capabilities + feedback.
- PROJECTED_DATA: fitted capability list — object form `{capabilities, capabilities_omitted}` under pressure.
- ACTUAL_MODEL_PAYLOAD (baseline): object-form inner payload became `{"capabilities": {"capabilities": [...], "capabilities_omitted": N}, ...}` — nested shape the membership contract cannot read at the documented path; marker buried one level deep; final size never re-budgeted after feedback.
- CONSUMER: selection membership validation.
- VALIDATION_INPUT (baseline): pre-wrap payload — diverged from dispatched shape under object-form projection.
- OUTPUT: RED — `names=∅ marker=0` on the dispatched block while validation used the pre-wrap set. Foreign selection additionally bound `capability_id` against the full foreign group — `beta.read_5` resolved despite being omitted from the dispatched summaries (fail-open). `_select_group` showed the same wrap defect shape-wise (nested `capability_groups` under optionals) though groups are never omitted, so its membership could not diverge.
- FIRST_DIVERGENCE: wrap executed after validation-input capture; no re-fit of the final block; foreign path had no projected-id binding at all.
- ROOT_CAUSE: final payload assembled after the selectable universe was extracted.

Fix (bounded): `_select_capability` assembles `{"capabilities": <projected entries>, "capabilities_omitted": N, "relevance_feedback": …}` first, re-fits the final block, and computes `visible` from that same dispatched payload; `_projected_capability_ids` binds foreign `capability_id` proposals to the ids actually present in the dispatched group summaries. The sibling defect in `_select_group` (feedback wrap over object-form summaries → nested `capability_groups.capability_groups` whenever `business_subject`/`prior_observation` was present) is flattened the same way and re-fitted; groups remain never-omitted, preserving the all-groups-visible invariant and `_resolve_live_group_key` membership. Tag-like feedback (`</capabilities>` inside strings) stays inert data — the envelope is prompt formatting, not a parse boundary for any consumer.

### Tests and runtime evidence

- `test_outcome_completeness_final_payload.py` — 15 cases (B1–B9 characterization + C1–C8). Causal RED on baseline checkout: `test_b2`, `test_b4` (partial projection rendered as complete count), `test_c3` (nested capabilities shape — dispatched block unreadable to membership contract), `test_c_foreign_selection_rejects_omitted_capability` (unprojected `beta.read_5` resolved), `test_c_group_selection_flat_final_payload_with_feedback` + `test_c_group_selection_feedback_pressure_stays_fitted` (nested `capability_groups` shape reproduced on baseline). Post-fix: GREEN.
- Focused regression: outcome assessment, projection integrity, C3 consumption, synthesis, continuity, comparison, selection quality/envelope, recovery, context budget, model invocation, adapters, presentation, CRI E1–E3, security, resume, generalization — all green. Full backend suite green (clean env). Architecture gates: 0 findings.
- Live Ollama eval (delia-json qwen2.5:3b, ctx 8192, instruction v22, real api-delpi DAVI via delegated exchange): 8 scenarios; 29/29 captured blocks valid JSON; three_bala reached 3 real DAVI invokes and ended in honest clarification; comparison ended honest authorization-denied; write_request refused as unauthorized; one typed `invalid_model_output` bounded failure. An invented foreign `capability_id` (`mcp:vista.get_catalog`) was rejected fail-closed live. `FALSE_POSITIVES=0`; `FALSE_COMPLETENESS=0`. Semantic capacity (3B routing) remains the outcome limiter — unchanged, documented.

Residuals: (a) Residual A (unknown-window over-target) still requires an adapter-declared window — architecture decision; (b) 3B semantic capacity — no model swap claimed; (c) completeness judgement beyond the rendered-header gate remains bounded to deterministic signals (markers, owner pagination), not LLM-declared.


## 17. Independent coordination review — f0ef92e789 — 2026-10-26

**VERDICT=ACCEPT_WITH_RESIDUAL (bounded B/C closure), DEPLOY_AUTHORIZED=NO, BUSINESS_OUTCOME=NOT_PROVEN.** Independently inspected GitHub commit `f0ef92e7890888afc8eb418a4ce22779dd7f2641`, its five-file diff and test fixture `test_outcome_completeness_final_payload.py`. No independent local pytest or Ollama rerun; 15 RED tests, ~500 focused green, backend clean green and local 8-scenario evaluation are executor-reported.

**B — FIX VERIFIED IN CODE:** `_synthesize_content` and `_prior_continuation_attempt` propagate `block['records_omitted']` into `_render_synthesis/_list_header`; an omitted-prefix rendering explicitly says the list is non-exhaustive while preserving `LIMITATION_EVIDENCE_PROJECTION_PARTIAL`. This retains valid partial examples and avoids claiming a complete source list. Provenance grounding remains distinct from satisfying the requested number/coverage. Note tests are mostly at helper/attempt surface; end-to-end count/goal satisfaction must remain its own outcome evidence.

**C — FIX VERIFIED IN CODE:** `_select_group` and `_select_capability` flatten the feedback envelope and call structural fit before invoking the model; `_select_capability` computes `_projected_capability_names` on the exact final string. Foreign capability selection now validates selected `capability_id` against ids serialized into the same dispatched group payload. This closes the identified pre/post wrap membership defect and nested-envelope shape error without new orchestration mechanism.

**Residual R-C1:** `_select_group` preserves all group summaries and may return an over-target block when optional fields are exhausted; this is already the explicitly documented soft compaction-target layering, not newly resolved. Retain release gate on declared/effective context parity and authoritative transport bound.

**Residual R-B1:** A header qualified as non-exhaustive is a presentation guarantee, not an independently verified business-outcome evaluator. `GROUNDED` for sourced no-data/partial records cannot be interpreted as user-request success. The three-record case still reached clarification after real DAVI calls, and O2 remained NON_GROUNDED; no positive record-count acceptance.

**Residual R-C2:** Re-fitting capability selection under heavy feedback uses trailing omission of real capability entries before dropping oversized feedback; this can degrade achievable selection coverage. Omission remains visible and excluded by membership checks, but representativeness and token/latency behavior on larger real catalogs are not proven in 8 local scenarios. Do not introduce provider-specific ranking heuristics without evidence.

**Next coordination:** Close this B/C scope as accepted-with-residual and stop iterative context plumbing changes without new causal evidence. Prioritize a **frozen-SHA semantic admission/goal/argument-fidelity evaluation** with authoritative outcome labels and a minimally sufficient corpus (multiple repetitions), keeping model 3B as baseline and no automatic model switch. Deployment remains blocked pending independent runtime/operational verification.
