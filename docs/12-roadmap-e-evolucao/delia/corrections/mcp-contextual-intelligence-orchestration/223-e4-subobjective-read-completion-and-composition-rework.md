# 223 — DÉLIA · E4 R1 — complete authorized subobjective READs and authoritative composition

**Date:** 2026-11-03. **TASK_ID:** `DELIA-C3-E4-SUBOBJECTIVE-READ-TO-COMPOSITION-REWORK-01`. **Reference E4 SHA:** `0f1985217584` (verified identical to main at review). **Status:** `REWORK_REQUIRED` for complete user-facing E4 outcome; no code deployed in this coordination review. **Authority:** 16→50→17→49→51→52→21→20→25; ADR 58, doc103, docs 219–222, ledger and .cursor rules. Reanchor actual latest HEAD/status before diff.

## 1. Independent findings

- E4-impl added `_flatten_evidence_records`, `_verify_evidence_composition`, `_render_evidence_comparison`, `_compose_multi_evidence` and decomposed comparison path in `orchestration.py`. Executor reports 8/8 unit PASS, live A03 `goal=compare → subobjective_decomposition=4 → PARTIAL×4 → SOURCE_UNAVAILABLE`; no full real outcome yet.
- At reviewed SHA, `_investigate_subobjectives()` calls `_governed_owner_path(sub.goal, ..., prior_turns=(), depth=depth)` per subgoal. All failing subrequests require stage-by-stage correlation of selection, discovery, candidate binding, owner execute, outcome, deadline and provenance. The specific failing internal branch is NOT PROVEN merely by the final PARTIAL status.
- At reviewed SHA, source id uses `re.search(r"\d{4,}", sub_goal)`; this wrongly derives a factual identity from LLM-generated text and conflates sources/occurrences, violates generalized typed provenance direction. Must remove, binding source identity only from authorized owner evidence plus stable typed record/capability refs.
- At reviewed SHA, `_subobjective_attempt_result` returns SUCCESS if `contents` nonempty; a comparison requires its own full-goal coverage status and cannot claim success on single partial read. Verify live outcome contract and correct if gap proven.
- `_compose_multi_evidence` uses `_fit_json_block(... MAX_SURFACE_CHARS)`; ensure the verifier operates on complete authoritative data separately from LLM projection, explicitly detects truncated input and does not market partial result as full coverage.
- As before, `prior_turns` may resolve referents semantically but cannot supply FACT, permissions or identifier provenance. No hardcoded product codes, regex by product or bypass of VISTA/TÉO ownership.
- `FUNCTIONAL_ACCEPTANCE_CANDIDATE=NO`; mandatory G04/G05/G07/G12 remain failing/pending.

## 2. Implementation authorization and bounded causal workflow

**Implement the smallest correct generalizing fix in existing owner. Do not stop at diagnosis or return with unit-only PASS.** Do not create new planner, owner, provider, context service or registry.

**S1 Reanchor and trace:** HEAD/status, relevant doc 221/222 and source consumers; correlate for EACH subgoal the exact `_governed_owner_path` stages, arguments, discovery candidate, follow-on substantive READ invocation, status/retry budget/authorization; compare path to successful direct single-read `90260147`, `90260148`. Log sanitized typed fields, no JWT or raw company payload.

**S2 Contract gap and RED:** identify why semantically equivalent subgoal cannot traverse same legitimate discover→candidate→execute chain. Does wording lose referents? Does nested depth disable resolver? Is candidate binding absent? Is deadline spent by excess subgoals? Does all-four decomposition produce irrelevant/duplicate goals? Prove first failed boundary with one traced subgoal; write RED test for original+unrelated sibling+negative. Never assume text prompt is root cause.

**S3 Correct reuse:** adapt only existing decomposition validation, subgoal contextual request, candidate-binding or recovery mechanics as proved. Preserve model semantic decision; input is typed objective + authorized relevant identity references, not hardcoded endpoint/product. Model must not choose unauthorized operations; live owner/Domain gates remain final. Reuse model/graph/attempt machinery, no second planner.

**S4 Remove regex-derived source identity:** replace source keys from `sub_goal` regex with typed authority-backed source/reference from `SpecialistOutcome`/EvidenceFacts and verified owner record. Preserve duplicate occurrences and source cardinality. Source id collision must be explicit rejection or unambiguous separate occurrence, never silent dict overwrite. `EXISTING_EQUIVALENT`/ `REUSE_DECISION` documented per symbol.

**S5 End-to-end completeness:** use verifier for all records, not truncated LLM sample; reject fabricated pair refs, false common `10030012`, missing true common `10030015`, incorrect units/occurrences; detect per-source partial coverage and fail honestly. Synthesis should return comparison content only when verified. If parent subgoals partially succeed, do not mark top-level comparison GROUNDED/complete without evidence sufficient for requested comparison. Preserve factual selection-only ADR 58/§6.145.

**S6 Live test and refinement:** REAL Qwen3 4B via installed Pydantic AI + LangGraph, `user@local.com` authentic Keycloak/Core and real DAVI/Domain. Verify A01→A02→A03 same conversation, single-turn compare, follow-up A04, two complete structures vs deterministic oracle, tests where sub READ fails/denied/partial. Maintain budget/timeout/cancel constraints; no production deploy or unauthorized AuthZ grants.

**S7 Regression/cleanup:** full relevant suite, original/sibling/unknown/ambiguous/injected/stale evidence/duplicate units/hierarchies; count removed custom branches and wire up consumers. Persist exact SHA/config/traces and gate matrix; safe push main without staging concurrent work. No removal of safety or legitimate rollback.

## 3. Mandatory acceptance

| Gate | Must pass |
|---|---|
| SR01 | For each substantive subgoal, trace confirms real discovery/candidate/execute when needed; no empty simulated success |
| SR02 | Two authoritative complete evidence source sets obtained or explicit authorized insufficiency |
| SR03 | Typed provenance identifies sources, records and occurrences; no regex-inferred source code |
| SR04 | Full deterministic comparator correct on both real BOM trees with complete coverage, including known Qwen3 errors |
| SR05 | A03 same-session compare reaches accurate grounded answer, no mere PARTIAL×4 |
| SR06 | Single-turn comparison reaches accurate grounded answer with two accessible structures |
| SR07 | Parent Outcome contract correctly distinguishes full comparison vs individual partial reads |
| SR08 | Unrelated original/sibling/negative/denied flows preserve ownership, security, timeouts |
| SR09 | Pydantic AI + LangGraph use existing ports/state; no new planner/owner/provider |
| SR10 | Final SHA real-model test, full relevant regression and ledger evidence, commit/push verified |

**No successful terminal if SR05/SR06/SR07 failed.** If evidence reveals a contradiction with a frozen authorized owner route or other authority, STOP only affected change, report exact `ARCHITECTURE_DECISION_REQUIRED` and finish safe independent work. Use `REWORK/INCONCLUSIVE`, never invent PASS.

## 4. Devin execution prompt

**TASK_ID=DELIA-C3-E4-SUBOBJECTIVE-READ-TO-COMPOSITION-REWORK-01.** Execute document 223 fully, under 221 R1 + 222 and canonic rules. Reanchor latest main. Diagnose first failed boundary of PARTIAL×4 against proven single-read, correct the existing governed subgoal READ path instead of adding special product rules, remove `re.search(r"\d{4,}", sub_goal)` as factual source identity, derive source refs from owner evidence, verify full comparison coverage and top-level Outcome. RED→GREEN, real authenticated same-session and single-turn Qwen3/DAVI/Domain E2E, independent oracle, negative/generalization, complete regressions and cleanup. Keep iterating within authorized scope until SR01–SR10 PASS, or precise governance/external blocker. Commit + push main; report evidence, SHA, tests, deletion matrix, latency/tokens and functional verdict. **PRODUCTION_DEPLOY=NOT_AUTHORIZED.**
