# 62 — G0 bounded I04 remediation (compare outcome + C02 budget)

**DATE:** 2026-10-19  
**TASK_ID:** `DELIA-C3-I04-G0-SINGLE-BOUNDED-REMEDIATION-01`  
**BASE_REFERENCE:** `fc93fbf3591a8115bd238a4c05af6c5b8a1c7361`  
**AUTHORITY:** Option A §6.304 / doc 61 §8 — `G0_REMEDIATION_AUTHORIZED=YES`; `Q01_AUTHORIZED=NO`  
**STATUS:** `IMPLEMENTATION_CANDIDATE`

## Reuse gate

| Responsibility | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| Prior continuation / synthesis | YES | **EXTEND** (compare ≠ list replay) |
| Interaction admission instruction | YES | **EXTEND** (formats/guidance catalogs → owner) |
| Conversational fallback after NOT_APPLICABLE | YES | **EXTEND** (stage cap + soft-land on timeout) |
| New planner / provider branches / free factual prose | — | **FORBIDDEN** |

## G0-01 — Compare vs list

**ROOT_CAUSE (PROVEN):** `recover_empty_selection` projected prior bullets as a list SUCCESS for compare/analyze asks (F33). Live L5 returned «Recuperei 2 itens…» counted as continuity latency PASS but **FAIL_TASK_OUTCOME** for comparison.

**FIX:** When `comparison_requested` / compare|analyze, never recover empty synthesis as a list. Prefer deterministic segment diffs from prior bullet units (`a — b — c`), else explicit insufficiency (`LIMITATION_INSUFFICIENT_EVIDENCE`). List replay after a successful synthesis is replaced the same way.

**TESTS:** `test_g0_01_compare_empty_selection_is_not_list_success`, opaque-prose insufficiency, segment helpers; CONT-T03 updated.

## G0-02 — VISTA C02 HTTP 504

**ROOT_CAUSE (PROVEN from prod logs, corr `089e31c8` / request `aa47991a`):**
1. `interaction_admission` classified «Quais formatos de dados estão disponíveis?» as **conversational** (~4.9s).
2. Orchestrator returned `NOT_APPLICABLE`.
3. Handler free-form fallback invoked the general model until **`model_timeout`** → HTTP **504** (~30s).

Not a VISTA owner hang: owner was never selected. Sibling earlier turn wrongly selected TEO methodology for a formatos-like ask (selection residual; not patched with specialist branches).

**FIX (provider-neutral):**
1. Admission instruction: owner-published formats/topics/guides/panels catalogs require `requires_owner_surface=true` / `operational`.
2. After governed `NOT_APPLICABLE`, cap conversational fallback stage at 12s and soft-land timeout into bounded NON_GROUNDED content (`turn_budget_limited`) instead of raising `MODEL_TIMEOUT`→504.

**TESTS:** soft-land timeout; admission instruction lock; fallback timeout ≤12s.

## Live

Password-grant for subject `user` returned `invalid_grant` at execution time; cached JWTs expired. **LIVE_POST_FIX=`TEST_NOT_RUN`** (auth blocker). Historical C02 stage chain remains the proven baseline for the patch.

## Gates

```text
I04_ACCEPTED=NO
G0_REMEDIATION_EXECUTED=YES
Q01_AUTHORIZED=NO
Q02_AUTHORIZED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_G0_REVIEW
```


## Coordination v10 — independent G0 review of implementation 95e6c612 (2026-10-19)

**REVIEW_VERDICT=REWORK** (one bounded rework allowed under roadmap 59; do not release Q01). Base comparison `fc93fbf359 → 95e6c612`: 2 commits, 9 files including unrelated concurrent Protheus identity documentation commits; G0 implementation itself touched orchestration.py, handle_interactive_turn.py, two test files, this doc, README and ledger §6.305. Preserved concurrent changes; source blob differs from old audit snapshot, as expected.

### Evidence accepted / not independently verified

- **PROVEN STATIC:** existing `OperationalCapabilityOrchestrator`, typed goal, `InvokeModel`, `TurnDeadline`, selection-only owner renderer, existing provider-neutral paths reused; no visible new planner, provider branches or public DTO/OpenAPI changes in G0 diff.
- **PROVEN STATIC:** compare empty-selection no longer replays the old full bullet list; fallback after `NOT_APPLICABLE` caps model invocation at 12 seconds and catches `MODEL_TIMEOUT` to return a bounded `NON_GROUNDED` message with `turn_budget_limited`.
- **EXECUTOR-REPORTED TESTS:** full `delia-api` pytest PASS and new unit tests PASS, not independently re-executed by GPT. Runtime/live post-fix `TEST_NOT_RUN` (reported `invalid_grant` / expired delegated JWT), no deploy, no cold/warm evaluation. Historical VISTA C02 stage evidence is a documented executor report; exact logs were not independently re-read in this review.
- **G0-02 residual:** instruction-string test asserts the words 'formats'/'operational', not an actual model decision or VISTA owner routing. A timeout soft-land prevents an edge HTTP 504 in a simulated path but does not prove C02 task outcome or eliminate wrong-owner TÉO selection. Keep `I04_ACCEPTED=NO`.

### Blocking finding G0-01: prior text positional comparison is not typed comparable evidence

`_segment_compare_prior_units()` splits rendered conversational lines by the ' — ' punctuation, silently uses `min(len(left_parts),len(right_parts),MAX_SYNTHESIS_FIELDS)`, and labels adjacent strings as differences; `_comparison_from_prior_excerpts()` chooses the first two bullet units even when an ordinal/subset might request others. Those lines are produced by `_prior_excerpt_records`, whose docstring explicitly calls them **untrusted conversational data, never live owner facts**. The helper does not verify attribute names, units, grain, schema, owner/source refs, selection of two intended records, equal cardinality or authoritative comparability. It can emit positional identifier/name differences as a 'Comparação' and bypass an empty/invalid model selection. The `_render_is_list_replay_not_compare()` success heuristic trusts literal headers 'Diferenças comprovadas:'/'Comparação:', not a typed task outcome. Test `test_g0_01_compare_empty_selection_is_not_list_success` currently rewards the questionable output and checks that `LIMITATION_INSUFFICIENT_EVIDENCE` is absent. This is a material contractual/data quality risk, not a merely unverified richer UX.

**Required single bounded rework:** On a compare/analyze request, if the prior context only offers free-text excerpts (not validated typed owner records and comparable fields under the existing frozen contract), return **explicit insufficiency with** `LIMITATION_PRIOR_TURN_CONTINUATION` + `LIMITATION_INSUFFICIENT_EVIDENCE` and truthful `NON_GROUNDED` handling; never convert formatted text to field-equivalent differences. Remove or disable the newly introduced positional segment compare and text-header-as-success paths where they could classify a compare task as accomplished. Do **not** rewrite/disable legitimate typed field-level owner comparisons elsewhere or broaden new contracts; use existing insufficiency helpers and current goal flags. No new planner/provider special casing and no model-authored factual prose. If typed owner comparison under current contract is demonstrably achievable, preserve it with direct owner-ref/schema evidence; otherwise do not claim business comparison succeeded.

**Mandatory RED/green additions:** different-length segment lines, swapped field order, arbitrary delimiter in content, compare second/third among 3 bullets, fake prior identifier, prior paraphrase/hypothesis vs owner fact, deceptive 'Comparação:' heading, empty/invalid synthesis and safe insufficiency; preserve subset/list-only follow-ups. Maintain existing 12s fallback and add actual admitted owner-selection behavioral assertion with fake model if possible inside existing test harness (an instruction literal assertion alone is insufficient). Full delia-api regression and zero ACT/security, strict 30s; live when identity/deploy authorization becomes available and record `TEST_NOT_RUN` otherwise.

**SCOPE LIMIT:** one bounded rework of G0-01 correctness and directly related G0-02 behavioral assertion only, **not** Q02-A/B/C. After this rework, if blockers persist, STOP→ROOT_CAUSE/OWNER/ARCHITECTURE_DECISION, no iteration chain. Failed independent live replay prevents I04 acceptance regardless of unit PASS. `ARCHITECTURE_DECISION_REQUIRED=NO` for safe insufficiency within existing contract; changing frozen synthesis/comparability instead would require new Product Master approval.

```text
REVIEWED_SHA=95e6c612649d98c47c6cd94c9fd4892c41f8ecea
REVIEW_VERDICT=REWORK
BLOCKER=G0_01_UNTRUSTED_POSITIONAL_STRING_COMPARISON
G0_02_STATIC_BUDGET_MITIGATION=PROVEN
G0_02_LIVE_TASK_OUTCOME=TEST_NOT_RUN
REWORK_QUOTA_REMAINING=1
I04_ACCEPTED=NO
Q01_AUTHORIZED=NO
Q02_AUTHORIZED=NO
C3_EXECUTED=NO
NEXT=SINGLE_BOUNDED_G0_REWORK_THEN_STOP_OR_REVIEW
```


## Bounded rework execution (DELIA-C3-I04-G0-BOUNDED-REWORK-01)

**DATE:** 2026-10-19. **REFERENCE_HEAD:** `8e7eb9640f6b5aa13b10b8f6978ac2e81b10afbc` (§6.306). Ledger: §6.308.

### Change

- **Removed** `_segment_compare_prior_units` / `_comparison_from_prior_excerpts` and all paths that converted free-text prior bullets into «Comparação» SUCCESS.
- **Compare/analyze** over prior continuation now requires `_prior_supports_typed_attribute_compare` (≥2 records sharing non-`excerpt` scalar fields). Current `_prior_excerpt_records` yields only excerpts → **explicit insufficiency** with `LIMITATION_PRIOR_TURN_CONTINUATION` + `LIMITATION_INSUFFICIENT_EVIDENCE` before synthesis.
- Empty/invalid synthesis and list replay on compare also fail closed to insufficiency. Only `Diferenças comprovadas:` counts as typed compare outcome (`_typed_compare_outcome_content`); bare `Comparação:` headers are rejected.
- **Preserved:** subset/list empty_selection recovery for non-compare; G0-02 12s conversational fallback soft-land.
- **G0-02 harness:** simulated admission with `requires_owner_surface=true` / `operational` routes formats ask into capability selection (not conversational NOT_APPLICABLE).

### Tests

RED/GREEN in `test_provider_neutral_semantic_provenance_and_continuity.py` (reorder, unequal segments, delimiter-in-value, 2nd/3rd items, fake id, invalid index, misleading header, typed-field helper). Admission behavioral + soft-land in `test_conversational_intelligence_recovery.py`. Full `delia-api` pytest PASS.

### Gates

```text
G0_BOUNDED_REWORK_EXECUTED=YES
G0_BOUNDED_REWORK_REMAINING=0
I04_ACCEPTED=NO
Q01_AUTHORIZED=NO
LIVE_POST_REWORK=TEST_NOT_RUN
NEXT=COORDINATION_INDEPENDENT_G0_REWORK_REVIEW
```


## Coordination v10 — final independent bounded-rework review (2026-10-19)

**REVIEWED_IMPLEMENTATION_SHA:** `cca468a365bd592498caa0be8cb20c8e0a6f75fe`. **MAIN_ON_REVIEW:** `9bad54ce583370fd6c75bd544d3181c914d218bd` (subsequent unrelated concurrent Protheus and production-control changes; the evaluated DÉLIA orchestration and interaction files remain at the reviewed blobs; any future runtime evaluation must revalidate HEAD). **REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL FOR BOUNDED REWORK ONLY**. **G0_I04_EXIT=BLOCKED_PENDING_LIVE_EVIDENCE**; `I04_ACCEPTED=NO`. The review is based on GitHub source/diff/tests and the executor report, **not** independent pytest execution or live replay.

### Findings and disposition

1. **REWORK BLOCKER CLOSED IN CURRENT FLOW:** `_segment_compare_prior_units` and `_comparison_from_prior_excerpts` removed. `_prior_continuation_attempt` rejects compare/analyze requests whose `_prior_excerpt_records` contain only untrusted `excerpt` strings, returning `LIMITATION_PRIOR_TURN_CONTINUATION` + `LIMITATION_INSUFFICIENT_EVIDENCE` rather than formatting positional fake differences. Invalid selections, empty selections and list replay are rejected for comparison. Noncompare extraction/subset path retained. `MODEL_AUTHORED_FACTUAL_PROSE=NONE` and selection-only remain frozen.
2. **RESIDUAL DESIGN — NOT A PROVEN TYPED PROVENANCE GATE:** `_prior_supports_typed_attribute_compare` checks two records' shared non-excerpt scalar keys, **not** SourceRef, owner source, types/units/grain or meaningful comparability. In the current call path its input originates from `_prior_excerpt_records` which returns only `excerpt`, so it fails closed; its positive helper test with fabricated dicts is NOT proof of owner-grounded comparison. `_typed_compare_outcome_content` checks the literal string `Diferenças comprovadas:`, not an authoritative outcome; its header-based permissiveness must never be reused as a general outcome/provenance validator. No further G0 code iteration is authorized; review genuine typed owner compare under Q02-C/contract gate only if phase is later authorized.
3. **G0-02 C02:** 12s post-NOT_APPLICABLE conversational stage cap and NON_GROUNDED `turn_budget_limited` soft-land preserved. Simulated admission sets `requires_owner_surface=true` as a *model fake* and establishes routing to live capability selection (a test of downstream wiring, not of real-model semantic admission or correct VISTA vs TÉO selection). Historical owner-never-invoked C02 root cause remains executor-reported. Live owner routing/outcome and cold/warm ≤30s are unverified on this SHA.
4. **TEST EVIDENCE:** 40/40 targeted, 12/12 bounded filter, 1647 collected full pytest PASS, security/ACT subset PASS are **EXECUTOR_REPORTED**, not GPT-independent re-executions; residual search old segment helpers absent reported, source reviewed confirms removal in this module. `LIVE_POST_REWORK=TEST_NOT_RUN`; `DEPLOY=NOT_RUN`; `INDEPENDENT_COLD_WARM=TEST_NOT_RUN` because delegated identity and authorized deploy not available. No evidence authorizes `I04_ACCEPTED=YES` or `Q01_AUTHORIZED=YES`.
5. **NONBLOCKING:** stale `_prior_continuation_attempt` docstring refers to 'deterministic segment comparison' but runtime path now rejects it. Record as residual documentation drift, not permission for another G0 patch.

### Anti-loop and next bounded decision

`G0_BOUNDED_REWORK_REMAINING=0`. Implementation/rework cycle is CLOSED; **no extra code patch in G0**. Keep roadmap59 six packages unchanged and preserve the higher-authority I04→Q01 gate. The only valid next evidence activity under Option A is a **non-code, authorized deployment and independent live read-only replay** of the predeclared G0 matrix on exact SHA/config/model/identity/owner surfaces, with stage traces, real comparative task honesty, VISTA C02 and no-tool, DAVI/TÉO/HTTP, negative IDs/injection, 0 ACT and cold/warm 30s. Production/auth runbook and legitimate user-delegated identity are prerequisites; credentials must not be fabricated or logged. If these prerequisites remain unavailable or failures persist, `STOP → ROOT_CAUSE / OWNER (Keycloak or deploy/owner environment) → PRODUCT_MASTER_PHASE_OR_CONTRACT_DECISION`; Option B still needs explicit canonical amendment; do not launch Q01 from docs-only acceptance. A validation-only replay is **not** a second implementation rework.

```text
REVIEWED_SHA=cca468a365bd592498caa0be8cb20c8e0a6f75fe
G0_BOUNDED_REWORK_REVIEW=ACCEPT_WITH_RESIDUAL
G0_IMPLEMENTATION_CYCLE=CLOSED
G0_REWORK_REMAINING=0
I04_ACCEPTED=NO
G0_I04_EXIT=BLOCKED_PENDING_LIVE_EVIDENCE
INDEPENDENT_PYTEST=TEST_NOT_RUN
LIVE_POST_REWORK=TEST_NOT_RUN
Q01_AUTHORIZED=NO
Q02_AUTHORIZED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=AUTHORIZED_VALIDATION_ONLY_OR_PRODUCT_MASTER_PHASE_DECISION
```
