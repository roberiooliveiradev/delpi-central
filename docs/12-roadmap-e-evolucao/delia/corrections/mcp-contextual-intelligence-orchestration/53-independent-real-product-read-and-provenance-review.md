# 53 — Independent real product owner READ review

Date: 2026-10-19. Reviewed main: 0d8617cbed5f1e8d0546a91f3841e9650590cd4e. Evaluated live code SHA reported: 4c4fc7d256. Sources: document 52, ledger §6.294, 4c4fc7d256 code diff. Verdict: ACCEPT_WITH_RESIDUAL for bounded live real-product owner READ; REWORK for semantic provenance guard, strict latency and multi-turn compare. Independent SSH/live replay TEST_NOT_RUN.

## Code-confirmed root cause
- Existing owner api-delpi GET /products/search (OpenAPI search_products) accepts optional description/code/group_code and pagination. Executor direct READ returns products in 33–158ms. Before change, selection and LLM-built arguments existed but optional owner-index probe was skipped because its headroom threshold (~66s) exceeds 30s global budget; subsequent gate discarded usable args before provider READ.
- The fix allows populated free-string args when _free_string_grounded_in_user_input reports overlap, or pagination-only args; empty {} remains blocked. This is bounded reuse of current Orchestrator, not a new provider integration. Reported live L1 pino ~23s, L2 olhal ~18s, L3 terminal near 30s, L4 no-match owner-grounded. These are executor-reported and represent meaningful progress.

## Critical provenance limitation
- _free_string_grounded_in_user_input uses regex tokenization and accepts ANY shared alphanumeric token with >=3 characters, or substring match. It checks lexical overlap, not semantic entailment or argument provenance. A proposed search value can share one incidental token while adding unsupported filters; a partial substring can also match. Passing this gate is not proof that every argument value was user-supplied or owner-evidenced.
- This helper is not an intent classifier but is a lexical heuristic applied as a security/evidence gate to natural-language arguments. It requires bounded REWORK or an explicit architectural decision aligned to user's instruction: LLM interprets semantics; deterministic validators check provenance/contracts, not infer meaning through token overlap. Do not remove current owner AuthZ or use free-form LLM claims as provenance. Prefer literal exact source spans or typed semantic evidence already available, with strict validation and fail-closed where unproven.
- Adversarial tests required: same incidental token but invented business qualifier; unrelated identifier sharing digits; partial word matching; paraphrase with no literal overlap; mixed owner-supplied versus user-supplied values; Unicode accents/case; renaming providers; READ versus WRITE. Current tests PASS executor-reported but do not prove these false-positive boundaries.

## Other residuals
- L5 comparison with prior records ends HTTP504 under 30s; continuity not accepted. L3 ~30s is too close to strict deadline to claim robust latency compliance across samples. Search precision pino versus TERM. PINO varies; schema-valid search can be broader than intent.
- Full delia-api pytest reported PASS, code SHA equal to deployed in execution report; independent live replay TEST_NOT_RUN. Final docs main advanced separately.
- No observed material ACT reported. No I04/C3/C4/C5/Q01 progression.

## Decision
REAL_PRODUCT_OWNER_READ_BOUNDED=ACCEPT_WITH_RESIDUAL
SEMANTIC_PROVENANCE_GUARD=REWORK
STRICT_30S_LATENCY=INCONCLUSIVE
MULTITURN_COMPARE=FAIL_SAMPLED
OWNER_DIRECT_TEST=PASS_EXECUTOR_REPORTED
INDEPENDENT_LIVE_REPLAY=TEST_NOT_RUN
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=BOUNDED_ARGUMENT_PROVENANCE_AND_MULTITURN_BUDGET_REWORK
