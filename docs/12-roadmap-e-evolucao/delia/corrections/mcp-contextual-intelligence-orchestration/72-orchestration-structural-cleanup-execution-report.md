# 72 — Orchestration structural cleanup — execution report

**TASK_ID:** `DELIA-ORCHESTRATION-STRUCTURAL-CLEANUP-01`
**Date:** 2026-10-21
**Mode:** `REANCHOR → RESIDUAL MATRIX → REUSE GATE → BEHAVIOR BASELINE → STRUCTURAL CLEANUP → REGRESSION → RESIDUAL SEARCH → REVIEW → DOCUMENT → COMMIT → PUSH MAIN → VERIFY`
**Scope:** structural hygiene of `delia-api/app/application/capability_provision/orchestration.py` only; no semantic redesign, no public-contract change, no new planner/classifier, no C3 promotion.

## 1. Reanchor

- Worktree: dedicated detached worktree at `origin/main` base `fe61449102a35d2636bd58047a019753f2ad6fd9` (`/home/analistaptd/delia-cleanup-wt`); the `main` linked worktree and the primary worktree were dirty with concurrent work and preserved untouched.
- `git fetch origin` at delivery time showed `origin/main` at `4f41f25de01d0dab3ebd7ea0142e32bfb064c996`; the two new commits touch only `controllership-finance` docs — integrated by fast-forward/rebase with zero overlap.
- Authorities revalidated in canonical order `16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25`, plus working documents 56, 57, 58, 59, 60, 67, 71, track README and ledger tail (§6.344–§6.347).
- Applicable transversal rules: `delia-execution-protocol`, `evidence-driven-execution`, `centralized-rules-first`, `clean-code-architecture-guardrails`, `english-code-identifiers`, `platform-quality-testing`, `platform-architecture-boundaries`, `platform-security-identity-authorization`, `presentation-operational-decoupling`, `contract-evolution-backward-compatibility`, `ai-external-tools-security`, `root-cause-generalized-fix`.
- Frozen state preserved verbatim: `Q01_Q03=CLOSED_WITH_RESIDUAL`, `Q03_VERDICT=ACCEPT_WITH_RESIDUAL`, `I04_ACCEPTED=NO`, `C3_EXECUTED=NO`, `B1=UNRESOLVED_FORMALLY_DEFERRED`, `MODEL_SEMANTIC_OWNERSHIP=APPROVED`, `SELECTION_ONLY_FACTUAL_SYNTHESIS=FROZEN`, budgets 30s/12s, `MATERIAL_ACT=NOT_AUTHORIZED`, `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2. Behavior baseline

- Baseline suite on clean `fe61449102` (before edits): `pytest tests/` in `delia-api` — **green** (full pass set; the worktree suite counts **1690 passed / 3 skipped** on the post-change run and the same suite was run green on the clean baseline before modifications; exact command `.venv/bin/pytest -q tests/`).
- Static baseline: `orchestration.py` had **10,248 lines** at base HEAD.

## 3. Reuse gate and residual matrix

`EXISTING_EQUIVALENT` and `REUSE_DECISION` were evaluated per candidate against real consumers (repo-wide `grep` across `app/`, `tests/`, `scripts/` — no inference from absence alone; each candidate was also checked for callers, test imports and composer wiring).

| Symbol / block | Audit anchor | Finding | Consumers | Decision | Evidence |
|---|---|---|---|---|---|
| `MAX_FOREIGN_GROUPS`, `MAX_SEMANTIC_PATH_CAPABILITIES` | S07–S10 clusters | Dead constants after semantic consolidation (single foreign group, path-cap math removed) | zero references repo-wide | **REMOVE** — `NO_LEGITIMATE_CONSUMER` | grep=0 in code and tests; suite green |
| `_INDEX_TOKEN_RE` | S07–S10 | Lexical token regex retained only as input to the removed ranking | zero references | **REMOVE** | grep=0 |
| `_BUSINESS_PAYLOAD_KEY` | S-pass-2 | Dead payload-key constant | zero references | **REMOVE** | grep=0 |
| `_guidance_intent_families(input_text)` | S02/S03 | Compat shell: ignored `input_text`, returned fixed tuple | 1 internal caller + 1 test | **CONSOLIDATE → constant** `_GUIDANCE_FAMILY_ORDER` — `BEHAVIOR_EQUIVALENT_REPLACEMENT_PROVEN` | identical output; tests updated to assert the constant |
| `_deterministic_guidance_content(input_text, …)` | S02/S03 | First param accepted and ignored after Q02-A delexicalization | 5 internal call sites + tests | **REMOVE param** — signature cleanup, projection semantics unchanged | all call sites rewired; guidance tests green |
| `_rank_index_options_by_overlap(input_text, options)` | S07–S10 | No-op compat wrapper returning owner catalog order | 1 internal caller + 3 test files | **REMOVE** — `BEHAVIOR_EQUIVALENT_REPLACEMENT_PROVEN`: callers use `_index_option_rows` catalog order directly | tests retargeted to `_index_option_rows` order assertions |
| `_index_selection_is_relevant(input_text, selected, options)` | S07–S10 | Compat-named membership check ignoring `input_text` | 1 internal caller + tests | **RENAME/SIMPLIFY → `_index_selection_is_member(selected, options)`** — same owner-membership gate | membership assertions preserved verbatim |
| `experimental_arguments_budget_guard` + `_budget_allows_arguments_propose` | S24 | Harness-only experiment; default `False`; no production consumer (composer never passes it) | only `test_i02r3a…` fixtures | **REMOVE** — `NO_LEGITIMATE_CONSUMER`; experiment retired per doc 15/ledger history | flag-on tests deleted or retargeted; `E2_tight` pins the unconditional attempt path |
| Duplicated model-invocation prelude/body in `_select_candidate` and `_propose_candidate_arguments` | S22 | Three copies of deadline check → stage timeout → request build → execute → error/timeout taxonomy → stage logging | 3 call families | **CONSOLIDATE → `_model_stage_proposal`** — `REUSE`: shared mechanics extracted; `_propose` keeps allowed-keys/`applicable` projection; candidate paths keep strict-key validation and own lineages | single `self._invoke_model.execute` site remains; 184 candidate/orchestration tests green; full suite green |
| `_budget_allows_resolver`, `_budget_allows_optional_index_probe` | S23-adjacent | Legitimate production budget gates with live callers | internal call sites verified | **PRESERVE** — real responsibility | callers present; suite green |
| `_single_free_text_argument_from_input` | S18 | Owner-declared sole-free-text passthrough | live caller at arguments resolution | **PRESERVE** | suite green |
| `_prior_transform_probe_eligible`, `_prior_supports_typed_attribute_compare` | S04/S05/S25 | Typed-goal gates — not lexical selectors | live callers | **PRESERVE** | typed-comparison tests green |
| `classify_result_intent`, `classify_personal_ticket_scope`, `unique_structural_ticket_list_capability` | B1 | Frozen residual — `UNRESOLVED_FORMALLY_DEFERRED` | external module | **PRESERVE — untouched** | B1_UNCHANGED |
| Presentation-style pure functions (`_render_synthesis`, `_compose_answer`, `_sanitize_renderable`, `_format_*`, `_guidance_section_records`, `_render_zero_candidate_discovery`) | 57 second-pass | Application-layer outcome projection + redaction, consumed by ≥8 test files directly; no distinct owner module exists | orchestrator + tests | **PRESERVE / no extraction** — moving them would create a new module purely for aesthetics and churn internal imports without reducing coupling; they already are module-level pure functions with a stable contract | no Pacote C candidate passed the extraction gates |

`REMOVAL_ALLOWED` gates applied per item: `NO_LEGITIMATE_CONSUMER` (constants, flag, regex) or `BEHAVIOR_EQUIVALENT_REPLACEMENT_PROVEN` (families→constant, rank wrapper→catalog order, param drops).

## 4. Changes applied

### Pacote A — dead/legacy removal
- Removed constants `MAX_FOREIGN_GROUPS`, `MAX_SEMANTIC_PATH_CAPABILITIES`, `_BUSINESS_PAYLOAD_KEY`, and regex `_INDEX_TOKEN_RE`.
- Removed `_guidance_intent_families` in favor of constant `_GUIDANCE_FAMILY_ORDER`; `_deterministic_guidance_content` signature drops the ignored `input_text` (5 internal + test call sites updated).
- Removed `_rank_index_options_by_overlap`; index binding now uses `_index_option_rows` owner order directly.
- Renamed `_index_selection_is_relevant(input_text, …)` → `_index_selection_is_member(selected, options)`; same exact owner-membership gate.
- Removed `experimental_arguments_budget_guard` ctor option, `_experimental_arguments_budget_guard` attribute, `_budget_allows_arguments_propose`, and the guarded skip branch (with its `budget_input_projection`/`skip_budget` decisions); the arguments proposal is attempted unconditionally, as production already behaved.

### Pacote B — model-invocation consolidation
- Extracted `_model_stage_proposal(...)`: deadline check (`TurnBudgetExhausted` → `_StageDeadlineExceeded("turn_budget_exhausted")`), stage-timeout resolution, cold-start headroom caps (`INTERACTION_ADMISSION_STAGE_CAP_SECONDS`, `CONVERSATIONAL_FALLBACK_RESERVE_SECONDS`), minimum-viable-budget fail-fast, `ModelInvocationRequest` assembly (lineage, schema id/version, expected fields, `EpistemicClass.HYPOTHESIS`, input_kind metadata), `ModelInvocationError` taxonomy (`TIMEOUT` → `_StageDeadlineExceeded("model_timeout")`), and bounded stage logging — now the single `self._invoke_model.execute` site.
- `_propose` keeps the proposal-projection layer (`allowed_keys` strip, `applicable` gate, expected-field completeness).
- `_select_candidate` and `_propose_candidate_arguments` delegate to the shared stage and keep their own strict-key validation, candidate lineages, `input_kind` metadata and candidate resolution.

### Pacote C — responsibilities
- No extraction performed: every audited candidate helper is a module-level pure projection/redaction function already inside the application layer with direct test consumers; no legitimate separate owner exists, and the extraction gates (independent responsibility + real external consumers + coupling reduction) were not met. Recorded as `PRESERVE`, not `DECISION_REQUIRED`.

## 5. Regression evidence

| Command | SHA | Result |
|---|---|---|
| `pytest -q tests/` (delia-api, baseline) | `fe61449102` clean | green (full pass set) |
| `pytest -q` on 6 touched suites (Pacote A) | working tree | **83/83 PASS** |
| `pytest -q` orchestration/selection/candidate/eval files (Pacote B) | working tree | **184/184 PASS** |
| `pytest tests/` full suite (post-change) | working tree | **1690 passed, 3 skipped** (~29.4s, exit 0) |
| `python -m py_compile orchestration.py` | working tree | SYNTAX_OK |
| Residual `grep` for every removed/renamed symbol | repo | 0 references in `app/`, `tests/`, `scripts/` |

- `TYPECHECK=N/A` — no mypy/ruff/flake8 configured in `delia-api`; static gate was `py_compile` + full-suite execution.
- `SECURITY_NEGATIVE_TESTS=PASS` — security-pinning tests (redaction, identifier provenance, membership gates, PREPARE/ACT, never-act-by-text) run inside the full suite; `test_malicious_provider_content_redacted_in_guidance`, membership rejection, and governed-write suites are green.
- `REAL_MODEL_REGRESSION=TEST_NOT_RUN` — no authorized live-model/live-provider environment in this task.
- `MATERIAL_ACT=0`.

## 6. Diff summary

- `orchestration.py`: **10,248 → 10,085 lines** (−163 net; −337 changed lines context: ~250 removed, ~90 added mostly the shared `_model_stage_proposal`).
- Test files touched: `test_q02a_semantic_consolidation.py`, `test_i02_k2_k3_output_quality.py`, `test_adaptive_capability_routing_completion.py`, `test_i02_grounded_knowledge_synthesis.py`, `test_i04_guidance_presentation.py`, `test_i02r3a_budget_and_critical_path_experiments.py` — signature/imports retargeted to the simplified contracts; two flag-only tests removed (dead path), one retargeted to pin the unconditional attempt.
- Total diff: 7 files, ~162 insertions / ~413 deletions.

## 7. Frozen-state verification

- `B1_UNCHANGED=YES` — `paginated_result_semantics.py` untouched.
- `SELECTION_ONLY_UNCHANGED=YES` — no factual free-prose path added; synthesis contract preserved.
- `AUTHORITY_BOUNDARIES_PRESERVED=YES` — Core/Domain AuthZ, owner schemas, confirmation, idempotency, postconditions, provenance gates untouched; model proposals remain hypotheses (all three stages still validate strictly before use).
- `PROVIDER_NEUTRALITY_PRESERVED=YES` — ports/adapters untouched; no provider-specific branch.
- Budgets unchanged: `GLOBAL_TURN_BUDGET_SECONDS=30`, `POST_ORCHESTRATION_FALLBACK_CAP_SECONDS=12`, stage timeouts identical (shared code path only).
- No public DTO/port/HTTP contract changed; `attempt(...)` signature, outcome fields, `PendingWriteStore`, `InvokeModel` unchanged.

## 8. Residuals

- **Material residuals:** none identified inside the accepted scope — all removed items passed `REMOVAL_ALLOWED`; the only known non-blockers remain.
- **Non-blocking residuals:** (a) render/projection helpers remain in `orchestration.py` by justified `PRESERVE` (Pacote C gates not met — no owner module exists and extraction would be aesthetic churn); (b) `REAL_MODEL_REGRESSION=TEST_NOT_RUN` per missing authorized environment; (c) `I04_ACCEPTED=NO`, `C3_EXECUTED=NO` unchanged.
- **DECISION_REQUIRED items:** none — every investigated candidate reached a disposition.

## 9. Verdict

`EXECUTOR_VERDICT=ACCEPT_WITH_RESIDUAL` recommended — bounded structural cleanup executed, proven removals only, single shared model-stage mechanism, zero public-contract drift, suite green. Final acceptance belongs to independent coordination review.
