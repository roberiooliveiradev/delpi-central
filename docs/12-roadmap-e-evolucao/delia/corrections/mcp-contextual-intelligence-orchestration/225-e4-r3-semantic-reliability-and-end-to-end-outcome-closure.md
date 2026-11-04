# 225 — DÉLIA · E4 R3 — Semantic reliability, stage ownership and final business outcome closure

**Date:** 2026-11-03. **TASK_ID:** `DELIA-C3-E4-R3-SEMANTIC-RELIABILITY-AND-OUTCOME-CLOSURE-01`. **INPUT_SHA:** `61087a87e5`, verified identical to `main` in coordination review. **STATUS:** `REWORK_REQUIRED`, mandatory client-side grounded comparison not consistently achieved. **PRODUCTION_DEPLOY=NOT_AUTHORIZED**.

## 0. Reanchor and authority

Before any implementation: actual HEAD/git status/origin/main, Project Instructions/.cursor, 16→50→17→49→51→52→21→20→25, architecture technical doc 02, product doc24, thematic docs ADR58, 103, 187, 189, 191, 213, 219–224, ledger. Identify CURRENT_PHASE, NEXT and CP/RQ on fresh HEAD. In conflicts STOP affected part `EXECUTION_DRIFT`/`ARCHITECTURE_DECISION_REQUIRED`; do not alter frozen synthesis or authorization. No new planner, provider, state store or agent tool loop.

## 1. Independent review of R2

- E4-R2 executor reports live two-tree comparison composition and HTTP 200 to client in some runs (117.8 s and 59.4 s). Other runs fail with `owner_path_unbound` / empty decomposition / NON_GROUNDED despite comparable request. **Variability is observed; root cause cannot be reduced to model capability alone without stage-controlled replay.**
- Main at `61087a87e5` confirms `_investigate_subobjectives` concurrent execution via `ThreadPoolExecutor(max_workers<=4)` and `contextvars.copy_context()` with tracker mutations on main thread. This establishes implementation shape, NOT safety under concurrency, immutable shared-state, cancellation, Core live AuthZ, checkpoint or token budgets.
- Main confirms `sources` keyed by owner root code and positional `#len(sources)` for collisions; `sources=3` is not proof that the two requested entities were completely and uniquely bound. Require target-set coverage from authorized typed refs, not count only.
- Current subgoal decisions remain model-proposed. An empty `subobjectives` response can legitimately fail closed, but a valid comparison request with two authorized readable targets should not need arbitrary redundant analytical subgoals to satisfy read→verify.
- Security SEC-01 accepted **as executor-reported with residual**: delegated token bound to subject fingerprint/resource and TTL, cached within MCP path only. A valid bearer does not by itself prove live Core/Domain authorization or immediate revocation. Preserve live `_policy_invocable` and owner gates and document revocation limitation. No auth policy changes.
- Latency 59.4–117.8 s touches ~120s gateway limit. Do NOT increase nginx timeout or generic retries by default. The documented PO budget doc103 max 300s is a turn safety ceiling, not a promise of client-delivered response under 120s gateway.
- G04/G05/G07/G12 remain `INCONCLUSIVE/FAIL` for consistently accurate, grounded, client-visible result; no functional acceptance.

## 2. Causal hypotheses and tight A/B experiments

Treat these as competing hypotheses, not truths:
H1 stage context/instruction overbreadth causes malformed or empty `subobjectives`;
H2 Qwen3 4B has inadequate structured-output reliability for current schema/prompt;
H3 decompose model proposes more/incorrect subtasks, causing owner-bound failure and wasted calls;
H4 schema/validation or response interpretation loses valid proposals;
H5 missing cross-turn referent binding / typed target propagation makes owner selection unbound;
H6 concurrent shared invocation state, model capacity/resource contention, budgets or token exchange makes identical work variable;
H7 incomplete source-to-requested-target reconciliation or factual rendering causes apparent success without correct outcome.

**S1 CONTROLLED replay:** same final request, same `prior_turns`, same stage, same instruction, same expected schema, same catalog, same model, same generation settings; repeat >=5 (prefer >=10) without changing code/model. Capture exact sanitized valid/invalid structured output or safe hashes, stages, chosen subgoal targets, missing fields, provider errors, and stop reason. Separate `admission`, `turn_goal`, `decomposition`, `owner_group`, `candidate`, `arggen`, `composition`, `renderer/outcome`. Use controlled replay only for hypothesis isolation, real authenticated E2E for acceptance.
**S2 paired stage variants:** change one dimension at a time: (a) stage-admissible bounded prior context; (b) current Pydantic AI structured-output strategy/validation compatible with installed runtime; (c) instruction/schema simplification preserving semantic intent and source refs; (d) identical subgoals with sequential vs concurrent governed READs to isolate model/provider contention. Ensure tests for original, sibling, unknown, injected, cross-user. Do not invent regex/fixed code routes.
**S3 model A/B only if justified:** if 4B remains demonstrably unreliable under correct schema/context, compare an available and approved larger local model under identical stages/evidence/limits on current hardware. Record model availability, quantization, input/output tokens, proposal validity, business outcome, p50/p95 and security. No automatic production model switch or external provider. If no approved larger model is actually present, mark `TEST_NOT_RUN`; do not invent hardware/cost or claim bigger is automatically better.
**S4 decision:** choose the smallest provably reliable framework-native/generalizable correction. Increase retries ONLY if a bounded A/B shows meaningful success improvement without gateway overrun and within doc103. A full 300s application safety cap does not authorize a 300s HTTP response behind a 120s gateway.

## 3. Generalizable semantic graph composition contract

**Owner:** DÉLIA Application/governed orchestration. **Framework mechanics:** Pydantic AI for stage inference/typed output and existing LangGraph state/fan-in where safe; existing `InvokeModel` port retained. **Authority:** Domain owner READ + Core AuthZ, deterministic Evidence verifier and Outcome. **Target behavior:**
- The semantic model proposes comparison objective and typed target/source references; a proposal is not binding until deterministic validation against real authorized context and owner data.
- For two distinct, identifiable authorized source targets, a comparison generally needs two evidence READs and then verification/compose, not a model-invented extra `compare` subgoal run through foreign analysis. This is a bounded orchestration policy based on typed objective/validated target-set cardinality, NEVER hardcoded product identifiers, owner branch or lexical trigger.
- Do not force decomposition when existing validated evidence is sufficient; otherwise investigate only missing authorized source evidence. Do not shortcut genuinely owner-owned analytics (VISTA/TÉO) when the user's request requires that separate authority.
- Each subgoal is a **typed independent READ objective** with validated target reference and expected evidence shape when supported by existing contract; passing a naked arbitrary natural-language subgoal through all stages is a candidate source of churn, but must be validated by evidence. Reuse existing candidate-token/discovery→execute path. Any new public contract demands versioning and gates.
- Composition input needs exactly the relevant authoritative target set with evidence completeness and scope, independent of the number of collected extra sources. Duplicated source codes across owners/occurrences cannot be conflated. Comparison completeness is evaluated against intended target coverage, not `len(sources)>=2` alone.
- The verifier computes source-backed differences, including repeated hierarchical nodes, units, quantities, and source refs. Reject known hallucinated pair `10030012` falsely common and ensure `10030015` common is not omitted; model candidate remains HYPOTHESIS.
- Existing `_subobjective_attempt_result` top-level outcome and semantic correctness must distinguish partial supporting reads from complete requested comparison. Final factual prose remains deterministic under ADR58/§6.145.

## 4. Concurrency, security and cancellation gates

- Audit actual shared state accessed from worker `_governed_owner_path`: `self` members, model provider concurrency, token/call ledgers, ContextVars, cancellation/turn deadline, cache and owner AuthZ. Verify graph/checkpoint ownership, idempotent reads, source results stable ordering, race-free tracker and no deadlock. `copy_context()` is transport of context variables, not a proof that downstream shared objects are thread-safe.
- Compare current ThreadPoolExecutor fanout to installed LangGraph `Send`/fanout equivalents; `EXISTING_EQUIVALENT=YES/PARTIAL` and `REUSE_DECISION=REUSE/EXTEND/REMOVE`. Keep worker pool only if demonstrably smaller/safe as infrastructure mechanics of existing bounded graph; remove duplicated scheduler semantics if LangGraph already covers them legitimately, with test parity.
- Check cached delegated bearer is never usable in a new HTTP request that failed upstream auth; Core live authorization and Domain final rule remains required. Verify subject/audience/expiry/revocation negatives. Never change RBAC for test.
- Cancellation/disconnect remains residual; no unbounded work or continued retries after cancel. Test stream terminal delivered before gateway timeout or honest bounded terminal, no fake progress/heartbeats.

## 5. Implementation steps and mandatory acceptance

**E4-R3.S1:** Reanchor; freeze per-stage trace and exact acceptance questions and reference oracle. Classify observed failure per stage and hypothesis; do not blame generic model until stage evidence.
**E4-R3.S2:** RED fixtures from actual sanitized traces: empty/malformed subgoals, owner_path_unbound, invalid candidate/provenance, extra redundant foreign subgoal, missing requested target, repeated codes, exhausted time budget, concurrency race.
**E4-R3.S3:** Implement minimal correction to existing stage/proposal/typed target/graph fan-in/Outcome boundaries; no new planner/provider; remove now-redundant local mechanics only with consumer proof. Re-run unit, stage and integration tests.
**E4-R3.S4:** Real E2E on final SHA: `user@local.com` + real Keycloak/Core AuthZ + DAVI Domain + local Ollama Qwen3/Pydantic AI/LangGraph, A01→A02→A03 + corrected follow-up, and single-turn two-tree comparison. No stale corpus or synthetic oracle in user-facing run.
**E4-R3.S5:** Verify deterministic oracle correctness, client-visible formatted response, actual HTTP/NDJSON terminal before gateway, latency/token counts and all negative security/scope tests. Run repeat matrix rather than a single lucky success; 5 repeated original and 5 sibling runs minimum if environment available, explicitly report any failures and reasons. Do not suppress model errors.
**E4-R3.S6:** Full relevant regression on evaluated/final SHA and residual search; document removed/added symbols and actual consumer/wiring; ledger update, safe push main. Reviewer issues independent acceptance.

**Acceptance required:**
1. `MODEL_STAGE_RELIABILITY`: repeated valid typed proposals or safe stage recovery with provenance, not merely overall HTTP 200.
2. `TARGET_SET_COVERAGE`: correct validated two source identities and authorized full evidence, no lost, duplicated or misjoined source.
3. `CONCURRENT_SAFE`: worker/graph state, AuthZ and budgets proven under contention.
4. `CLIENT_DELIVERED`: both same-session and single-turn grounded comparison arrives to user before gateway closure, with useful margin in typical/worst-case measured trials.
5. `BUSINESS_CORRECT`: answer agrees with deterministic full-tree oracle and clearly represents limitations.
6. `GENERALIZATION`: sibling targets, same/different owner, correction, unknown, partial, revoked and injected context must not hallucinate facts or bypass policy.
7. `NO_AUTHORITY_DRIFT`: model cannot authorize; no implicit owner bypass, no external Chat runtime, no new planner.
8. `G04/G05/G07/G12`: must all PASS on final SHA/config for `FUNCTIONAL_ACCEPTANCE_CANDIDATE`.

**Terminal verdict:** `FUNCTIONAL_ACCEPTANCE_CANDIDATE` only when mandatory gates pass; otherwise `REWORK` / `INCONCLUSIVE` / precise `ARCHITECTURE_DECISION_REQUIRED`. No production deployment, no silent model switch, no reset of frozen budget/authority rules.

## 6. Devin execution contract

**TASK_ID=DELIA-C3-E4-R3-SEMANTIC-RELIABILITY-AND-OUTCOME-CLOSURE-01.** Execute document 225 in full. Do not conclude that Qwen3 is the cause solely from variable outcomes. Reproduce and classify exact failing stages with paired controlled replays, run framework-native schema/context improvements with one-variable-at-a-time A/B, reuse or simplify existing graph/state/typed targets, remove redundant subgoals only through validated semantic objective policy, and make client-visible grounded single/multi-turn comparison reliable and correct. Examine shared-state concurrency and AuthZ. Run repeated real Qwen3+DAVI+Keycloak/Core full-tree E2E and independent deterministic oracle on final SHA. Only benchmark larger local model after showing 4B insufficient under correct conditions, and never switch production without approval. Full regressions, docs/ledger, commit/push main, no prod deploy. Return FUNCTIONAL_ACCEPTANCE_CANDIDATE only after G04/G05/G07/G12 and safety pass; otherwise precise blockers with evidence and completed independent work.
