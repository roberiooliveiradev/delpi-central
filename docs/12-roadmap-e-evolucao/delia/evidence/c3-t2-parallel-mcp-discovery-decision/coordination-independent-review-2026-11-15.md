# DÉLIA — C3/T2 · Independent coordination review — vocabulary reliability & MCP discovery gate

**Date:** 2026-11-15  
**Review task:** `COORDINATION_C3_T2_VOCABULARY_RELIABILITY_AND_PARALLEL_GATE_INDEPENDENT_REVIEW`  
**Reviewed HEAD:** `7df9118a8e2db3252cc9f859467ffcb655683325`  
**Verdict:** `ACCEPT_WITH_RESIDUAL`  
**Next bounded task:** `DELIA-C3-T2-PARALLEL-MCP-DISCOVERY-GUARDED-EXPERIMENT-01`

## Scope and observed evidence

Independent GitHub diff/document inspection of `e24e6526e6`, `40320fc5f3`, `7df9118a8e`, the canonical MCP discovery decision proposal, and the prior execution ledger. Independent runtime tests were **not run** in this review.

- **Comprehension:** existing catalog projection now distinguishes `invocation_surface`, `selector_args`, `anchor_contract`, `operation_classes`, `goal_classes`, `expected_delivery`. No new registry or authority; Application acceptor unchanged. Executor-reported real evaluation at `e24e6526e6` and `40320fc5f3`: first-accept 10/12 in each; 0 dotted-anchor failures in first run, 1 residual in second; invented goal-class 0 in second. Median 83.7s in second run vs previous sample 135.6s; attribution to this change alone is **not proven**. `ACCEPT_WITH_RESIDUAL`, residual `T2-COMPREHENSION-DOTTED-ID-ANCHOR-FLAKE=OPEN_LOW`.
- **Investigation:** handoff, shared budget and previous R2 native page-walk remain preserved per executor; `R5_MULTIPAGE_UNION=OPEN`, `INT3_OBLIGATION_DEMONSTRATION_DEPTH=OPEN_LOW`. No production or phase promotion.
- **Discovery:** the material serial seam is *within* `McpCapabilityProvider.list_groups`, per specialist, with synchronous `requests/urllib3` I/O. `asyncio.gather` on synchronous `provider.list_groups` and outer provider fan-out are **not the target**. Subject bearer is ContextVar/flask.g bound; worker threads lack it unless using existing `bind_subject_bearer`/`unbind_subject_bearer` seam. Thread-safe token cache and per-call transports are supported by code inventory, not by an independently executed threaded stress test.
- **Test caveat:** existing catalog test contains `assert "authorization" not in serialized.lower() or True`, an ineffective assertion; replace with meaningful allowed/forbidden-field assertions, without suppressing useful security phrasing.
- **Concurrency cancellation caveat:** `ThreadPoolExecutor.shutdown(wait=False)` and `Future.cancel()` do not abort an already executing synchronous HTTP read. In-flight work must be bounded by a **proven end-to-end transport/request deadline**, prevent late result adoption, clean bearer in `finally`, and have measurable/acceptable worker lifetime. A per-recv inactivity timeout alone does not establish a strict total duration.

## Coordination decision

```yaml
REVIEW_VERDICT: ACCEPT_WITH_RESIDUAL
COMPREHENSION_VOCABULARY_REWORK: ACCEPT_WITH_RESIDUAL
FIRST_ACCEPT: PROVEN_IN_SAMPLE_10_OF_12
DOTTED_ANCHOR_RESIDUAL: OPEN_LOW
INDEPENDENT_RUNTIME_TESTS: TEST_NOT_RUN
R2_PAGE_WALK: PROVEN_IN_PRIOR_SAMPLE
R5_MULTIPAGE_UNION: OPEN
INT3_OBLIGATION_DEMONSTRATION_DEPTH: OPEN_LOW
MCP_DISCOVERY_PARALLELISM: AUTHORIZED_FOR_BOUNDED_ISOLATED_EXPERIMENT_ONLY
EXPERIMENT_GATES:
  - RECONCILE_ARCHITECTURE_PROPOSAL (remove obsolete provider-level asyncio plan)
  - VERIFY_PER_SPECIALIST_SYNC_BOUNDARY
  - SUBJECT_BEARER_BIND_UNBIND_PER_WORKER
  - PROVE_TOTAL_TIMEOUT_AND_LATE_RESULT_ISOLATION
  - CANCEL_AND_RESOURCE_CLEANUP_TESTS
  - FAILURE_ISOLATION_AND_STABLE_ORDER_TESTS
  - REPLACE_INERT_SECURITY_ASSERTION
  - SERIAL_DEFAULT_AND_ROLLBACK_FLAG
  - ACTUAL_SEQUENTIAL_VS_PARALLEL_LATENCY_AND_AUTH_TESTS
TWO_AGENTS: PRESERVE_EXPERIMENTAL
THIRD_FOURTH_AGENTS: NOT_AUTHORIZED
PRODUCTION_DEPLOY: NOT_AUTHORIZED
PRODUCTION_PARALLELISM: NOT_AUTHORIZED
PHASE_ADVANCEMENT: NO
NEXT: DELIA-C3-T2-PARALLEL-MCP-DISCOVERY-GUARDED-EXPERIMENT-01
```

## Execution boundary

The next task may implement the smallest **isolated, flag-gated experimental** per-specialist fan-out **only after** documentation-first inventory and safety proofs; a failed safety/timeout gate yields `ARCHITECTURE_DECISION_REQUIRED` and **no parallel implementation**. Existing sequential implementation remains the default. All writes or unsafe capability exposure are forbidden. Real evaluation on fixed SHA/config is required; missing evidence stays `INCONCLUSIVE/PENDING`. No production deploy or phase change.
