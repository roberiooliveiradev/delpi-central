# 199 — LangGraph B1 production activation, legacy fallback and bounded validation

TASK_ID: `DELIA-C3-PLUGGABLE-ORCHESTRATION-LANGGRAPH-PRODUCTION-ACTIVATION-01`
TYPE: Production promotion (product-owner authorized), conditioned on
mandatory safety/contract gates.
DECISION OWNER: Product owner authorization (adopt B1 as default
production engine, retain Engine A as selectable legacy). This document
records execution evidence; it does not extend the authorization.
EXECUTED_AT: `6fc0d7cb98` (engine-selection implementation) — local
deployed-runtime evidence captured on that image.

## 1. Canonical reanchor

- BASE_HEAD: `181b238da8` → `b385380924` (concurrent api-delpi LMP +
  controllership-finance work landed between sessions; no delia-api
  drift).
- FINAL_HEAD (implementation): `6fc0d7cb98`, pushed and verified on
  `origin/main`.
- Concurrent local commit `5c7505b092` (controllership-finance docs)
  landed atop `6fc0d7cb98` during this task — preserved, not mine.
- Working tree retains unrelated uncommitted concurrent changes
  (engineering-api, helpdesk-api) — only task-owned files staged.
- Phase: C3 unchanged. No phase advancement inferred from the
  authorization.

## 2. Contract and ownership review

- RESPONSIBILITY: production orchestration-implementation selection.
- OWNER: DÉLIA composition root (`root_composer`).
- EXISTING_EQUIVALENT=YES → REUSE_DECISION=EXTEND.
- No new registry, port, planner, governance engine or composition
  mechanism. `SupportsGovernedCapabilityAttempt` remains the only
  application-facing contract; the adapter stays under Infrastructure
  and receives governed gates (`SupportsGovernedStageGates`) by
  injection — the governed primitive implementation is still
  `OperationalCapabilityOrchestrator` (accepted residual from Task 03).

## 3. Engine selection (AC01–AC03, AC09–AC11)

`DELIA_ORCHESTRATION_ENGINE` resolved once per application composition
by `_resolve_orchestration_attempt(engine_name, gates)`:

| value | resolves to | semantics |
|---|---|---|
| `langgraph` (default) | `LangGraphCapabilityOrchestrator(gates, recovery_reuse_enabled=True)` | B1 |
| `delia` | the gates object itself (Engine A) | legacy rollback |

- Unknown value → `ValueError` at startup validation; nothing is
  silently selected (fail-closed, AC10).
- Selection is backend configuration only. Request body, confirmation,
  provider/MCP metadata, model output and workspace context have no
  path into the resolver (P4/P5 verified by the route's
  `ALLOWED_BODY_KEYS` allow-list — `input`, `context`, `confirmation`,
  `workspace`, `max_execution_stage`, `command` — plus P4/P5 tests).
- One engine executes one turn; no dual execution, no per-request
  replay (AC03/AC11 — no fallback path exists in code).
- The LangGraph import is lazy inside the resolver, so `delia` starts
  even when the framework package is absent (rollback independence).

## 4. Dependency promotion

- `langgraph==1.2.16` promoted to `delia-api/requirements.txt` with the
  exact pinned transitive tree resolved from the previously validated
  eval environment: `langchain-core==1.7.1`,
  `langchain-protocol==0.0.20`, `langgraph-checkpoint==4.3.1`,
  `langgraph-prebuilt==1.1.1`, `langgraph-sdk==0.4.10`, `ormsgpack`,
  `pydantic==2.14.1` (+ `pydantic-core`, `typing-inspection`,
  `annotated-types`, `xxhash`).
- `requirements-eval.txt` slimmed to the eval-only delta.
- Scope held: no agents, vector stores, model providers, LangGraph
  Cloud, external tracing, or framework persistence.
- Verified inside the built image: `pip list` shows exactly the pinned
  set.

## 5. RED → GREEN evidence

`tests/test_engine_production_selection.py` (P1–P12 + composed-path
integration): genuine RED (`_resolve_orchestration_attempt` absent)
then 13/13 GREEN covering default=B1, legacy selection, fail-closed
config, no user/provider selection, single engine per turn, no
automatic replay, injected-gates consumption, request isolation,
cancellation/deadline, rollback, sanitized engine identification, and
the real composed `HandleInteractiveConversationTurn → contract →
LangGraph adapter` path.

Three pre-activation frozen-decision guards
(`test_engine_b_architecture_isolation.py`,
`test_governed_attempt_contract.py`) were updated to assert the new
invariants — authorized decision change, not expectation masking:
lazy import isolation, exact scoped pins, config-gated selection.

## 6. Safety verification (§9–§11)

- Contract conformance: A 43/43, B0 43/43, B1 43/43.
- Full regression on the candidate: **2603 passed, 2 failed,
  3 skipped**. The 2 failures are the unchanged pre-existing
  environmental pair recorded since Task 04/05
  (`test_cri_instruction_variant_carries_requirements_clause`,
  `test_infra_and_env_carry_no_direct_delpi_wiring`) — verified to
  predate the candidate, touch no release-critical contract.
- Architecture Phase-3 audit: PASS; backend-boundary audit: 0 findings.
- Request isolation, cancellation, budget, PREPARE/ACT, idempotency
  and observability suites: all green (carried by the full sweep).

## 7. Production deployment evidence (local runtime)

- Image: `infra-delia-api:latest`,
  digest `sha256:62519548c03433f317fd93c7bca7f2d6296a8c348581f6bab09a1fdbd5dd680f`,
  code `6fc0d7cb98`.
- Deployed via established compose path
  (`docker-compose.dev.yml` + `docker-compose.minimal.yml`,
  `delpi-delia-api` container).
- `DELIA_ORCHESTRATION_ENGINE=langgraph` confirmed in-container;
  resolver exercised in the deployed runtime: `langgraph` →
  `LangGraphCapabilityOrchestrator`, `delia` → gates (Engine A),
  unknown → fail-closed `ValueError`.
- Health 200; startup clean; zero unhandled errors in logs.

## 8. Rollback (AC15)

Executed and reversed during this task:

1. `DELIA_ORCHESTRATION_ENGINE=delia` + compose `up -d` → container
   recreated, `Settings().orchestration_engine == 'delia'`, health 200,
   no business action replayed (rollback is a controlled restart, not
   a per-request switch).
2. Restored `langgraph` → health 200, zero unhandled errors.

ROLLBACK_AVAILABLE=YES, ROLLBACK_TESTED=YES, ROLLBACK_EXECUTED=YES.

## 9. Bounded production comparison (§14–§15)

3 paired READ cases, 6 executions, sequential engine switch (no
request-level selection added). Real `delia-json:latest` (3.1B,
Q4_K_M) on local Ollama; provider-reported tokens from
`result.observability`. Model nondeterminism (Task 05 finding) limits
semantic parity — the comparison measures contract/cost equivalence,
not answer equality.

| case | engine | HTTP | grounding | calls | in/out tok | latency | stages reach |
|---|---|---|---|---|---|---|---|
| C1 simple lookup | B1 | 200 | NON_GROUNDED | 5 | 10637/145 | 13.1s | native_assessment→foreign_selection |
| C1 | A | 200 | NON_GROUNDED | 5 | 10644/166 | 9.5s | same chain |
| C2 multi-result | B1 | 200 | NON_GROUNDED | 5 | 10582/165 | 8.0s | same chain |
| C2 | A | 200 | NON_GROUNDED | 5 | 10586/169 | 7.0s | same chain |
| C3 contextual | B1 | 200 | GROUNDED | 7 | 12439/168 | 10.9s | index_select + real MCP owner call |
| C3 | A | 200 | NON_GROUNDED | 6 | 11863/166 | 6.3s | same chain, no owner call |

Findings:

- Stage-sequence parity: B1 executes the identical governed stage
  chain (admission → turn_goal → select_group → select_capability →
  native_assessment → selection → owner path) — verified through the
  real deployed `HandleInteractiveConversationTurn` path.
- Contract parity: same response shape, same typed outcomes,
  provenance populated on grounded execution (C3-B1 shows a real MCP
  `get_product_guide` call via the TEO specialist with complete
  provenance: correlation_id, sources, specialist_id).
- Cost parity: ~2.1–2.4k input tokens per call on both engines; the
  ±1 call deltas are model retry stochasticity
  (`invalid_structured_output` on the 3.1B), not engine overhead.
- No recovery window appeared on either engine (all E2–E6 counters 0)
  — consistent with Task 05's real-model finding.
- C3 grounding divergence (B1 grounded, A not) is semantic selection
  by the same model on near-identical premises — a model-capability
  observation, not a sequencing defect; both failed closed safely
  where they did not ground (no fabrication on any turn).

## 10. Post-deployment observation (§16)

Bounded check on the live container: startup clean, `/health` 200,
authenticated turns return 200 with typed outcomes, invalid structured
output retries remain bounded by the existing attempt policy, no
duplicate execution, no write governance anomaly, no unexpected token
consumption (per-call cost matches Engine A within noise).

## 11. Limitations

- Runtime is the local development stack, not the production host —
  "production activation" here means the shipped code path, image and
  configuration are production-selected and verified on the runtime
  available to this task; environment promotion of the real host
  remains its own authorized step.
- The dev LLM endpoint drifted to an external provider (refused
  outside production by `llm_egress_blocked_reason`); the comparison
  used a runtime override to local `delia-json` — no repo/env file
  change.
- 3.1B model nondeterminism prevents exact semantic parity claims;
  token totals are provider-reported.
- Reuse never triggered on real traffic yet — B1's reuse path remains
  load-bearing on S11-level synthetic evidence plus conformance.

## 12. Production recommendation

B1 is the active default engine on the deployed runtime with a tested
config-select rollback to Engine A, full conformance, clean audits,
stage/cost/contract parity on real authenticated turns, and zero
observed governance regression. Recommendation: keep `langgraph` as
the default; collect `recovery_opportunity` counters on real traffic
(the next bounded step from Task 06) before any keep-or-retire
decision on the reuse path itself.

UNRESOLVED: eligibility frequency on real traffic (per-turn counters
now flow in production responses; cross-turn aggregation remains a
separately authorized step).
