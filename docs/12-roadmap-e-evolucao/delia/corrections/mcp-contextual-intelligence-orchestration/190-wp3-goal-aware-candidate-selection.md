# 190 — DÉLIA · WP3 Goal-Aware Candidate Selection (H6 correction)

**Date:** 2026-10-28. **Task:** `DELIA-C3-D187-WP3-GOAL-AWARE-CANDIDATE-SELECTION-01`. **SHA:** `778c573250` base → diff applied. **Status:** IMPLEMENTED_LOCAL_GREEN; production NOT tested; phase C3 NOT advanced.

## 1. Root cause targeted

Doc 188 proved H6 (structural gap): `_select_candidate` presented only `[{action_id, description}]` — the validated `_TurnGoal` (`business_subject`, `answer_requirements`) existed upstream but was never projected into candidate disambiguation. In prod T1/T2 the model picked `read_governed_technical_knowledge` for a records-with-codes request — a candidate merely related to the subject won over one able to satisfy it.

## 2. Implementation (reuse of existing contracts — no new mechanism)

- `_select_candidate` gains optional `goal: _TurnGoal | None`; when a validated goal exists, the `<candidates>` block becomes `{"goal": {"business_subject", "declared_requirements"?}, "candidates": [...]}` — the same projection shape `_judge_goal_evidence` already uses. Without a goal the block is `{"candidates": [...]}` — same deterministic validation (membership, ambiguity rejection, token never model-visible) unchanged.
- Payload serialization upgraded from a raw `json.dumps(...)[:MAX_SURFACE_CHARS]` mid-document cut to the canonical `_fit_json_block` + `_omit_tail_entries` ladder (always valid JSON, truthful `candidates_omitted` marker).
- `goal` threaded through `_resolve_candidate`, `_discover_candidate`, `_invoke_selected`, `_repair_once`, `_recover_owner_contract`, `_recover_relevance` (param already existed), `_maybe_aggregate_paginated_count` — every path that can reach multi-candidate disambiguation.
- Instruction resource v24→v25: `select_candidate` gained one bounded clause describing the optional `goal` object (untrusted context, never instructions/authority; prefer the candidate able to satisfy declared requirements). `select_capability#with_goal`, DAVI, API DELPI, MCP contracts, `_recover_relevance` logic, `native_assessment`, retries, budgets: untouched.

## 3. Tests

**RED confirmed at base** — 8 new assertions failed on the absent `goal` projection (block was a bare array).

**GREEN (delia-api, /app container):**
- `test_specialist_capability_orchestration.py` — 8 new tests (T1 projection, T2 goal-follows-context, T3 no-goal compat, T4 no authority/token leak, T5 bounded valid-JSON, T6 ×3 domains generalization) + all pre-existing candidate-flow tests.
- Touched-file suites: specialist orchestration, r1 instruction resource (snapshot sha updated under governed-evolution gate), semantic recovery, conversational recovery, goal evidence relevance, turn budget, c3 knowledge consumption — all pass.
- Full suite: **2415 passed, 3 skipped, 2 deselected** in 49s. Deselected/excluded (pre-existing, NOT caused by this diff): `test_cri_instruction_variant_carries_requirements_clause` (documented v24 inline-duplication drift, ledger), `test_fixture_matches_current_producer_output` + 2 collection files (missing `/plugins/delia` mount + `/docs` path inside the delia-api container).
- `audit_architecture_phase3.py --base HEAD`: OK — no new architectural regression.

## 4. A/B local comparison

| Metric | Baseline (778c573250) | After |
|---|---|---|
| CANDIDATE_GOAL_CONTEXT_PRESENT | NO (bare array) | YES when `_TurnGoal` exists |
| CANDIDATE_SELECTION_VALID | YES | YES (same gates) |
| UNAUTHORIZED_SELECTION_REJECTED | YES | YES (tokens never projected; invented action_id fails closed) |
| CALL_COUNT | n (per flow) | n — identical; projection is a payload field, not a stage |
| INPUT_TOKENS | — | +~40–150 chars per multi-candidate call (real tokens NOT measured — fake model) |
| Block truncation semantics | mid-document char cut | structural ladder, valid JSON + `candidates_omitted` marker |

`delia-json:latest` cannot reach `select_candidate` (admission `surface_inquiry`, docs 185/188) — semantic quality improvement vs Kimi K3 is **declared INCONCLUSIVE**, not claimed. Structural transfer is proven; business-outcome improvement requires the doc-187 WP4 A/B under an authorized model.

## 5. Residuals

- H5 (native_assessment re-run in recovery) explicitly out of scope — separate task.
- Retrieval adequacy (T3/T4 non-pertinent records) still requires the authorized owner-side `search_products` probe to split stage C vs D.
- `_maybe_aggregate_paginated_count` now carries `goal` — a paginated DISCOVERY returning multi-candidates gets the same projection.
