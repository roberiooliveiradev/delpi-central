# 56 — Full-orchestration audit, checkpoint 1: semantic ownership candidates

**Date:** 2026-10-19. **Repository:** `roberiooliveiradev/delpi-central`. **Reviewed SHA:** `8fc45e2119f3cc7b1b34a0f79bca144e5f822516`. **Path:** `delia-api/app/application/capability_provision/orchestration.py` (10,592 lines, 179 class/function definitions). **Scope:** static inspection and function references; independent runtime/live test `TEST_NOT_RUN`. **Status:** `AUDIT_FINDINGS_TO_VALIDATE`, *not an approved deletion plan*.

## Purpose and canonical constraints

User requested full code-level review to identify code taking semantic decisions away from the LLM. Preserve DÉLIA standalone, canonical phase, provider-neutral existing orchestration, Core/Domain live authority, typed schema validation, policy/confirmation/PREPARE/ACT, security, evidence/provenance, idempotency, rollback and audit. Reanchor instruction order before any future implementation. `DOCUMENTATION != RUNTIME` and `0 search results != absence`.

## First-pass identified candidates (25)

| ID | Current source line(s) | Functions/blocks | Candidate disposition | Why |
|---|---|---|---|---|
| S01 | 1331-1365 | `_COVERAGE_INQUIRY_POSITIVE/NEGATIVE; _is_information_coverage_inquiry` | `REMOVE_LANGUAGE_RULE` | regex interprets user catalog coverage; call at _select_target |
| S02 | 2887-2911 | `_GUIDANCE_{PREREQ,STEPS,CRITERIA}_CUE_RE` | `REMOVE_LANGUAGE_RULE` | keyword/regex infers requested guidance goal |
| S03 | 2914-2931 | `_guidance_intent_families` | `REPLACE_SEMANTICS` | maps user text to fixed prerequisite/steps/criteria families |
| S04 | 2356-2375 | `_PRIOR_TRANSFORM_CUE_RE / _LIVE_FACT_CUE_RE` | `REMOVE_LANGUAGE_RULE` | vetoes/activates prior reasoning by phrase |
| S05 | 2378-2403 | `_prior_transform_probe_eligible` | `REPLACE_SEMANTICS` | typed goal partly present but text cues still drive |
| S06 | 3221-3239 | `_USER_LIST_ORDINAL_PATTERNS / _user_list_ordinal` | `REPLACE_SEMANTICS` | lexical ordinal interpretation for resolver |
| S07 | 3648-3695 | `_INDEX_INTENT_CLUSTERS` | `REMOVE_FIXED_DOMAIN_VOCAB` | hard-coded dashboard/formats/schedule subject clusters |
| S08 | 3699-3722 | `_index_text_tokens/_index_cluster_hits/_tokens_stem_related` | `REMOVE_SEMANTIC_SCORING` | token/stem inference; parsing alone remains legitimate elsewhere |
| S09 | 3725-3771 | `_index_option_relevance_score` | `REMOVE_SEMANTIC_SCORING` | hand-tuned relevance scoring conflicts with semantic selection |
| S10 | 3773-3823 | `_rank_index_options_by_overlap/_index_selection_is_relevant` | `REMOVE_SEMANTIC_SCORING` | reorders and vetoes model owner-index choice by lexical score; retain owner id membership |
| S11 | 3827-3843 | `_EXTRACTION_FOLLOWUP_RE/_LIMITATION_FOLLOWUP_RE` | `REMOVE_LANGUAGE_RULE` | classifies multi-turn extraction/limitations by regex |
| S12 | 3870-3917 | `_count_covered_extraction_units/_prior_extraction_incomplete` | `REPLACE_OUTCOME_VALIDATION` | word occurrence not user-task sufficiency |
| S13 | 3826 | `_MIN_USEFUL_CONTINUITY_CHARS` | `REMOVE_QUALITY_HEURISTIC` | length is not meaningful outcome evidence |
| S14 | 3919-3957; 6881-6924 | `_recover_prior_extraction_after_invalid_index/_extraction_list_from_prior_excerpts / recover_empty_selection` | `REPLACE_FALLBACK` | cannot return list for compare and call that SUCCESS; preserve fail-closed |
| S15 | 3242-3291 | `_prior_listing_hint` | `REPLACE_TEXT_PARSING` | counts ID strings/UUID/encontrei in assistant text vs typed prior evidence |
| S16 | 2311-2353 | `_prior_excerpt_records (as evidence reconstruction)` | `REPLACE_TEXT_PARSING` | prior rendered text not authoritative structured evidence; presentation-only parsing can remain |
| S17 | 875-945; 5729+ | `_token_covered_by_user_tokens/_free_string_grounded_in_user_input` | `REPLACE_PROVENANCE_HEURISTIC` | full lexical coverage is neither authorization nor exact origin proof |
| S18 | 3548-3589; 9855+ | `_single_free_text_argument_from_input` | `REVIEW_REMOVE_FALLBACK` | copies full user sentence into single free field on deadline; allow only owner-declared passthrough |
| S19 | 3372-3390; 3425-3473 | `_resolved_values_proven/_unproven_identifier_inputs literal substring` | `REPLACE_PROVENANCE_HEURISTIC` | fail-closed id gate must remain, stronger typed source refs required |
| S20 | 9381-9385 | `_select_group singleton implicit selection` | `REMOVE_UNGUARDED_SHORTCUT` | one group does not prove user applicability; only optimize post-admission |
| S21 | 9283-9285 | `_admit_conversational_turn prior_turns skip` | `REMOVE_UNCONDITIONAL_SKIP` | blocks conversation and topic change after operational history |
| S22 | 4893-5235; 9267-9609 | `admission/group/capability/goal/native_assessment repeated decisions` | `CONSOLIDATE_EXISTING_CONTRACTS` | semantic fragmentation and model-call budget; not remove needed gates |
| S23 | 6735-6759; 9609-9650 | `optional index model probe with 2 stages+headroom` | `REMOVE_UNREACHABLE_OPTIONAL_PATH_IF_PROVEN` | 30s stage config vs approx 66s headroom makes optional path dead; owner-declared index stays |
| S24 | 4778-4793; 6761-6782 | `experimental_arguments_budget_guard` | `REMOVE_IF_UNUSED` | default false, inventory consumers and tests before removal |
| S25 | 1589-1716 | `_compare_records semantics vs comparison instruction` | `RECONCILE_CONTRACT` | model allows context_fields empty; runtime treats empty context as INCONCLUSIVE; preserve comparability safety |

## Additional responsibility relocation candidates

- Guidance: `_GUIDANCE_SECTION_FAMILIES`, `_guidance_family_for_key`, `_deterministic_guidance_content`: lexical domain/category-to-prose mapping should not replace typed model intent or owner schema; preserve honest truncation and bounded projections.
- Presentation: `_render_synthesis`, `_compose_answer`, `_FIELD_CLAUSE_LABELS`, `_business_lines`, `_format_structured`: evaluate existing shared owner/render contract before relocation; retain redaction and factual leaf accuracy.
- Pagination/personal: `_project_paginated_personal_or_count`, `_maybe_aggregate_paginated_count`: keep deterministic count/pagination and identity/AuthZ, but replace natural-language classifier where used as source of truth.
- Clarification: `_clarification_content`, `_candidate_clarification_content`: preserve safe fallback; semantic missing-information assessment must come from contract/evidence, not arbitrary text.

## Explicit preserve list

`TurnDeadline`; schema validation; live capability surface revalidation; owner-declared enum/const/default; identifier provenance gate (replace unsafe mechanism, not gate); context data trust boundary; secret redaction; Core/Domain AuthZ and business authority; governed PREPARE/ACT, confirmation, idempotency, audit, authoritative outcome; count/has_more semantics; bounded sanitization; provider-neutral ports/adapters. Structural checks, tokenization for formats and regex for *syntactic security redaction* are not semantic classifiers.

## Verification and change gate

All findings are audit hypotheses/candidates, not delete-ready. Before changes, establish per candidate: responsibility → owner → canonical authority → consumers/call sites → contract & tests → replacement/reuse decision → first failing outcome → safe migration/rollback → live generalized results. No new planner, memory, provider special-case branches or regex intent engine. Further code sweep and consolidated audit to follow in next numbered document.

```text
EXISTING_EQUIVALENT=TO_INVENTORY_FOR_EACH_REPLACEMENT
REUSE_DECISION=PENDING_PER_BOUNDARY
CODE_REMOVAL_AUTHORIZED=NO
INDEPENDENT_RUNTIME_TEST=TEST_NOT_RUN
GLOBAL_I04_ACCEPTED=NO
C3_EXECUTED=NO
NEXT=SECOND_PASS_ALL_10592_LINES_DEPENDENCY_AUDIT
```
