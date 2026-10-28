# 188 — DÉLIA · WP0+WP1 Causal Diagnostic — Context, Evidence, Tokens, Progress

**Date:** 2026-10-28. **Task:** `DELIA-C3-D187-WP0-WP1-CAUSAL-DIAGNOSTIC-01` (plan: doc 187). **Analyzed SHA:** `3060ab0741` (main). **Status:** DIAGNOSTIC_DONE; NO_CODE_CHANGES; LOCAL_ONLY.

## 1. Real stage inventory (code-verified, `capability_provision/orchestration.py`)

Every model call flows through `_model_stage_proposal` (L8482): identical mechanics — deadline check, stage timeout, governed in-call retry (`LLM_CALL_MAX_ATTEMPTS`), `ModelCallLedger` record. Payload per call = `instruction_content` (per-stage, 1.2k–8.2k chars; **not** the whole 56 KB resource file) + `<user_message>` + workspace block + stage `<block>` + `prior_context` (bounded client turns).

| Stage | Purpose id | Block contents | Output | Next consumer |
|---|---|---|---|---|
| Admission | `interaction_admission` | fixed ~200-ch hint | owner_surface / conversational / surface_inquiry | gate |
| Turn goal (only w/ prior_turns) | `turn_goal` | — | `_TurnGoal`: business_subject, scope_constraints, answer_requirements, class | selection, arguments, judgment, recovery |
| Group selection | `select_group` | group summaries ≤`MAX_SURFACE_CHARS`(6000) + prior_observation + business_subject + relevance_feedback | group_key | capability selection |
| Capability selection | `select_capability` (`#with_goal` folds goal) | per-capability name+desc payload + feedback | descriptor | assessment/arguments |
| Native assessment | `native_assessment` | target-group block | foreign_evidence_required | foreign selection |
| Foreign selection | `foreign_selection` | foreign group summaries | enrichment capability | foreign invoke |
| Arguments | `arguments` (instr. 8152 ch — largest) | capability + desc + **full input_schema** + owner_vocabulary + foreign_evidence + business_subject + relevance_feedback ≤`MAX_ARGUMENTS_BLOCK_CHARS`(14000) | args / missing_inputs | provider invoke |
| Provider invoke | — (deterministic) | — | discover envelope / records | candidate or render |
| Candidate selection | `select_candidate` | `[{action_id, description}]` ≤6000 — **no goal, no business_subject, no answer_requirements** | candidate by action_id | candidate arguments |
| Candidate arguments | `candidate_arguments` | candidate argument_schema + business_subject | merged args → deterministic schema validation | execute |
| Relevance judgment | `goal_evidence_relevance` | business_subject + scope_constraints + declared_requirements + records ≤`MAX_RELEVANCE_EVIDENCE_CHARS` | correspondence + mismatch_hint | recovery / render |
| Recovery | `_recover_relevance` (deterministic coordinator) | feedback payload: prior_correspondence, mismatch_hint, coverage{counts}, prior_result_preview (bounded), owner_error hint | single reselection round: select_group + select_capability + arguments + execute | relevance re-judge |
| Synthesis | `grounded_synthesis` or deterministic render | typed `EvidenceFacts` | content | user |

## 2. WP0 findings — evidence continuity

**Transferred correctly (H2 refuted for recovery):** into `_recover_relevance` — prior_correspondence, mismatch_hint, business_subject, scope_constraints, coverage{`returned_count`/`total_count`/`coverage_complete`/`explicit_empty`}, bounded prior_result_preview, prior_arguments (dedup: identical query never re-executed). Into arguments — owner_vocabulary, foreign_evidence, business_subject.

**Proven gap (H6):** `_select_candidate` block carries only `[{action_id, description}]`. The validated `_TurnGoal` (business_subject, answer_requirements — "2 products with codes") exists upstream and is projected into selection/arguments/judgment, but **not** into candidate selection. Consistent with prod T1/T2 picking `read_governed_technical_knowledge` (sounds product-relevant; no goal to discriminate vs `search_products`).

**Proven gap (H5):** recovery round unconditionally re-runs `native_assessment` with the identical question (foreign_evidence_required already established) and re-runs `select_group`+`select_capability` even when reformulation stays on the same capability.

**Truncation (H3):** fit ladders with truthful `*_omitted` markers at every block; no material loss proven. **Discovery repetition (H4):** second discover in prod turns was a distinct post-enrichment query or the single recovery round — legitimate.

## 3. WP1 — real per-stage telemetry (prod T3, 16 calls / T4.2, 19 calls; `ModelCallLedger` per-call stage+tokens+latency)

| Stage | T3 calls | T3 input | T3 output | T3 latency | T4.2 calls | T4.2 input | T4.2 latency |
|---|---|---|---|---|---|---|---|
| admission | 1 | 1,301 | 113 | 3.0s | 1 | 1,368 | 3.5s |
| turn_goal | — | — | — | — | 1 | 1,540 | 6.1s |
| select_group | 2 | 6,191 | 582 | 10.3s | 2 | 6,152 | 23.4s |
| select_capability | 2 | 3,548 | 758 | 8.3s | 2 | 3,438 | 12.7s |
| native_assessment | 2 | 2,849 | 900 | 9.3s | 2 | 3,294 | 34.7s |
| foreign_selection | — | — | — | — | 1 | 2,015 | 13.4s |
| arguments | 3 (2 err) | 4,889+ | 1,333+ | **43.4s** | 3 | 8,837 | 45.2s |
| select_candidate | 1 | 525 | 245 | 7.9s | 2 | 1,190 | 11.7s |
| candidate_arguments | 2 | 1,788 | 1,390 | 14.3s | 2 (1 err) | 1,917 | 29.7s |
| goal_evidence_relevance | 2 | 2,628 | 571 | 6.7s | 2 | 2,519 | 9.1s |
| **Total** | **16** | **~23.7k** | **~5.9k** | **~113s** | **19** | **~32.3k** | **~193s** |

Provider usage correlates per call via `stage`+attempt (status `reported`/`partial`). OpenRouter generation IDs are not carried → historical per-call correlation = `INCONCLUSIVE` (documented gap, doc 187 acknowledged).

**Progress classification:** recovery round costs ≈9 model calls / ~14–15k input tokens — it re-executes the whole semantic chain (select→assess→args→candidate→judge) with only the feedback payload added. `native_assessment` round-2 = `REDUNDANT` (identical inputs, identical decision re-made). `arguments`/`candidate_arguments` retries on `invalid_structured_output` = 16–36 s/turn pure latency cost (recoverable-retry machinery working as designed — cost proven, not logic defect).

## 4. H1–H6

| H | Verdict | Evidence |
|---|---|---|
| H1 redundant context | **INCONCLUSIVE→bounded** — per-call instruction+user+prior_turns resend is structurally required (stateless API, scoped instructions); no prefix caching exists | `_model_stage_proposal` L8610–8650; instruction sizes measured |
| H2 evidence loss | **REFUTED** | `_recover_relevance` feedback payload L9560–9720 |
| H3 truncation | **REFUTED** | fit ladders + `*_omitted` markers; unproven material loss |
| H4 discovery repeated | **REFUTED** | second discover = post-enrichment query or single recovery round |
| H5 redundant semantic calls | **PROVEN** | `native_assessment` re-run in recovery (T3/T4.2 telemetry); unconditional reselection when reformulating same capability |
| H6 goal-orientation failure | **PROVEN** | `select_candidate` block = action_id+desc only (L11340–11390); `_TurnGoal` fields not projected → wrong-candidate class in prod T1/T2 |

## 5. Local tests

- `governed_read_recovery_eval.py` (real Ollama `delia-json` + fake owner wire): all 5 scenarios terminated at `admission=surface_inquiry` (1 call each) — local model cannot drive the chain (doc-185 RC3 consistent). LOCAL_MODEL_EVAL=ran; semantics not equivalent to prod.
- Deterministic suite `test_semantic_intelligence_orchestration_recovery.py` + `test_conversational_intelligence_recovery.py`: **21/21 pass** — recovery bounded, no verbatim re-exec, dedup, contract flow verified.
- S1–S4 matrix: S1/S2/S3 flow contracts proven deterministically; semantic outcomes INCONCLUSIVE locally.

## 6. Minimal correction candidates (documentary only — WP3 input)

1. **Project goal into `select_candidate`** — add `business_subject` (+bounded `answer_requirements` summary) to the candidate block. Owner: `_select_candidate`; additive block field; directly targets the proven H6 wrong-candidate class (T1/T2 knowledge-action pick). Smallest verified-change surface.
2. **Skip `native_assessment` in the recovery round** — carry the round-1 `foreign_evidence_required` verdict into `_recover_relevance`; saves 1 call / ~1–2.2k input / 6–25 s per recovered turn. Owner: same orchestrator; deterministic carry.
3. Observation only: arguments retry latency (16–36 s on invalid output) — retry machinery is correct; improving output-contract conformance is a model/instruction matter, not this task.

## 7. A/B plan sketch (doc 187 WP4)

Baseline vs candidate on identical 4 scenarios + fixtures: same SHA lineage, same model (kimi-k3 authorized env for semantics; deterministic doubles for flow), same contracts. Metrics: BUSINESS_OUTCOME (2 correct product codes), GOAL_REQUIREMENT_COVERAGE, model calls, input/output tokens, latency, REDUNDANT_CALLS, GROUNDING, safety. No productive A/B executed.

## 8. Compliance

CODE_CHANGED=NO; PRODUCTION_CALLS=0 (telemetry read only); DEPLOY_EXECUTED=NO; no secrets/CoT persisted; phase C3 not advanced. `EXISTING_EQUIVALENT=YES` — all continuity mechanisms (`_TurnGoal`, `EvidenceFacts`, relevance_feedback, `ModelCallLedger`, fit ladders) exist; both proposals are reuse/extend of current contracts, not new abstractions.
