# C3-T2 · Parallel MCP Discovery — Architectural Decision Proposal

**Status:** AUTHORIZED_FOR_BOUNDED_ISOLATED_EXPERIMENT_ONLY — coordination review 2026-11-15. NOT implemented; sequential stays default.
**Task origin:** `DELIA-C3-T2-R5-INT3-SUFFICIENCY-AND-PARALLEL-MCP-DISCOVERY-01`.
**Independent review:** `coordination-independent-review-2026-11-15.md` (reviewed `7df9118a8e`).
**Next task:** `DELIA-C3-T2-PARALLEL-MCP-DISCOVERY-GUARDED-EXPERIMENT-01`.

The original proposal targeted provider-level `asyncio.gather`; the subsequent source inventory **supersedes that direction**. There is one MCP provider with a synchronous per-specialist discovery loop. The sole candidate seam is bounded per-specialist concurrency inside `McpCapabilityProvider.list_groups` if all security/lifetime gates pass. This document is a proposal and does not establish production authorization.

```yaml
DECISION_ID: C3_T2_PARALLEL_MCP_DISCOVERY
RESPONSIBILITY: Governed per-specialist MCP tools/list discovery
OWNER: McpCapabilityProvider.list_groups
CONSUMERS: OperationalCapabilityOrchestrator._groups -> Application live catalog
EXISTING_EQUIVALENT: YES
REUSE_DECISION: EXTEND_EXISTING_AFTER_GATES
CURRENT_PATH: Synchronous per-specialist loop, delegated exchange + initialize + tools/list
CANDIDATE_PATH: Bounded ThreadPoolExecutor within existing MCP provider
DO_NOT_USE: asyncio.gather on sync calls; outer provider fan-out
SUBJECT_CONTEXT: Capture on caller, existing bind_subject_bearer/unbind_subject_bearer per worker in try/finally
CREDENTIALS: No shared user bearer logging; do not copy Flask request context; live Core/Domain AuthZ unchanged
TIMEOUT: Shared deadline plus PROVEN total I/O bound; per-recv timeout alone insufficient
CANCELLATION: Cooperative; queued futures cancellable; running synchronous reads not forcibly interruptible
LATE_RESULTS: Never publish results collected after turn cancellation/deadline; no leaked identity bindings
PARTIAL_FAILURE: Per-specialist errors preserved, distinguish unavailable vs absent
ORDERING: Submission-order failure reporting and deterministic catalog merging
RETRIES: One existing bounded transient retry, never multiplied or regranted
LIMITS: Existing bounded specialist registry and explicit maximum workers
OBSERVABILITY: Per-specialist durations, auth errors, timeouts, late completions, thread lifetime; secrets redacted
ROLLBACK: Sequential path default; experimental flag OFF by default
EXPECTED_LATENCY: 15.2s sequential baseline -> 5-6s candidate TARGET, not PROVEN
BLOCKERS:
  - Prove transport end-to-end deadline and worker lifetime
  - Prove no bearer crossing/leaks and cleanup after exception/cancellation
  - Prove negative auth tests, deterministic failures and serial regression
  - Replace inert catalog security assertion
DECISION: AUTHORIZED_FOR_BOUNDED_ISOLATED_EXPERIMENT_ONLY
PRODUCTION_DEPLOY: NOT_AUTHORIZED
PHASE_ADVANCEMENT: NO
```

## Dependency analysis (historical inventory — interpreted under revised decision)

- Per-provider `list_groups` calls are **independent**: no provider's
  output feeds another's input; each resolves its own delegated token
  and its own tools/list (verified in `_groups` loop and FakeProvider
  contract `list_groups(correlation_id, timeout_seconds)`).
- The **shared** pre-stage (subject session mint) already happens once
  before `_groups` — not parallelized, unchanged.
- Ordering is deterministic post-merge (dict keyed by provider:group).
- Partial failure already modeled per provider (`failures` list +
  `catalog_failure` markers surfaced to the model).

## Concurrency gate inventory (WS-B, SHA ecb464c3a9)

All findings verified against source — nothing presumed.

```yaml
SYNC_ASYNC_VERIFICATION: |
  PROVEN — the whole path is synchronous blocking I/O.
  `provider.list_groups` is a plain def; `McpCapabilityProvider.
  list_groups` (mcp_provider.py:66) loops specialists synchronously
  calling `SpecialistInterop.discover_catalog` (specialist_interop.py
  :149) → `port.list_remote_tools` (adapter.py:103) →
  `DelpiMcpTransport` over `requests`/urllib3 with a custom
  deadline_transport (per-recv inactivity bounds). `asyncio.gather`
  is NOT applicable — the only compatible fan-out is a bounded
  thread executor (concurrent.futures).

REAL_COST_SEAM: |
  PROVEN — `_groups` iterates providers, but in practice there is ONE
  mcp provider; the ~15.2s lives INSIDE `McpCapabilityProvider.
  list_groups` looping N specialists (each: delegated exchange +
  MCP initialize + tools/list, ~5s). Provider-level fan-out alone
  gains ~0. The parallel seam is per-specialist inside the provider.

TOKEN_EXCHANGE_SAFETY: |
  PROVEN-SAFE-MECHANISM — `InMemoryDelegatedTokenCache`
  (delegation.py:120) guards get/put/invalidate with
  `threading.Lock`; keys are (subject_fingerprint, resource_audience)
  so per-specialist exchanges never collide. Benign race only: two
  threads could exchange for the SAME audience concurrently → both
  tokens valid, last write wins.

  MATERIAL-BLOCKER-FOUND — `credential_for` resolves the subject
  bearer via `current_subject_bearer()` (root_composer.py:389), which
  reads `contextvars.ContextVar` + `flask.g` (auth/subject_bearer.py).
  Worker threads see NONE — a naive ThreadPoolExecutor.submit would
  make EVERY parallel discovery fail `MCP_AUTHENTICATION_FAILED`.
  Existing precedent seam: `bind_subject_bearer`/`unbind_subject_bearer`
  (created for the NDJSON worker transport) — any parallel design
  MUST capture the bearer on the caller thread and bind/unbind per
  task (or pre-resolve credentials caller-side), never copy_context
  casually (bearer lifetime must stay bounded).

CLIENT_CONCURRENCY_SAFETY: |
  PROVEN-SAFE — `transport_factory` builds a NEW DelpiMcpTransport
  per connect (adapter.py:90-97); no shared Session/pool between
  specialists. `requests`/urllib3 is thread-safe when each task owns
  its transport. `_invalidate_on_auth_failure` → cache invalidate is
  lock-guarded.

SHARED_STATE: |
  None mutable beyond the locked token cache. `list_groups` builds
  fresh `groups`/`failures` per call.

DEADLINE: |
  Shared TurnDeadline is a clock — each worker receives
  `deadline.remaining_seconds()` at dispatch; `remaining_budget`
  already clamps per-leg timeouts inside the provider loop. A hung
  call burns only its own share — but a leaked thread finishing a
  blocked recv is bounded only by its own transport deadline;
  executor shutdown must not wait indefinitely (wait=False or
  bounded join).

CANCELLATION: |
  Threads are not interruptible mid-recv — cancellation stays
  cooperative: check `_cancel_observed()` before dispatch and at
  join; in-flight calls finish on their own recv deadlines.
  `bind_subject_bearer` must be undone in finally per task so a
  cancelled worker never outlives its binding.

RETRY: |
  Existing single bounded transient retry lives in `_groups` — under
  per-specialist fan-out the retry policy belongs per task with the
  same remaining-budget condition (>15s), never widened.

PARTIAL_FAILURE: |
  Per-specialist exception → failures.append(code) — same contract;
  aggregation must preserve deterministic order (submission order,
  not completion order) so traces stay diffable.

ORDERING: |
  groups keyed `provider_id:group_id` — deterministic by key.
  Failures list MUST be emitted in specialist submission order, not
  completion order (new constraint vs sequential).

CLEANUP: |
  Transports are per-call — nothing pooled to close. Bound bearer
  tokens MUST be unbound in finally (leak = credential exposure to
  unrelated work on the pooled thread).

RESOURCE_LIMITS: |
  Fan-out width = len(specialist_ids) (small, settings-bounded);
  optional hard cap (e.g. 4) for future owner growth. Keycloak
  exchange concurrency: N parallel RFC 8693 exchanges — no documented
  limit found; N is small; risk LOW.

ROLLBACK: |
  Sequential path remains the default; parallel mode flag-gated so a
  revert is a config flip, not a code change.
```

## Gate decision matrix

| Aspect | Verdict | Evidence |
|---|---|---|
| list_groups sync/async | SYNC (blocking requests) | mcp_provider.py:66, adapter.py:103, transport.py:25 |
| Shared mutable state | Token cache only, lock-guarded | delegation.py:120-172 |
| HTTP client thread-safe | YES — per-call transport, no shared session | adapter.py:90-97 |
| Subject credential in worker | **NO — ContextVar/flask.g** | subject_bearer.py, delegation.py:215 |
| Existing binding seam for workers | YES — bind_subject_bearer (NDJSON precedent) | subject_bearer.py:35-50 |
| Timeout aborts in-flight call | Cooperative recv deadlines; per-call bound | deadline_transport.py |
| Failure of one affects others | No — isolated per specialist | mcp_provider.py:94-96 |
| Deterministic ordering | By dict key; failures need submission order | orchestrator.py:1626 |
| Cleanup on cancel | Bearer unbind in finally; transport per-call | subject_bearer.py:46-50 |

```yaml
RECOMMENDED_PATH: |
  Bounded ThreadPoolExecutor INSIDE `McpCapabilityProvider.list_groups`
  (per-specialist discover_catalog fan-out) — NOT asyncio (sync path),
  NOT provider-level (one mcp provider → no gain). Caller thread
  captures subject bearer once; each task binds/unbinds via the
  existing seam in try/finally. Submission-order aggregation;
  shared TurnDeadline; per-task transient retry under the same
  remaining-budget condition; flag-gated with sequential default.

  Alternative considered and weaker: pre-resolve all delegated
  credentials on the caller thread then fan out only tools/list —
  simpler (no binding seam needed in workers) but serializes the
  exchange portion (~40% of per-specialist cost) — still a valid
  first increment if coordination prefers minimal binding risk.

EXPECTED_LATENCY: |
  ~15.2s → ~max(specialist latencies) + merge ≈ 5–6s (TARGET, not
  PROVEN — real measurement required post-implementation).
RISKS: |
  - Credential binding bug → all-parallel auth failure (mitigation:
    seam exists + negative test)
  - Thread leak on hang (bounded by per-call recv deadline +
    wait=False join)
  - N concurrent Keycloak exchanges (small N, monitor)
  - Determinism drift in failures ordering (submission-order emit)

DECISION: SUPERSEDED_BY_COORDINATION_REVIEW
  This historical inventory proposed the experiment. The current decision
  appears at the top of this document: bounded isolated experiment only,
  subject to effective total timeout, identity isolation, and test gates.
  No production implementation is authorized.
```
